#!/usr/bin/env python3
"""Build WebSailor-style synthetic financial reasoning data from data/raw.

Pipeline:
1. Extract source units from structured/text/image files under data/raw.
2. Use a VLM/LLM to extract evidence-grounded financial facts.
3. Build a relation graph and sample non-linear subgraphs with random walks.
4. Generate obfuscated, multi-step numerical questions under hard constraints.
5. Programmatically verify arithmetic and grounding, then reconstruct concise reasoning.
6. Export FINAR-VL SFT and Reasoning-RL JSONL.
"""

from __future__ import annotations

import argparse
import ast
import base64
import csv
import hashlib
import io
import json
import os
import random
import re
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Iterable

from PIL import Image


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RAW_ROOT = PROJECT_ROOT / "data" / "raw"
DEFAULT_OUTPUT_ROOT = PROJECT_ROOT / "data" / "synthetic" / "finance_sailorfog"
DEFAULT_BASE_URL = "https://api-inference.modelscope.cn/v1"
DEFAULT_MODEL = "Qwen/Qwen3-VL-235B-A22B-Instruct"
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}
SUPPORTED_SUFFIXES = {".jsonl", ".json", ".csv", ".parquet", ".txt", ".md"} | IMAGE_SUFFIXES
SUPERVISION_KEYS = {
    "answer",
    "answers",
    "assistant",
    "gold",
    "gold_answer",
    "label",
    "labels",
    "response",
    "solution",
    "target",
    "program",
    "programs",
    "cot",
    "reasoning",
    "rationale",
    "explanation",
    "question",
    "questions",
    "query",
    "prompt",
    "instruction",
    "choices",
    "options",
}
ALLOWED_CONSTANTS = {
    Decimal("0"),
    Decimal("1"),
    Decimal("2"),
    Decimal("4"),
    Decimal("12"),
    Decimal("100"),
    Decimal("360"),
    Decimal("365"),
    Decimal("10000"),
    Decimal("100000000"),
}
NUMBER_RE = re.compile(r"[-+]?\d[\d,]*(?:\.\d+)?")


FACT_SYSTEM_PROMPT = """你是金融证据抽取器。只从输入原始材料和图片中抽取可以直接核验的事实，不做推测、不补常识、不使用原数据集的答案字段作为证据。
严格输出单个 JSON 对象：
{"facts":[{"entity":"主体","metric":"指标或属性","value_text":"原文值","numeric_value":"若为数值则给十进制数字字符串，否则为空字符串","unit":"单位及量级","period":"报告期/日期","scope":"合并/母公司/分部/产品等口径","fact_type":"numeric|categorical|temporal|text","evidence_quote":"尽量短的原文证据","page":null,"source_mode":"text|image","image_index":null}]}
要求：
1. 每条事实必须能在输入中逐字或从图表直接读出；禁止推导后的数值。
2. numeric_value 保持 value_text 的原始量级，例如“12.3亿元”写 12.3，unit 写“亿元”；“8.2%”写 8.2，unit 写“%”。
3. entity、metric、period、scope 能确定时必须写明；不能确定就留空字符串。
4. source_mode=image 时 image_index 使用从 0 开始的图片序号；source_mode=text 时为 null。
5. 优先抽取收入、利润、现金流、资产负债、增长率、比率、估值、风险指标、分部数据、行业/公司对比等可组合事实。
只输出 JSON。"""


QUESTION_SYSTEM_PROMPT = """你是金融困难问题构造器。输入是一张从真实金融材料抽取的证据子图。你要模仿 WebSailor 的“复杂子图 + 信息模糊化”思想，生成一条可程序验证的金融数值推理题。
严格输出单个 JSON 对象：
{
  "question":"中文问题",
  "answer_value":"最终十进制数字字符串",
  "answer_unit":"最终单位",
  "answer":"最终答案文本，只含最终数值和单位",
  "evidence_ids":["事实ID"],
  "calculation_steps":[
    {"expression":"只使用 v0/v1/... 与允许常数的算式","claimed_result":"十进制数字字符串","unit":"单位"},
    {"expression":"必须引用上一结果 s1 的算式","claimed_result":"十进制数字字符串","unit":"单位"}
  ],
  "obfuscations":[{"type":"time_range|entity_description|metric_description|qualitative_anchor","original":"被隐藏的直接定位线索","rendered":"题目中的间接描述","evidence_ids":["事实ID"]}]
}
硬约束：
1. evidence_ids 至少 3 个，且所有计算变量必须来自输入 facts；不得新增任何金融数字、比例、日期、主体、业务口径或外部事实。
2. calculation_steps 至少 2 步；从第 2 步开始必须直接引用上一步 s1/s2/...，形成依赖链，禁止两次并列一步运算。
3. 表达式只能使用输入给出的 v0/v1/...、前序 s1/s2/...、括号和 + - * /；字面常数只允许 0,1,2,4,12,100,360,365,10000,100000000。
4. 最终答案必须由最后一步唯一得到，且不能直接等于某个输入事实值。
5. 必须做至少 1 个信息模糊化：只模糊“定位线索”，例如精确期点改成前后期描述、主体名改成可唯一识别的业务描述、指标名改成财务定义描述。不得模糊计算所需的精确数值，不得造成多解。
6. 题目应迫使模型进行跨证据定位、比较/组合和数值计算；避免直接问某个表格单元格。
7. 金融口径必须一致：主体、报告期、合并/母公司/分部、币种、单位量级必须可核验。涉及单位换算时只能使用允许常数。
8. 不得根据负现金流等单一信号断言造假、利润失真或经营失败；不得生成投资买卖建议。
9. question 中出现的所有阿拉伯数字必须来自输入事实/报告期或允许常数；answer 不得泄露在 question 中。
只输出 JSON。"""


RECONSTRUCT_SYSTEM_PROMPT = """你是金融推导重建器。给定已经程序验证通过的问题、证据和计算骨架，写简短、教学式推导。只解释已验证步骤，不增加新事实、新数字或额外判断。输出 JSON：{"reasoning":"2到4句简洁推导"}。不要输出思维草稿或探索过程。"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="WebSailor-style financial data synthesis")
    parser.add_argument("--stage", choices=("extract", "graph", "synthesize", "all"), default="all")
    parser.add_argument("--raw-root", type=Path, default=DEFAULT_RAW_ROOT)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--base-url", default=os.environ.get("FINAR_SYNTH_BASE_URL", DEFAULT_BASE_URL))
    parser.add_argument("--api-key", default=os.environ.get("FINAR_SYNTH_API_KEY") or os.environ.get("MODELSCOPE_SDK_TOKEN") or "EMPTY")
    parser.add_argument("--model", default=os.environ.get("FINAR_SYNTH_MODEL", DEFAULT_MODEL))
    parser.add_argument("--reconstruct-model", default=os.environ.get("FINAR_RECONSTRUCT_MODEL", ""))
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--max-units", type=int, default=0)
    parser.add_argument("--max-unit-chars", type=int, default=16000)
    parser.add_argument("--target", type=int, default=2000)
    parser.add_argument("--attempt-multiplier", type=int, default=20)
    parser.add_argument("--min-nodes", type=int, default=5)
    parser.add_argument("--min-edges", type=int, default=5)
    parser.add_argument("--max-nodes", type=int, default=9)
    parser.add_argument("--min-evidence-groups", type=int, default=2)
    parser.add_argument("--require-image", action="store_true")
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def stable_id(prefix: str, *parts: Any) -> str:
    payload = "\0".join(str(part) for part in parts)
    return f"{prefix}_{hashlib.sha256(payload.encode('utf-8')).hexdigest()[:16]}"


def strip_supervision(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: strip_supervision(item) for key, item in value.items() if str(key).casefold() not in SUPERVISION_KEYS}
    if isinstance(value, list):
        return [strip_supervision(item) for item in value]
    return value


def iter_file_records(path: Path) -> Iterable[tuple[int, Any]]:
    suffix = path.suffix.lower()
    if suffix == ".jsonl":
        with path.open(encoding="utf-8-sig") as handle:
            for index, line in enumerate(handle, 1):
                if line.strip():
                    yield index, json.loads(line)
    elif suffix == ".json":
        value = json.loads(path.read_text(encoding="utf-8-sig"))
        if isinstance(value, list):
            for index, row in enumerate(value, 1):
                yield index, row
        elif isinstance(value, dict):
            sequence = next((value[key] for key in ("data", "items", "records", "examples", "questions") if isinstance(value.get(key), list)), None)
            if sequence is None:
                yield 1, value
            else:
                for index, row in enumerate(sequence, 1):
                    yield index, row
    elif suffix == ".csv":
        with path.open(encoding="utf-8-sig", newline="") as handle:
            for index, row in enumerate(csv.DictReader(handle), 1):
                yield index, row
    elif suffix == ".parquet":
        import pyarrow.parquet as pq

        index = 0
        for batch in pq.ParquetFile(path).iter_batches(batch_size=256):
            for row in batch.to_pylist():
                index += 1
                yield index, row
    elif suffix in {".txt", ".md"}:
        yield 1, {"text": path.read_text(encoding="utf-8", errors="replace")}
    elif suffix in IMAGE_SUFFIXES:
        yield 1, {"image": path.as_posix()}


def resolve_image(value: str, source_file: Path, raw_root: Path) -> Path | None:
    candidate = Path(value)
    candidates = [candidate] if candidate.is_absolute() else [source_file.parent / candidate, raw_root / candidate, PROJECT_ROOT / candidate]
    for path in candidates:
        if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES:
            return path.resolve()
    return None


def collect_images(value: Any, source_file: Path, raw_root: Path) -> list[str]:
    found: list[Path] = []

    def visit(item: Any) -> None:
        if isinstance(item, dict):
            for nested in item.values():
                visit(nested)
        elif isinstance(item, list):
            for nested in item:
                visit(nested)
        elif isinstance(item, str) and Path(item).suffix.lower() in IMAGE_SUFFIXES:
            resolved = resolve_image(item, source_file, raw_root)
            if resolved is not None and resolved not in found:
                found.append(resolved)

    visit(value)
    if source_file.suffix.lower() in IMAGE_SUFFIXES and source_file.resolve() not in found:
        found.insert(0, source_file.resolve())
    paths = []
    for path in found[:5]:
        try:
            paths.append(path.relative_to(PROJECT_ROOT.resolve()).as_posix())
        except ValueError:
            continue
    return paths


def record_source_id(record: Any, index: int) -> str:
    if isinstance(record, dict):
        for key in ("document_id", "doc_id", "report_id", "source_id", "sample_id", "id", "uid", "qid"):
            if record.get(key) not in (None, ""):
                return str(record[key])
    return str(index)


def record_page(record: Any) -> int | None:
    if isinstance(record, dict):
        for key in ("page_number", "page_num", "page"):
            value = record.get(key)
            if isinstance(value, int):
                return value
            if isinstance(value, str) and value.isdigit():
                return int(value)
    return None


def extract_source_units(raw_root: Path, max_units: int, max_chars: int) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    units: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    for path in sorted(raw_root.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in SUPPORTED_SUFFIXES:
            continue
        try:
            for index, record in iter_file_records(path):
                cleaned = strip_supervision(record)
                text = json.dumps(cleaned, ensure_ascii=False, separators=(",", ":"))
                if not text.strip() and path.suffix.lower() not in IMAGE_SUFFIXES:
                    continue
                relative = path.relative_to(PROJECT_ROOT).as_posix()
                dataset = path.relative_to(raw_root).parts[0] if path != raw_root else "raw"
                source_id = record_source_id(record, index)
                units.append(
                    {
                        "unit_id": stable_id("u", relative, source_id, index),
                        "dataset": dataset,
                        "source_ref": f"{relative}#{index}",
                        "source_id": source_id,
                        "page": record_page(record),
                        "text": text[:max_chars],
                        "images": collect_images(record, path, raw_root),
                    }
                )
                if max_units and len(units) >= max_units:
                    return units, failures
        except Exception as error:
            failures.append({"stage": "extract", "source": str(path), "error": str(error)})
    return units, failures


def image_data_url(path: Path) -> str:
    image = Image.open(path).convert("RGB")
    image.thumbnail((2048, 2048), Image.Resampling.LANCZOS)
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=90)
    return f"data:image/jpeg;base64,{base64.b64encode(buffer.getvalue()).decode('ascii')}"


def extract_json_object(text: str) -> dict[str, Any]:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```(?:json)?\s*", "", stripped)
        stripped = re.sub(r"\s*```$", "", stripped)
    start = stripped.find("{")
    end = stripped.rfind("}")
    if start < 0 or end < start:
        raise ValueError("model output contains no JSON object")
    return json.loads(stripped[start : end + 1])


def call_json(client: Any, model: str, system_prompt: str, prompt: str, images: list[str], temperature: float, max_tokens: int) -> dict[str, Any]:
    content: list[dict[str, Any]] = [{"type": "text", "text": prompt}]
    for image in images:
        content.append({"type": "image_url", "image_url": {"url": image_data_url(PROJECT_ROOT / image)}})
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": content}],
        temperature=temperature,
        top_p=0.9,
        max_tokens=max_tokens,
    )
    return extract_json_object(response.choices[0].message.content or "")


def decimal_string(value: Any) -> str:
    text = str(value or "").strip().replace(",", "")
    if not text:
        return ""
    try:
        return format(Decimal(text), "f")
    except InvalidOperation:
        return ""


def close_decimal(left: Decimal, right: Decimal) -> bool:
    tolerance = max(Decimal("0.000001"), abs(left) * Decimal("0.000001"))
    return abs(left - right) <= tolerance


def extract_unit_facts(client: Any, model: str, unit: dict[str, Any]) -> list[dict[str, Any]]:
    prompt = f"source_ref={unit['source_ref']}\npage={unit.get('page')}\n原始材料：\n{unit['text']}"
    result = call_json(client, model, FACT_SYSTEM_PROMPT, prompt, unit["images"], 0.1, 4096)
    facts = []
    for index, raw in enumerate(result.get("facts") or []):
        if not isinstance(raw, dict):
            continue
        quote = str(raw.get("evidence_quote") or "").strip()
        metric = str(raw.get("metric") or "").strip()
        if not quote or not metric:
            continue
        numeric_value = decimal_string(raw.get("numeric_value"))
        source_mode = "image" if raw.get("source_mode") == "image" else "text"
        image_index = raw.get("image_index") if source_mode == "image" else None
        image_path = ""
        if isinstance(image_index, int) and 0 <= image_index < len(unit["images"]):
            image_path = unit["images"][image_index]
        if source_mode == "image" and not image_path:
            continue
        if source_mode == "text":
            haystack = re.sub(r"\s+", "", unit["text"])
            needle = re.sub(r"\s+", "", quote)
            if not needle or needle not in haystack:
                continue
        if numeric_value:
            observed_numbers = []
            for text in (quote, str(raw.get("value_text") or "")):
                for match in NUMBER_RE.findall(text):
                    try:
                        observed_numbers.append(Decimal(match.replace(",", "")))
                    except InvalidOperation:
                        pass
            if not any(close_decimal(Decimal(numeric_value), observed) for observed in observed_numbers):
                continue
        facts.append(
            {
                "fact_id": stable_id("f", unit["unit_id"], index, quote, metric),
                "unit_id": unit["unit_id"],
                "dataset": unit["dataset"],
                "source_ref": unit["source_ref"],
                "source_id": unit["source_id"],
                "page": raw.get("page") if isinstance(raw.get("page"), int) else unit.get("page"),
                "entity": str(raw.get("entity") or "").strip(),
                "metric": metric,
                "value_text": str(raw.get("value_text") or "").strip(),
                "numeric_value": numeric_value,
                "unit": str(raw.get("unit") or "").strip(),
                "period": str(raw.get("period") or "").strip(),
                "scope": str(raw.get("scope") or "").strip(),
                "fact_type": str(raw.get("fact_type") or ("numeric" if numeric_value else "text")),
                "evidence_quote": quote[:600],
                "source_mode": source_mode,
                "image": image_path,
            }
        )
    return facts


def build_facts(client: Any, model: str, units: list[dict[str, Any]], workers: int) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    facts: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(extract_unit_facts, client, model, unit): unit for unit in units}
        for future in as_completed(futures):
            unit = futures[future]
            try:
                facts.extend(future.result())
            except Exception as error:
                failures.append({"stage": "fact_extraction", "source": unit["source_ref"], "error": str(error)})
    facts.sort(key=lambda fact: fact["fact_id"])
    return facts, failures


def norm(value: str) -> str:
    return re.sub(r"[^\u4e00-\u9fffA-Za-z0-9]+", "", value).casefold()


def fact_group(fact: dict[str, Any]) -> str:
    page = fact.get("page")
    return f"{fact['source_ref']}@{page}" if page is not None else fact["source_ref"]


def build_edges(facts: list[dict[str, Any]]) -> list[dict[str, str]]:
    groups: dict[tuple[str, str], list[str]] = defaultdict(list)
    for fact in facts:
        entity = norm(fact["entity"])
        metric = norm(fact["metric"])
        period = norm(fact["period"])
        if entity and metric:
            groups[("entity_metric", f"{entity}|{metric}")].append(fact["fact_id"])
        if entity and period:
            groups[("entity_period", f"{entity}|{period}")].append(fact["fact_id"])
        if metric and period:
            groups[("metric_period", f"{metric}|{period}")].append(fact["fact_id"])
        groups[("evidence_group", fact_group(fact))].append(fact["fact_id"])

    edges: dict[tuple[str, str, str], dict[str, str]] = {}
    edge_type_map = {
        "entity_metric": "same_metric_cross_period",
        "entity_period": "same_entity_same_period",
        "metric_period": "peer_comparison",
        "evidence_group": "same_evidence_group",
    }
    for (group_type, _), ids in groups.items():
        ids = sorted(set(ids))[:20]
        for left, right in zip(ids, ids[1:]):
            a, b = sorted((left, right))
            edge_type = edge_type_map[group_type]
            edges[(a, b, edge_type)] = {"a": a, "b": b, "type": edge_type}
    return sorted(edges.values(), key=lambda edge: (edge["a"], edge["b"], edge["type"]))


def graph_adjacency(edges: list[dict[str, str]]) -> dict[str, list[tuple[str, str]]]:
    adjacency: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for edge in edges:
        adjacency[edge["a"]].append((edge["b"], edge["type"]))
        adjacency[edge["b"]].append((edge["a"], edge["type"]))
    return adjacency


def sample_subgraph(rng: random.Random, facts_by_id: dict[str, dict[str, Any]], adjacency: dict[str, list[tuple[str, str]]], min_nodes: int, min_edges: int, max_nodes: int) -> tuple[list[dict[str, Any]], list[dict[str, str]]] | None:
    seeds = [fact_id for fact_id, fact in facts_by_id.items() if fact["numeric_value"] and adjacency.get(fact_id)]
    if not seeds:
        return None
    seeds.sort(key=lambda fact_id: (len(adjacency[fact_id]), fact_id))
    seed = rng.choice(seeds[: max(1, len(seeds) // 2)])
    nodes = [seed]
    node_set = {seed}
    sampled_edges: dict[tuple[str, str, str], dict[str, str]] = {}
    current = seed

    for _ in range(max_nodes * 8):
        base = rng.choice(nodes) if rng.random() < 0.45 else current
        options = [(neighbor, edge_type) for neighbor, edge_type in adjacency.get(base, []) if neighbor not in node_set]
        if not options:
            expandable = [node for node in nodes if any(neighbor not in node_set for neighbor, _ in adjacency.get(node, []))]
            if not expandable:
                break
            base = rng.choice(expandable)
            options = [(neighbor, edge_type) for neighbor, edge_type in adjacency[base] if neighbor not in node_set]
        neighbor, edge_type = rng.choice(options)
        a, b = sorted((base, neighbor))
        sampled_edges[(a, b, edge_type)] = {"a": a, "b": b, "type": edge_type}
        nodes.append(neighbor)
        node_set.add(neighbor)
        current = neighbor
        for linked, linked_type in adjacency.get(neighbor, []):
            if linked in node_set:
                x, y = sorted((neighbor, linked))
                sampled_edges[(x, y, linked_type)] = {"a": x, "b": y, "type": linked_type}
        if len(nodes) >= min_nodes and len(sampled_edges) >= min_edges:
            break
        if len(nodes) >= max_nodes:
            break

    if len(nodes) < min_nodes or len(sampled_edges) < min_edges:
        return None
    return [facts_by_id[fact_id] for fact_id in nodes], list(sampled_edges.values())


def subgraph_hardness(facts: list[dict[str, Any]], edges: list[dict[str, str]], min_evidence_groups: int, require_image: bool) -> tuple[bool, str]:
    numeric = [fact for fact in facts if fact["numeric_value"]]
    groups = {fact_group(fact) for fact in facts}
    relation_types = {edge["type"] for edge in edges}
    degree = Counter()
    for edge in edges:
        degree[edge["a"]] += 1
        degree[edge["b"]] += 1
    if len(numeric) < 3:
        return False, "subgraph_numeric_facts_lt_3"
    if len(groups) < min_evidence_groups:
        return False, "subgraph_evidence_groups_too_few"
    if len(relation_types) < 2:
        return False, "subgraph_relation_types_lt_2"
    if max(degree.values(), default=0) < 2:
        return False, "subgraph_has_no_branch"
    if require_image and not any(fact.get("image") for fact in facts):
        return False, "subgraph_has_no_image"
    periods = {norm(fact["period"]) for fact in numeric if norm(fact["period"])}
    metrics = {norm(fact["metric"]) for fact in numeric if norm(fact["metric"])}
    if len(periods) < 2 and len(metrics) < 3:
        return False, "subgraph_temporal_or_metric_diversity_too_low"
    return True, "accepted"


def candidate_prompt(facts: list[dict[str, Any]], edges: list[dict[str, str]]) -> tuple[str, dict[str, str]]:
    aliases: dict[str, str] = {}
    rendered = []
    numeric_index = 0
    for fact in facts:
        item = dict(fact)
        if fact["numeric_value"]:
            alias = f"v{numeric_index}"
            numeric_index += 1
            aliases[alias] = fact["fact_id"]
            item["variable"] = alias
        else:
            item["variable"] = ""
        rendered.append(item)
    payload = {"facts": rendered, "edges": edges}
    return "证据子图：\n" + json.dumps(payload, ensure_ascii=False, separators=(",", ":")), aliases


def expression_names(expression: str) -> set[str]:
    tree = ast.parse(expression, mode="eval")
    return {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}


def eval_expression(expression: str, values: dict[str, Decimal]) -> Decimal:
    tree = ast.parse(expression, mode="eval")

    def evaluate(node: ast.AST) -> Decimal:
        if isinstance(node, ast.Expression):
            return evaluate(node.body)
        if isinstance(node, ast.Name) and node.id in values:
            return values[node.id]
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            value = Decimal(str(node.value))
            if value not in ALLOWED_CONSTANTS:
                raise ValueError(f"literal constant not allowed: {value}")
            return value
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
            value = evaluate(node.operand)
            return value if isinstance(node.op, ast.UAdd) else -value
        if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Sub, ast.Mult, ast.Div)):
            left = evaluate(node.left)
            right = evaluate(node.right)
            if isinstance(node.op, ast.Add):
                return left + right
            if isinstance(node.op, ast.Sub):
                return left - right
            if isinstance(node.op, ast.Mult):
                return left * right
            return left / right
        raise ValueError("unsupported expression")

    return evaluate(tree)


def allowed_question_numbers(facts: list[dict[str, Any]]) -> list[Decimal]:
    allowed = list(ALLOWED_CONSTANTS)
    for fact in facts:
        if fact["numeric_value"]:
            allowed.append(Decimal(fact["numeric_value"]))
        for text in (fact["period"], fact["value_text"]):
            for match in NUMBER_RE.findall(text or ""):
                try:
                    allowed.append(Decimal(match.replace(",", "")))
                except InvalidOperation:
                    pass
    return allowed


def verify_candidate(candidate: dict[str, Any], facts: list[dict[str, Any]], aliases: dict[str, str], min_evidence_groups: int) -> tuple[bool, str, dict[str, Any]]:
    fact_map = {fact["fact_id"]: fact for fact in facts}
    evidence_ids = candidate.get("evidence_ids") or []
    if len(set(evidence_ids)) < 3 or any(fact_id not in fact_map for fact_id in evidence_ids):
        return False, "invalid_evidence_ids", {}
    used_facts = [fact_map[fact_id] for fact_id in dict.fromkeys(evidence_ids)]
    if len({fact_group(fact) for fact in used_facts}) < min_evidence_groups:
        return False, "used_evidence_groups_too_few", {}

    steps = candidate.get("calculation_steps") or []
    if len(steps) < 2:
        return False, "calculation_steps_lt_2", {}
    values = {alias: Decimal(fact_map[fact_id]["numeric_value"]) for alias, fact_id in aliases.items() if fact_map[fact_id]["numeric_value"]}
    used_aliases: set[str] = set()
    step_results: list[Decimal] = []
    for index, step in enumerate(steps, 1):
        expression = str(step.get("expression") or "")
        try:
            names = expression_names(expression)
            if any(name not in values for name in names):
                return False, "expression_uses_unknown_variable", {}
            if index > 1 and f"s{index - 1}" not in names:
                return False, "calculation_chain_not_dependent", {}
            used_aliases.update(name for name in names if name.startswith("v"))
            result = eval_expression(expression, values)
            claimed = Decimal(decimal_string(step.get("claimed_result")))
        except Exception:
            return False, "arithmetic_expression_invalid", {}
        if not close_decimal(result, claimed):
            return False, "claimed_step_result_mismatch", {}
        values[f"s{index}"] = result
        step_results.append(result)

    calc_fact_ids = {aliases[alias] for alias in used_aliases if alias in aliases}
    if len(calc_fact_ids) < 3 or not calc_fact_ids.issubset(set(evidence_ids)):
        return False, "calculation_uses_lt_3_grounded_facts", {}

    answer_value_text = decimal_string(candidate.get("answer_value"))
    if not answer_value_text:
        return False, "answer_value_invalid", {}
    answer_value = Decimal(answer_value_text)
    if not close_decimal(answer_value, step_results[-1]):
        return False, "final_answer_mismatch", {}
    if any(close_decimal(answer_value, Decimal(fact_map[fact_id]["numeric_value"])) for fact_id in calc_fact_ids):
        return False, "answer_is_direct_fact", {}

    question = str(candidate.get("question") or "").strip()
    answer = str(candidate.get("answer") or "").strip()
    if not question or not answer:
        return False, "question_or_answer_empty", {}
    answer_numbers = []
    for match in NUMBER_RE.findall(answer):
        try:
            answer_numbers.append(Decimal(match.replace(",", "")))
        except InvalidOperation:
            pass
    if len(answer_numbers) != 1 or not close_decimal(answer_numbers[0], answer_value):
        return False, "answer_format_invalid", {}
    for match in NUMBER_RE.findall(question):
        try:
            if close_decimal(Decimal(match.replace(",", "")), answer_value):
                return False, "answer_leaked_in_question", {}
        except InvalidOperation:
            pass

    allowed_numbers = allowed_question_numbers(used_facts)
    for match in NUMBER_RE.findall(question):
        value = Decimal(match.replace(",", ""))
        if not any(close_decimal(value, allowed) for allowed in allowed_numbers):
            return False, "question_contains_ungrounded_number", {}

    obfuscations = candidate.get("obfuscations") or []
    if not obfuscations:
        return False, "missing_obfuscation", {}
    valid_obfuscation = False
    for item in obfuscations:
        original = str(item.get("original") or "").strip()
        rendered = str(item.get("rendered") or "").strip()
        refs = set(item.get("evidence_ids") or [])
        if not (original and rendered and rendered in question and original not in question and refs and refs.issubset(set(evidence_ids))):
            continue
        masks_required_value = False
        for fact_id in refs:
            fact = fact_map[fact_id]
            numeric_texts = {str(fact.get("value_text") or "").strip(), str(fact.get("numeric_value") or "").strip()}
            if original in numeric_texts and original:
                masks_required_value = True
                break
        if not masks_required_value:
            valid_obfuscation = True
            break
    if not valid_obfuscation:
        return False, "obfuscation_not_safe_or_effective", {}

    images = sorted({fact.get("image") for fact in used_facts if fact.get("image")})
    if len(images) > 5:
        return False, "too_many_images", {}
    return True, "accepted", {"used_facts": used_facts, "calc_fact_ids": sorted(calc_fact_ids), "step_results": [format(value, "f") for value in step_results], "images": images}


def deterministic_reasoning(candidate: dict[str, Any]) -> str:
    lines = []
    for index, step in enumerate(candidate["calculation_steps"], 1):
        lines.append(f"第{index}步得到 {step['claimed_result']}{step.get('unit', '')}。")
    return "".join(lines)


def reconstruct_reasoning(client: Any, model: str, candidate: dict[str, Any], used_facts: list[dict[str, Any]]) -> str:
    prompt = json.dumps({"question": candidate["question"], "evidence": used_facts, "calculation_steps": candidate["calculation_steps"], "answer": candidate["answer"]}, ensure_ascii=False, separators=(",", ":"))
    try:
        result = call_json(client, model, RECONSTRUCT_SYSTEM_PROMPT, prompt, [], 0.1, 1024)
        reasoning = str(result.get("reasoning") or "").strip()
        if reasoning:
            return reasoning
    except Exception:
        pass
    return deterministic_reasoning(candidate)


def render_training_prompt(candidate: dict[str, Any], used_facts: list[dict[str, Any]], images: list[str]) -> str:
    image_prefix = "<image>" * len(images)
    text_evidence = []
    for index, fact in enumerate(used_facts, 1):
        if fact["source_mode"] == "text":
            page = f"，第{fact['page']}页" if fact.get("page") is not None else ""
            text_evidence.append(f"[E{index}] {fact['source_ref']}{page}：{fact['evidence_quote']}")
    context = "\n".join(text_evidence)
    material = f"参考材料：\n{context}\n\n" if context else ""
    return f"{image_prefix}{material}问题：{candidate['question']}"


def build_rows(sample_id: str, candidate: dict[str, Any], verified: dict[str, Any], reasoning: str, graph_stats: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    used_facts = verified["used_facts"]
    images = verified["images"]
    user_prompt = render_training_prompt(candidate, used_facts, images)
    metadata = {
        "synthetic_method": "finance_sailorfog_v1",
        "source_refs": sorted({fact["source_ref"] for fact in used_facts}),
        "evidence_ids": [fact["fact_id"] for fact in used_facts],
        "calculation_fact_ids": verified["calc_fact_ids"],
        "calculation_steps": candidate["calculation_steps"],
        "obfuscations": candidate["obfuscations"],
        "graph_stats": graph_stats,
        "program_verification_checked": True,
    }
    sft = {
        "messages": [{"role": "user", "content": user_prompt}, {"role": "assistant", "content": f"{reasoning}\n\n答案：{candidate['answer']}"}],
        "source": "finance_sailorfog",
        "split": "train",
        "images": images,
        "task": "multi_step_numerical_reasoning",
        "metadata": metadata,
    }
    rl = {
        "sample_id": sample_id,
        "messages": [{"role": "user", "content": user_prompt}],
        "source": "finance_sailorfog",
        "split": "train",
        "images": images,
        "task": "multi_step_numerical_reasoning",
        "output_format": "number_or_free_text",
        "solution": candidate["answer"],
        "metadata": metadata,
        "reward_type": "rule",
        "reward_subtype": "numeric",
        "verifier_type": "numeric",
        "_reward_routing": {"version": "finance_sailorfog_v1", "reason": "verified_multi_step_numeric_synthesis", "program_verification_checked": True},
    }
    return sft, rl


def synthesize(client: Any, model: str, reconstruct_model: str, facts: list[dict[str, Any]], edges: list[dict[str, str]], args: argparse.Namespace) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], dict[str, int]]:
    rng = random.Random(args.seed)
    facts_by_id = {fact["fact_id"]: fact for fact in facts}
    adjacency = graph_adjacency(edges)
    sft_rows: list[dict[str, Any]] = []
    rl_rows: list[dict[str, Any]] = []
    candidates: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    reason_counts: Counter[str] = Counter()
    seen_questions: set[str] = set()

    for attempt in range(args.target * args.attempt_multiplier):
        if len(sft_rows) >= args.target:
            break
        sampled = sample_subgraph(rng, facts_by_id, adjacency, args.min_nodes, args.min_edges, args.max_nodes)
        if sampled is None:
            reason_counts["no_valid_subgraph"] += 1
            continue
        subgraph_facts, subgraph_edges = sampled
        hard_ok, hard_reason = subgraph_hardness(subgraph_facts, subgraph_edges, args.min_evidence_groups, args.require_image)
        if not hard_ok:
            reason_counts[hard_reason] += 1
            continue
        prompt, aliases = candidate_prompt(subgraph_facts, subgraph_edges)
        try:
            candidate = call_json(client, model, QUESTION_SYSTEM_PROMPT, prompt, [], 0.7, 4096)
        except Exception as error:
            reason_counts["question_generation_error"] += 1
            rejected.append({"stage": "question_generation", "attempt": attempt, "error": str(error)})
            continue
        valid, reason, verified = verify_candidate(candidate, subgraph_facts, aliases, args.min_evidence_groups)
        if not valid:
            reason_counts[reason] += 1
            rejected.append({"stage": "verification", "attempt": attempt, "reason": reason, "candidate": candidate})
            continue
        question_key = re.sub(r"\s+", "", candidate["question"])
        if question_key in seen_questions:
            reason_counts["duplicate_question"] += 1
            continue
        seen_questions.add(question_key)
        graph_stats = {
            "node_count": len(subgraph_facts),
            "edge_count": len(subgraph_edges),
            "relation_type_count": len({edge["type"] for edge in subgraph_edges}),
            "evidence_group_count": len({fact_group(fact) for fact in verified["used_facts"]}),
            "numeric_fact_count": sum(bool(fact["numeric_value"]) for fact in subgraph_facts),
        }
        sample_id = stable_id("sailorfog_fin", candidate["question"], candidate["answer"])
        reasoning = reconstruct_reasoning(client, reconstruct_model or model, candidate, verified["used_facts"])
        sft, rl = build_rows(sample_id, candidate, verified, reasoning, graph_stats)
        candidate_record = {"sample_id": sample_id, "candidate": candidate, "used_facts": verified["used_facts"], "graph_edges": subgraph_edges, "graph_stats": graph_stats}
        candidates.append(candidate_record)
        sft_rows.append(sft)
        rl_rows.append(rl)
        reason_counts["accepted"] += 1
    return sft_rows, rl_rows, candidates, rejected, dict(reason_counts)


def main() -> None:
    args = parse_args()
    args.output_root.mkdir(parents=True, exist_ok=True)
    failure_rows: list[dict[str, Any]] = []

    if args.stage in {"extract", "all"}:
        if not args.raw_root.is_dir():
            print(json.dumps({"error": f"raw directory not found: {args.raw_root}"}, ensure_ascii=False))
            return
        units, failures = extract_source_units(args.raw_root.resolve(), args.max_units, args.max_unit_chars)
        write_jsonl(args.output_root / "source_units.jsonl", units)
        failure_rows.extend(failures)
        print(json.dumps({"stage": "extract", "units": len(units), "failures": len(failures)}, ensure_ascii=False), flush=True)

    if args.stage in {"graph", "synthesize", "all"}:
        try:
            from openai import OpenAI

            client = OpenAI(api_key=args.api_key, base_url=args.base_url)
        except Exception as error:
            print(json.dumps({"error": f"cannot initialize OpenAI-compatible client: {error}"}, ensure_ascii=False))
            return

    if args.stage in {"graph", "all"}:
        units_path = args.output_root / "source_units.jsonl"
        if not units_path.is_file():
            print(json.dumps({"error": f"missing {units_path}; run --stage extract first"}, ensure_ascii=False))
            return
        units = read_jsonl(units_path)
        facts, failures = build_facts(client, args.model, units, args.workers)
        edges = build_edges(facts)
        write_jsonl(args.output_root / "graph_facts.jsonl", facts)
        write_jsonl(args.output_root / "graph_edges.jsonl", edges)
        failure_rows.extend(failures)
        print(json.dumps({"stage": "graph", "facts": len(facts), "edges": len(edges), "failures": len(failures)}, ensure_ascii=False), flush=True)

    if args.stage in {"synthesize", "all"}:
        facts_path = args.output_root / "graph_facts.jsonl"
        edges_path = args.output_root / "graph_edges.jsonl"
        if not facts_path.is_file() or not edges_path.is_file():
            print(json.dumps({"error": "missing graph_facts.jsonl or graph_edges.jsonl; run --stage graph first"}, ensure_ascii=False))
            return
        facts = read_jsonl(facts_path)
        edges = read_jsonl(edges_path)
        sft_rows, rl_rows, candidates, rejected, reasons = synthesize(client, args.model, args.reconstruct_model, facts, edges, args)
        write_jsonl(args.output_root / "candidates.jsonl", candidates)
        write_jsonl(args.output_root / "train_sft.jsonl", sft_rows)
        write_jsonl(args.output_root / "train_rl_reasoning.jsonl", rl_rows)
        failure_rows.extend(rejected)
        audit = {
            "method": "finance_sailorfog_v1",
            "raw_root": str(args.raw_root),
            "model": args.model,
            "target": args.target,
            "accepted": len(sft_rows),
            "facts": len(facts),
            "edges": len(edges),
            "reasons": reasons,
            "hard_constraints": {
                "min_nodes": args.min_nodes,
                "min_edges": args.min_edges,
                "min_evidence_groups": args.min_evidence_groups,
                "min_numeric_facts": 3,
                "min_calculation_steps": 2,
                "dependent_calculation_chain": True,
                "min_relation_types": 2,
                "graph_branch_required": True,
                "safe_obfuscation_required": True,
                "programmatic_arithmetic_verification": True,
                "max_images": 5,
            },
        }
        (args.output_root / "audit.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(audit, ensure_ascii=False), flush=True)

    if failure_rows:
        write_jsonl(args.output_root / "rejected.jsonl", failure_rows)


if __name__ == "__main__":
    main()
