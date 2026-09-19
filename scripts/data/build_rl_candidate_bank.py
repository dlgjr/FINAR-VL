#!/usr/bin/env python3
"""Build FINAR-VL RL candidate data from Finance World, existing QA and Bad Cases.

The script constructs data only. It does not run rollout profiling or quality scoring.
It writes two candidate banks:

  data/synthetic/rl_candidates/reasoning.jsonl
  data/synthetic/rl_candidates/generation.jsonl

Construction routes:
  1) existing: strip assistant targets from existing SFT/QA and keep hidden gold;
  2) reasoning: sample Finance World facts, determine gold first, then render questions;
  3) generation: build coherent evidence bundles, then ask Qwen235 to create a new
     open-ended question + grounded reference answer;
  4) badcase: use task_type/error_type/scenario_tags only as construction constraints,
     and build new questions from new Finance World evidence.

The output fields are compatible with the repository's RL preparation pipeline.

The reasoning route also contains an Agent-World-inspired graph synthesizer:
  graph skeleton -> executable financial program -> hard distractors -> question rendering.
The difficult samples are hard because of evidence topology, multi-hop operators,
period/scope/metric alignment and distractors, not because of obfuscated wording.
"""
from __future__ import annotations

import argparse
import ast
import base64
import hashlib
import io
import json
import math
import os
import random
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from typing import Any, Iterable, Iterator, Mapping, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[2]
FINANCE_WORLD = PROJECT_ROOT / "data" / "synthetic" / "finance_world"
DEFAULT_FACTS = FINANCE_WORLD / "graph_facts.jsonl"
DEFAULT_EDGES = FINANCE_WORLD / "graph_edges.jsonl"
DEFAULT_BADCASE = PROJECT_ROOT / "data" / "synthetic" / "badcase_flywheel" / "classification.jsonl"
DEFAULT_OUT = PROJECT_ROOT / "data" / "synthetic" / "rl_candidates"
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}
NUMBER_RE = re.compile(r"[-+]?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?")
YEAR_RE = re.compile(r"(?<!\d)(20\d{2})(?!\d)")
PROGRAMMATIC_VERIFIERS = {
    "numeric", "numeric_final", "composite_numeric", "single_choice",
    "multiple_choice", "true_false", "page_numbers",
}
GENERATION_TASK_PREFERENCES = (
    "financial_report_analysis", "financial_risk_analysis", "financial_data_interpretation",
    "document_explanation", "document_comparative_explanation", "document_inference",
    "financial_summarization", "document_summarization", "summary_announcement",
    "business_strategy_analysis", "industry_analysis_and_competition", "industry_trend_inference",
    "risk_sentiment_policy", "investment_advice_strategy", "compliance_safety_suitability",
    "research_report_opinion_qa", "financial_audit_fundamentals", "accounting_audit_reasoning",
)
FINANCIAL_FORMULA_PAIRS = {
    "gross_margin": ("gross_profit", "revenue"),
    "net_margin": ("net_profit", "revenue"),
    "current_ratio": ("current_assets", "current_liabilities"),
    "debt_ratio": ("total_liabilities", "total_assets"),
    "cash_conversion": ("operating_cash_flow", "net_profit"),
    "roe": ("net_profit", "equity"),
    "roa": ("net_profit", "total_assets"),
    "segment_contribution": ("segment_revenue", "revenue"),
}

BADCASE_REASONING_ERRORS = {
    "visual_ocr_number_error", "chart_value_reading_error", "table_header_error",
    "table_row_column_alignment_error", "table_merged_cell_error", "chart_axis_error",
    "chart_legend_series_error", "candlestick_ohlc_error", "period_confusion_error",
    "scope_confusion_error", "metric_confusion_error", "statement_line_item_error",
    "segment_confusion_error", "unit_scale_error", "currency_error", "sign_direction_error",
    "baseline_reference_error", "entity_confusion_error", "formula_selection_error",
    "arithmetic_error", "ratio_percentage_error", "aggregation_error", "reconciliation_error",
    "multi_step_reasoning_error", "comparison_error", "ranking_error", "temporal_reasoning_error",
    "conditional_logic_error", "fact_verification_error", "choice_mapping_error",
}


def default_model() -> Path:
    a = PROJECT_ROOT / "model" / "qwen235"
    b = PROJECT_ROOT / "models" / "qwen235"
    return a if a.exists() or not b.exists() else b


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--stage", choices=("existing", "reasoning", "generation", "badcase", "all"), default="all")
    p.add_argument("--facts", type=Path, default=DEFAULT_FACTS)
    p.add_argument("--edges", type=Path, default=DEFAULT_EDGES)
    p.add_argument("--existing-input", type=Path, action="append", default=[])
    p.add_argument("--badcase-classification", type=Path, default=DEFAULT_BADCASE)
    p.add_argument("--output-root", type=Path, default=DEFAULT_OUT)
    p.add_argument("--reasoning-target", type=int, default=20000)
    p.add_argument("--generation-target", type=int, default=10000)
    p.add_argument("--badcase-target", type=int, default=10000)
    p.add_argument("--graph-hard-ratio", type=float, default=0.40,
                   help="Fraction of ordinary Reasoning RL candidates built by the graph hard-sample synthesizer.")
    p.add_argument("--badcase-graph-ratio", type=float, default=0.75,
                   help="Fraction of Bad Case conditioned reasoning candidates built as graph hard samples.")
    p.add_argument("--graph-distractors", type=int, default=4,
                   help="Number of high-confusion distractor facts added to each graph hard sample.")
    p.add_argument("--disable-graph-hard", action="store_true",
                   help="Disable Agent-World-style graph hard-sample construction.")
    p.add_argument("--existing-limit", type=int, default=0)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--max-images", type=int, default=8)
    p.add_argument("--max-context-chars", type=int, default=2200)
    p.add_argument("--bundle-min", type=int, default=4)
    p.add_argument("--bundle-max", type=int, default=9)
    p.add_argument("--model", type=Path, default=default_model())
    p.add_argument("--backend", choices=("vllm", "openai"), default="vllm")
    p.add_argument("--base-url", default=os.environ.get("FINAR_SYNTH_BASE_URL", "http://127.0.0.1:8000/v1"))
    p.add_argument("--api-key", default=os.environ.get("FINAR_SYNTH_API_KEY", "EMPTY"))
    p.add_argument("--tensor-parallel-size", type=int, default=8)
    p.add_argument("--gpu-memory-utilization", type=float, default=0.90)
    p.add_argument("--max-model-len", type=int, default=32768)
    p.add_argument("--llm-batch-size", type=int, default=12)
    p.add_argument("--llm-max-tokens", type=int, default=1800)
    p.add_argument("--llm-temperature", type=float, default=0.25)
    return p.parse_args()


def jd(x: Any) -> str:
    return json.dumps(x, ensure_ascii=False, separators=(",", ":"))


def h(x: Any) -> str:
    return hashlib.sha1(jd(x).encode()).hexdigest()


def iter_jsonl(path: Path) -> Iterator[dict[str, Any]]:
    if not path.exists():
        return
    with path.open(encoding="utf-8-sig") as f:
        for i, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(row, dict):
                row.setdefault("_source_line", i)
                yield row


def iter_inputs(paths: Sequence[Path]) -> Iterator[tuple[Path, int, dict[str, Any]]]:
    for item in paths:
        files = sorted(item.rglob("*.jsonl")) if item.is_dir() else [item]
        for path in files:
            if not path.exists():
                continue
            with path.open(encoding="utf-8-sig") as f:
                for i, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        row = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if isinstance(row, dict):
                        yield path, i, row


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as f:
        for row in rows:
            f.write(jd(row) + "\n")


def pick(m: Mapping[str, Any], keys: Sequence[str], default: Any = "") -> Any:
    for k in keys:
        v = m.get(k)
        if v not in (None, "", [], {}):
            return v
    return default


def npick(row: Mapping[str, Any], keys: Sequence[str], default: Any = "") -> Any:
    v = pick(row, keys, None)
    if v not in (None, "", [], {}):
        return v
    meta = row.get("metadata")
    if isinstance(meta, Mapping):
        v = pick(meta, keys, None)
        if v not in (None, "", [], {}):
            return v
    return default


def to_decimal(v: Any) -> Decimal | None:
    if v in (None, ""):
        return None
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        if isinstance(v, float) and not math.isfinite(v):
            return None
        try:
            return Decimal(str(v))
        except InvalidOperation:
            return None
    m = NUMBER_RE.search(str(v))
    if not m:
        return None
    try:
        return Decimal(m.group(0).replace(",", ""))
    except InvalidOperation:
        return None


def dtext(x: Decimal, digits: int = 6) -> str:
    q = Decimal(1).scaleb(-digits)
    s = format(x.quantize(q, rounding=ROUND_HALF_UP), "f").rstrip("0").rstrip(".")
    return s if s not in {"", "-0"} else "0"


def year(period: str) -> int | None:
    m = YEAR_RE.search(str(period or ""))
    return int(m.group(1)) if m else None


def sampler_tasks() -> tuple[str, ...]:
    tasks: set[str] = set()
    base = PROJECT_ROOT / "scripts" / "sft" / "sample_plan_base.py"
    wrapper = PROJECT_ROOT / "scripts" / "sft" / "sample_plan.py"
    if base.exists():
        try:
            tree = ast.parse(base.read_text(encoding="utf-8"))
            for node in tree.body:
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name) and target.id == "TASK_TO_FAMILY":
                            obj = ast.literal_eval(node.value)
                            if isinstance(obj, dict):
                                tasks.update(map(str, obj))
        except Exception:
            pass
    if wrapper.exists():
        tasks.update(re.findall(r'TASK_TO_FAMILY\["([^"]+)"\]\s*=', wrapper.read_text(encoding="utf-8")))
    tasks.update({
        "basic_arithmetic_metrics", "multi_step_numerical_reasoning", "single_table_qa",
        "multi_table_reasoning", "chart_data_extraction", "chart_statement_verification",
        "financial_ocr", "financial_truthfulness_qa", "statistics_comparison_ranking",
        "cross_modal_multi_hop", "financial_report_analysis", "financial_risk_analysis",
        "financial_data_interpretation", "document_explanation", "financial_summarization",
        "document_summarization", "summary_announcement", "risk_sentiment_policy",
    })
    return tuple(sorted(tasks))


TASKS = sampler_tasks()
TASK_SET = set(TASKS)
GEN_TASKS = tuple(t for t in GENERATION_TASK_PREFERENCES if t in TASK_SET) or TASKS


@dataclass(frozen=True)
class Fact:
    id: str
    entity_key: str
    entity: str
    metric_key: str
    metric: str
    period: str
    scope: str
    unit: str
    value: Decimal | None
    raw_value: str
    doc_key: str
    doc: str
    page: str
    image: str
    visual: str
    text: str
    raw: dict[str, Any]


def image_field(row: Mapping[str, Any]) -> str:
    v = npick(row, ("image_path", "image", "page_image", "rendered_image", "media_path", "figure_path"), "")
    if isinstance(v, list):
        idx = row.get("image_index")
        if isinstance(idx, int) and 0 <= idx < len(v) and str(v[idx]).strip():
            return str(v[idx]).strip()
        v = next((x for x in v if isinstance(x, str) and x.strip()), "")
    if isinstance(v, str) and v.strip():
        return v.strip()
    imgs = row.get("images")
    if isinstance(imgs, list):
        idx = row.get("image_index")
        if isinstance(idx, int) and 0 <= idx < len(imgs) and str(imgs[idx]).strip():
            return str(imgs[idx]).strip()
        return next((str(x).strip() for x in imgs if str(x).strip()), "")
    return ""


def vtype(s: str) -> str:
    s = str(s or "").lower()
    if any(x in s for x in ("candlestick", "kline", "ohlc")):
        return "candlestick"
    if any(x in s for x in ("chart", "plot", "bar_", "line_", "pie_", "scatter")):
        return "chart"
    if any(x in s for x in ("table", "spreadsheet")):
        return "table"
    if any(x in s for x in ("relationship", "ownership", "equity_structure", "diagram")):
        return "relationship"
    return s or "document"


def norm_fact(row: Mapping[str, Any], i: int) -> Fact:
    fid = str(pick(row, ("fact_id", "id", "uid", "node_id", "evidence_id"), f"f{i:09d}_{h(row)[:10]}"))
    ek = str(npick(row, ("company_entity_id", "company_id", "entity_id", "issuer_id", "entity"), ""))
    en = str(npick(row, ("company_name", "entity_name", "issuer_name", "subject_name", "entity"), ek))
    if not ek:
        ek = en
    mk = str(npick(row, ("canonical_metric", "metric", "metric_id", "field", "item", "line_item"), ""))
    mn = str(npick(row, ("metric_name", "display_metric", "label", "line_item", "metric", "field"), mk))
    if not mk:
        mk = mn
    period = str(npick(row, ("period", "fiscal_period", "report_period", "year", "date", "fiscal_year"), ""))
    scope = str(npick(row, ("scope", "reporting_scope", "statement_scope", "consolidation_scope", "segment"), ""))
    unit = str(npick(row, ("unit", "currency_unit", "scale_unit", "value_unit"), ""))
    rv = npick(row, ("numeric_value", "normalized_value", "value", "value_text", "amount", "number", "fact_value"), "")
    dk = str(npick(row, ("document_entity_id", "document_id", "doc_id", "report_id", "source_ref"), ""))
    dn = str(npick(row, ("document_name", "doc_name", "report_name", "source_name", "title"), dk))
    page = str(npick(row, ("page", "page_no", "page_num", "page_number"), ""))
    image = image_field(row)
    visual = vtype(str(npick(row, ("visual_type", "media_type", "figure_type", "content_type"), "")))
    text = str(npick(row, ("evidence_quote", "evidence_text", "source_text", "ocr_text", "text", "content", "quote"), "")).strip()
    return Fact(fid, ek, en, mk, mn, period, scope, unit, to_decimal(rv), str(rv).strip(), dk, dn, page, image, visual, text, dict(row))


def load_facts(path: Path) -> list[Fact]:
    return [norm_fact(row, i) for i, row in enumerate(iter_jsonl(path), 1)]


def resolve_image(value: str) -> Path | None:
    if not value:
        return None
    p = Path(value)
    roots = (PROJECT_ROOT, PROJECT_ROOT / "data", PROJECT_ROOT / "data" / "raw", FINANCE_WORLD)
    candidates = [p] if p.is_absolute() else [root / p for root in roots]
    for c in candidates:
        if c.is_file() and c.suffix.lower() in IMAGE_SUFFIXES:
            return c.resolve()
    return None


def portable(path: Path) -> str:
    try:
        return path.relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return str(path)


class Index:
    def __init__(self, facts: Sequence[Fact], edges: Sequence[Mapping[str, Any]] = ()) -> None:
        self.facts = list(facts)
        self.by_id = {f.id: f for f in facts}
        self.by_series: dict[tuple[str, str, str, str], list[Fact]] = defaultdict(list)
        self.by_entity_period: dict[tuple[str, str], list[Fact]] = defaultdict(list)
        self.by_metric_period: dict[tuple[str, str, str], list[Fact]] = defaultdict(list)
        self.by_doc: dict[str, list[Fact]] = defaultdict(list)
        self.by_entity: dict[str, list[Fact]] = defaultdict(list)
        self.by_entity_scope_unit: dict[tuple[str, str, str], list[Fact]] = defaultdict(list)
        self.by_metric_scope_unit: dict[tuple[str, str, str], list[Fact]] = defaultdict(list)
        self.explicit_adj: dict[str, list[tuple[str, str]]] = defaultdict(list)
        self.explicit_type: dict[tuple[str, str], str] = {}

        for f in facts:
            self.by_series[(f.entity_key, f.metric_key, f.scope, f.unit)].append(f)
            self.by_entity_period[(f.entity_key, f.period)].append(f)
            self.by_metric_period[(f.metric_key, f.period, f.unit)].append(f)
            self.by_entity_scope_unit[(f.entity_key, f.scope, f.unit)].append(f)
            self.by_metric_scope_unit[(f.metric_key, f.scope, f.unit)].append(f)
            if f.doc_key:
                self.by_doc[f.doc_key].append(f)
            if f.entity_key:
                self.by_entity[f.entity_key].append(f)

        for group in self.by_series.values():
            group.sort(key=lambda f: (year(f.period) or 0, f.period, f.id))

        # build_finance_sailorfog.py currently writes {a,b,type}; accept a few
        # aliases so this script stays tolerant to graph schema evolution.
        for edge in edges:
            a = str(pick(edge, ("a", "source", "src", "source_id", "from_id"), ""))
            b = str(pick(edge, ("b", "target", "dst", "target_id", "to_id"), ""))
            typ = str(pick(edge, ("type", "edge_type", "relation"), "explicit_relation"))
            if not a or not b or a == b or a not in self.by_id or b not in self.by_id:
                continue
            self.explicit_adj[a].append((b, typ))
            self.explicit_adj[b].append((a, typ))
            self.explicit_type[(a, b)] = typ
            self.explicit_type[(b, a)] = typ

    def edge_type(self, a: Fact, b: Fact) -> str:
        explicit = self.explicit_type.get((a.id, b.id))
        if explicit:
            return explicit
        if (
            a.entity_key and a.entity_key == b.entity_key
            and a.metric_key and a.metric_key == b.metric_key
            and a.scope == b.scope and a.unit == b.unit
            and a.period != b.period
        ):
            return "same_metric_across_period"
        if (
            a.entity_key and a.entity_key == b.entity_key
            and a.period and a.period == b.period
            and a.scope == b.scope and a.unit == b.unit
            and a.metric_key != b.metric_key
        ):
            return "same_period_related_metric"
        if (
            a.metric_key and a.metric_key == b.metric_key
            and a.period and a.period == b.period
            and a.unit == b.unit
            and a.entity_key != b.entity_key
        ):
            return "same_metric_peer"
        if (
            a.entity_key and a.entity_key == b.entity_key
            and a.metric_key and a.metric_key == b.metric_key
            and a.period and a.period == b.period
            and a.unit == b.unit and a.scope != b.scope
        ):
            return "scope_variant"
        if a.doc_key and a.doc_key == b.doc_key:
            return "same_document"
        return "related_financial_fact"

    def graph_edge(self, a: Fact, b: Fact) -> dict[str, str]:
        return {"source": a.id, "target": b.id, "type": self.edge_type(a, b)}

    def bundle(self, rng: random.Random, nmin: int, nmax: int) -> list[Fact]:
        groups = [g for g in self.by_doc.values() if len(g) >= nmin]
        if groups and rng.random() < 0.75:
            g = list(rng.choice(groups))
        else:
            groups = [g for g in self.by_entity_period.values() if len(g) >= nmin]
            if not groups:
                groups = [g for g in self.by_entity.values() if len(g) >= nmin]
            if not groups:
                return []
            g = list(rng.choice(groups))
        rng.shuffle(g)
        selected: list[Fact] = []
        seen_metric: set[str] = set()
        for f in g:
            if f.metric_key not in seen_metric or len(selected) < nmin:
                selected.append(f)
                seen_metric.add(f.metric_key)
            if len(selected) >= nmax:
                break
        if len(selected) < nmin:
            for f in g:
                if f not in selected:
                    selected.append(f)
                if len(selected) >= nmin:
                    break
        return selected[:nmax]


def entity(f: Fact) -> str:
    return f.entity or f.entity_key or "该公司"


def metric(f: Fact) -> str:
    return f.metric or f.metric_key or "该指标"


def fvalue(f: Fact) -> str:
    if f.raw_value and any(ch.isdigit() for ch in f.raw_value):
        return f.raw_value if not f.unit or f.unit in f.raw_value else f.raw_value + f.unit
    return (dtext(f.value) if f.value is not None else "") + f.unit


def images_for(facts: Sequence[Fact], max_images: int) -> tuple[list[str], list[str]]:
    out, ids, seen = [], [], set()
    for f in facts:
        p = resolve_image(f.image)
        if p is None:
            continue
        q = portable(p)
        if q in seen:
            continue
        seen.add(q)
        out.append(q)
        ids.append(f.id)
        if len(out) >= max_images:
            break
    return out, ids


def fact_line(f: Fact, hide_visual: bool) -> str:
    if f.image and hide_visual and resolve_image(f.image):
        bits = [entity(f), f.period, metric(f), f"第{f.page}页" if f.page else ""]
        return "图像证据：" + " / ".join(x for x in bits if x)
    if f.text:
        return re.sub(r"\s+", " ", f.text).strip()[:500]
    return "；".join(x for x in (entity(f), f.period, metric(f), fvalue(f)) if x)


def context(facts: Sequence[Fact], max_chars: int, hide_visual: bool = True) -> str:
    parts, total = [], 0
    for i, f in enumerate(facts, 1):
        s = f"材料{i}：{fact_line(f, hide_visual)}"
        if total + len(s) > max_chars:
            break
        parts.append(s)
        total += len(s)
    return "\n".join(parts)


def messages(question: str, images: Sequence[str], ctx: str = "") -> list[dict[str, str]]:
    body = []
    if images:
        body.append("".join("<image>" for _ in images))
    if ctx:
        body.append(ctx)
    body.append(question)
    return [{"role": "user", "content": "\n".join(body)}]


def meta(builder: str, facts: Sequence[Fact], visual_ids: Sequence[str], extra: Mapping[str, Any] | None = None) -> dict[str, Any]:
    x = {
        "version": "rl_candidate_bank_v2",
        "builder": builder,
        "fact_ids": [f.id for f in facts],
        "visual_fact_ids": list(visual_ids),
        "entity_keys": sorted({f.entity_key for f in facts if f.entity_key}),
        "periods": sorted({f.period for f in facts if f.period}),
        "document_keys": sorted({f.doc_key for f in facts if f.doc_key}),
        "scopes": sorted({f.scope for f in facts if f.scope}),
        "units": sorted({f.unit for f in facts if f.unit}),
    }
    if extra:
        x.update(dict(extra))
    return x


def task_for_pair(a: Fact, b: Fact, op: str) -> str:
    pa, pb = resolve_image(a.image), resolve_image(b.image)
    if pa and pb and pa != pb:
        if a.visual == b.visual == "table" and "multi_table_reasoning" in TASK_SET:
            return "multi_table_reasoning"
        if a.visual in {"chart", "candlestick"} and b.visual in {"chart", "candlestick"} and "multimodal_financial_chart_reasoning_v5" in TASK_SET:
            return "multimodal_financial_chart_reasoning_v5"
        if "cross_modal_multi_hop" in TASK_SET:
            return "cross_modal_multi_hop"
    if op == "difference" and "basic_arithmetic_metrics" in TASK_SET:
        return "basic_arithmetic_metrics"
    if op == "ratio" and "table_ratio_reasoning" in TASK_SET:
        return "table_ratio_reasoning"
    return "multi_step_numerical_reasoning"


def numeric_row(question: str, facts: Sequence[Fact], result: Decimal, unit: str, program: str, task: str, builder: str, args: argparse.Namespace, source: str, extra: Mapping[str, Any] | None = None) -> dict[str, Any]:
    imgs, vids = images_for(facts, args.max_images)
    ctx = context(facts, args.max_context_chars, hide_visual=True)
    if any(f.image and f.id not in set(vids) for f in facts):
        ctx += "\n" + context([f for f in facts if f.image and f.id not in set(vids)], args.max_context_chars, hide_visual=False)
    answer = dtext(result) + unit
    return {
        "messages": messages(question, imgs, ctx.strip()),
        "question": question,
        "solution": answer,
        "task": task if task in TASK_SET else "multi_step_numerical_reasoning",
        "source": source,
        "split": "train",
        "images": imgs,
        "output_format": "number_or_free_text",
        "reward_type": "rule",
        "reward_subtype": "numeric",
        "verifier_type": "numeric",
        "metadata": {
            "program": program,
            "operation_count": program.count("("),
            "gold_readable_answer": answer,
            "evidence_ids": [f.id for f in facts],
            "construction": meta(builder, facts, vids, extra),
        },
    }


def visual_lookup(f: Fact, args: argparse.Namespace, source: str, extra: Mapping[str, Any] | None = None) -> dict[str, Any] | None:
    if f.value is None:
        return None
    p = resolve_image(f.image)
    if p is None:
        return None
    q = f"请根据图中信息，读取{entity(f)}{f.period}的{metric(f)}数值，并保留原有单位。"
    task = "chart_data_extraction" if f.visual == "chart" else "candlestick_time_series" if f.visual == "candlestick" else "financial_ocr"
    if task not in TASK_SET:
        task = "single_table_qa"
    return {
        "messages": messages(q, [portable(p)]), "question": q, "solution": fvalue(f),
        "task": task, "source": source, "split": "train", "images": [portable(p)],
        "output_format": "numeric_or_short_text", "reward_type": "rule",
        "reward_subtype": "numeric", "verifier_type": "numeric",
        "metadata": {"evidence_ids": [f.id], "construction": meta("visual_lookup", [f], [f.id], extra)},
    }


def ranking_row(group: Sequence[Fact], rng: random.Random, args: argparse.Namespace, source: str, extra: Mapping[str, Any] | None = None) -> dict[str, Any] | None:
    by_entity: dict[str, Fact] = {}
    for f in group:
        if f.value is not None and f.entity:
            by_entity.setdefault(f.entity_key or f.entity, f)
    facts = list(by_entity.values())
    if len(facts) < 3:
        return None
    rng.shuffle(facts)
    facts = facts[: min(4, len(facts))]
    if len({f.value for f in facts}) != len(facts):
        return None
    winner = max(facts, key=lambda x: x.value)
    opts = [(chr(65 + i), f.entity) for i, f in enumerate(facts)]
    letter = next(k for k, v in opts if v == winner.entity)
    q = f"根据材料，比较各公司{facts[0].period}的{metric(facts[0])}，数值最高的是哪一家？\n" + "\n".join(f"{k}. {v}" for k, v in opts)
    imgs, vids = images_for(facts, args.max_images)
    ctx = context(facts, args.max_context_chars, hide_visual=(len(imgs) == len(facts)))
    return {
        "messages": messages(q, imgs, ctx), "question": q, "solution": letter,
        "task": "statistics_comparison_ranking", "source": source, "split": "train", "images": imgs,
        "output_format": "single_choice", "reward_type": "rule", "reward_subtype": "single_choice",
        "verifier_type": "single_choice", "gold_option_text": winner.entity, "options_shuffled": True,
        "metadata": {"evidence_ids": [f.id for f in facts], "construction": meta("single_choice_ranking", facts, vids, extra)},
    }



def _profile_text(profile: Mapping[str, Any] | None) -> str:
    if not profile:
        return ""
    return " ".join(
        [str(profile.get("task_type") or ""), str(profile.get("error_type") or "")]
        + [str(x) for x in (profile.get("scenario_tags") or [])]
    ).lower()


def distractors_for(
    index: Index,
    required: Sequence[Fact],
    rng: random.Random,
    count: int,
    profile: Mapping[str, Any] | None = None,
) -> list[Fact]:
    """Select high-confusion facts without changing the executable gold path."""
    if count <= 0:
        return []
    required_ids = {f.id for f in required}
    ptext = _profile_text(profile)
    scored: dict[str, tuple[float, Fact]] = {}

    def add(f: Fact, score: float) -> None:
        if f.id in required_ids or f.value is None:
            return
        old = scored.get(f.id)
        jitter = rng.random() * 0.01
        candidate = (score + jitter, f)
        if old is None or candidate[0] > old[0]:
            scored[f.id] = candidate

    for r in required:
        # Explicit graph neighbors are usually semantically close.
        for nid, _etype in index.explicit_adj.get(r.id, []):
            f = index.by_id.get(nid)
            if f is not None:
                add(f, 7.5)

        # Wrong period, same entity/metric/scope/unit.
        for f in index.by_series.get((r.entity_key, r.metric_key, r.scope, r.unit), []):
            if f.period != r.period:
                add(f, 10.0 if "period" in ptext or "temporal" in ptext else 7.0)

        # Wrong metric, same entity/period/scope/unit.
        for f in index.by_entity_period.get((r.entity_key, r.period), []):
            if f.metric_key != r.metric_key and f.scope == r.scope and f.unit == r.unit:
                add(f, 10.0 if "metric" in ptext or "line_item" in ptext else 6.5)

        # Wrong scope, same entity/metric/period/unit.
        for f in index.by_entity.get(r.entity_key, []):
            if (
                f.metric_key == r.metric_key and f.period == r.period and f.unit == r.unit
                and f.scope != r.scope
            ):
                add(f, 10.0 if "scope" in ptext or "segment" in ptext else 8.0)

        # Peer company, same metric/period/unit.
        for f in index.by_metric_period.get((r.metric_key, r.period, r.unit), []):
            if f.entity_key != r.entity_key:
                add(f, 10.0 if "entity" in ptext or "company" in ptext else 5.5)

        # Same document noise is useful for multi-table / multi-chart search.
        if r.doc_key:
            for f in index.by_doc.get(r.doc_key, []):
                if f.id != r.id:
                    add(f, 8.5 if "table" in ptext or "chart" in ptext or "retrieval" in ptext else 4.5)

    ranked = sorted(scored.values(), key=lambda item: item[0], reverse=True)
    return [f for _, f in ranked[:count]]


def difficulty_vector(
    required: Sequence[Fact],
    distractors: Sequence[Fact],
    path_edges: Sequence[Mapping[str, Any]],
    operator_count: int,
) -> dict[str, Any]:
    docs = {f.doc_key for f in required if f.doc_key}
    visuals = [f for f in required if resolve_image(f.image)]
    periods = [f.period for f in required if f.period]
    scopes = [f.scope for f in required if f.scope]
    cross_modal = 0
    for a, b in zip(required, required[1:]):
        va, vb = bool(resolve_image(a.image)), bool(resolve_image(b.image))
        if va != vb:
            cross_modal += 1
    score = (
        len(path_edges)
        + operator_count
        + min(len(distractors), 6) * 0.75
        + max(0, len(docs) - 1) * 1.5
        + max(0, len(set(periods)) - 1) * 0.75
        + max(0, len(set(scopes)) - 1) * 0.75
        + cross_modal
    )
    label = "hard" if score >= 10 else "medium" if score >= 6 else "easy"
    return {
        "label": label,
        "score": round(score, 2),
        "reasoning_hops": len(path_edges),
        "required_fact_count": len(required),
        "operator_count": operator_count,
        "distractor_count": len(distractors),
        "document_count": len(docs),
        "visual_count": len(visuals),
        "period_count": len(set(periods)),
        "scope_count": len(set(scopes)),
        "cross_modal_hops": cross_modal,
    }


def graph_numeric_row(
    question: str,
    required: Sequence[Fact],
    distractors: Sequence[Fact],
    result: Decimal,
    unit: str,
    program: str,
    task: str,
    builder: str,
    path_edges: Sequence[Mapping[str, Any]],
    args: argparse.Namespace,
    source: str,
    rng: random.Random,
    profile: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    prompt_facts = list(required) + list(distractors)
    # Required facts are inserted before distractors when collecting images so
    # a max-images cap cannot accidentally remove required visual evidence.
    imgs, visual_ids = images_for(prompt_facts, args.max_images)
    rng.shuffle(prompt_facts)
    ctx = context(prompt_facts, args.max_context_chars, hide_visual=True)
    included_visual = set(visual_ids)
    missing_required_visual = [
        f for f in required if resolve_image(f.image) is not None and f.id not in included_visual
    ]
    if missing_required_visual:
        # Keep the sample answerable if max-images is set below the number of
        # required visual facts. This fallback is recorded in metadata.
        ctx += "\n" + context(missing_required_visual, args.max_context_chars, hide_visual=False)

    answer = dtext(result) + unit
    diff = difficulty_vector(required, distractors, path_edges, program.count("("))
    extra: dict[str, Any] = {
        "required_evidence_ids": [f.id for f in required],
        "distractor_ids": [f.id for f in distractors],
        "reasoning_graph": {
            "nodes": [f.id for f in required],
            "edges": [dict(x) for x in path_edges],
        },
        "difficulty": diff,
        "image_fallback_required_ids": [f.id for f in missing_required_visual],
    }
    if profile:
        extra["badcase_profile"] = dict(profile)

    return {
        "messages": messages(question, imgs, ctx.strip()),
        "question": question,
        "solution": answer,
        "task": task if task in TASK_SET else "multi_step_numerical_reasoning",
        "source": source,
        "split": "train",
        "images": imgs,
        "output_format": "number_or_free_text",
        "reward_type": "rule",
        "reward_subtype": "numeric",
        "verifier_type": "numeric",
        "metadata": {
            "program": program,
            "operation_count": program.count("("),
            "gold_readable_answer": answer,
            "evidence_ids": [f.id for f in required],
            "distractor_ids": [f.id for f in distractors],
            "construction": meta(builder, required, [f.id for f in required if resolve_image(f.image)], extra),
        },
    }


class GraphReasoningSampler:
    """Agent-World-inspired hard financial task synthesizer.

    It samples a graph skeleton first, executes the deterministic operator path,
    expands high-confusion distractor branches, and only then renders a natural
    question. The natural language never determines the gold answer.
    """

    def __init__(self, index: Index, rng: random.Random, args: argparse.Namespace) -> None:
        self.index = index
        self.rng = rng
        self.args = args

    def sample(self, target: int, profile: Mapping[str, Any] | None = None) -> list[dict[str, Any]]:
        if target <= 0:
            return []
        builders = self._builders_for_profile(profile)
        rows: list[dict[str, Any]] = []
        attempts = 0
        max_attempts = max(100, target * 30)
        while len(rows) < target and attempts < max_attempts:
            attempts += 1
            builder = builders[attempts % len(builders)]
            row = builder(profile)
            if row is not None:
                rows.append(row)
                rows = dedup(rows)
        self.rng.shuffle(rows)
        return rows[:target]

    def _builders_for_profile(self, profile: Mapping[str, Any] | None):
        ptext = _profile_text(profile)
        if any(x in ptext for x in ("ranking", "comparison", "entity_confusion", "company_comparison")):
            return [self._peer_growth_gap, self._ratio_change, self._growth_acceleration]
        if any(x in ptext for x in ("period", "temporal", "baseline_reference")):
            return [self._growth_acceleration, self._ratio_change, self._peer_growth_gap]
        if any(x in ptext for x in ("ratio", "percentage", "formula", "metric", "scope", "segment")):
            return [self._ratio_change, self._growth_acceleration, self._peer_growth_gap]
        return [self._ratio_change, self._growth_acceleration, self._peer_growth_gap]

    def _ratio_change(self, profile: Mapping[str, Any] | None) -> dict[str, Any] | None:
        buckets = list(self.index.by_entity_scope_unit.items())
        if not buckets:
            return None
        (_key, facts) = self.rng.choice(buckets)
        by_metric: dict[str, dict[str, Fact]] = defaultdict(dict)
        for f in facts:
            if f.value is not None and f.metric_key and f.period:
                by_metric[f.metric_key][f.period] = f
        metrics = [m for m, per in by_metric.items() if len(per) >= 2]
        if len(metrics) < 2:
            return None
        metric_set = set(metrics)
        formula_pairs = [
            (name, num, den)
            for name, (num, den) in FINANCIAL_FORMULA_PAIRS.items()
            if num in metric_set and den in metric_set
        ]
        if not formula_pairs:
            return None
        formula_name, m_num, m_den = self.rng.choice(formula_pairs)
        common = sorted(
            set(by_metric[m_num]) & set(by_metric[m_den]),
            key=lambda p: (year(p) or 0, p),
        )
        if len(common) < 2:
            return None
        old_p, new_p = self.rng.sample(common, 2)
        if (year(old_p) or 0, old_p) > (year(new_p) or 0, new_p):
            old_p, new_p = new_p, old_p
        num_old, den_old = by_metric[m_num][old_p], by_metric[m_den][old_p]
        num_new, den_new = by_metric[m_num][new_p], by_metric[m_den][new_p]
        if den_old.value == 0 or den_new.value == 0:
            return None
        required = [num_old, den_old, num_new, den_new]
        result = (num_new.value / den_new.value - num_old.value / den_old.value) * Decimal(100)
        program = (
            f"divide({dtext(num_old.value,12)},{dtext(den_old.value,12)}),"
            "multiply(#0,100),"
            f"divide({dtext(num_new.value,12)},{dtext(den_new.value,12)}),"
            "multiply(#2,100),subtract(#3,#1)"
        )
        edges = [
            self.index.graph_edge(num_old, num_new),
            self.index.graph_edge(den_old, den_new),
            self.index.graph_edge(num_old, den_old),
            self.index.graph_edge(num_new, den_new),
        ]
        distractors = distractors_for(
            self.index, required, self.rng, self.args.graph_distractors, profile
        )
        question = (
            f"根据给定材料，分别计算{entity(num_new)}{old_p}和{new_p}"
            f"{metric(num_new)}相对于{metric(den_new)}的比例，并计算{new_p}比例减去{old_p}比例的差值（以百分数差值表示）。"
        )
        task = self._task(required, preferred="multi_step_numerical_reasoning")
        return graph_numeric_row(
            question, required, distractors, result, "%", program, task,
            f"graph_ratio_change:{formula_name}", edges, self.args,
            "badcase_conditioned_rl_builder" if profile else "finance_world_graph_rl_builder",
            self.rng, profile,
        )

    def _growth_acceleration(self, profile: Mapping[str, Any] | None) -> dict[str, Any] | None:
        groups = [g for g in self.index.by_series.values() if len([f for f in g if f.value is not None and f.period]) >= 3]
        if not groups:
            return None
        facts = [f for f in self.rng.choice(groups) if f.value is not None and f.period]
        facts.sort(key=lambda f: (year(f.period) or 0, f.period))
        if len(facts) < 3:
            return None
        start = self.rng.randrange(0, len(facts) - 2)
        a, b, c = facts[start:start + 3]
        if a.value == 0 or b.value == 0:
            return None
        g1 = (b.value - a.value) / a.value * Decimal(100)
        g2 = (c.value - b.value) / b.value * Decimal(100)
        result = g2 - g1
        required = [a, b, c]
        program = (
            f"subtract({dtext(b.value,12)},{dtext(a.value,12)}),"
            f"divide(#0,{dtext(a.value,12)}),multiply(#1,100),"
            f"subtract({dtext(c.value,12)},{dtext(b.value,12)}),"
            f"divide(#3,{dtext(b.value,12)}),multiply(#4,100),subtract(#5,#2)"
        )
        edges = [self.index.graph_edge(a, b), self.index.graph_edge(b, c)]
        distractors = distractors_for(
            self.index, required, self.rng, self.args.graph_distractors, profile
        )
        question = (
            f"根据给定材料，计算{entity(c)}{metric(c)}从{a.period}到{b.period}、"
            f"以及从{b.period}到{c.period}的两个阶段增长率，并给出后一阶段增长率减去前一阶段增长率的差值（以百分数差值表示）。"
        )
        preferred = "temporal_financial_reasoning" if "temporal_financial_reasoning" in TASK_SET else "multi_step_numerical_reasoning"
        task = self._task(required, preferred=preferred)
        return graph_numeric_row(
            question, required, distractors, result, "%", program, task,
            "graph_growth_acceleration", edges, self.args,
            "badcase_conditioned_rl_builder" if profile else "finance_world_graph_rl_builder",
            self.rng, profile,
        )

    def _peer_growth_gap(self, profile: Mapping[str, Any] | None) -> dict[str, Any] | None:
        groups = list(self.index.by_metric_scope_unit.items())
        if not groups:
            return None
        (_key, facts) = self.rng.choice(groups)
        by_entity: dict[str, dict[str, Fact]] = defaultdict(dict)
        for f in facts:
            if f.value is not None and f.entity_key and f.period:
                by_entity[f.entity_key][f.period] = f
        entities = [e for e, per in by_entity.items() if len(per) >= 2]
        if len(entities) < 2:
            return None
        self.rng.shuffle(entities)
        e1, e2 = entities[:2]
        common = sorted(
            set(by_entity[e1]) & set(by_entity[e2]),
            key=lambda p: (year(p) or 0, p),
        )
        if len(common) < 2:
            return None
        old_p, new_p = self.rng.sample(common, 2)
        if (year(old_p) or 0, old_p) > (year(new_p) or 0, new_p):
            old_p, new_p = new_p, old_p
        a_old, a_new = by_entity[e1][old_p], by_entity[e1][new_p]
        b_old, b_new = by_entity[e2][old_p], by_entity[e2][new_p]
        if a_old.value == 0 or b_old.value == 0:
            return None
        ga = (a_new.value - a_old.value) / a_old.value * Decimal(100)
        gb = (b_new.value - b_old.value) / b_old.value * Decimal(100)
        result = ga - gb
        required = [a_old, a_new, b_old, b_new]
        program = (
            f"subtract({dtext(a_new.value,12)},{dtext(a_old.value,12)}),"
            f"divide(#0,{dtext(a_old.value,12)}),multiply(#1,100),"
            f"subtract({dtext(b_new.value,12)},{dtext(b_old.value,12)}),"
            f"divide(#3,{dtext(b_old.value,12)}),multiply(#4,100),subtract(#2,#5)"        )
        edges = [
            self.index.graph_edge(a_old, a_new),
            self.index.graph_edge(b_old, b_new),
            self.index.graph_edge(a_old, b_old),
            self.index.graph_edge(a_new, b_new),
        ]
        distractors = distractors_for(
            self.index, required, self.rng, self.args.graph_distractors, profile
        )
        question = (
            f"根据给定材料，分别计算{entity(a_new)}和{entity(b_new)}的{metric(a_new)}"
            f"从{old_p}到{new_p}的增长率，并给出{entity(a_new)}增长率减去{entity(b_new)}增长率的差值（以百分比数值表示）。"
        )
        task = self._task(required, preferred="multi_step_numerical_reasoning")
        return graph_numeric_row(
            question, required, distractors, result, "%", program, task,
            "graph_peer_growth_gap", edges, self.args,
            "badcase_conditioned_rl_builder" if profile else "finance_world_graph_rl_builder",
            self.rng, profile,
        )

    def _task(self, required: Sequence[Fact], preferred: str) -> str:
        paths = [resolve_image(f.image) for f in required]
        image_paths = [p for p in paths if p is not None]
        visuals = {f.visual for f in required if resolve_image(f.image)}
        if len(set(map(str, image_paths))) >= 2:
            if visuals == {"table"} and "multi_table_reasoning" in TASK_SET:
                return "multi_table_reasoning"
            if visuals and visuals <= {"chart", "candlestick"} and "multimodal_financial_chart_reasoning_v5" in TASK_SET:
                return "multimodal_financial_chart_reasoning_v5"
            if "cross_modal_multi_hop" in TASK_SET:
                return "cross_modal_multi_hop"
        return preferred if preferred in TASK_SET else "multi_step_numerical_reasoning"

def simple_reasoning_pool(index: Index, rng: random.Random, target: int, args: argparse.Namespace, profile: Mapping[str, Any] | None = None) -> list[dict[str, Any]]:
    source = "badcase_conditioned_rl_builder" if profile else "finance_world_rl_builder"
    extra = {"badcase_profile": dict(profile)} if profile else None
    rows: list[dict[str, Any]] = []
    groups = list(index.by_series.values())
    rng.shuffle(groups)
    for g in groups:
        vals = [f for f in g if f.value is not None and f.period]
        if len(vals) < 2:
            continue
        rng.shuffle(vals)
        for a, b in zip(vals, vals[1:]):
            if a.period == b.period:
                continue
            ya, yb = year(a.period), year(b.period)
            old, new = (a, b) if ya is None or yb is None or ya <= yb else (b, a)
            diff = new.value - old.value
            q = f"根据给定材料，计算{entity(new)}{metric(new)}从{old.period}到{new.period}的变化额。"
            rows.append(numeric_row(q, [old, new], diff, new.unit, f"subtract({dtext(new.value,12)},{dtext(old.value,12)})", task_for_pair(old, new, "difference"), "period_difference", args, source, extra))
            if old.value != 0:
                pct = (new.value - old.value) / old.value * Decimal(100)
                q = f"根据给定材料，计算{entity(new)}{metric(new)}由{old.period}到{new.period}的变动百分比。"
                prog = f"subtract({dtext(new.value,12)},{dtext(old.value,12)}),divide(#0,{dtext(old.value,12)}),multiply(#1,100)"
                rows.append(numeric_row(q, [old, new], pct, "%", prog, task_for_pair(old, new, "ratio"), "period_percentage_change", args, source, extra))
            if len(rows) >= target * 2:
                break
        if len(rows) >= target * 2:
            break

    # Same-period metric ratios.
    ep = list(index.by_entity_period.values())
    rng.shuffle(ep)
    for g in ep:
        by_unit: dict[str, list[Fact]] = defaultdict(list)
        for f in g:
            if f.value is not None and f.unit and f.metric_key:
                by_unit[f.unit].append(f)
        for ug in by_unit.values():
            if len(ug) < 2:
                continue
            rng.shuffle(ug)
            a, b = ug[0], ug[1]
            if a.metric_key == b.metric_key or b.value == 0:
                continue
            pct = a.value / b.value * Decimal(100)
            q = f"根据给定材料，计算{entity(a)}{a.period}{metric(a)}相对于{metric(b)}的比例（%）。"
            prog = f"divide({dtext(a.value,12)},{dtext(b.value,12)}),multiply(#0,100)"
            rows.append(numeric_row(q, [a, b], pct, "%", prog, task_for_pair(a, b, "ratio"), "same_period_metric_ratio", args, source, extra))
            if len(rows) >= target * 3:
                break
        if len(rows) >= target * 3:
            break

    # Visual lookup.
    visual = [f for f in index.facts if f.value is not None and resolve_image(f.image)]
    rng.shuffle(visual)
    for f in visual[: max(1, target // 3)]:
        row = visual_lookup(f, args, source, extra)
        if row:
            rows.append(row)

    # Ranking as single-choice.
    mp = list(index.by_metric_period.values())
    rng.shuffle(mp)
    for g in mp[: max(20, target // 2)]:
        row = ranking_row(g, rng, args, source, extra)
        if row:
            rows.append(row)

    rows = dedup(rows)
    rng.shuffle(rows)
    return rows[:target]



def reasoning_pool(index: Index, rng: random.Random, target: int, args: argparse.Namespace, profile: Mapping[str, Any] | None = None) -> list[dict[str, Any]]:
    if target <= 0:
        return []
    ratio = 0.0 if args.disable_graph_hard else (args.badcase_graph_ratio if profile else args.graph_hard_ratio)
    ratio = max(0.0, min(1.0, float(ratio)))
    graph_target = int(round(target * ratio))
    simple_target = max(0, target - graph_target)

    rows: list[dict[str, Any]] = []
    if graph_target:
        rows.extend(GraphReasoningSampler(index, rng, args).sample(graph_target, profile=profile))
    if simple_target:
        rows.extend(simple_reasoning_pool(index, rng, simple_target, args, profile=profile))

    # If the graph topology cannot satisfy the requested ratio, backfill from
    # the simple deterministic builders rather than silently shrinking output.
    if len(rows) < target:
        rows.extend(simple_reasoning_pool(index, rng, target - len(rows), args, profile=profile))
    rows = dedup(rows)
    rng.shuffle(rows)
    return rows[:target]

def dedup(rows: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    out, seen = [], set()
    for row in rows:
        key = h({"question": row.get("question"), "images": row.get("images"), "task": row.get("task"), "solution": row.get("solution")})
        if key in seen:
            continue
        seen.add(key)
        x = dict(row)
        x.setdefault("sample_id", "rlc_" + key[:20])
        out.append(x)
    return out


def message_text(messages_obj: Any, role: str | None = None) -> str:
    if not isinstance(messages_obj, list):
        return ""
    parts = []
    for m in messages_obj:
        if not isinstance(m, Mapping):
            continue
        if role and str(m.get("role") or "") != role:
            continue
        c = m.get("content")
        if isinstance(c, str):
            parts.append(c)
        elif isinstance(c, list):
            for x in c:
                if isinstance(x, Mapping) and x.get("type") == "text":
                    parts.append(str(x.get("text") or ""))
    return "\n".join(parts)


def existing_candidates(paths: Sequence[Path], limit: int) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    reasoning, generation = [], []
    for path, line, row in iter_inputs(paths):
        if limit and len(reasoning) + len(generation) >= limit:
            break
        q = message_text(row.get("messages"), "user").strip() or str(row.get("question") or "").strip()
        sol = str(pick(row, ("solution", "answer", "reference", "gold_final_answer"), "")).strip() or message_text(row.get("messages"), "assistant").strip()
        if not q or not sol:
            continue
        task = str(row.get("task") or "").strip()
        if task not in TASK_SET:
            task = "financial_report_analysis"
        verifier = str(row.get("verifier_type") or row.get("reward_subtype") or "").strip()
        output_format = str(row.get("output_format") or "").strip()
        if verifier not in PROGRAMMATIC_VERIFIERS:
            if output_format in {"single_choice", "multiple_choice", "true_false", "page_numbers"}:
                verifier = output_format
            elif any(k in task for k in ("calculation", "numerical", "arithmetic", "ratio", "rate_change")) and NUMBER_RE.search(sol):
                verifier, output_format = "numeric", "number_or_free_text"
            else:
                verifier, output_format = "model_judge", "free_text"
        msgs = [dict(m) for m in (row.get("messages") or []) if isinstance(m, Mapping) and m.get("role") != "assistant"] or [{"role": "user", "content": q}]
        x = {
            "messages": msgs, "question": q, "solution": sol, "task": task,
            "source": f"existing_rl_extraction:{row.get('source') or path.name}", "split": "train",
            "images": list(row.get("images") or []), "output_format": output_format or "number_or_free_text",
            "reward_type": "judge" if verifier == "model_judge" else "rule", "reward_subtype": verifier,
            "verifier_type": verifier, "metadata": {**dict(row.get("metadata") or {}), "construction": {
                "version": "rl_candidate_bank_v2", "builder": "existing_prompt_extraction", "source_file": str(path), "source_line": line,
            }},
        }
        (generation if verifier == "model_judge" else reasoning).append(x)
    return dedup(reasoning), dedup(generation)


def public_fact(f: Fact) -> dict[str, Any]:
    has_image = resolve_image(f.image) is not None
    return {
        "fact_id": f.id, "entity": entity(f), "period": f.period, "metric": metric(f),
        "scope": f.scope, "unit": f.unit, "document": f.doc or f.doc_key, "page": f.page,
        "visual_type": f.visual, "has_image": has_image,
        "evidence": "该事实来自随附图片，请直接查看图片。" if has_image else fact_line(f, False),
    }


GEN_SYSTEM = """你负责为 FINAR-VL 构造新的 Generation RL 候选数据。\n\n输入是一组新的金融证据以及可能存在的图片。基于这些证据生成一道新的开放式金融问题，并给出严格受证据支持的参考答案。\n\n要求：\n1. 问题只能依赖当前给定证据和图片回答，不得要求外部知识。\n2. 至少综合两条证据，不要生成单个数字抄取题。\n3. 图片存在且相关时，图片中的信息必须实际参与。\n4. 参考答案不得引入证据外的原因、预测、政策影响或公司动机。\n5. 问题不得直接泄露参考答案。\n6. task 必须逐字从 task_labels 中选择。\n7. used_fact_ids 必须来自输入 fact_id，至少两个。\n8. 证据不足时返回 reject。\n\n严格输出一个 JSON：\n{\"status\":\"accepted\",\"task\":\"...\",\"question\":\"...\",\"reference_answer\":\"...\",\"used_fact_ids\":[\"...\"]}\n或 {\"status\":\"reject\",\"reason\":\"...\"}\n只输出 JSON。"""

BADCASE_GEN_SYSTEM = """你负责根据能力缺口构造新的 FINAR-VL RL 候选问题。\n\n输入包含 task_type / error_type / scenario_tags 分类画像，以及与原 Bad Case 内容无关的一组新金融证据。根据分类画像构造一道新的问题，但不得复述或改写原 Bad Case。所有事实必须来自当前新证据。\n\n要求：\n1. 问题针对 error_type 对应能力。\n2. 开放式问题至少综合两条当前证据。\n3. 视觉/跨模态能力要求图片真实参与。\n4. 参考答案不得引入证据外信息。\n5. task 必须逐字从 task_labels 中选择。\n6. used_fact_ids 必须来自当前输入，至少两个。\n7. 当前证据不适合该画像时返回 reject。\n\n严格输出 JSON：\n{\"status\":\"accepted\",\"task\":\"...\",\"question\":\"...\",\"reference_answer\":\"...\",\"used_fact_ids\":[\"...\"]}\n或 {\"status\":\"reject\",\"reason\":\"...\"}\n只输出 JSON。"""


@dataclass
class Request:
    system: str
    user: str
    images: list[Path]


class Runner:
    def __init__(self, args: argparse.Namespace) -> None:
        self.backend = args.backend
        self.model = str(args.model)
        self.max_images = args.max_images
        if self.backend == "openai":
            from openai import OpenAI
            self.client = OpenAI(api_key=args.api_key, base_url=args.base_url)
            self.processor = self.llm = self.SamplingParams = None
        else:
            from transformers import AutoProcessor
            from vllm import LLM, SamplingParams
            self.processor = AutoProcessor.from_pretrained(self.model, trust_remote_code=True)
            self.llm = LLM(model=self.model, tensor_parallel_size=args.tensor_parallel_size, gpu_memory_utilization=args.gpu_memory_utilization, max_model_len=args.max_model_len, trust_remote_code=True, limit_mm_per_prompt={"image": args.max_images})
            self.SamplingParams = SamplingParams
            self.client = None

    @staticmethod
    def parse(s: str) -> dict[str, Any]:
        s = re.sub(r"^```(?:json)?\s*|\s*```$", "", s.strip())
        a, b = s.find("{"), s.rfind("}")
        if a < 0 or b < a:
            raise ValueError("no JSON object")
        x = json.loads(s[a:b+1])
        if not isinstance(x, dict):
            raise ValueError("not object")
        return x

    def batch(self, reqs: Sequence[Request], temp: float, max_tokens: int) -> list[dict[str, Any] | Exception]:
        if self.backend == "openai":
            from PIL import Image
            out = []
            for r in reqs:
                try:
                    content = [{"type": "text", "text": r.user}]
                    for p in r.images[:self.max_images]:
                        with Image.open(p) as im:
                            im = im.convert("RGB")
                            buf = io.BytesIO(); im.save(buf, format="JPEG", quality=90)
                        data = base64.b64encode(buf.getvalue()).decode()
                        content.append({"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + data}})
                    z = self.client.chat.completions.create(model=self.model, messages=[{"role":"system","content":r.system},{"role":"user","content":content}], temperature=temp, max_tokens=max_tokens)
                    out.append(self.parse(z.choices[0].message.content or ""))
                except Exception as e:
                    out.append(e)
            return out

        from qwen_vl_utils import process_vision_info
        prompts = []
        for r in reqs:
            content = [{"type": "text", "text": r.user}] + [{"type":"image","image":str(p)} for p in r.images[:self.max_images]]
            msgs = [{"role":"system","content":r.system},{"role":"user","content":content}]
            prompt = self.processor.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)
            ii, vi = process_vision_info(msgs)
            mm = {}
            if ii: mm["image"] = ii
            if vi: mm["video"] = vi
            prompts.append({"prompt": prompt, "multi_modal_data": mm})
        raw = self.llm.generate(prompts, self.SamplingParams(temperature=temp, max_tokens=max_tokens), use_tqdm=False)
        out = []
        for z in raw:
            try: out.append(self.parse(z.outputs[0].text))
            except Exception as e: out.append(e)
        return out


def gen_request(bundle: Sequence[Fact], profile: Mapping[str, Any] | None, args: argparse.Namespace) -> Request:
    imgs, seen = [], set()
    for f in bundle:
        p = resolve_image(f.image)
        if p and str(p) not in seen:
            seen.add(str(p)); imgs.append(p)
        if len(imgs) >= args.max_images: break
    payload = {"task_labels": list(GEN_TASKS), "evidence": [public_fact(f) for f in bundle]}
    if profile: payload["badcase_profile"] = dict(profile)
    return Request(BADCASE_GEN_SYSTEM if profile else GEN_SYSTEM, json.dumps(payload, ensure_ascii=False, indent=2), imgs)


def valid_gen(x: Mapping[str, Any], ids: set[str]) -> tuple[bool, str]:
    if x.get("status") != "accepted": return False, str(x.get("reason") or "model_rejected")
    if str(x.get("task") or "") not in set(GEN_TASKS): return False, "invalid_task"
    if not str(x.get("question") or "").strip() or not str(x.get("reference_answer") or "").strip(): return False, "empty_question_or_answer"
    used = x.get("used_fact_ids")
    if not isinstance(used, list) or len(used) < 2: return False, "too_few_used_fact_ids"
    if any(str(i) not in ids for i in used): return False, "unknown_fact_id"
    return True, ""


def gen_row(x: Mapping[str, Any], bundle: Sequence[Fact], profile: Mapping[str, Any] | None, args: argparse.Namespace) -> dict[str, Any]:
    lookup = {f.id: f for f in bundle}
    used = [lookup[str(i)] for i in x["used_fact_ids"] if str(i) in lookup]
    imgs, vids = images_for(used, args.max_images)
    ctx = context(used, args.max_context_chars, hide_visual=True)
    q, ans = str(x["question"]).strip(), str(x["reference_answer"]).strip()
    extra = {"badcase_profile": dict(profile)} if profile else None
    return {
        "messages": messages(q, imgs, ctx), "question": q, "solution": ans, "reference_answer": ans,
        "task": str(x["task"]), "source": "badcase_conditioned_rl_builder" if profile else "finance_world_rl_builder",
        "split": "train", "images": imgs, "output_format": "free_text", "reward_type": "judge",
        "reward_subtype": "model_judge", "verifier_type": "model_judge",
        "metadata": {"evidence_ids": [f.id for f in used], "construction": meta("badcase_open_ended" if profile else "open_ended_evidence_bundle", used, vids, extra)},
    }


def generation_pool(index: Index, runner: Runner, rng: random.Random, target: int, args: argparse.Namespace, profiles: Sequence[Mapping[str, Any]] | None = None) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    accepted, rejected, pending = [], [], []
    attempts, max_attempts = 0, max(100, target * 4)
    profiles = list(profiles or [])
    while len(accepted) < target and attempts < max_attempts:
        attempts += 1
        bundle = index.bundle(rng, args.bundle_min, args.bundle_max)
        if len(bundle) < args.bundle_min: break
        profile = rng.choice(profiles) if profiles else None
        pending.append((gen_request(bundle, profile, args), bundle, profile))
        if len(pending) < args.llm_batch_size and attempts < max_attempts: continue
        outs = runner.batch([p[0] for p in pending], args.llm_temperature, args.llm_max_tokens)
        for (_, bundle, profile), x in zip(pending, outs):
            if isinstance(x, Exception):
                rejected.append({"stage":"generation","reason":f"llm_error:{x}","fact_ids":[f.id for f in bundle],"profile":profile}); continue
            ok, reason = valid_gen(x, {f.id for f in bundle})
            if ok: accepted.append(gen_row(x, bundle, profile, args))
            else: rejected.append({"stage":"generation","reason":reason,"output":x,"fact_ids":[f.id for f in bundle],"profile":profile})
            if len(accepted) >= target: break
        pending = []
    return dedup(accepted)[:target], rejected


def badcase_profiles(path: Path) -> list[dict[str, Any]]:
    out = []
    for row in iter_jsonl(path):
        c = row.get("classification") if isinstance(row.get("classification"), Mapping) else row
        task = str(pick(c, ("task_type", "task", "predicted_task"), "")).strip()
        err = str(pick(c, ("error_type", "primary_error_type", "error"), "")).strip()
        sc = pick(c, ("scenario_tags", "scenarios", "scenario"), [])
        if isinstance(sc, str): sc = [sc]
        if task or err: out.append({"task_type": task, "error_type": err, "scenario_tags": [str(x) for x in sc] if isinstance(sc, list) else []})
    return out


def split_profiles(profiles: Sequence[Mapping[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    r, g = [], []
    for p in profiles:
        err, task = str(p.get("error_type") or ""), str(p.get("task_type") or "")
        if err in BADCASE_REASONING_ERRORS or any(x in task for x in ("numerical", "table", "chart", "ocr", "ranking", "candlestick", "fact_consistency")):
            r.append(dict(p))
        else:
            g.append(dict(p))
    return r, g


def audit(reasoning: Sequence[Mapping[str, Any]], generation: Sequence[Mapping[str, Any]], rejected: Sequence[Mapping[str, Any]], facts: int, edges: int, profiles: int) -> dict[str, Any]:
    tasks, builders, sources, mods, difficulties = Counter(), Counter(), Counter(), Counter(), Counter()
    for route, rows in (("reasoning", reasoning), ("generation", generation)):
        for row in rows:
            tasks[f"{route}:{row.get('task','')}"] += 1
            sources[str(row.get("source") or "")] += 1
            mods[f"{route}:{'multi' if row.get('images') else 'text'}"] += 1
            construction = ((row.get("metadata") or {}).get("construction") or {})
            builders[str(construction.get("builder") or "unknown")] += 1
            difficulty = construction.get("difficulty") or {}
            if isinstance(difficulty, Mapping) and difficulty.get("label"):
                difficulties[f"{route}:{difficulty['label']}"] += 1
    return {
        "version": "rl_candidate_bank_v2", "facts": facts, "edges": edges, "task_vocabulary_size": len(TASKS),
        "badcase_profiles": profiles, "reasoning": len(reasoning), "generation": len(generation), "rejected": len(rejected),
        "task_counts": dict(tasks), "builder_counts": dict(builders), "source_counts": dict(sources),
        "modality_counts": dict(mods), "difficulty_counts": dict(difficulties),
    }


def main() -> None:
    args = parse_args(); rng = random.Random(args.seed); args.output_root.mkdir(parents=True, exist_ok=True)
    facts = load_facts(args.facts)
    if not facts and args.stage != "existing": raise SystemExit(f"no facts loaded from {args.facts}")
    edges = list(iter_jsonl(args.edges)) if args.edges.exists() else []
    index = Index(facts, edges)
    reasoning: list[dict[str, Any]] = []; generation: list[dict[str, Any]] = []; rejected: list[dict[str, Any]] = []

    if args.stage in {"existing", "all"} and args.existing_input:
        a, b = existing_candidates(args.existing_input, args.existing_limit); reasoning += a; generation += b
    if args.stage in {"reasoning", "all"}:
        reasoning += reasoning_pool(index, rng, args.reasoning_target, args)

    runner = None
    if args.stage in {"generation", "all"} and args.generation_target > 0:
        runner = Runner(args); rows, rej = generation_pool(index, runner, rng, args.generation_target, args); generation += rows; rejected += rej

    profiles = badcase_profiles(args.badcase_classification) if args.badcase_classification.exists() else []
    if args.stage in {"badcase", "all"} and args.badcase_target > 0 and profiles:
        rp, gp = split_profiles(profiles)
        rt = args.badcase_target if rp and not gp else int(args.badcase_target * 0.65) if rp else 0
        gt = args.badcase_target - rt
        badcase_reasoning: list[dict[str, Any]] = []
        attempts = 0
        while rt > 0 and len(badcase_reasoning) < rt and attempts < max(20, rt * 3):
            attempts += 1
            p = rng.choice(rp)
            need = rt - len(badcase_reasoning)
            badcase_reasoning.extend(reasoning_pool(index, rng, min(12, need), args, profile=p))
            badcase_reasoning = dedup(badcase_reasoning)[:rt]
        reasoning += badcase_reasoning
        if gt > 0 and gp:
            if runner is None: runner = Runner(args)
            rows, rej = generation_pool(index, runner, rng, gt, args, profiles=gp); generation += rows; rejected += rej

    reasoning, generation = dedup(reasoning), dedup(generation)
    write_jsonl(args.output_root / "reasoning.jsonl", reasoning)
    write_jsonl(args.output_root / "generation.jsonl", generation)
    write_jsonl(args.output_root / "rejected.jsonl", rejected)
    report = audit(reasoning, generation, rejected, len(facts), len(edges), len(profiles))
    (args.output_root / "audit.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()