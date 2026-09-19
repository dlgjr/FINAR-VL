#!/usr/bin/env python3
"""
Build FINAR-VL Generation-RL candidates with a two-model pipeline.

Model split
===========
- Evidence extraction / evidence fact normalization: 32B VLM only.
- Task planning, hard-sample construction, question generation, reference-answer
  generation, and optional construction verification: 235B VLM only.

The script intentionally separates the two model stages so a single 8-GPU DLC
machine does not need to keep 32B and 235B loaded at the same time.

Pipeline
========
1. evidence_units.jsonl + document_entities.jsonl
       -> 32B evidence extraction
       -> generation_evidence_facts.jsonl
2. evidence facts
       -> financial evidence graph
       -> graph-path / coherent-bundle sampling
       -> required facts + distractors + difficulty profile
3. sampled bundle
       -> 235B task planner
       -> Generation task skeleton
4. skeleton + original evidence/images
       -> 235B renderer
       -> question + grounded reference answer
5. optional 235B construction verification
       -> generation.jsonl

This script constructs data only. It does not perform rollout profiling and does
not implement reward scoring.
"""

from __future__ import annotations

import argparse
import ast
import base64
import gc
import hashlib
import io
import json
import math
import os
import random
import re
from collections import Counter, defaultdict, deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Iterator, Mapping, Sequence

from PIL import Image


PROJECT_ROOT = Path(__file__).resolve().parents[2]
FINANCE_WORLD_ROOT = PROJECT_ROOT / "data" / "synthetic" / "finance_world"
DEFAULT_EVIDENCE_UNITS = FINANCE_WORLD_ROOT / "evidence_units.jsonl"
DEFAULT_DOCUMENT_ENTITIES = FINANCE_WORLD_ROOT / "document_entities.jsonl"
DEFAULT_OUTPUT_ROOT = PROJECT_ROOT / "data" / "synthetic" / "generation_rl"
DEFAULT_BADCASE = PROJECT_ROOT / "data" / "synthetic" / "badcase_flywheel" / "classification.jsonl"
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}
NUMBER_RE = re.compile(r"[-+]?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?")
YEAR_RE = re.compile(r"(?<!\d)(20\d{2})(?!\d)")


def _first_existing(candidates: Sequence[Path]) -> Path:
    return next((path for path in candidates if path.exists()), candidates[0])


def default_evidence_model() -> Path:
    return _first_existing(
        [
            PROJECT_ROOT / "model" / "qwen32",
            PROJECT_ROOT / "models" / "qwen32",
            PROJECT_ROOT / "model" / "qwen32b",
            PROJECT_ROOT / "models" / "qwen32b",
            PROJECT_ROOT / "model" / "Qwen3-VL-32B-Instruct",
            PROJECT_ROOT / "models" / "Qwen3-VL-32B-Instruct",
        ]
    )


def default_construct_model() -> Path:
    return _first_existing(
        [
            PROJECT_ROOT / "model" / "qwen235",
            PROJECT_ROOT / "models" / "qwen235",
        ]
    )


GENERATION_TASK_PREFERENCES = (
    "financial_report_analysis",
    "financial_data_interpretation",
    "financial_metric_interpretation",
    "document_explanation",
    "document_comparative_explanation",
    "document_comparison",
    "document_inference",
    "financial_summarization",
    "document_summarization",
    "summary_announcement",
    "financial_risk_analysis",
    "financial_audit_fundamentals",
    "accounting_audit_reasoning",
    "financial_audit_and_controls",
    "business_strategy_analysis",
    "industry_analysis_and_competition",
    "industry_trend_inference",
    "research_report_opinion_qa",
    "risk_sentiment_policy",
    "financial_regulation_and_compliance",
    "economics_and_monetary_policy",
    "macroeconomic_impact_inference",
    "global_events_impact",
    "compliance_safety_suitability",
    "investment_advice_strategy",
    "portfolio_allocation_risk_return",
    "esg_investment_reasoning",
    "sustainable_finance",
)

OPEN_ENDED_ERROR_HINTS = {
    "explanation_error",
    "causal_attribution_error",
    "anomaly_interpretation_error",
    "fundamental_analysis_error",
    "audit_reasoning_error",
    "industry_trend_error",
    "company_comparison_error",
    "risk_identification_error",
    "risk_severity_error",
    "sentiment_error",
    "policy_interpretation_error",
    "policy_impact_error",
    "regulatory_interpretation_error",
    "compliance_judgment_error",
    "suitability_error",
    "strategy_evaluation_error",
    "portfolio_allocation_error",
    "portfolio_risk_return_error",
    "summary_keypoint_omission_error",
    "summary_fact_distortion_error",
    "announcement_interpretation_error",
    "unsupported_inference_error",
    "insufficient_evidence_handling_error",
    "answer_granularity_error",
}

VISUAL_SCENARIO_TAGS = {
    "single_table",
    "multi_table",
    "single_chart",
    "multi_chart",
    "table_chart_mixed",
    "text_table_mixed",
    "text_chart_mixed",
    "cross_modal",
    "relationship_diagram",
    "candlestick_chart",
}

FACT_TYPES = {
    "numeric_metric",
    "financial_claim",
    "risk_disclosure",
    "cause_explanation",
    "management_guidance",
    "policy_rule",
    "regulatory_requirement",
    "audit_finding",
    "event",
    "relationship",
    "segment_fact",
    "accounting_policy",
    "other",
}


EVIDENCE_SYSTEM = """你是 FINAR-VL 的金融证据事实抽取器。你的模型只负责从给定原始材料中抽取可用于后续 Generation RL 构造的证据事实。

要求：
1. 只抽取输入文本和图片中能够直接确认的事实，不使用外部知识，不推断公司动机，不补全缺失原因。
2. 数值事实需要尽量保留主体、期间、指标、scope、单位、币种和原始值。
3. 非数值事实可包括风险披露、原因说明、管理层指引、政策规则、监管要求、审计事项、事件、关系、会计政策等。
4. 如果事实来自图片，source_mode="image"，必须给 image_index；不要把看不清的内容猜出来。
5. 如果事实来自文本，source_mode="text"，evidence_quote 应是材料中的短证据片段。
6. 同一事实不要重复输出。
7. confidence 只能是 high / medium / low；low 不会进入后续构造。
8. fact_type 必须来自给定 fact_types。

严格输出单个 JSON：
{
  "facts": [
    {
      "fact_type": "numeric_metric",
      "entity": "",
      "period": "",
      "metric": "",
      "scope": "",
      "value_text": "",
      "numeric_value": "",
      "unit": "",
      "currency": "",
      "claim": "",
      "topic": "",
      "source_mode": "text|image",
      "image_index": null,
      "visual_type": "table|chart|candlestick|relationship_diagram|document|none",
      "evidence_quote": "",
      "confidence": "high|medium|low"
    }
  ]
}
只输出 JSON。"""


PLANNER_SYSTEM = """你是 FINAR-VL Generation RL 数据构造规划器。你收到的是已经抽取好的新金融证据事实、图上的关系路径、候选干扰事实和可选 Bad Case 能力画像。

你的任务是先构造一个开放式 Generation RL 任务骨架，不直接写最终答案。

原则：
1. task 必须逐字来自 task_labels。
2. required_fact_ids 必须来自 candidate_required_fact_ids；至少使用 2 条，hard 样本通常使用 4 条及以上。
3. distractor_ids 只能来自 candidate_distractor_ids，可以为空。干扰证据不能成为参考答案必需事实。
4. analysis_dimensions 必须具体，例如 revenue_growth / profitability / cashflow_quality / risk / audit_issue / policy_scope / peer_comparison / summary_keypoints。
5. 问题意图必须可以只凭 required facts 和原始图片/文本回答。
6. 不得要求股票价格预测、无法验证的未来预测或材料之外的外部知识。
7. 图像事实存在时，可以设计真实依赖图片的任务；不要把图片事实的完整值直接写进问题意图。
8. 若 evidence bundle 不足以形成自然、有训练价值的开放式任务，返回 reject。
9. 如果提供 badcase_profile，只借用其能力缺口作为构造约束；不得复述或改写原 Bad Case。

严格输出：
{
  "status": "accepted",
  "task": "task_labels 中一个",
  "task_intent": "一句话说明要训练的能力",
  "analysis_dimensions": ["..."],
  "required_fact_ids": ["..."],
  "distractor_ids": ["..."],
  "question_requirements": ["问题必须满足的约束"]
}

或：
{"status":"reject","reason":"..."}
只输出 JSON。"""


RENDER_SYSTEM = """你是 FINAR-VL Generation RL 数据生成器。输入包含已经固定的 task skeleton、required evidence、distractors 和原始图片。请严格按照 skeleton 生成最终训练问题和参考答案。

要求：
1. 不得修改 task、required_fact_ids、distractor_ids 和 analysis_dimensions。
2. question 必须自然、专业、明确，不写成元任务，不出现 fact_id、required evidence、distractor 等内部术语。
3. question 不得直接泄露最终结论或关键中间结果。
4. reference_answer 必须只使用 required evidence 能支持的内容。可以做必要的比较、归纳和材料内推理，但不能补充外部事实。
5. 若 required evidence 含图片事实，reference_answer 可以使用图片中的事实；最终用户输入会提供原始图片，不会把隐藏抽取值全部暴露在文本里。
6. distractor 只用于增加定位和口径判断难度，reference_answer 不应依赖 distractor。
7. 摘要类任务要覆盖 skeleton 指定的核心维度；分析类任务需要明确说明依据，避免空泛套话。
8. 不生成个性化买卖指令。

严格输出：
{
  "status": "accepted",
  "question": "...",
  "reference_answer": "...",
  "used_fact_ids": ["必须等于 required_fact_ids 的集合"]
}

或：
{"status":"reject","reason":"..."}
只输出 JSON。"""


VERIFY_SYSTEM = """你是 FINAR-VL Generation RL 构造结果检查器。只检查刚生成的数据是否与给定证据一致，不重新改写答案。

检查：
- question 是否可由 required evidence 回答；
- reference_answer 是否只包含 required evidence 支持的事实和合理材料内推理；
- entity / period / metric / scope / unit / currency 是否混淆；
- visual_required=true 时图片是否真正参与；
- 是否误用了 distractor；
- 是否存在问题中直接泄露答案；
- 是否自然且有训练价值。

严格输出：
{
  "accepted": true,
  "issues": [],
  "visual_required": true,
  "required_fact_ids": ["实际支撑答案的 fact_id"]
}
只输出 JSON。"""


@dataclass
class EvidenceUnit:
    unit_id: str
    document_id: str
    dataset: str
    source_ref: str
    page: str
    text: str
    images: list[str]
    layout: str
    metadata_hints: dict[str, Any]
    raw: dict[str, Any]


@dataclass
class EvidenceFact:
    fact_id: str
    unit_id: str
    document_id: str
    dataset: str
    source_ref: str
    page: str
    entity: str
    period: str
    fact_type: str
    metric: str
    scope: str
    value_text: str
    numeric_value: str
    unit: str
    currency: str
    claim: str
    topic: str
    source_mode: str
    image_index: int | None
    visual_type: str
    evidence_quote: str
    confidence: str
    images: list[str]
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class Bundle:
    required: list[EvidenceFact]
    distractors: list[EvidenceFact]
    path_edges: list[dict[str, str]]
    difficulty: dict[str, Any]
    badcase_profile: dict[str, Any] | None = None


@dataclass
class LLMRequest:
    system: str
    user: str
    images: list[Path]
    meta: dict[str, Any]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--stage",
        choices=("extract", "construct", "all"),
        default="all",
        help="extract=32B evidence facts; construct=235B Generation RL; all=sequentially run both.",
    )
    parser.add_argument("--evidence-units", type=Path, default=DEFAULT_EVIDENCE_UNITS)
    parser.add_argument("--document-entities", type=Path, default=DEFAULT_DOCUMENT_ENTITIES)
    parser.add_argument(
        "--evidence-facts",
        type=Path,
        default=None,
        help="Existing evidence fact JSONL. Defaults to <output-root>/generation_evidence_facts.jsonl.",
    )
    parser.add_argument("--badcase-classification", type=Path, default=DEFAULT_BADCASE)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)

    parser.add_argument("--evidence-model", type=Path, default=default_evidence_model())
    parser.add_argument("--construct-model", type=Path, default=default_construct_model())
    parser.add_argument("--evidence-backend", choices=("vllm", "openai"), default="vllm")
    parser.add_argument("--construct-backend", choices=("vllm", "openai"), default="vllm")
    parser.add_argument(
        "--evidence-base-url",
        default=os.environ.get("FINAR_EVIDENCE_BASE_URL", "http://127.0.0.1:8000/v1"),
    )
    parser.add_argument(
        "--construct-base-url",
        default=os.environ.get("FINAR_CONSTRUCT_BASE_URL", "http://127.0.0.1:8000/v1"),
    )
    parser.add_argument("--api-key", default=os.environ.get("FINAR_SYNTH_API_KEY", "EMPTY"))
    parser.add_argument("--tensor-parallel-size", type=int, default=8)
    parser.add_argument("--gpu-memory-utilization", type=float, default=0.90)
    parser.add_argument("--max-model-len", type=int, default=32768)
    parser.add_argument("--max-images", type=int, default=8)
    parser.add_argument("--extract-batch-size", type=int, default=12)
    parser.add_argument("--construct-batch-size", type=int, default=8)
    parser.add_argument("--extract-max-tokens", type=int, default=2500)
    parser.add_argument("--construct-max-tokens", type=int, default=2500)

    parser.add_argument("--max-units", type=int, default=0)
    parser.add_argument("--target", type=int, default=10000)
    parser.add_argument("--hard-ratio", type=float, default=0.70)
    parser.add_argument("--badcase-ratio", type=float, default=0.35)
    parser.add_argument("--min-required-facts", type=int, default=3)
    parser.add_argument("--max-required-facts", type=int, default=8)
    parser.add_argument("--max-distractors", type=int, default=5)
    parser.add_argument("--max-text-context-chars", type=int, default=9000)
    parser.add_argument("--verify", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def json_dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def stable_id(prefix: str, *parts: Any) -> str:
    payload = "|".join(str(part) for part in parts)
    return f"{prefix}_{hashlib.sha1(payload.encode('utf-8')).hexdigest()[:20]}"


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.is_file():
        return rows
    with path.open(encoding="utf-8-sig") as handle:
        for line_no, raw in enumerate(handle, 1):
            raw = raw.strip()
            if not raw:
                continue
            try:
                obj = json.loads(raw)
            except json.JSONDecodeError:
                continue
            if isinstance(obj, dict):
                obj.setdefault("_line", line_no)
                rows.append(obj)
    return rows


def write_jsonl(path: Path, rows: Iterable[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json_dumps(dict(row)) + "\n")


def normalize_text(value: Any) -> str:
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return "\n".join(normalize_text(item) for item in value if item not in (None, ""))
    if isinstance(value, Mapping):
        return json.dumps(value, ensure_ascii=False)
    return str(value or "").strip()


def normalize_images(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value] if value.strip() else []
    if isinstance(value, list):
        output: list[str] = []
        for item in value:
            if isinstance(item, str) and item.strip():
                output.append(item.strip())
            elif isinstance(item, Mapping) and isinstance(item.get("path"), str):
                output.append(str(item["path"]).strip())
        return output
    return []


def resolve_image(value: str, source_parent: Path | None = None) -> Path | None:
    if not value:
        return None
    raw = Path(value)
    if raw.is_absolute() and raw.is_file():
        return raw.resolve()
    roots = [
        PROJECT_ROOT,
        PROJECT_ROOT / "data",
        PROJECT_ROOT / "data" / "raw",
        FINANCE_WORLD_ROOT,
    ]
    if source_parent is not None:
        roots.insert(0, source_parent)
    for root in roots:
        candidate = (root / raw).resolve()
        if candidate.is_file() and candidate.suffix.lower() in IMAGE_SUFFIXES:
            return candidate
    return None


def portable_path(path: Path) -> str:
    try:
        return path.relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return str(path)


def load_units(path: Path) -> list[EvidenceUnit]:
    units: list[EvidenceUnit] = []
    for row in read_jsonl(path):
        units.append(
            EvidenceUnit(
                unit_id=str(row.get("unit_id") or stable_id("u", row.get("source_ref"), row.get("_line"))),
                document_id=str(row.get("document_id") or ""),
                dataset=str(row.get("dataset") or ""),
                source_ref=str(row.get("source_ref") or ""),
                page=str(row.get("page") or ""),
                text=normalize_text(row.get("text")),
                images=normalize_images(row.get("images")),
                layout=normalize_text(row.get("layout")),
                metadata_hints=dict(row.get("metadata_hints") or {}),
                raw=row,
            )
        )
    return units


def load_document_entities(path: Path) -> dict[str, dict[str, Any]]:
    entities: dict[str, dict[str, Any]] = {}
    for row in read_jsonl(path):
        document_id = str(row.get("document_id") or "")
        if document_id:
            entities[document_id] = row
    return entities


def task_vocabulary_from_sampler() -> tuple[str, ...]:
    tasks: set[str] = set()
    base = PROJECT_ROOT / "scripts" / "sft" / "sample_plan_base.py"
    wrapper = PROJECT_ROOT / "scripts" / "sft" / "sample_plan.py"
    if base.is_file():
        try:
            tree = ast.parse(base.read_text(encoding="utf-8"))
            for node in tree.body:
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name) and target.id == "TASK_TO_FAMILY":
                            value = ast.literal_eval(node.value)
                            if isinstance(value, dict):
                                tasks.update(str(key) for key in value)
        except Exception:
            pass
    if wrapper.is_file():
        text = wrapper.read_text(encoding="utf-8")
        tasks.update(re.findall(r'TASK_TO_FAMILY\["([^"]+)"\]\s*=', text))
    tasks.update(GENERATION_TASK_PREFERENCES)
    return tuple(sorted(tasks))


TASK_VOCABULARY = task_vocabulary_from_sampler()
TASK_SET = set(TASK_VOCABULARY)
GENERATION_TASKS = tuple(task for task in GENERATION_TASK_PREFERENCES if task in TASK_SET)


def unload_model(runner: Any) -> None:
    try:
        del runner
    except Exception:
        pass
    gc.collect()
    try:
        import torch

        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.ipc_collect()
    except Exception:
        pass


class QwenRunner:
    def __init__(
        self,
        *,
        backend: str,
        model: Path,
        base_url: str,
        api_key: str,
        tensor_parallel_size: int,
        gpu_memory_utilization: float,
        max_model_len: int,
        max_images: int,
    ) -> None:
        self.backend = backend
        self.model_name = str(model)
        self.max_images = max_images
        if backend == "openai":
            from openai import OpenAI

            self.client = OpenAI(api_key=api_key, base_url=base_url)
            self.processor = None
            self.llm = None
            self.SamplingParams = None
        else:
            from transformers import AutoProcessor
            from vllm import LLM, SamplingParams

            self.processor = AutoProcessor.from_pretrained(self.model_name, trust_remote_code=True)
            self.llm = LLM(
                model=self.model_name,
                tensor_parallel_size=tensor_parallel_size,
                gpu_memory_utilization=gpu_memory_utilization,
                max_model_len=max_model_len,
                trust_remote_code=True,
                limit_mm_per_prompt={"image": max_images},
            )
            self.SamplingParams = SamplingParams
            self.client = None

    @staticmethod
    def parse_json(text: str) -> dict[str, Any]:
        stripped = text.strip()
        stripped = re.sub(r"^```(?:json)?\s*", "", stripped)
        stripped = re.sub(r"\s*```$", "", stripped)
        start, end = stripped.find("{"), stripped.rfind("}")
        if start < 0 or end < start:
            raise ValueError("model output contains no JSON object")
        obj = json.loads(stripped[start : end + 1])
        if not isinstance(obj, dict):
            raise ValueError("model output is not a JSON object")
        return obj

    @staticmethod
    def image_data_url(path: Path) -> str:
        with Image.open(path) as image:
            image = image.convert("RGB")
            image.thumbnail((1800, 1800), Image.Resampling.LANCZOS)
            buffer = io.BytesIO()
            image.save(buffer, format="JPEG", quality=88)
        return "data:image/jpeg;base64," + base64.b64encode(buffer.getvalue()).decode("ascii")

    def _openai_one(self, request: LLMRequest, *, temperature: float, max_tokens: int) -> dict[str, Any]:
        content: list[dict[str, Any]] = [{"type": "text", "text": request.user}]
        for image in request.images[: self.max_images]:
            content.append({"type": "image_url", "image_url": {"url": self.image_data_url(image)}})
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": request.system},
                {"role": "user", "content": content},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return self.parse_json(response.choices[0].message.content or "")

    def batch(
        self,
        requests: Sequence[LLMRequest],
        *,
        temperature: float,
        max_tokens: int,
    ) -> list[dict[str, Any] | Exception]:
        if not requests:
            return []
        if self.backend == "openai":
            output: list[dict[str, Any] | Exception] = []
            for request in requests:
                try:
                    output.append(self._openai_one(request, temperature=temperature, max_tokens=max_tokens))
                except Exception as exc:
                    output.append(exc)
            return output

        from qwen_vl_utils import process_vision_info

        prompts: list[dict[str, Any]] = []
        for request in requests:
            content: list[dict[str, Any]] = [{"type": "text", "text": request.user}]
            for image in request.images[: self.max_images]:
                content.append({"type": "image", "image": str(image)})
            messages = [
                {"role": "system", "content": request.system},
                {"role": "user", "content": content},
            ]
            prompt = self.processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
            image_inputs, video_inputs = process_vision_info(messages)
            mm: dict[str, Any] = {}
            if image_inputs:
                mm["image"] = image_inputs
            if video_inputs:
                mm["video"] = video_inputs
            prompts.append({"prompt": prompt, "multi_modal_data": mm})

        sampling = self.SamplingParams(temperature=temperature, max_tokens=max_tokens)
        raw = self.llm.generate(prompts, sampling, use_tqdm=False)
        output: list[dict[str, Any] | Exception] = []
        for item in raw:
            try:
                output.append(self.parse_json(item.outputs[0].text))
            except Exception as exc:
                output.append(exc)
        return output


def evidence_request(unit: EvidenceUnit, entity: Mapping[str, Any], max_images: int) -> LLMRequest:
    images: list[Path] = []
    for value in unit.images[:max_images]:
        path = resolve_image(value)
        if path is not None:
            images.append(path)
    payload = {
        "fact_types": sorted(FACT_TYPES),
        "document_entity": dict(entity),
        "unit": {
            "unit_id": unit.unit_id,
            "document_id": unit.document_id,
            "source_ref": unit.source_ref,
            "page": unit.page,
            "text": unit.text,
            "layout": unit.layout,
            "metadata_hints": unit.metadata_hints,
            "image_count": len(images),
        },
    }
    return LLMRequest(
        system=EVIDENCE_SYSTEM,
        user=json.dumps(payload, ensure_ascii=False, indent=2),
        images=images,
        meta={"unit_id": unit.unit_id},
    )


def normalize_fact_from_model(unit: EvidenceUnit, item: Mapping[str, Any], ordinal: int) -> EvidenceFact | None:
    fact_type = str(item.get("fact_type") or "other")
    if fact_type not in FACT_TYPES:
        fact_type = "other"
    confidence = str(item.get("confidence") or "").lower()
    if confidence not in {"high", "medium", "low"}:
        confidence = "medium"
    if confidence == "low":
        return None

    source_mode = str(item.get("source_mode") or "text").lower()
    if source_mode not in {"text", "image"}:
        source_mode = "text"
    image_index = item.get("image_index")
    if source_mode == "image":
        try:
            image_index = int(image_index)
        except (TypeError, ValueError):
            image_index = 0 if unit.images else None
        if image_index is not None and not (0 <= image_index < len(unit.images)):
            return None
    else:
        image_index = None

    value_text = normalize_text(item.get("value_text"))
    numeric_value = normalize_text(item.get("numeric_value"))
    if numeric_value and not NUMBER_RE.search(numeric_value):
        numeric_value = ""

    claim = normalize_text(item.get("claim"))
    metric = normalize_text(item.get("metric"))
    evidence_quote = normalize_text(item.get("evidence_quote"))
    if not any((claim, metric, value_text, evidence_quote)):
        return None

    fact_id = stable_id(
        "gef",
        unit.unit_id,
        ordinal,
        fact_type,
        item.get("entity"),
        item.get("period"),
        metric,
        value_text,
        claim,
    )
    return EvidenceFact(
        fact_id=fact_id,
        unit_id=unit.unit_id,
        document_id=unit.document_id,
        dataset=unit.dataset,
        source_ref=unit.source_ref,
        page=unit.page,
        entity=normalize_text(item.get("entity")),
        period=normalize_text(item.get("period")),
        fact_type=fact_type,
        metric=metric,
        scope=normalize_text(item.get("scope")),
        value_text=value_text,
        numeric_value=numeric_value,
        unit=normalize_text(item.get("unit")),
        currency=normalize_text(item.get("currency")),
        claim=claim,
        topic=normalize_text(item.get("topic")),
        source_mode=source_mode,
        image_index=image_index,
        visual_type=normalize_text(item.get("visual_type")) or ("document" if source_mode == "image" else "none"),
        evidence_quote=evidence_quote,
        confidence=confidence,
        images=list(unit.images),
        raw=dict(item),
    )


def fact_to_row(fact: EvidenceFact) -> dict[str, Any]:
    return {
        "fact_id": fact.fact_id,
        "unit_id": fact.unit_id,
        "document_id": fact.document_id,
        "dataset": fact.dataset,
        "source_ref": fact.source_ref,
        "page": fact.page,
        "entity": fact.entity,
        "period": fact.period,
        "fact_type": fact.fact_type,
        "metric": fact.metric,
        "scope": fact.scope,
        "value_text": fact.value_text,
        "numeric_value": fact.numeric_value,
        "unit": fact.unit,
        "currency": fact.currency,
        "claim": fact.claim,
        "topic": fact.topic,
        "source_mode": fact.source_mode,
        "image_index": fact.image_index,
        "visual_type": fact.visual_type,
        "evidence_quote": fact.evidence_quote,
        "confidence": fact.confidence,
        "images": fact.images,
    }


def row_to_fact(row: Mapping[str, Any]) -> EvidenceFact:
    return EvidenceFact(
        fact_id=str(row.get("fact_id") or stable_id("gef", row.get("unit_id"), row.get("_line"))),
        unit_id=str(row.get("unit_id") or ""),
        document_id=str(row.get("document_id") or ""),
        dataset=str(row.get("dataset") or ""),
        source_ref=str(row.get("source_ref") or ""),
        page=str(row.get("page") or ""),
        entity=str(row.get("entity") or ""),
        period=str(row.get("period") or ""),
        fact_type=str(row.get("fact_type") or "other"),
        metric=str(row.get("metric") or ""),
        scope=str(row.get("scope") or ""),
        value_text=str(row.get("value_text") or ""),
        numeric_value=str(row.get("numeric_value") or ""),
        unit=str(row.get("unit") or ""),
        currency=str(row.get("currency") or ""),
        claim=str(row.get("claim") or ""),
        topic=str(row.get("topic") or ""),
        source_mode=str(row.get("source_mode") or "text"),
        image_index=row.get("image_index") if isinstance(row.get("image_index"), int) else None,
        visual_type=str(row.get("visual_type") or "none"),
        evidence_quote=str(row.get("evidence_quote") or ""),
        confidence=str(row.get("confidence") or "medium"),
        images=normalize_images(row.get("images")),
        raw=dict(row),
    )


def extract_evidence_facts(args: argparse.Namespace) -> tuple[list[EvidenceFact], list[dict[str, Any]]]:
    units = load_units(args.evidence_units)
    if args.max_units:
        units = units[: args.max_units]
    entities = load_document_entities(args.document_entities)
    if not units:
        raise RuntimeError(f"no evidence units found: {args.evidence_units}")

    runner = QwenRunner(
        backend=args.evidence_backend,
        model=args.evidence_model,
        base_url=args.evidence_base_url,
        api_key=args.api_key,
        tensor_parallel_size=args.tensor_parallel_size,
        gpu_memory_utilization=args.gpu_memory_utilization,
        max_model_len=args.max_model_len,
        max_images=args.max_images,
    )
    facts: list[EvidenceFact] = []
    failures: list[dict[str, Any]] = []

    for start in range(0, len(units), args.extract_batch_size):
        batch_units = units[start : start + args.extract_batch_size]
        requests = [
            evidence_request(unit, entities.get(unit.document_id, {}), args.max_images)
            for unit in batch_units
        ]
        outputs = runner.batch(requests, temperature=0.0, max_tokens=args.extract_max_tokens)
        for unit, output in zip(batch_units, outputs):
            if isinstance(output, Exception):
                failures.append({"stage": "extract", "unit_id": unit.unit_id, "error": str(output)})
                continue
            items = output.get("facts")
            if not isinstance(items, list):
                failures.append({"stage": "extract", "unit_id": unit.unit_id, "error": "missing facts list"})
                continue
            for ordinal, item in enumerate(items, 1):
                if not isinstance(item, Mapping):
                    continue
                fact = normalize_fact_from_model(unit, item, ordinal)
                if fact is not None:
                    facts.append(fact)
        print(json.dumps({"stage": "extract", "processed": min(start + len(batch_units), len(units)), "facts": len(facts)}, ensure_ascii=False), flush=True)

    unload_model(runner)
    # Deduplicate same source fact emitted twice.
    unique: dict[str, EvidenceFact] = {}
    for fact in facts:
        signature = stable_id(
            "sig",
            fact.unit_id,
            fact.entity,
            fact.period,
            fact.fact_type,
            fact.metric,
            fact.value_text,
            fact.claim,
            fact.source_mode,
            fact.image_index,
        )
        if signature not in unique or unique[signature].confidence == "medium" and fact.confidence == "high":
            unique[signature] = fact
    return list(unique.values()), failures


class EvidenceGraph:
    def __init__(self, facts: Sequence[EvidenceFact]) -> None:
        self.facts = list(facts)
        self.by_id = {fact.fact_id: fact for fact in facts}
        self.adj: dict[str, list[tuple[str, str, float]]] = defaultdict(list)
        self.by_document: dict[str, list[EvidenceFact]] = defaultdict(list)
        self.by_entity: dict[str, list[EvidenceFact]] = defaultdict(list)
        self.by_entity_period: dict[tuple[str, str], list[EvidenceFact]] = defaultdict(list)
        self.by_metric: dict[str, list[EvidenceFact]] = defaultdict(list)
        self.by_topic: dict[str, list[EvidenceFact]] = defaultdict(list)
        self._build()

    def _connect(self, a: EvidenceFact, b: EvidenceFact, edge_type: str, weight: float) -> None:
        if a.fact_id == b.fact_id:
            return
        self.adj[a.fact_id].append((b.fact_id, edge_type, weight))
        self.adj[b.fact_id].append((a.fact_id, edge_type, weight))

    @staticmethod
    def _bounded_pairs(group: Sequence[EvidenceFact], max_group: int = 60) -> Iterator[tuple[EvidenceFact, EvidenceFact]]:
        items = list(group)[:max_group]
        for i, a in enumerate(items):
            for b in items[i + 1 :]:
                yield a, b

    def _build(self) -> None:
        for fact in self.facts:
            if fact.document_id:
                self.by_document[fact.document_id].append(fact)
            if fact.entity:
                self.by_entity[fact.entity].append(fact)
            if fact.entity and fact.period:
                self.by_entity_period[(fact.entity, fact.period)].append(fact)
            if fact.metric:
                self.by_metric[fact.metric].append(fact)
            if fact.topic:
                self.by_topic[fact.topic].append(fact)

        for group in self.by_document.values():
            for a, b in self._bounded_pairs(group):
                weight = 3.0 if a.page == b.page and a.page else 2.2
                self._connect(a, b, "same_document", weight)
        for group in self.by_entity_period.values():
            for a, b in self._bounded_pairs(group):
                self._connect(a, b, "same_entity_period", 3.4)
        for entity, group in self.by_entity.items():
            del entity
            by_metric: dict[str, list[EvidenceFact]] = defaultdict(list)
            for fact in group:
                if fact.metric:
                    by_metric[fact.metric].append(fact)
            for metric_group in by_metric.values():
                for a, b in self._bounded_pairs(metric_group, max_group=30):
                    if a.period and b.period and a.period != b.period:
                        self._connect(a, b, "same_metric_cross_period", 4.0)
        for topic_group in self.by_topic.values():
            for a, b in self._bounded_pairs(topic_group, max_group=30):
                if a.entity == b.entity or a.document_id == b.document_id:
                    self._connect(a, b, "same_topic", 2.7)

        # Cross-modal bridge inside the same unit/document is especially useful
        # for Generation RL tasks that must combine text and visual evidence.
        by_unit: dict[str, list[EvidenceFact]] = defaultdict(list)
        for fact in self.facts:
            by_unit[fact.unit_id].append(fact)
        for group in by_unit.values():
            for a, b in self._bounded_pairs(group, max_group=30):
                if a.source_mode != b.source_mode:
                    self._connect(a, b, "cross_modal_same_unit", 4.2)

    def neighbors(self, fact_id: str) -> list[tuple[EvidenceFact, str, float]]:
        return [
            (self.by_id[target], edge_type, weight)
            for target, edge_type, weight in self.adj.get(fact_id, [])
            if target in self.by_id
        ]


class BundleSampler:
    def __init__(self, graph: EvidenceGraph, rng: random.Random, args: argparse.Namespace) -> None:
        self.graph = graph
        self.rng = rng        self.args = args

    def _difficulty_target(self, hard: bool) -> tuple[int, int]:
        if hard:
            min_count = max(4, self.args.min_required_facts)
            max_count = max(min_count, self.args.max_required_facts)
        else:
            min_count = self.args.min_required_facts
            max_count = min(max(min_count, 5), self.args.max_required_facts)
        return min_count, max_count

    def _seed_candidates(self, profile: Mapping[str, Any] | None) -> list[EvidenceFact]:
        facts = self.graph.facts
        if not profile:
            return facts
        tags = {str(x) for x in profile.get("scenario_tags", [])}
        error = str(profile.get("error_type") or "")
        visual_needed = bool(tags & VISUAL_SCENARIO_TAGS) or any(
            token in error for token in ("visual", "chart", "table", "ocr")
        )
        if visual_needed:
            visual = [fact for fact in facts if fact.source_mode == "image"]
            if visual:
                return visual
        return facts

    def _walk(self, target_count: int, profile: Mapping[str, Any] | None) -> tuple[list[EvidenceFact], list[dict[str, str]]]:
        seeds = self._seed_candidates(profile)
        if not seeds:
            return [], []
        seed = self.rng.choice(seeds)
        required = [seed]
        used = {seed.fact_id}
        edges: list[dict[str, str]] = []
        current = seed

        for _ in range(target_count * 5):
            if len(required) >= target_count:
                break
            options = [item for item in self.graph.neighbors(current.fact_id) if item[0].fact_id not in used]
            if not options:
                # Continue from any already selected node before giving up.
                candidates = []
                for selected in required:
                    candidates.extend(
                        item for item in self.graph.neighbors(selected.fact_id)
                        if item[0].fact_id not in used
                    )
                options = candidates
            if not options:
                break

            # Bias toward stronger graph relations while retaining diversity.
            weights = [max(0.1, item[2]) for item in options]
            choice = self.rng.choices(options, weights=weights, k=1)[0]
            nxt, edge_type, _ = choice
            required.append(nxt)
            used.add(nxt.fact_id)
            edges.append({"source": current.fact_id, "target": nxt.fact_id, "type": edge_type})
            current = nxt
        return required, edges

    @staticmethod
    def _similarity(anchor: EvidenceFact, candidate: EvidenceFact, profile: Mapping[str, Any] | None) -> float:
        if anchor.fact_id == candidate.fact_id:
            return -1.0
        score = 0.0
        if anchor.document_id and anchor.document_id == candidate.document_id:
            score += 1.5
        if anchor.entity and anchor.entity == candidate.entity:
            score += 1.6
        if anchor.period and anchor.period == candidate.period:
            score += 1.0
        if anchor.metric and anchor.metric == candidate.metric:
            score += 1.8
        if anchor.scope and anchor.scope == candidate.scope:
            score += 0.4
        if anchor.fact_type == candidate.fact_type:
            score += 0.5
        if anchor.source_mode == candidate.source_mode:
            score += 0.2

        if profile:
            error = str(profile.get("error_type") or "")
            if "period_confusion" in error and anchor.metric == candidate.metric and anchor.period != candidate.period:
                score += 3.0
            if "metric_confusion" in error and anchor.period == candidate.period and anchor.metric != candidate.metric:
                score += 3.0
            if "scope_confusion" in error and anchor.metric == candidate.metric and anchor.scope != candidate.scope:
                score += 3.0
            if "entity_confusion" in error and anchor.metric == candidate.metric and anchor.entity != candidate.entity:
                score += 3.0
        return score

    def _distractors(self, required: Sequence[EvidenceFact], profile: Mapping[str, Any] | None) -> list[EvidenceFact]:
        required_ids = {fact.fact_id for fact in required}
        scored: list[tuple[float, EvidenceFact]] = []
        for candidate in self.graph.facts:
            if candidate.fact_id in required_ids:
                continue
            best = max(self._similarity(anchor, candidate, profile) for anchor in required)
            if best >= 1.5:
                scored.append((best + self.rng.random() * 0.2, candidate))
        scored.sort(key=lambda item: item[0], reverse=True)
        output: list[EvidenceFact] = []
        seen_units: set[tuple[str, str, str, str]] = set()
        for _, fact in scored:
            signature = (fact.entity, fact.period, fact.metric, fact.scope)
            if signature in seen_units:
                continue
            seen_units.add(signature)
            output.append(fact)
            if len(output) >= self.args.max_distractors:
                break
        return output

    @staticmethod
    def _difficulty(required: Sequence[EvidenceFact], distractors: Sequence[EvidenceFact], edges: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
        documents = {fact.document_id for fact in required if fact.document_id}
        pages = {(fact.document_id, fact.page) for fact in required if fact.page}
        periods = {fact.period for fact in required if fact.period}
        entities = {fact.entity for fact in required if fact.entity}
        visuals = [fact for fact in required if fact.source_mode == "image"]
        modes = {fact.source_mode for fact in required}
        relation_types = {str(edge.get("type") or "") for edge in edges}
        score = (
            len(required) * 0.8
            + len(distractors) * 0.45
            + len(documents) * 0.8
            + max(0, len(periods) - 1) * 0.8
            + max(0, len(entities) - 1) * 0.8
            + len(visuals) * 0.4
            + (1.5 if len(modes) > 1 else 0.0)
            + len(relation_types) * 0.25
        )
        label = "hard" if score >= 8.5 else "medium" if score >= 5.5 else "easy"
        return {
            "label": label,
            "score": round(score, 2),
            "required_fact_count": len(required),
            "distractor_count": len(distractors),
            "document_count": len(documents),
            "page_count": len(pages),
            "period_count": len(periods),
            "entity_count": len(entities),
            "visual_fact_count": len(visuals),
            "cross_modal": len(modes) > 1,
            "graph_hops": len(edges),
            "relation_types": sorted(relation_types),
        }

    def sample(self, *, hard: bool, profile: Mapping[str, Any] | None = None) -> Bundle | None:
        min_count, max_count = self._difficulty_target(hard)
        target_count = self.rng.randint(min_count, max_count)
        required, edges = self._walk(target_count, profile)
        if len(required) < min_count:
            return None
        distractors = self._distractors(required, profile)
        difficulty = self._difficulty(required, distractors, edges)
        return Bundle(
            required=required,
            distractors=distractors,
            path_edges=edges,
            difficulty=difficulty,
            badcase_profile=dict(profile) if profile else None,
        )


def fact_hidden_payload(fact: EvidenceFact) -> dict[str, Any]:
    return {
        "fact_id": fact.fact_id,
        "entity": fact.entity,
        "period": fact.period,
        "fact_type": fact.fact_type,
        "metric": fact.metric,
        "scope": fact.scope,
        "value_text": fact.value_text,
        "numeric_value": fact.numeric_value,
        "unit": fact.unit,
        "currency": fact.currency,
        "claim": fact.claim,
        "topic": fact.topic,
        "source_mode": fact.source_mode,
        "visual_type": fact.visual_type,
        "document_id": fact.document_id,
        "page": fact.page,
        "evidence_quote": fact.evidence_quote if fact.source_mode == "text" else "",
    }


def fact_prompt_text(fact: EvidenceFact, *, distractor: bool = False, image_number: int | None = None) -> str:
    # Required evidence and distractors use the same surface label. Do not tell
    # the training model which material is a distractor.
    del distractor
    label = "材料"
    if fact.source_mode == "image":
        parts = [fact.entity, fact.period, fact.metric, f"第{fact.page}页" if fact.page else ""]
        image_label = f"第{image_number}张图片" if image_number is not None else "对应原始图片"
        return f"{label}：请查看{image_label}（{' / '.join(part for part in parts if part)}）。"
    quote = fact.evidence_quote or fact.claim
    if quote:
        return f"{label}：{quote.strip()}"
    pieces = [fact.entity, fact.period, fact.metric, fact.value_text, fact.claim]
    return f"{label}：" + "；".join(piece for piece in pieces if piece)


def fact_image_path(fact: EvidenceFact) -> Path | None:
    if fact.source_mode != "image" or not fact.images:
        return None
    index = fact.image_index if fact.image_index is not None else 0
    if index < 0 or index >= len(fact.images):
        return None
    return resolve_image(fact.images[index])


def bundle_images(bundle: Bundle, max_images: int) -> list[Path]:
    output: list[Path] = []
    seen: set[str] = set()
    for fact in [*bundle.required, *bundle.distractors]:
        path = fact_image_path(fact)
        if path is None or str(path) in seen:
            continue
        seen.add(str(path))
        output.append(path)
        if len(output) >= max_images:
            break
    return output


def planner_request(bundle: Bundle, max_images: int) -> LLMRequest:
    payload = {
        "task_labels": list(GENERATION_TASKS or TASK_VOCABULARY),
        "difficulty": bundle.difficulty,
        "candidate_required_fact_ids": [fact.fact_id for fact in bundle.required],
        "candidate_distractor_ids": [fact.fact_id for fact in bundle.distractors],
        "reasoning_graph": {
            "nodes": [fact.fact_id for fact in bundle.required],
            "edges": bundle.path_edges,
        },
        "required_candidates": [fact_hidden_payload(fact) for fact in bundle.required],
        "distractor_candidates": [fact_hidden_payload(fact) for fact in bundle.distractors],
        "badcase_profile": bundle.badcase_profile,
    }
    return LLMRequest(
        system=PLANNER_SYSTEM,
        user=json.dumps(payload, ensure_ascii=False, indent=2),
        images=bundle_images(bundle, max_images),
        meta={"bundle": bundle},
    )


def validate_plan(plan: Mapping[str, Any], bundle: Bundle) -> tuple[bool, str]:
    if str(plan.get("status") or "") != "accepted":
        return False, str(plan.get("reason") or "planner_rejected")
    task = str(plan.get("task") or "")
    if task not in set(GENERATION_TASKS or TASK_VOCABULARY):
        return False, f"invalid_task:{task}"
    required_ids = plan.get("required_fact_ids")
    if not isinstance(required_ids, list) or len(required_ids) < 2:
        return False, "invalid_required_fact_ids"
    allowed_required = {fact.fact_id for fact in bundle.required}
    if any(str(fid) not in allowed_required for fid in required_ids):
        return False, "required_fact_outside_bundle"
    distractors = plan.get("distractor_ids") or []
    if not isinstance(distractors, list):
        return False, "invalid_distractor_ids"
    allowed_distractors = {fact.fact_id for fact in bundle.distractors}
    if any(str(fid) not in allowed_distractors for fid in distractors):
        return False, "distractor_outside_bundle"
    dimensions = plan.get("analysis_dimensions")
    if not isinstance(dimensions, list) or not dimensions:
        return False, "missing_analysis_dimensions"
    return True, ""


def render_request(bundle: Bundle, plan: Mapping[str, Any], max_images: int) -> LLMRequest:
    by_id = {fact.fact_id: fact for fact in [*bundle.required, *bundle.distractors]}
    required = [by_id[str(fid)] for fid in plan.get("required_fact_ids", []) if str(fid) in by_id]
    distractors = [by_id[str(fid)] for fid in plan.get("distractor_ids", []) if str(fid) in by_id]
    payload = {
        "task_skeleton": dict(plan),
        "required_evidence": [fact_hidden_payload(fact) for fact in required],
        "distractors": [fact_hidden_payload(fact) for fact in distractors],
        "difficulty": bundle.difficulty,
    }
    return LLMRequest(
        system=RENDER_SYSTEM,
        user=json.dumps(payload, ensure_ascii=False, indent=2),
        images=bundle_images(Bundle(required, distractors, bundle.path_edges, bundle.difficulty, bundle.badcase_profile), max_images),
        meta={"bundle": bundle, "plan": dict(plan)},
    )


def validate_render(rendered: Mapping[str, Any], plan: Mapping[str, Any]) -> tuple[bool, str]:
    if str(rendered.get("status") or "") != "accepted":
        return False, str(rendered.get("reason") or "renderer_rejected")
    question = str(rendered.get("question") or "").strip()
    answer = str(rendered.get("reference_answer") or "").strip()
    if not question or not answer:
        return False, "empty_question_or_answer"
    used = rendered.get("used_fact_ids")
    if not isinstance(used, list):
        return False, "missing_used_fact_ids"
    expected = {str(x) for x in plan.get("required_fact_ids", [])}
    if {str(x) for x in used} != expected:
        return False, "used_fact_ids_mismatch"
    return True, ""


def verification_request(
    bundle: Bundle,
    plan: Mapping[str, Any],
    rendered: Mapping[str, Any],
    max_images: int,
) -> LLMRequest:
    by_id = {fact.fact_id: fact for fact in [*bundle.required, *bundle.distractors]}
    required = [by_id[str(fid)] for fid in plan.get("required_fact_ids", []) if str(fid) in by_id]
    distractors = [by_id[str(fid)] for fid in plan.get("distractor_ids", []) if str(fid) in by_id]
    payload = {
        "task": plan.get("task"),
        "analysis_dimensions": plan.get("analysis_dimensions"),
        "question": rendered.get("question"),
        "reference_answer": rendered.get("reference_answer"),
        "required_evidence": [fact_hidden_payload(fact) for fact in required],
        "distractors": [fact_hidden_payload(fact) for fact in distractors],
        "visual_required": any(fact.source_mode == "image" for fact in required),
    }
    return LLMRequest(
        system=VERIFY_SYSTEM,
        user=json.dumps(payload, ensure_ascii=False, indent=2),
        images=bundle_images(Bundle(required, distractors, bundle.path_edges, bundle.difficulty, bundle.badcase_profile), max_images),
        meta={},
    )


def load_badcase_profiles(path: Path) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    if not path.is_file():
        return output
    for row in read_jsonl(path):
        obj = row.get("classification") if isinstance(row.get("classification"), Mapping) else row
        error = str(obj.get("error_type") or obj.get("primary_error_type") or "")
        task = str(obj.get("task_type") or obj.get("task") or "")
        tags = obj.get("scenario_tags") or []
        if isinstance(tags, str):
            tags = [tags]
        if not isinstance(tags, list):
            tags = []
        # Generation builder only consumes open-ended/analysis-like failures.
        if error in OPEN_ENDED_ERROR_HINTS or any(
            token in task
            for token in (
                "analysis",
                "summary",
                "policy",
                "risk",
                "audit",
                "strategy",
                "compliance",
                "interpretation",
                "explanation",
            )
        ):
            output.append({"task_type": task, "error_type": error, "scenario_tags": [str(x) for x in tags]})
    return output


def final_prompt_and_images(
    required: Sequence[EvidenceFact],
    distractors: Sequence[EvidenceFact],
    question: str,
    max_images: int,
    max_text_chars: int,
) -> tuple[str, list[str]]:
    ordered = [*required, *distractors]
    images: list[str] = []
    image_map: dict[str, int] = {}
    for fact in ordered:
        path = fact_image_path(fact)
        if path is None:
            continue
        portable = portable_path(path)
        if portable not in image_map and len(images) < max_images:
            image_map[portable] = len(images)
            images.append(portable)

    lines: list[str] = []
    total = 0
    for fact in ordered:
        image_number = None
        if fact.source_mode == "image":
            path = fact_image_path(fact)
            if path is not None and portable_path(path) in image_map:
                image_number = image_map[portable_path(path)] + 1
        line = fact_prompt_text(fact, distractor=fact in distractors, image_number=image_number)
        if fact.source_mode == "image":
            path = fact_image_path(fact)
            if path is None or portable_path(path) not in image_map:
                # If image cannot be supplied, do not silently leak the hidden
                # image fact value into text; simply omit this unusable fact.
                continue
        if total + len(line) > max_text_chars:
            break
        lines.append(line)
        total += len(line)

    prefix = "".join("<image>" for _ in images)
    content = "\n".join(part for part in (prefix, "\n".join(lines), "问题：" + question.strip()) if part)
    return content, images


def generation_row(
    bundle: Bundle,
    plan: Mapping[str, Any],
    rendered: Mapping[str, Any],
    args: argparse.Namespace,
) -> dict[str, Any]:
    all_facts = {fact.fact_id: fact for fact in [*bundle.required, *bundle.distractors]}
    required = [all_facts[str(fid)] for fid in plan.get("required_fact_ids", []) if str(fid) in all_facts]
    distractors = [all_facts[str(fid)] for fid in plan.get("distractor_ids", []) if str(fid) in all_facts]
    content, images = final_prompt_and_images(
        required,
        distractors,
        str(rendered["question"]),
        args.max_images,
        args.max_text_context_chars,
    )
    sample_id = stable_id(
        "genrl",
        plan.get("task"),
        rendered.get("question"),
        [fact.fact_id for fact in required],
    )
    return {
        "sample_id": sample_id,
        "messages": [{"role": "user", "content": content}],
        "question": str(rendered["question"]),
        "solution": str(rendered["reference_answer"]),
        "reference_answer": str(rendered["reference_answer"]),
        "source": "finance_world_generation_rl",
        "split": "train",
        "images": images,
        "task": str(plan["task"]),
        "output_format": "free_text",
        "reward_type": "judge",
        "reward_subtype": "model_judge",
        "verifier_type": "model_judge",
        "metadata": {
            "required_evidence_ids": [fact.fact_id for fact in required],
            "distractor_ids": [fact.fact_id for fact in distractors],
            "generation_spec": {
                "task_intent": plan.get("task_intent"),
                "analysis_dimensions": plan.get("analysis_dimensions"),
                "question_requirements": plan.get("question_requirements"),
            },
            "reasoning_graph": {
                "nodes": [fact.fact_id for fact in required],
                "edges": [
                    edge for edge in bundle.path_edges
                    if edge.get("source") in {f.fact_id for f in required}
                    and edge.get("target") in {f.fact_id for f in required}
                ],
            },
            "difficulty": bundle.difficulty,
            "badcase_profile": bundle.badcase_profile,
            "construction": {
                "evidence_model_role": "32B evidence extraction only",
                "construct_model_role": "235B task planning, question/reference construction, verification",
                "builder": "financial_graph_generation_rl_v1",
            },
        },
    }


def construct_generation(args: argparse.Namespace, facts: Sequence[EvidenceFact]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if not facts:
        raise RuntimeError("no evidence facts available for construction")
    graph = EvidenceGraph(facts)
    rng = random.Random(args.seed)
    sampler = BundleSampler(graph, rng, args)
    profiles = load_badcase_profiles(args.badcase_classification)

    runner = QwenRunner(
        backend=args.construct_backend,
        model=args.construct_model,
        base_url=args.construct_base_url,
        api_key=args.api_key,
        tensor_parallel_size=args.tensor_parallel_size,
        gpu_memory_utilization=args.gpu_memory_utilization,
        max_model_len=args.max_model_len,
        max_images=args.max_images,
    )

    accepted: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    seen_questions: set[str] = set()
    attempts = 0
    max_attempts = max(args.target * 6, 100)

    while len(accepted) < args.target and attempts < max_attempts:
        batch_bundles: list[Bundle] = []
        while len(batch_bundles) < args.construct_batch_size and attempts < max_attempts:
            attempts += 1
            hard = rng.random() < args.hard_ratio
            profile = rng.choice(profiles) if profiles and rng.random() < args.badcase_ratio else None
            bundle = sampler.sample(hard=hard, profile=profile)
            if bundle is not None:
                batch_bundles.append(bundle)
        if not batch_bundles:
            break

        plan_requests = [planner_request(bundle, args.max_images) for bundle in batch_bundles]
        plans = runner.batch(plan_requests, temperature=0.25, max_tokens=args.construct_max_tokens)

        render_items: list[tuple[Bundle, dict[str, Any]]] = []
        for bundle, plan in zip(batch_bundles, plans):
            if isinstance(plan, Exception):
                rejected.append({"stage": "plan", "reason": f"model_error:{plan}"})
                continue
            ok, reason = validate_plan(plan, bundle)
            if not ok:
                rejected.append({"stage": "plan", "reason": reason, "output": plan})
                continue
            render_items.append((bundle, dict(plan)))

        render_requests = [render_request(bundle, plan, args.max_images) for bundle, plan in render_items]
        rendered_outputs = runner.batch(render_requests, temperature=0.35, max_tokens=args.construct_max_tokens)

        verify_items: list[tuple[Bundle, dict[str, Any], dict[str, Any]]] = []
        for (bundle, plan), rendered in zip(render_items, rendered_outputs):
            if isinstance(rendered, Exception):
                rejected.append({"stage": "render", "reason": f"model_error:{rendered}", "plan": plan})
                continue
            ok, reason = validate_render(rendered, plan)
            if not ok:
                rejected.append({"stage": "render", "reason": reason, "plan": plan, "output": rendered})
                continue
            question_key = re.sub(r"\s+", "", str(rendered.get("question") or "")).lower()
            if question_key in seen_questions:
                rejected.append({"stage": "render", "reason": "duplicate_question"})
                continue
            verify_items.append((bundle, plan, dict(rendered)))

        if args.verify and verify_items:
            verify_requests = [
                verification_request(bundle, plan, rendered, args.max_images)
                for bundle, plan, rendered in verify_items
            ]
            verify_outputs = runner.batch(verify_requests, temperature=0.0, max_tokens=1200)
        else:
            verify_outputs = [{"accepted": True, "issues": []} for _ in verify_items]

        for (bundle, plan, rendered), verification in zip(verify_items, verify_outputs):
            if isinstance(verification, Exception):
                rejected.append({"stage": "verify", "reason": f"model_error:{verification}"})
                continue
            if not bool(verification.get("accepted")):
                rejected.append({
                    "stage": "verify",
                    "reason": "construction_verification_failed",
                    "issues": verification.get("issues") or [],
                    "plan": plan,
                    "question": rendered.get("question"),
                })
                continue
            expected = {str(x) for x in plan.get("required_fact_ids", [])}
            verified_ids = verification.get("required_fact_ids")
            if isinstance(verified_ids, list) and verified_ids and not set(map(str, verified_ids)).issubset(expected):
                rejected.append({"stage": "verify", "reason": "verifier_used_nonrequired_fact"})
                continue
            row = generation_row(bundle, plan, rendered, args)
            question_key = re.sub(r"\s+", "", row["question"]).lower()
            seen_questions.add(question_key)
            accepted.append(row)
            if len(accepted) >= args.target:
                break

        print(
            json.dumps(
                {
                    "stage": "construct",
                    "accepted": len(accepted),
                    "rejected": len(rejected),
                    "attempts": attempts,
                },
                ensure_ascii=False,
            ),
            flush=True,
        )

    unload_model(runner)
    return accepted, rejected


def audit_report(
    facts: Sequence[EvidenceFact],
    rows: Sequence[Mapping[str, Any]],
    rejected: Sequence[Mapping[str, Any]],
    extract_failures: Sequence[Mapping[str, Any]],
    args: argparse.Namespace,
) -> dict[str, Any]:
    fact_types = Counter(fact.fact_type for fact in facts)
    source_modes = Counter(fact.source_mode for fact in facts)
    tasks = Counter(str(row.get("task") or "") for row in rows)
    difficulty = Counter(str((row.get("metadata") or {}).get("difficulty", {}).get("label") or "") for row in rows)
    badcase = sum(1 for row in rows if (row.get("metadata") or {}).get("badcase_profile"))
    visual = sum(1 for row in rows if row.get("images"))
    return {
        "version": "financial_graph_generation_rl_v1",
        "models": {
            "evidence": str(args.evidence_model),
            "evidence_role": "evidence fact extraction only",
            "construct": str(args.construct_model),
            "construct_role": "task planning, question/reference construction, verification",
        },
        "evidence_facts": len(facts),
        "evidence_fact_types": dict(fact_types),
        "evidence_source_modes": dict(source_modes),
        "accepted": len(rows),
        "rejected": len(rejected),
        "extract_failures": len(extract_failures),
        "tasks": dict(tasks),
        "difficulty": dict(difficulty),
        "visual_samples": visual,
        "badcase_conditioned_samples": badcase,
    }


def main() -> None:
    args = parse_args()
    args.output_root.mkdir(parents=True, exist_ok=True)
    evidence_facts_path = args.evidence_facts or (args.output_root / "generation_evidence_facts.jsonl")
    extract_failures: list[dict[str, Any]] = []

    if args.stage in {"extract", "all"}:
        facts, extract_failures = extract_evidence_facts(args)
        write_jsonl(evidence_facts_path, (fact_to_row(fact) for fact in facts))
        write_jsonl(args.output_root / "evidence_extract_failures.jsonl", extract_failures)
        print(
            json.dumps(
                {
                    "stage": "extract_complete",
                    "facts": len(facts),
                    "failures": len(extract_failures),
                    "output": str(evidence_facts_path),
                },
                ensure_ascii=False,
            ),
            flush=True,
        )
        # 32B must be completely unloaded before the 235B model is initialized.
        gc.collect()
        try:
            import torch

            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                torch.cuda.ipc_collect()
        except Exception:
            pass

    if args.stage == "extract":
        return

    fact_rows = read_jsonl(evidence_facts_path)
    facts = [row_to_fact(row) for row in fact_rows]
    # Image-derived facts are only usable when the original image can actually
    # be supplied to the training sample. Never fall back to leaking the hidden
    # extracted image value as text.
    facts = [fact for fact in facts if fact.source_mode != "image" or fact_image_path(fact) is not None]
    if not facts:
        raise SystemExit(f"no evidence facts found: {evidence_facts_path}; run --stage extract first")

    rows, rejected = construct_generation(args, facts)
    write_jsonl(args.output_root / "generation.jsonl", rows)
    write_jsonl(args.output_root / "rejected.jsonl", rejected)
    report = audit_report(facts, rows, rejected, extract_failures, args)
    (args.output_root / "audit.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()