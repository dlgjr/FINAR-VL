#!/usr/bin/env python3
"""使用多模态模型从财报输入包生成可追溯的困难问答。"""

from __future__ import annotations

import argparse
import ast
import copy
import json
import os
import re
import sys
import traceback
from collections import Counter
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from typing import Any, Callable, Sequence
import unicodedata

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.pass_at_k import (  # noqa: E402
    JsonlRecordError,
    ensure_run_config,
    iter_jsonl_shard,
    repair_jsonl_tail,
    stable_seed,
    validate_runtime_dependencies,
    wait_for_workers,
)


DEFAULT_ROOT = "/mnt/nas/bihaoran/qwen3vl"
DEFAULT_MODEL = "/mnt/nas/bihaoran/model/qwen235"
DEFAULT_INPUT = f"{DEFAULT_ROOT}/data/finance_qa/all.jsonl"
DEFAULT_PROMPTS = (
    f"{DEFAULT_ROOT}/data/finance_qa/prompts/"
    "financial_multimodal_prompt_library.md"
)
DEFAULT_OUTPUT = f"{DEFAULT_ROOT}/output/finance_qa/runs/default"
QUESTION_MODEL_IMAGE_MAX_PIXELS = 2_000_000
STANDARD_FINANCIAL_FORMULA_CONSTANTS = {
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
SCRIPT_MANAGED_QUESTION_FIELDS = {
    "candidate_id",
    "bundle_id",
    "generation_prompt_id",
    "task_type",
}

QUESTION_SYSTEM_PROMPT = """你是金融困难问题构造器。当前阶段只生成问题候选，不生成答案、最终数值或结论。
严格输出单个 JSON 对象，不使用 Markdown 代码围栏，不附加解释。业务字段必须包括：
{
  "question": "中文困难问题",
  "media_paths": ["从输入 media_paths 中保留的1至5张图片"],
  "evidence": [{"source_ref": "输入中的图片或上下文路径", "page": 1, "media_index": 0, "bbox": [0,0,1,1], "table_cell": null, "text_quote": "短证据"}],
  "expected_steps": ["至少两步预期计算或分析步骤"],
  "metric_refs": [{"name": "指标名", "page": 1, "value": "证据中的值", "unit": "单位", "evidence_index": 0}],
  "chart_text_alignment": [{"visual_ref": "图片路径", "text_ref": "上下文路径", "relationship": "图表与文字口径关系"}],
  "formula_selection_reason": "根据隐含金融场景选择公式或判断规则的理由",
  "hardness": {"page_count": 2, "independent_evidence_count": 3, "modality_count": 2, "calculation_step_count": 2},
  "finance_checks": {"entity": true, "report_period": true, "scope": true, "currency_unit": true, "rounding": true}
}
问题必须跨至少2页定位至少3个指标，建立图表或表格与文字口径的对应关系，完成至少2步计算，并能仅依靠保留图片唯一回答。
跨页证据必须实际参与计算、口径选择或结论验证，不得使用目录、封面或报告期释义凑页数。
至少两步计算必须形成前后依赖，或包含跨页变动率核验；不得并列执行两次互不依赖的一步运算。
chart_text_alignment 描述表格或图表指标与另一页文字中的变动原因、定义、会计口径或风险解释。
metric_refs 必须写清 name、page、value、unit、evidence_index；evidence_index 指向提供该指标原始值的 evidence。
禁止把整体指标改称特定产品或特定业务指标；禁止把季度整体数据、区域数据或公司合计数据归因给未披露的细分业务。
金融结论必须限定证据边界；不得仅凭负经营现金流断言利润不真实、存在造假或经营亏损。
真实素材阶段不得新增虚构数字、比例、成本率、收入、利润、资产、负债或报告期；不得把真实公司与假设收入、假设占比、假设成本率混合成问题。
如果输入真实素材缺少完成困难题所需的金融数值或口径，应依赖同文档补充页面；仍不足时不要构造带图问题。
不要输出模型自检字段、自检说明、思考过程、分析草稿或 <think> 标签；只输出单个 JSON。若素材不足以构造真实多模态困难题，输出最小 JSON 候选并让 evidence 保持不足，不要硬凑虚构数字。
candidate_id、bundle_id、generation_prompt_id 和 task_type 由脚本写入，不要自行生成。"""

SYNTHETIC_QUESTION_SYSTEM_PROMPT = """你是金融困难问题构造器。当前阶段只生成自包含的虚构金融问题候选，不生成答案、最终数值或结论。
严格输出单个 JSON 对象，不使用 Markdown 代码围栏，不附加解释。字段类型必须严格符合下列结构：
{
  "question": "包含至少3个独立数值事实、全部口径和舍入规则的中文困难问题",
  "media_paths": [],
  "evidence": [{"source_ref": "inline:{source_id}", "page": null, "media_index": null, "bbox": null, "table_cell": null, "text_quote": "题面中的一个完整数值事实"}],
  "expected_steps": ["至少两项前后依赖的计算步骤"],
  "metric_refs": [{"name": "指标名", "page": null, "value": "题面中的原始值", "unit": "单位", "evidence_index": 0}],
  "chart_text_alignment": [],
  "formula_selection_reason": "选择公式或判断规则的理由",
  "hardness": {"page_count": 0, "independent_evidence_count": 3, "modality_count": 1, "calculation_step_count": 2},
  "finance_checks": {"entity": true, "report_period": true, "scope": true, "currency_unit": true, "rounding": true}
}
evidence 和 metric_refs 必须分别至少包含3个对象；expected_steps 必须至少包含2个字符串。不要把这些字段输出成字符串或字符串数组。
不要输出思考过程、分析草稿或 <think> 标签；只输出单个 JSON。
candidate_id、bundle_id、generation_prompt_id 和 task_type 由脚本写入，不要自行生成。"""

FINANCIAL_TERMS = (
    "财务",
    "年度报告",
    "收入",
    "利润",
    "资产",
    "负债",
    "现金流",
    "股东",
    "资本",
    "风险",
    "银行",
    "证券",
    "投资",
    "审计",
    "同比",
    "环比",
    "亿元",
    "万元",
    "人民币",
)

RETRIEVAL_HINT_TRANSLATIONS = {
    "reconciliation": ("勾稽", "合计", "附注", "变动原因"),
    "profit": ("净利润", "利润"),
    "cash": (
        "经营活动产生的现金流量净额",
        "经营性活动产生的现金流量净额",
        "现金流量分析",
        "现金流量",
        "销售商品收到的现金",
        "购买商品支付的现金",
        "收现",
        "付现",
    ),
    "quality": ("主要系", "变动原因", "应收账款", "存货"),
    "unit": ("单位", "人民币元", "万元"),
    "ratio": ("比率", "比例", "增长率", "占比"),
    "risk": ("风险", "风险因素"),
    "scenario": ("情景", "假设", "敏感性"),
    "growth": ("增长", "同比", "变动"),
    "mix": ("构成", "占比", "分部"),
    "regulatory": ("监管指标", "资本充足率", "不良贷款率"),
    "restatement": ("重述", "调整前", "调整后"),
    "abnormal": ("异常", "大幅", "主要系"),
    "movement": ("变动", "增加", "减少", "下降"),
    "ranking": ("排名", "排序", "贡献度"),
}

COMPATIBLE_PREFIXES = {
    "page_qa": ("AUD", "CAE", "DET", "IND", "KQA", "OCR", "RSP"),
    "table_qa": ("ARI", "AUD", "CAE", "MNR", "STA", "TAB"),
    "figure_qa": ("CHT", "KQA", "KTS", "REL"),
    "cross_page_qa": ("CAE", "MNR", "STA", "XMH"),
    "long_document_qa": ("AGT", "AUD", "IND", "INV", "LDR", "MTD", "RAG", "RSP"),
}

HARD_TEMPLATE_PREFIXES = {
    "page_qa": ("HPA",),
    "table_qa": ("HTA",),
    "figure_qa": ("HFI",),
    "cross_page_qa": ("HCP",),
    "long_document_qa": ("HLD",),
}

FEW_SHOT_BY_PREFIX = {
    "OCR": "FS-1",
    "DET": "FS-1",
    "REL": "FS-1",
    "TAB": "FS-2",
    "CHT": "FS-2",
    "KTS": "FS-2",
    "ARI": "FS-3",
    "STA": "FS-3",
    "MNR": "FS-3",
    "XMH": "FS-3",
    "LDR": "FS-3",
    "KQA": "FS-4",
    "CAE": "FS-4",
    "AUD": "FS-4",
    "IND": "FS-4",
    "RSP": "FS-4",
    "INV": "FS-4",
    "RAG": "FS-5",
    "MTD": "FS-5",
    "AGT": "FS-5",
}

SYNTHETIC_TEXT_PROMPT = """生成一条自包含的中文金融困难问题候选。
题目必须给出完成计算或判断所需的全部虚构数字、条件、时间、单位、口径和舍入规则，不使用真实公司、行情、法规或外部事实。
问题必须包含至少3个独立数值事实并需要至少两步推理。只输出问题候选 JSON，不得输出答案、最终数值或结论。
source_id={{source_id}}
generation_seed={{generation_seed}}
"""


@dataclass(frozen=True)
class PromptTemplate:
    prompt_id: str
    prefix: str
    title: str
    text: str


@dataclass(frozen=True)
class PromptLibrary:
    system_prompt: str
    templates: dict[str, PromptTemplate]
    few_shots: dict[str, str]


class GeneratedText(str):
    def __new__(
        cls,
        value: str,
        *,
        finish_reason: str | None = None,
        stop_reason: str | int | None = None,
    ) -> "GeneratedText":
        instance = super().__new__(cls, value)
        instance.finish_reason = finish_reason
        instance.stop_reason = stop_reason
        return instance


def _first_code_block(text: str, language: str = "text") -> str:
    match = re.search(
        rf"```{re.escape(language)}\s*\n(.*?)```",
        text,
        flags=re.DOTALL,
    )
    if match is None:
        raise ValueError(f"missing {language} code block")
    return match.group(1).strip()


def parse_prompt_library(path: Path) -> PromptLibrary:
    text = path.read_text(encoding="utf-8")
    system_start = re.search(r"^## 2\..*$", text, flags=re.MULTILINE)
    if system_start is None:
        raise ValueError("missing public system prompt section")
    system_tail = text[system_start.end() :]
    system_prompt = _first_code_block(system_tail, "text")

    headings = list(
        re.finditer(
            r"^### (FM-([A-Z]+)-\d{2})[｜|](.*)$",
            text,
            flags=re.MULTILINE,
        )
    )
    headings.extend(
        re.finditer(
            r"^### (FM-([A-Z]+)-\d{2})～(.*)$",
            text,
            flags=re.MULTILINE,
        )
    )
    headings.sort(key=lambda item: item.start())
    templates: dict[str, PromptTemplate] = {}
    for index, heading in enumerate(headings):
        end = headings[index + 1].start() if index + 1 < len(headings) else len(text)
        section = text[heading.end() : end]
        try:
            prompt_text = _first_code_block(section, "text")
        except ValueError:
            continue
        prompt_id = heading.group(1)
        templates[prompt_id] = PromptTemplate(
            prompt_id=prompt_id,
            prefix=heading.group(2),
            title=heading.group(3).strip(),
            text=prompt_text,
        )
    if not templates:
        raise ValueError("no generation templates found")

    few_shot_headings = list(
        re.finditer(r"^### (FS-\d+)[｜|].*$", text, flags=re.MULTILINE)
    )
    few_shot_headings.extend(
        re.finditer(r"^### (FS-\d+)～.*$", text, flags=re.MULTILINE)
    )
    few_shot_headings.sort(key=lambda item: item.start())
    few_shots: dict[str, str] = {}
    for index, heading in enumerate(few_shot_headings):
        end = (
            few_shot_headings[index + 1].start()
            if index + 1 < len(few_shot_headings)
            else len(text)
        )
        few_shots[heading.group(1)] = text[heading.start() : end].strip()
    return PromptLibrary(
        system_prompt=system_prompt,
        templates=templates,
        few_shots=few_shots,
    )


def select_templates(
    templates: dict[str, PromptTemplate],
    *,
    package_type: str,
    count: int,
    usage: dict[str, int],
) -> list[PromptTemplate]:
    prefixes = HARD_TEMPLATE_PREFIXES.get(package_type)
    if prefixes is None:
        raise ValueError(f"unsupported package type: {package_type}")
    candidates = [
        template
        for template in templates.values()
        if template.prefix in prefixes
    ]
    if not candidates:
        prefixes = COMPATIBLE_PREFIXES.get(package_type)
        candidates = [
            template
            for template in templates.values()
            if template.prefix in prefixes
        ]
    candidates.sort(key=lambda item: (usage.get(item.prompt_id, 0), item.prompt_id))
    if len(candidates) < count:
        raise ValueError(
            f"not enough compatible templates for {package_type}: "
            f"requested {count}, found {len(candidates)}"
        )
    selected = candidates[:count]
    for template in selected:
        usage[template.prompt_id] = usage.get(template.prompt_id, 0) + 1
    return selected


def _read_context(
    bundle: dict[str, Any],
    project_root: Path,
    *,
    max_total_chars: int = 40000,
    max_file_chars: int = 10000,
) -> str:
    parts = []
    total = 0
    for kind, paths in (bundle.get("context_files") or {}).items():
        for relative in paths or []:
            path = project_root / relative
            if not path.is_file():
                raise FileNotFoundError(f"context file does not exist: {relative}")
            content = path.read_text(encoding="utf-8", errors="replace")
            content = content[:max_file_chars]
            remaining = max_total_chars - total
            if remaining <= 0:
                return "\n\n".join(parts)
            content = content[:remaining]
            parts.append(f"[{kind}:{relative}]\n{content}")
            total += len(content)
    return "\n\n".join(parts)


def _financial_material(bundle: dict[str, Any], project_root: Path) -> bool:
    context = _read_context(bundle, project_root, max_total_chars=30000)
    return any(term in context for term in FINANCIAL_TERMS)


def _skip_weak_debug_bundle(bundle: dict[str, Any], *, debug_mode: bool) -> bool:
    if not debug_mode or bundle.get("package_type") != "page_qa":
        return False
    pages = {int(page) for page in bundle.get("page_numbers") or []}
    context_files = bundle.get("context_files") or {}
    has_crops = bool(context_files.get("tables") or context_files.get("figures"))
    return pages.issubset({1}) and not has_crops


def _skip_nonfinancial_debug_bundle(
    bundle: dict[str, Any],
    *,
    financial: bool,
    debug_mode: bool,
) -> bool:
    return (
        debug_mode
        and bundle.get("package_type") == "page_qa"
        and not financial
    )


def _long_document_bundle(
    bundle: dict[str, Any],
    project_root: Path,
    template: PromptTemplate,
    *,
    question_min_images: int = 6,
    question_max_images: int = 10,
) -> dict[str, Any]:
    if bundle.get("package_type") != "long_document_qa":
        return bundle
    page_index = (bundle.get("page_region_map") or {}).get("page_index") or []
    query_terms = _chinese_bigrams(template.text)
    retrieval_hints = _retrieval_hints(template)
    scored = []
    for item in page_index:
        text_path = project_root / item["text"]
        text = text_path.read_text(encoding="utf-8", errors="replace")
        overlap = len(query_terms & _chinese_bigrams(text))
        financial = sum(term in text for term in FINANCIAL_TERMS)
        matched_hints = {hint for hint in retrieval_hints if hint in text}
        if _is_obviously_weak_page(text) or (
            not matched_hints and financial < 2
        ):
            continue
        scored.append(
            (
                len(matched_hints) * 2000
                + financial * 100
                + overlap
                + min(len(text), 10000) / 10000,
                int(item["page_number"]),
                item,
                matched_hints,
            )
        )
    selected = _select_retrieval_pages(
        scored,
        question_min_images=question_min_images,
        question_max_images=question_max_images,
    )
    resolved = dict(bundle)
    resolved["page_numbers"] = [int(item["page_number"]) for item in selected]
    resolved["media_paths"] = [item["image"] for item in selected]
    resolved["context_files"] = {
        "pdf_text": [item["text"] for item in selected],
        "ocr": [item["ocr"] for item in selected],
        "tables": [],
        "figures": [],
    }
    resolved["page_region_map"] = {"page_index": selected}
    return resolved


def expand_bundle_for_hard_chain(
    bundle: dict[str, Any],
    project_root: Path,
    template: PromptTemplate,
    *,
    question_min_images: int = 6,
    question_max_images: int = 10,
) -> dict[str, Any]:
    if (
        question_min_images < 1
        or question_max_images < question_min_images
        or question_max_images > 10
    ):
        raise ValueError("question image limits must satisfy 1 <= min <= max <= 10")
    if bundle.get("package_type") == "long_document_qa":
        return _long_document_bundle(
            bundle,
            project_root,
            template,
            question_min_images=question_min_images,
            question_max_images=question_max_images,
        )

    long_bundle_path = (
        project_root
        / "data"
        / "finance_qa"
        / "assets"
        / "long_document_qa"
        / str(bundle["document_id"])
        / "bundle.json"
    )
    if not long_bundle_path.is_file():
        return bundle
    long_bundle = json.loads(long_bundle_path.read_text(encoding="utf-8"))
    page_index = (long_bundle.get("page_region_map") or {}).get("page_index") or []
    if len(page_index) < 2:
        return bundle

    current_pages = {
        int(page_number) for page_number in bundle.get("page_numbers") or []
    }
    anchor = min(current_pages) if current_pages else 1
    query_terms = _chinese_bigrams(template.text)
    retrieval_hints = _retrieval_hints(template)
    scored = []
    for item in page_index:
        page_number = int(item["page_number"])
        text = (project_root / item["text"]).read_text(
            encoding="utf-8",
            errors="replace",
        )
        matched_hints = {hint for hint in retrieval_hints if hint in text}
        financial = sum(term in text for term in FINANCIAL_TERMS)
        if _is_obviously_weak_page(text) or (
            not matched_hints and financial < 2
        ):
            continue
        score = (
            (10000 if page_number in current_pages else 0)
            + max(0, 1000 - abs(page_number - anchor) * 100)
            + len(matched_hints) * 2000
            + financial * 100
            + len(query_terms & _chinese_bigrams(text))
        )
        scored.append((score, page_number, item, matched_hints))
    selected = _select_retrieval_pages(
        scored,
        question_min_images=question_min_images,
        question_max_images=question_max_images,
    )
    selected.sort(key=lambda item: int(item["page_number"]))

    resolved = dict(bundle)
    resolved["page_numbers"] = [int(item["page_number"]) for item in selected]
    if bundle.get("package_type") == "page_qa":
        resolved["media_paths"] = [
            path
            for path in bundle.get("media_paths") or []
            if "/tables/" in path or "/figures/" in path
        ][:question_max_images]
    else:
        resolved["media_paths"] = list(
            bundle.get("media_paths") or []
        )[:question_max_images]
    for item in selected:
        if (
            item["image"] not in resolved["media_paths"]
            and len(resolved["media_paths"]) < question_max_images
        ):
            resolved["media_paths"].append(item["image"])
    original_context = bundle.get("context_files") or {}
    if str(bundle.get("package_type") or "") == "page_qa":
        original_pdf_text: list[str] = []
        original_ocr: list[str] = []
    else:
        original_pdf_text = list(original_context.get("pdf_text") or [])
        original_ocr = list(original_context.get("ocr") or [])
    original_pages = {int(page) for page in bundle.get("page_numbers") or []}
    selected_pdf_context = [
        item
        for item in selected
        if str(bundle.get("package_type") or "") == "page_qa"
        or not original_pdf_text
        or int(item["page_number"]) not in original_pages
    ]
    selected_ocr_context = [
        item
        for item in selected
        if str(bundle.get("package_type") or "") == "page_qa"
        or not original_ocr
        or int(item["page_number"]) not in original_pages
    ]
    resolved["context_files"] = {
        "pdf_text": list(dict.fromkeys(original_pdf_text + [item["text"] for item in selected_pdf_context])),
        "ocr": list(dict.fromkeys(original_ocr + [item["ocr"] for item in selected_ocr_context])),
        "tables": list(original_context.get("tables") or []),
        "figures": list(original_context.get("figures") or []),
    }
    page_region_map = dict(bundle.get("page_region_map") or {})
    page_region_map["retrieval_expansion"] = {
        "selected_pages": resolved["page_numbers"],
        "added_pages": [
            page_number
            for page_number in resolved["page_numbers"]
            if page_number not in current_pages
        ],
        "page_index": selected,
    }
    resolved["page_region_map"] = page_region_map
    return resolved


def _is_obviously_weak_page(text: str) -> bool:
    stripped = text.strip()
    if stripped.startswith("目录"):
        return True
    return len(stripped) < 300 and "年度报告" in stripped


def _select_retrieval_pages(
    scored: Sequence[tuple[float, int, dict[str, Any], set[str]]],
    *,
    question_min_images: int,
    question_max_images: int,
) -> list[dict[str, Any]]:
    ranked = sorted(scored, key=lambda value: (-value[0], value[1]))
    if not ranked:
        return []
    base_count = min(question_min_images, len(ranked))
    selected = list(ranked[:base_count])
    covered_hints = set().union(*(item[3] for item in selected))
    for item in ranked[base_count:]:
        if len(selected) >= question_max_images:
            break
        page_number = item[1]
        selected_pages = {chosen[1] for chosen in selected}
        adds_hint = bool(item[3] - covered_hints)
        continues_selected_page = any(
            abs(page_number - selected_page) == 1
            for selected_page in selected_pages
        ) and bool(item[2].get("tables"))
        if question_min_images == question_max_images or adds_hint or continues_selected_page:
            selected.append(item)
            covered_hints.update(item[3])
    return [item[2] for item in selected[:question_max_images]]


def _retrieval_hints(template: PromptTemplate) -> set[str]:
    source = f"{template.title} {template.text}".lower()
    return {
        hint
        for token, hints in RETRIEVAL_HINT_TRANSLATIONS.items()
        if token in source
        for hint in hints
    }


def _chinese_bigrams(text: str) -> set[str]:
    normalized = re.sub(r"[^\u4e00-\u9fffA-Za-z0-9]", "", text)
    return {
        normalized[index : index + 2]
        for index in range(max(0, len(normalized) - 1))
    }


def _replace_placeholders(
    template: str,
    *,
    bundle: dict[str, Any],
    context: str,
    generation_seed: int,
) -> str:
    values = {
        "source_dataset": "finance_reports",
        "source_id": bundle["bundle_id"],
        "media_paths": json.dumps(
            bundle.get("media_paths") or [], ensure_ascii=False
        ),
        "document_text_or_ocr": context,
        "page_region_map": json.dumps(
            bundle.get("page_region_map") or {},
            ensure_ascii=False,
            separators=(",", ":"),
        ),
        "prior_dialogue": "[]",
        "allowed_tools": "[]",
        "generation_seed": str(generation_seed),
    }
    result = template
    for name, value in values.items():
        result = result.replace("{{" + name + "}}", value)
    return result


def _model_input_image(image: Any) -> Any:
    from PIL import Image

    model_image = image.convert("RGB")
    if model_image.width * model_image.height > QUESTION_MODEL_IMAGE_MAX_PIXELS:
        scale = (
            QUESTION_MODEL_IMAGE_MAX_PIXELS
            / (model_image.width * model_image.height)
        ) ** 0.5
        model_image = model_image.resize(
            (
                max(1, int(model_image.width * scale)),
                max(1, int(model_image.height * scale)),
            ),
            Image.Resampling.LANCZOS,
        )
    return model_image.copy()


def build_prompt_input(
    *,
    bundle: dict[str, Any],
    template: PromptTemplate,
    library: PromptLibrary,
    processor: Any,
    project_root: Path,
    generation_seed: int,
    question_min_images: int = 6,
    question_max_images: int = 10,
) -> dict[str, Any]:
    resolved = expand_bundle_for_hard_chain(
        bundle,
        project_root,
        template,
        question_min_images=question_min_images,
        question_max_images=question_max_images,
    )
    context = _read_context(resolved, project_root)
    prompt_text = _replace_placeholders(
        template.text,
        bundle=resolved,
        context=context,
        generation_seed=generation_seed,
    )
    prompt_text = (
        f"generation_prompt_id={template.prompt_id}\n"
        "STAGE=QUESTION_ONLY\n"
        "必须构造完整困难链：跨至少2页定位至少3个指标；建立图表或表格与文字口径的对应关系；"
        "根据隐含金融场景说明公式选择理由；完成至少2步计算；给出可由保留图片复核的证据结论。\n"
        "JSON 必须额外包含 metric_refs（至少3项）、chart_text_alignment（至少1项）和"
        "formula_selection_reason。hardness 必须满足 page_count>=2、"
        "independent_evidence_count>=3、modality_count>=2、calculation_step_count>=2。\n"
        f"{prompt_text}"
    )
    content: list[dict[str, Any]] = []
    images = []
    from PIL import Image

    for relative in resolved.get("media_paths") or []:
        path = project_root / relative
        if not path.is_file():
            raise FileNotFoundError(f"media file does not exist: {relative}")
        with Image.open(path) as image:
            images.append(_model_input_image(image))
        content.append({"type": "image"})
    content.append({"type": "text", "text": prompt_text})
    messages = [
        {"role": "system", "content": QUESTION_SYSTEM_PROMPT},
        {"role": "user", "content": content},
    ]
    result = {
        "prompt": processor.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
            enable_thinking=False,
        ),
        "_resolved_bundle": resolved,
        "_stage": "question",
    }
    if images:
        result["multi_modal_data"] = {"image": images}
    return result


def normalize_question_candidate(
    candidate: dict[str, Any],
    *,
    bundle: dict[str, Any],
    generation_prompt_id: str,
    candidate_index: int,
) -> dict[str, Any]:
    normalized = dict(candidate)
    if isinstance(candidate.get("evidence"), list):
        normalized["evidence"] = [
            dict(item) if isinstance(item, dict) else item
            for item in candidate["evidence"]
        ]
    if isinstance(candidate.get("chart_text_alignment"), list):
        normalized["chart_text_alignment"] = [
            dict(item) if isinstance(item, dict) else item
            for item in candidate["chart_text_alignment"]
        ]
    media_paths = [
        item for item in normalized.get("media_paths") or [] if isinstance(item, str)
    ]
    allowed_media = list(bundle.get("media_paths") or [])
    media_paths = [
        _normalize_bundle_path_ref(item, allowed_media)
        for item in media_paths
    ]
    for item in normalized.get("evidence") or []:
        if not isinstance(item, dict):
            continue
        item["source_ref"] = _normalize_bundle_path_ref(
            item.get("source_ref"),
            _all_source_paths(bundle),
            page=item.get("page") if item.get("page") is not None else None,
        )
        source_ref = item.get("source_ref")
        if (
            isinstance(source_ref, str)
            and source_ref in allowed_media
            and source_ref not in media_paths
            and len(media_paths) < 5
        ):
            media_paths.append(source_ref)
    for item in normalized.get("chart_text_alignment") or []:
        if not isinstance(item, dict):
            continue
        item["visual_ref"] = _normalize_bundle_path_ref(
            item.get("visual_ref"),
            allowed_media,
        )
        visual_ref = item.get("visual_ref")
        if (
            isinstance(visual_ref, str)
            and visual_ref in allowed_media
            and visual_ref not in media_paths
            and len(media_paths) < 5
        ):
            media_paths.append(visual_ref)
    selected_or_allowed_text_refs = _all_source_paths(bundle) | set(media_paths)
    for item in normalized.get("chart_text_alignment") or []:
        if not isinstance(item, dict):
            continue
        item["text_ref"] = _normalize_bundle_path_ref(
            item.get("text_ref"),
            selected_or_allowed_text_refs,
        )
    normalized["media_paths"] = media_paths
    media_index = {path: index for index, path in enumerate(media_paths)}
    for item in normalized.get("evidence") or []:
        if not isinstance(item, dict):
            continue
        source_ref = item.get("source_ref")
        if isinstance(source_ref, str):
            page_number = _page_number_from_path(source_ref)
            if page_number is not None:
                item["page"] = page_number
            if source_ref in media_index:
                item["media_index"] = media_index[source_ref]
    normalized["candidate_id"] = (
        f"{bundle['bundle_id']}:{generation_prompt_id}:{candidate_index}"
    )
    normalized["bundle_id"] = bundle["bundle_id"]
    normalized["generation_prompt_id"] = generation_prompt_id
    normalized["task_type"] = bundle["package_type"]
    return normalized


def _normalize_source_refs(
    evidence: list[Any],
    allowed_source_refs: set[str],
) -> None:
    for item in evidence:
        if not isinstance(item, dict):
            continue
        item["source_ref"] = _normalize_bundle_path_ref(
            item.get("source_ref"),
            allowed_source_refs,
            page=item.get("page") if item.get("page") is not None else None,
        )


def _normalize_evidence_bboxes(
    evidence: list[Any],
    project_root: Path | None = None,
) -> None:
    for item in evidence:
        if not isinstance(item, dict):
            continue
        bbox = item.get("bbox")
        if not isinstance(bbox, list) or len(bbox) != 4:
            continue
        try:
            values = [float(value) for value in bbox]
        except (TypeError, ValueError):
            continue
        if all(0 <= value <= 1 for value in values):
            continue
        if all(0 <= value <= 1.05 for value in values):
            item["bbox"] = [min(1.0, max(0.0, value)) for value in values]
            continue
        source_ref = item.get("source_ref")
        if project_root is None or not isinstance(source_ref, str):
            continue
        image_path = project_root / source_ref
        if not image_path.is_file():
            continue
        from PIL import Image

        with Image.open(image_path) as image:
            width, height = image.size
        scaled = [
            values[0] / width,
            values[1] / height,
            values[2] / width,
            values[3] / height,
        ]
        if all(0 <= value <= 1.05 for value in scaled):
            item["bbox"] = [min(1.0, max(0.0, value)) for value in scaled]


def _normalize_cot(sample: dict[str, Any]) -> None:
    cot = sample.get("cot")
    if isinstance(cot, str):
        stripped = cot.strip()
        if stripped.startswith("<think>") and stripped.endswith("</think>"):
            sample["cot"] = stripped
        elif stripped:
            sample["cot"] = f"<think>{stripped}</think>"
        return
    if cot is None:
        cot = (sample.get("metadata") or {}).get("solution_trace")
    if isinstance(cot, (dict, list)) and cot:
        sample["cot"] = (
            "<think>"
            + json.dumps(cot, ensure_ascii=False, default=str)
            + "</think>"
        )


def normalize_answer_sample(
    sample: dict[str, Any],
    question_candidate: dict[str, Any],
    allowed_source_refs: set[str],
) -> dict[str, Any]:
    normalized = dict(sample)
    normalized["question"] = question_candidate["question"]
    normalized["media"] = list(question_candidate.get("media_paths") or [])
    metadata = normalized.get("metadata")
    if not isinstance(metadata, dict):
        metadata = {}
        normalized["metadata"] = metadata
    generation_prompt_id = question_candidate.get("generation_prompt_id")
    if generation_prompt_id is not None:
        metadata["generation_prompt_id"] = generation_prompt_id
    metadata["generation_status"] = "accepted"
    evidence = metadata.get("evidence")
    if not isinstance(evidence, list) or not evidence:
        evidence = copy.deepcopy(question_candidate.get("evidence") or [])
        metadata["evidence"] = evidence
    if isinstance(evidence, list):
        _normalize_source_refs(evidence, allowed_source_refs)
    _normalize_cot(normalized)
    return normalized


def _page_number_from_path(path: str) -> int | None:
    match = re.search(r"page_(\d+)", path)
    return int(match.group(1)) if match else None


def _restrict_bundle_for_answer(
    bundle: dict[str, Any],
    question_candidate: dict[str, Any],
) -> dict[str, Any]:
    selected_media = list(question_candidate.get("media_paths") or [])
    selected_pages = {
        page
        for page in (
            _page_number_from_path(path) for path in selected_media
        )
        if page is not None
    }
    selected_pages.update(
        int(item["page"])
        for item in question_candidate.get("evidence") or []
        if isinstance(item, dict) and item.get("page") is not None
    )
    resolved = dict(bundle)
    resolved["media_paths"] = selected_media
    resolved["page_numbers"] = sorted(selected_pages)
    resolved["context_files"] = {
        kind: [
            path
            for path in paths or []
            if _page_number_from_path(path) in selected_pages
        ]
        for kind, paths in (bundle.get("context_files") or {}).items()
    }
    return resolved


def build_answer_input(
    *,
    bundle: dict[str, Any],
    question_candidate: dict[str, Any],
    library: PromptLibrary,
    processor: Any,
    project_root: Path,
    generation_seed: int,
) -> dict[str, Any]:
    expanded = expand_bundle_for_hard_chain(
        bundle,
        project_root,
        PromptTemplate(
            str(question_candidate["generation_prompt_id"]),
            "",
            "",
            str(question_candidate["question"]),
        ),
    )
    resolved = _restrict_bundle_for_answer(expanded, question_candidate)
    context = _read_context(resolved, project_root)
    answer_chain_requirement = (
        "答案推导链必须依次写明：检索到的页码与至少3个指标；"
        "图表或表格与文字口径的对应关系；金融场景及公式选择理由；"
        "公式、数值代入和至少2步中间计算；单位换算与舍入；"
        "最终结论及其证据回指。不得跳过任一环节。\n"
    )
    prompt_text = (
        "STAGE=ANSWER_ONLY\n"
        "FIXED_QUESTION\n"
        f"{answer_chain_requirement}"
        "第二阶段：根据固定问题和原始证据生成答案。固定问题不得改写。\n"
        f"固定问题：{question_candidate['question']}\n"
        f"问题候选 JSON：{json.dumps(question_candidate, ensure_ascii=False)}\n"
        f"原始证据上下文：\n{context}\n\n"
        "JSON 外不得输出思考过程、分析草稿或 <think> 标签。只输出 JSON 对象。"
        "必须包含 record_id、source_dataset、source_id、modality、"
        "question、answer、cot、task_type、media、is_complete、missing_assets、metadata。"
        "cot 必须是且只能是一个 <think>...</think> 块，内部写完整连续推导链，"
        "包括证据读取、公式或判断规则、数值代入、中间结果、单位换算、舍入和最终复核。"
        "metadata.solution_trace 必须包含 retrieved_metrics、chart_text_alignment、"
        "formula_selection_reason、steps、calculations、unit_and_rounding 和"
        "evidence_conclusion；retrieved_metrics 至少3项，calculations 至少2项。"
        "calculations 中每项必须是对象，并包含 expression、claimed_result、unit、"
        "rounding_digits、evidence_indices。expression 只能使用不带千分位逗号的数字、"
        "括号、+、-、*、/ 和 abs()；claimed_result 必须是按 rounding_digits "
        "舍入后的数值；evidence_indices 必须指向提供计算输入值的证据。"
    )
    content: list[dict[str, Any]] = []
    images = []
    from PIL import Image

    for relative in question_candidate.get("media_paths") or resolved.get("media_paths") or []:
        path = project_root / relative
        if not path.is_file():
            raise FileNotFoundError(f"media file does not exist: {relative}")
        with Image.open(path) as image:
            images.append(_model_input_image(image))
        content.append({"type": "image"})
    content.append({"type": "text", "text": prompt_text})
    messages = [
        {"role": "system", "content": library.system_prompt},
        {"role": "user", "content": content},
    ]
    result = {
        "prompt": processor.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
            enable_thinking=False,
        ),
        "_resolved_bundle": resolved,
        "_question_candidate": question_candidate,
        "_stage": "answer",
    }
    if images:
        result["multi_modal_data"] = {"image": images}
    return result


def build_synthetic_text_input(
    *,
    bundle: dict[str, Any],
    library: PromptLibrary,
    processor: Any,
    generation_seed: int,
) -> dict[str, Any]:
    text = _replace_placeholders(
        SYNTHETIC_TEXT_PROMPT,
        bundle={**bundle, "media_paths": [], "page_region_map": {}},
        context="",
        generation_seed=generation_seed,
    )
    messages = [
        {"role": "system", "content": SYNTHETIC_QUESTION_SYSTEM_PROMPT},
        {"role": "user", "content": text},
    ]
    return {
        "prompt": processor.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
            enable_thinking=False,
        ),
        "_resolved_bundle": {
            **bundle,
            "package_type": "synthetic_text",
            "media_paths": [],
            "context_files": {},
            "page_region_map": {},
        },
        "_stage": "question",
    }


def parse_generated_sample(text: str) -> dict[str, Any]:
    def is_preferred_object(value: dict[str, Any]) -> bool:
        question_fields = {
            "question",
            "media_paths",
            "evidence",
            "expected_steps",
            "metric_refs",
        }
        answer_fields = {"record_id", "question", "answer", "metadata"}
        return question_fields.issubset(value) or answer_fields.issubset(value)

    value = text.strip()
    candidates = [
        match.group(1).strip()
        for match in re.finditer(
            r"```(?:json)?\s*(.*?)\s*```",
            value,
            flags=re.DOTALL | re.IGNORECASE,
        )
    ]
    candidates.append(value)
    if "</think>" in value:
        candidates.append(value.rsplit("</think>", 1)[1].strip())

    decoder = json.JSONDecoder()
    for candidate in candidates:
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError:
            pass
        else:
            if isinstance(parsed, dict):
                return parsed
            continue

        embedded = []
        for match in re.finditer(r"\{", candidate):
            try:
                item, _ = decoder.raw_decode(candidate[match.start() :])
            except json.JSONDecodeError:
                continue
            if isinstance(item, dict):
                embedded.append(item)
        if embedded:
            for item in embedded:
                if is_preferred_object(item):
                    return item
            return embedded[-1]

    json.loads(value)
    raise ValueError("generated output must be a JSON object")


def _all_source_paths(bundle: dict[str, Any]) -> set[str]:
    paths = set(bundle.get("media_paths") or [])
    for values in (bundle.get("context_files") or {}).values():
        paths.update(values or [])
    paths.add(f"inline:{bundle['bundle_id']}")
    return paths


def _normalize_bundle_path_ref(
    value: Any,
    allowed_paths: set[str] | list[str],
    *,
    page: int | None = None,
) -> Any:
    if not isinstance(value, str):
        return value
    allowed = set(allowed_paths)
    if value in allowed:
        return value
    prefixes = ("pdf_text:", "ocr:", "table:", "figure:")
    stripped = value
    for prefix in prefixes:
        if stripped.startswith(prefix):
            stripped = stripped[len(prefix) :]
            if stripped in allowed:
                return stripped
            break
    value_name = Path(stripped).name
    value_stem = Path(stripped).stem
    candidates = [
        path
        for path in allowed
        if Path(path).name in (stripped, value_name)
        or Path(path).stem in (stripped, value_stem)
    ]
    if page is not None:
        page_candidates = [
            path
            for path in candidates
            if _page_number_from_path(path) == int(page)
        ]
        if len(page_candidates) == 1:
            candidates = page_candidates
    return candidates[0] if len(candidates) == 1 else value


def _validate_evidence_paths(
    evidence: list[dict[str, Any]],
    bundle: dict[str, Any],
    project_root: Path,
) -> None:
    allowed = _all_source_paths(bundle)
    for item in evidence:
        source_ref = item.get("source_ref")
        source_ref = _normalize_bundle_path_ref(
            source_ref,
            allowed,
            page=item.get("page") if item.get("page") is not None else None,
        )
        item["source_ref"] = source_ref
        if source_ref not in allowed:
            raise ValueError(f"evidence source is not in bundle: {source_ref}")
        if isinstance(source_ref, str) and not source_ref.startswith("inline:"):
            if not (project_root / source_ref).is_file():
                raise ValueError(f"evidence source does not exist: {source_ref}")


def _normalize_grounding_text(value: Any) -> str:
    text = unicodedata.normalize("NFKC", str(value or "")).lower()
    return re.sub(r"[\s,，。；;：:、\"'“”‘’（）()\[\]【】]", "", text)


def _number_tokens(value: Any) -> set[tuple[Decimal, bool]]:
    tokens: set[tuple[Decimal, bool]] = set()
    text = unicodedata.normalize("NFKC", str(value or ""))
    for match in re.finditer(
        r"[-+]?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?%?",
        text,
    ):
        raw = match.group(0)
        is_percent = raw.endswith("%")
        raw = raw.rstrip("%").replace(",", "")
        try:
            tokens.add((Decimal(raw), is_percent))
        except InvalidOperation:
            continue
    return tokens


def _page_source_text(
    bundle: dict[str, Any],
    project_root: Path,
    page: int,
) -> str:
    paths: list[str] = []
    for values in (bundle.get("context_files") or {}).values():
        for path in values or []:
            path_page = _page_number_from_path(path)
            if path_page in (None, page):
                paths.append(path)
    for item in (bundle.get("page_region_map") or {}).get("page_index") or []:
        if int(item.get("page_number") or 0) != page:
            continue
        for field in ("text", "ocr"):
            path = item.get(field)
            if isinstance(path, str):
                paths.append(path)
        paths.extend(
            path
            for path in (item.get("tables") or [])
            if isinstance(path, str)
        )
    chunks: list[str] = []
    for relative in dict.fromkeys(paths):
        path = project_root / relative
        if not path.is_file():
            continue
        try:
            chunks.append(path.read_text(encoding="utf-8", errors="ignore"))
        except OSError:
            continue
    return "\n".join(chunks)


def _metric_name_is_grounded(name: str, evidence_text: str) -> bool:
    normalized_name = _normalize_grounding_text(name)
    normalized_evidence = _normalize_grounding_text(evidence_text)
    if normalized_name and normalized_name in normalized_evidence:
        return True
    financial_terms = (
        "营业收入",
        "净利润",
        "现金流",
        "应收账款",
        "毛利率",
        "周转率",
        "增长率",
        "资产",
        "负债",
        "利润",
        "收入",
        "成本",
        "费用",
        "损失",
        "收益",
    )
    return any(
        term in normalized_name and term in normalized_evidence
        for term in financial_terms
    )


def _validate_metric_and_evidence_grounding(
    candidate: dict[str, Any],
    bundle: dict[str, Any],
    project_root: Path,
) -> dict[str, Any]:
    evidence = candidate.get("evidence") or []
    if bundle.get("package_type") != "synthetic_text":
        for index, item in enumerate(evidence):
            quote = str(item.get("text_quote") or "").strip()
            page = item.get("page")
            if not quote or page is None:
                raise ValueError(f"evidence[{index}] missing text_quote or page")

    metric_refs = candidate.get("metric_refs") or []
    required_fields = ("name", "page", "value", "unit", "evidence_index")
    for metric in metric_refs:
        if not isinstance(metric, dict):
            raise ValueError("metric_refs items must be objects")
        for field in required_fields:
            if field not in metric or (
                field not in ("page", "unit")
                and not str(metric.get(field)).strip()
            ):
                raise ValueError(f"missing metric field: {field}")
        try:
            evidence_index = int(metric["evidence_index"])
        except (TypeError, ValueError):
            raise ValueError("invalid metric evidence_index") from None
        if not 0 <= evidence_index < len(evidence):
            raise ValueError("invalid metric evidence_index")
        linked = evidence[evidence_index]
        if metric.get("page") != linked.get("page"):
            raise ValueError(f"metric page does not match evidence: {metric['name']}")
        linked_text = " ".join(
            (
                str(linked.get("text_quote") or ""),
                json.dumps(
                    linked.get("table_cell"),
                    ensure_ascii=False,
                    default=str,
                ),
            )
        )
        metric_numbers = _number_tokens(metric["value"])
        if metric_numbers:
            if not metric_numbers.issubset(_number_tokens(linked_text)):
                raise ValueError(
                    f"metric value lacks evidence: {metric['name']}"
                )
        elif (
            _normalize_grounding_text(metric["value"])
            not in _normalize_grounding_text(linked_text)
        ):
            raise ValueError(f"metric value lacks evidence: {metric['name']}")
    return {
        "metrics_passed": True,
        "evidence_grounding_passed": True,
    }


def _evaluate_decimal_expression(expression: str) -> Decimal:
    def evaluate(node: ast.AST) -> Decimal:
        if isinstance(node, ast.Expression):
            return evaluate(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return Decimal(str(node.value))
        if isinstance(node, ast.UnaryOp) and isinstance(
            node.op, (ast.UAdd, ast.USub)
        ):
            value = evaluate(node.operand)
            return value if isinstance(node.op, ast.UAdd) else -value
        if isinstance(node, ast.BinOp) and isinstance(
            node.op, (ast.Add, ast.Sub, ast.Mult, ast.Div)
        ):
            left = evaluate(node.left)
            right = evaluate(node.right)
            if isinstance(node.op, ast.Add):
                return left + right
            if isinstance(node.op, ast.Sub):
                return left - right
            if isinstance(node.op, ast.Mult):
                return left * right
            return left / right
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "abs"
            and len(node.args) == 1
            and not node.keywords
        ):
            return abs(evaluate(node.args[0]))
        raise ValueError("unsupported calculation expression")

    try:
        return evaluate(ast.parse(expression, mode="eval"))
    except (SyntaxError, InvalidOperation, ZeroDivisionError) as error:
        raise ValueError(f"invalid calculation expression: {expression}") from error


def _validate_structured_calculations(
    calculations: list[Any],
    evidence: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    if not isinstance(calculations, list) or len(calculations) < 2:
        raise ValueError("solution_trace needs at least two calculations")
    results: list[dict[str, Any]] = []
    required = (
        "expression",
        "claimed_result",
        "unit",
        "rounding_digits",
        "evidence_indices",
    )
    for index, calculation in enumerate(calculations):
        if not isinstance(calculation, dict):
            raise ValueError("calculations must contain structured objects")
        for field in required:
            if field not in calculation:
                raise ValueError(f"calculation[{index}] missing field: {field}")
        evidence_indices = calculation["evidence_indices"]
        if not isinstance(evidence_indices, list) or not evidence_indices:
            raise ValueError(f"calculation[{index}] has no evidence_indices")
        linked_evidence: list[dict[str, Any]] = []
        for evidence_index in evidence_indices:
            if not isinstance(evidence_index, int) or not (
                0 <= evidence_index < len(evidence)
            ):
                raise ValueError(f"calculation[{index}] invalid evidence index")
            linked_evidence.append(evidence[evidence_index])
        expression = str(calculation["expression"]).strip()
        computed = _evaluate_decimal_expression(expression)
        try:
            digits = int(calculation["rounding_digits"])
            claimed = Decimal(str(calculation["claimed_result"]))
        except (TypeError, ValueError, InvalidOperation) as error:
            raise ValueError(
                f"calculation[{index}] has invalid result or rounding"
            ) from error
        if not 0 <= digits <= 8:
            raise ValueError(f"calculation[{index}] invalid rounding_digits")
        quantum = Decimal("1").scaleb(-digits)
        rounded = computed.quantize(quantum, rounding=ROUND_HALF_UP)
        if claimed != rounded:
            raise ValueError(
                "calculation result mismatch: "
                f"claimed {claimed}, computed {rounded}"
            )
        results.append(
            {
                "expression": expression,
                "computed_result": float(rounded),
                "unit": str(calculation["unit"]),
                "rounding_digits": digits,
            }
        )
    return results


def validate_question_candidate(
    candidate: dict[str, Any],
    bundle: dict[str, Any],
    project_root: Path,
) -> dict[str, Any]:
    if "answer" in candidate:
        raise ValueError("question candidate must not contain answer")
    for field in (
        "candidate_id",
        "bundle_id",
        "generation_prompt_id",
        "question",
        "task_type",
        "media_paths",
        "evidence",
        "expected_steps",
        "metric_refs",
        "chart_text_alignment",
        "formula_selection_reason",
        "hardness",
        "finance_checks",
    ):
        if field not in candidate:
            raise ValueError(f"missing question candidate field: {field}")
    if candidate["bundle_id"] != bundle["bundle_id"]:
        raise ValueError("question candidate bundle_id mismatch")
    if not str(candidate.get("question") or "").strip():
        raise ValueError("question candidate has no question")
    if bundle.get("package_type") == "synthetic_text":
        if candidate.get("media_paths") != []:
            raise ValueError("synthetic question must not contain images")
        evidence = candidate.get("evidence") or []
        if not isinstance(evidence, list) or len(evidence) < 3:
            raise ValueError("synthetic question needs at least three facts")
        _validate_evidence_paths(evidence, bundle, project_root)
        metric_refs = candidate.get("metric_refs") or []
        if not isinstance(metric_refs, list) or len(metric_refs) < 3:
            raise ValueError("synthetic question needs at least three metrics")
        expected_steps = candidate.get("expected_steps") or []
        if not isinstance(expected_steps, list) or len(expected_steps) < 2:
            raise ValueError("synthetic question needs at least two steps")
        if not str(candidate.get("formula_selection_reason") or "").strip():
            raise ValueError("formula_selection_reason is required")
        hardness = candidate.get("hardness") or {}
        if (
            int(hardness.get("independent_evidence_count") or 0) < 3
            or int(hardness.get("calculation_step_count") or 0) < 2
        ):
            raise ValueError("not a hard synthetic question")
        finance_checks = candidate.get("finance_checks") or {}
        for name in ("entity", "report_period", "scope", "currency_unit", "rounding"):
            if finance_checks.get(name) is not True:
                raise ValueError(f"finance check failed: {name}")
        return _validate_metric_and_evidence_grounding(
            candidate,
            bundle,
            project_root,
        )
    media_paths = candidate.get("media_paths") or []
    if not isinstance(media_paths, list) or not 1 <= len(media_paths) <= 5:
        raise ValueError("question candidate must keep 1 to 5 images")
    allowed_media = set(bundle.get("media_paths") or [])
    media_paths = [
        _normalize_bundle_path_ref(path, allowed_media)
        for path in media_paths
    ]
    candidate["media_paths"] = media_paths
    selected_media = set(media_paths)
    for path in media_paths:
        if path not in allowed_media:
            raise ValueError(f"question media path is not in bundle: {path}")
        if not (project_root / path).is_file():
            raise ValueError(f"question media path does not exist: {path}")
    evidence = candidate.get("evidence") or []
    if not isinstance(evidence, list) or len(evidence) < 3:
        raise ValueError("question needs at least three evidence items")
    _validate_evidence_paths(evidence, bundle, project_root)
    media_index = {path: index for index, path in enumerate(media_paths)}
    for item in evidence:
        source_ref = item.get("source_ref") if isinstance(item, dict) else None
        if isinstance(source_ref, str) and source_ref in allowed_media:
            if source_ref not in selected_media:
                raise ValueError(
                    f"evidence image is not kept in question media: {source_ref}"
                )
            if item.get("media_index") is not None and int(item["media_index"]) != media_index[source_ref]:
                raise ValueError("evidence media_index does not match question media")

    actual_pages = {
        int(page_number) for page_number in bundle.get("page_numbers") or []
    }
    if len(actual_pages) < 2:
        raise ValueError("bundle has fewer than two pages")
    evidence_pages = {
        int(item["page"])
        for item in evidence
        if item.get("page") is not None
    }
    if len(evidence_pages & actual_pages) < 2:
        raise ValueError("evidence must span at least two bundle pages")
    metric_refs = candidate.get("metric_refs") or []
    if not isinstance(metric_refs, list) or len(metric_refs) < 3:
        raise ValueError("metric_refs must contain at least three metrics")
    grounding_report = _validate_metric_and_evidence_grounding(
        candidate,
        bundle,
        project_root,
    )
    chart_text_alignment = candidate.get("chart_text_alignment") or []
    if not isinstance(chart_text_alignment, list) or not chart_text_alignment:
        raise ValueError("chart_text_alignment must describe visual-text alignment")
    allowed_text_refs = {
        path
        for paths in (bundle.get("context_files") or {}).values()
        for path in paths or []
    }
    for item in chart_text_alignment:
        if not isinstance(item, dict):
            continue
        item["visual_ref"] = _normalize_bundle_path_ref(
            item.get("visual_ref"),
            selected_media,
        )
        item["text_ref"] = _normalize_bundle_path_ref(
            item.get("text_ref"),
            allowed_text_refs | selected_media,
        )
    if any(
        item.get("visual_ref") not in selected_media
        or (
            item.get("text_ref") not in allowed_text_refs
            and item.get("text_ref") not in selected_media
        )
        for item in chart_text_alignment
        if isinstance(item, dict)
    ):
        raise ValueError("chart_text_alignment references visual not kept in question media or invalid text")
    if not str(candidate.get("formula_selection_reason") or "").strip():
        raise ValueError("formula_selection_reason is required")

    hardness = candidate.get("hardness") or {}
    independent = int(hardness.get("independent_evidence_count") or len(evidence))
    calc_steps = int(hardness.get("calculation_step_count") or 0)
    page_count = int(
        hardness.get("page_count") or len(set(bundle.get("page_numbers") or []))
    )
    modality_count = int(hardness.get("modality_count") or 0)
    if not (
        independent >= 3
        and page_count >= 2
        and modality_count >= 2
        and calc_steps >= 2
    ):
        raise ValueError("not a hard question")

    finance_checks = candidate.get("finance_checks") or {}
    for name in ("entity", "report_period", "scope", "currency_unit", "rounding"):
        if finance_checks.get(name) is not True:
            raise ValueError(f"finance check failed: {name}")

    tables = (bundle.get("page_region_map") or {}).get("tables") or []
    if any(table.get("review_required") is True for table in tables):
        consistency = candidate.get("review_required_consistency") or {}
        if any(
            consistency.get(name) is not True
            for name in ("table_json", "markdown", "ocr", "image")
        ):
            raise ValueError("review_required table lacks cross-source consistency")
    return grounding_report


def validate_generated_sample(
    sample: dict[str, Any],
    bundle: dict[str, Any],
    project_root: Path,
) -> None:
    for field in (
        "record_id",
        "source_dataset",
        "source_id",
        "modality",
        "question",
        "task_type",
        "media",
        "is_complete",
        "missing_assets",
        "metadata",
    ):
        if field not in sample:
            raise ValueError(f"missing generated field: {field}")
    metadata = sample["metadata"]
    if metadata.get("generation_status") != "accepted":
        raise ValueError("generated sample was rejected")
    if not sample.get("is_complete") or sample.get("missing_assets"):
        raise ValueError("accepted sample is incomplete")
    if not isinstance(sample.get("answer"), str) or not sample["answer"].strip():
        raise ValueError("accepted sample has no answer")
    if not isinstance(sample.get("question"), str) or not sample["question"].strip():
        raise ValueError("accepted sample has no question")

    evidence = metadata.get("evidence") or []
    steps = (metadata.get("solution_trace") or {}).get("steps") or []
    page_count = len(set(bundle.get("page_numbers") or []))
    if len(evidence) < 2 and len(steps) < 2 and page_count < 2:
        raise ValueError("not a hard question")

    _validate_evidence_paths(evidence, bundle, project_root)

    answer = re.sub(r"\s+", "", sample["answer"])
    question = re.sub(r"\s+", "", sample["question"])
    if len(answer) >= 4 and answer in question:
        raise ValueError("question leaks the answer")


def validate_answer_sample(
    sample: dict[str, Any],
    question_candidate: dict[str, Any],
    bundle: dict[str, Any],
    project_root: Path,
) -> dict[str, Any]:
    sample_question = re.sub(r"\s+", "", str(sample.get("question") or ""))
    fixed_question = re.sub(
        r"\s+",
        "",
        str(question_candidate.get("question") or ""),
    )
    if sample_question != fixed_question:
        raise ValueError("answer changed the fixed question")
    if isinstance(sample.get("media"), list):
        sample["media"] = [
            _normalize_bundle_path_ref(path, question_candidate.get("media_paths") or [])
            for path in sample["media"]
        ]
    if sample.get("media") != question_candidate.get("media_paths"):
        raise ValueError("answer media does not match question candidate")
    cot = sample.get("cot")
    if not isinstance(cot, str):
        raise ValueError("answer sample missing cot")
    stripped = cot.strip()
    if (
        stripped.count("<think>") != 1
        or stripped.count("</think>") != 1
        or not re.fullmatch(r"<think>[\s\S]+</think>", stripped)
    ):
        raise ValueError("cot must be a single think block")
    solution_trace = (
        (sample.get("metadata") or {}).get("solution_trace") or {}
    )
    trace_steps = solution_trace.get("steps") or []
    if len(trace_steps) < 2:
        raise ValueError("cot lacks at least two reasoning steps")
    retrieved_metrics = (
        solution_trace.get("retrieved_metrics")
        or question_candidate.get("metric_refs")
        or []
    )
    if len(retrieved_metrics) < 3:
        raise ValueError("solution_trace needs at least three retrieved_metrics")
    chart_text_alignment = (
        solution_trace.get("chart_text_alignment")
        or question_candidate.get("chart_text_alignment")
        or []
    )
    if not chart_text_alignment:
        raise ValueError("solution_trace missing chart_text_alignment")
    allowed_text_refs = {
        path
        for paths in (bundle.get("context_files") or {}).values()
        for path in paths or []
    }
    for item in chart_text_alignment:
        if not isinstance(item, dict):
            continue
        item["visual_ref"] = _normalize_bundle_path_ref(
            item.get("visual_ref"),
            question_candidate.get("media_paths") or [],
        )
        item["text_ref"] = _normalize_bundle_path_ref(
            item.get("text_ref"),
            allowed_text_refs | set(question_candidate.get("media_paths") or []),
        )
    formula_selection_reason = (
        solution_trace.get("formula_selection_reason")
        or question_candidate.get("formula_selection_reason")
    )
    if not str(formula_selection_reason or "").strip():
        raise ValueError("solution_trace missing formula_selection_reason")
    if len(solution_trace.get("calculations") or []) < 2:
        raise ValueError("solution_trace needs at least two calculations")
    if len(re.findall(r"[=+\-*/%]|率|比较|计算|代入", stripped)) < 2:
        raise ValueError("cot lacks checkable calculation or comparison")
    expected_prompt = question_candidate.get("generation_prompt_id")
    actual_prompt = (sample.get("metadata") or {}).get("generation_prompt_id")
    if actual_prompt != expected_prompt:
        raise ValueError("generation_prompt_id does not match question candidate")
    grounding_report = _validate_metric_and_evidence_grounding(
        question_candidate,
        bundle,
        project_root,
    )
    calculation_results = _validate_structured_calculations(
        solution_trace.get("calculations") or [],
        (sample.get("metadata") or {}).get("evidence") or [],
    )
    report = {
        **grounding_report,
        "arithmetic_passed": True,
        "calculation_results": calculation_results,
        "failures": [],
    }
    sample["metadata"]["programmatic_validation"] = report
    validate_generated_sample(sample, bundle, project_root)
    return report


def project_training_record(
    sample: dict[str, Any],
    bundle: dict[str, Any],
    *,
    media_paths: Sequence[str] | None = None,
) -> dict[str, Any]:
    media = list(
        sample.get("media") or []
        if media_paths is None
        else media_paths
    )
    question = sample["question"].strip()
    user_content = "<image>" * len(media) + question
    cot = str(sample.get("cot") or "").strip()
    if cot:
        record = {
            "record_id": sample["record_id"],
            "messages": [
                {"role": "user", "content": user_content},
                {
                    "role": "assistant",
                    "content": f"{cot}\n\n答案：{sample['answer'].strip()}",
                },
            ],
            "source": (
                "synthetic_finance_text"
                if not media
                else "finance_reports_generated"
            ),
            "split": "train",
            "task": bundle.get("package_type") or "finance_qa",
        }
        if media:
            record["images"] = media
        return record
    trace = sample["metadata"].get("solution_trace") or {}
    steps = [
        str(item.get("description") or "").strip()
        for item in trace.get("steps") or []
        if str(item.get("description") or "").strip()
    ]
    explanation = "\n".join(
        f"{index}. {description}"
        for index, description in enumerate(steps, start=1)
    )
    if not explanation:
        explanation = str(trace.get("summary") or "").strip()
    assistant = (
        f"{explanation}\n\n答案：{sample['answer'].strip()}"
        if explanation
        else f"答案：{sample['answer'].strip()}"
    )
    record = {
        "record_id": sample["record_id"],
        "messages": [
            {"role": "user", "content": user_content},
            {"role": "assistant", "content": assistant},
        ],
        "source": (
            "synthetic_finance_text"
            if not media
            else "finance_reports_generated"
        ),
        "split": "train",
        "task": bundle.get("package_type") or "finance_qa",
    }
    if media:
        record["images"] = media
    return record


def copy_training_images(
    sample: dict[str, Any],
    *,
    project_root: Path,
    output_dir: Path,
) -> list[str]:
    source_paths = list(sample.get("media") or [])
    if not source_paths:
        return []
    import hashlib
    import shutil

    identity = str(sample["record_id"]) + "\0" + "\0".join(source_paths)
    record_dir = (
        output_dir
        / "assets"
        / hashlib.sha256(identity.encode("utf-8")).hexdigest()[:16]
    )
    record_dir.mkdir(parents=True, exist_ok=True)
    copied = []
    for index, relative in enumerate(source_paths, start=1):
        source = project_root / relative
        destination = record_dir / f"image_{index:02d}{source.suffix.lower()}"
        shutil.copy2(source, destination)
        copied.append(destination.relative_to(project_root).as_posix())
    return copied


def _json_line(value: dict[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":")) + "\n"


def _sha256_file(path: Path) -> str | None:
    if not path.is_file():
        return None
    import hashlib

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _part_path(output_dir: Path, kind: str, rank: int) -> Path:
    return output_dir / ".parts" / kind / f"rank_{rank:04d}.jsonl"


def _rank_checkpoint(output_dir: Path, rank: int) -> dict[str, Any]:
    candidates = []
    for kind in ("answers", "questions"):
        path = output_dir / "checkpoints" / kind / f"rank_{rank:04d}.json"
        if path.exists():
            candidates.append(path)
    if not candidates:
        return {}
    path = max(candidates, key=lambda item: item.stat().st_mtime)
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def _completed_keys(output_dir: Path, rank: int) -> set[str]:
    completed = set()
    for path in (
        _part_path(output_dir, "raw", rank),
        _part_path(output_dir, "errors", rank),
    ):
        repair_jsonl_tail(path)
        if not path.exists():
            continue
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    completed.add(str(json.loads(line)["record_key"]))
    return completed


def _accepted_record_ids(output_dir: Path, rank: int) -> set[str]:
    accepted = set()
    for kind in ("multi", "text"):
        path = _part_path(output_dir, kind, rank)
        repair_jsonl_tail(path)
        if not path.exists():
            continue
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    accepted.add(str(json.loads(line)["record_id"]))
    return accepted


def _call_generate_batch(
    generate_batch: Callable[..., Sequence[str]],
    inputs: Sequence[dict[str, Any]],
    seeds: Sequence[int],
    temperatures: Sequence[float],
) -> list[str]:
    try:
        return list(generate_batch(inputs, seeds, temperatures))
    except TypeError as error:
        if "positional" not in str(error) and "argument" not in str(error):
            raise
        return list(generate_batch(inputs, seeds))


def process_shard(
    *,
    input_path: Path,
    project_root: Path,
    output_dir: Path,
    rank: int,
    world_size: int,
    library: PromptLibrary,
    processor: Any,
    generate_batch: Callable[..., Sequence[str]],
    batch_size: int,
    base_seed: int,
    max_records: int | None = None,
    max_records_per_type: int | None = None,
    heartbeat_callback: Callable[[], None] | None = None,
    target_accepted: int | None = None,
    question_temperature: float = 0.9,
    answer_temperature: float = 0.6,
    max_model_calls: int | None = None,
    question_min_images: int = 6,
    question_max_images: int = 10,
) -> dict[str, Any]:
    if batch_size < 1:
        raise ValueError("batch_size must be positive")
    if target_accepted is not None and target_accepted < 1:
        raise ValueError("target_accepted must be positive")
    if max_model_calls is not None and max_model_calls < 1:
        raise ValueError("max_model_calls must be positive")
    if (
        question_min_images < 1
        or question_max_images < question_min_images
        or question_max_images > 10
    ):
        raise ValueError("question image limits must satisfy 1 <= min <= max <= 10")
    completed = _completed_keys(output_dir, rank)
    accepted_record_ids = _accepted_record_ids(output_dir, rank)
    checkpoint_state = _rank_checkpoint(output_dir, rank)
    checkpoint_counters = checkpoint_state.get("counters") or {}
    model_calls = int(
        checkpoint_state.get("model_calls")
        or checkpoint_counters.get("model_calls")
        or 0
    )
    stop_reason = checkpoint_state.get("stop_reason") or checkpoint_counters.get(
        "stop_reason"
    )
    counters = {
        "accepted_multi": 0,
        "accepted_text": 0,
        "errors": 0,
        "skipped": 0,
        "model_calls": model_calls,
        "accepted_total": len(accepted_record_ids),
        "stop_reason": stop_reason,
    }

    def sync_counters() -> None:
        counters["model_calls"] = model_calls
        counters["accepted_total"] = len(accepted_record_ids)
        counters["stop_reason"] = stop_reason

    def remaining_model_calls() -> int | None:
        if max_model_calls is None:
            return None
        return max(max_model_calls - model_calls, 0)

    def model_call_budget_exhausted() -> bool:
        remaining = remaining_model_calls()
        return remaining is not None and remaining <= 0

    def set_stop_reason(reason: str) -> None:
        nonlocal stop_reason
        if stop_reason != "target_accepted":
            stop_reason = reason
        sync_counters()

    if model_call_budget_exhausted():
        set_stop_reason("max_model_calls")
        return counters
    if (
        target_accepted is not None
        and len(accepted_record_ids) >= target_accepted
    ):
        set_stop_reason("target_accepted")
        return counters
    usage: dict[str, int] = {}
    selected_by_type: Counter[str] = Counter()
    paths = {
        kind: _part_path(output_dir, kind, rank)
        for kind in (
            "raw",
            "raw_questions",
            "questions",
            "raw_answers",
            "multi",
            "text",
            "errors",
        )
    }
    for path in paths.values():
        path.parent.mkdir(parents=True, exist_ok=True)

    with (
        paths["raw"].open("a", encoding="utf-8") as raw_handle,
        paths["raw_questions"].open("a", encoding="utf-8") as raw_question_handle,
        paths["questions"].open("a", encoding="utf-8") as question_handle,
        paths["raw_answers"].open("a", encoding="utf-8") as raw_answer_handle,
        paths["multi"].open("a", encoding="utf-8") as multi_handle,
        paths["text"].open("a", encoding="utf-8") as text_handle,
        paths["errors"].open("a", encoding="utf-8") as error_handle,
    ):
        accepted_by_offset: Counter[int] = Counter()

        def write_checkpoints(record_key: str | None) -> None:
            sync_counters()
            payload = {
                "rank": rank,
                "record_key": record_key,
                "counters": counters,
                "model_calls": model_calls,
                "accepted_total": len(accepted_record_ids),
                "stop_reason": stop_reason,
            }
            for kind in ("answers", "questions"):
                checkpoint = (
                    output_dir
                    / "checkpoints"
                    / kind
                    / f"rank_{rank:04d}.json"
                )
                checkpoint.parent.mkdir(parents=True, exist_ok=True)
                checkpoint.write_text(
                    json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8",
                )

        def process_batch(
            batch: list[
                tuple[
                    str,
                    int,
                    int,
                    dict[str, Any],
                    PromptTemplate,
                    dict[str, Any],
                ]
            ],
        ) -> bool:
            nonlocal model_calls
            valid = [item for item in batch if "_input_error" not in item[5]]
            question_outputs: dict[str, str] = {}
            generation_errors: dict[str, Exception] = {}

            def generate_items(
                items: list[
                    tuple[
                        str,
                        int,
                        int,
                        dict[str, Any],
                        PromptTemplate,
                        dict[str, Any],
                    ]
                ],
            ) -> None:
                nonlocal model_calls
                if not items:
                    return
                remaining = remaining_model_calls()
                if remaining is not None and remaining <= 0:
                    set_stop_reason("max_model_calls")
                    return
                submitted = items
                if remaining is not None and len(submitted) > remaining:
                    submitted = submitted[:remaining]
                try:
                    seeds = [
                        stable_seed(
                            base_seed,
                            f"finance_qa:{item[2]}:{item[4].prompt_id}:question",
                            item[1],
                        )
                        for item in submitted
                    ]
                    model_calls += len(submitted)
                    sync_counters()
                    generated = _call_generate_batch(
                        generate_batch,
                        [item[5] for item in submitted],
                        seeds,
                        [question_temperature for _ in submitted],
                    )
                    if len(generated) != len(submitted):
                        raise ValueError(
                            f"generator returned {len(generated)} outputs "
                            f"for {len(submitted)} inputs"
                        )
                    question_outputs.update(
                        {
                            item[0]: value
                            for item, value in zip(submitted, generated)
                        }
                    )
                except Exception as error:
                    if len(submitted) == 1:
                        generation_errors[submitted[0][0]] = error
                        return
                    middle = len(submitted) // 2
                    generate_items(submitted[:middle])
                    generate_items(submitted[middle:])
                if model_call_budget_exhausted():
                    set_stop_reason("max_model_calls")

            generate_items(valid)

            target_reached = False
            for key, offset, sample_index, row, template, prompt_input in batch:
                question_raw = question_outputs.get(key)
                answer_raw = ""
                skip_error_record = False
                try:
                    if "_input_error" in prompt_input:
                        raise prompt_input["_input_error"]
                    if (
                        key not in question_outputs
                        and key not in generation_errors
                        and model_call_budget_exhausted()
                    ):
                        target_reached = True
                        skip_error_record = True
                        continue
                    if key in generation_errors:
                        raise generation_errors[key]
                    requested = int(row.get("samples_requested") or 2)
                    if accepted_by_offset[offset] >= requested:
                        counters["skipped"] += 1
                        continue
                    resolved = prompt_input["_resolved_bundle"]
                    question_raw = question_outputs[key]
                    question_candidate = parse_generated_sample(question_raw)
                    question_candidate = normalize_question_candidate(
                        question_candidate,
                        bundle=resolved,
                        generation_prompt_id=template.prompt_id,
                        candidate_index=sample_index,
                    )
                    _normalize_source_refs(
                        question_candidate.get("evidence") or [],
                        _all_source_paths(resolved),
                    )
                    _normalize_evidence_bboxes(
                        question_candidate.get("evidence") or [],
                        project_root,
                    )
                    validate_question_candidate(
                        question_candidate,
                        resolved,
                        project_root,
                    )
                    raw_question_handle.write(
                        _json_line(
                            {
                                "record_key": key,
                                "byte_offset": offset,
                                "candidate_index": sample_index,
                                "bundle_id": row["bundle_id"],
                                "generation_prompt_id": template.prompt_id,
                                "raw_text": question_raw,
                            }
                        )
                    )
                    question_handle.write(
                        _json_line(
                            {
                                "record_key": key,
                                "byte_offset": offset,
                                "candidate": question_candidate,
                            }
                        )
                    )
                    if model_call_budget_exhausted():
                        target_reached = True
                        skip_error_record = True
                        continue
                    answer_input = build_answer_input(
                        bundle=resolved,
                        question_candidate=question_candidate,
                        library=library,
                        processor=processor,
                        project_root=project_root,
                        generation_seed=stable_seed(
                            base_seed,
                            f"finance_qa:{sample_index}:{template.prompt_id}:answer",
                            offset,
                        ),
                    )
                    last_error: Exception | None = None
                    sample = None
                    for answer_attempt in range(2):
                        if model_call_budget_exhausted():
                            target_reached = True
                            break
                        try:
                            answer_seed = stable_seed(
                                base_seed,
                                (
                                    f"finance_qa:{sample_index}:"
                                    f"{template.prompt_id}:answer:{answer_attempt}"
                                ),
                                offset,
                            )
                            model_calls += 1
                            sync_counters()
                            answer_raw = _call_generate_batch(
                                generate_batch,
                                [answer_input],
                                [answer_seed],
                                [answer_temperature],
                            )[0]
                            raw_answer_handle.write(
                                _json_line(
                                    {
                                        "record_key": key,
                                        "byte_offset": offset,
                                        "candidate_index": sample_index,
                                        "attempt": answer_attempt + 1,
                                        "bundle_id": row["bundle_id"],
                                        "generation_prompt_id": template.prompt_id,
                                        "raw_text": answer_raw,
                                    }
                                )
                            )
                            sample = parse_generated_sample(answer_raw)
                            sample = normalize_answer_sample(
                                sample,
                                question_candidate,
                                _all_source_paths(resolved),
                            )
                            _normalize_evidence_bboxes(
                                (sample.get("metadata") or {}).get("evidence") or [],
                                project_root,
                            )
                            validate_answer_sample(
                                sample,
                                question_candidate,
                                resolved,
                                project_root,
                            )
                            break
                        except Exception as error:
                            last_error = error
                            sample = None
                            if model_call_budget_exhausted():
                                set_stop_reason("max_model_calls")
                                target_reached = True
                                break
                    if sample is None:
                        if target_reached and last_error is None:
                            skip_error_record = True
                            continue
                        assert last_error is not None
                        raise last_error
                    assert sample is not None
                    copied_media = copy_training_images(
                        sample,
                        project_root=project_root,
                        output_dir=output_dir,
                    )
                    training = project_training_record(
                        sample,
                        resolved,
                        media_paths=copied_media,
                    )
                    raw_handle.write(
                        _json_line(
                            {
                                "record_key": key,
                                "byte_offset": offset,
                                "sample_index": sample_index,
                                "bundle_id": row["bundle_id"],
                                "generation_prompt_id": template.prompt_id,
                                "question_candidate": question_candidate,
                                "sample": sample,
                                "validation": {
                                    "question": "accepted",
                                    "answer": "accepted",
                                },
                            }
                        )
                    )
                    if training.get("images"):
                        multi_handle.write(_json_line(training))
                        counters["accepted_multi"] += 1
                    else:
                        text_handle.write(_json_line(training))
                        counters["accepted_text"] += 1
                    accepted_record_ids.add(str(training["record_id"]))
                    accepted_by_offset[offset] += 1
                    if (
                        target_accepted is not None
                        and len(accepted_record_ids) >= target_accepted
                    ):
                        set_stop_reason("target_accepted")
                        target_reached = True
                except Exception as error:
                    if not skip_error_record:
                        error_handle.write(
                            _json_line(
                                {
                                    "record_key": key,
                                    "byte_offset": offset,
                                    "sample_index": sample_index,
                                    "bundle_id": row.get("bundle_id"),
                                    "generation_prompt_id": template.prompt_id,
                                    "error_type": type(error).__name__,
                                    "error": str(error),
                                    "raw_question_text": question_raw,
                                    "raw_answer_text": answer_raw or None,
                                    "question_finish_reason": getattr(
                                        question_raw,
                                        "finish_reason",
                                        None,
                                    ),
                                    "answer_finish_reason": getattr(
                                        answer_raw,
                                        "finish_reason",
                                        None,
                                    ),
                                    "traceback": traceback.format_exc(),
                                }
                            )
                        )
                        counters["errors"] += 1
                if model_call_budget_exhausted() and stop_reason != "target_accepted":
                    set_stop_reason("max_model_calls")
                    target_reached = True
                for handle in (
                        raw_handle,
                        raw_question_handle,
                        question_handle,
                        raw_answer_handle,
                        multi_handle,
                        text_handle,
                        error_handle,
                ):
                    handle.flush()
                write_checkpoints(key)
                if heartbeat_callback is not None:
                    heartbeat_callback()
                if target_reached:
                    break
            return target_reached

        tasks: list[
            tuple[str, int, int, dict[str, Any], PromptTemplate, dict[str, Any]]
        ] = []
        target_reached = False
        for offset, row in iter_jsonl_shard(
            input_path,
            rank,
            world_size,
            max_records=max_records,
        ):
            if isinstance(row, JsonlRecordError):
                tasks.append(
                    (
                        f"{offset}:0",
                        offset,
                        0,
                        {"bundle_id": f"malformed:{offset}"},
                        PromptTemplate("INVALID", "INVALID", "", ""),
                        {"_input_error": row},
                    )
                )
                if len(tasks) == batch_size:
                    target_reached = process_batch(tasks)
                    tasks = []
                if target_reached:
                    break
                continue

            package_type = str(row.get("package_type") or "")
            if _skip_weak_debug_bundle(row, debug_mode=max_model_calls is not None):
                counters["skipped"] += 1
                continue
            financial = _financial_material(row, project_root)
            if _skip_nonfinancial_debug_bundle(
                row,
                financial=financial,
                debug_mode=max_model_calls is not None,
            ):
                counters["skipped"] += 1
                continue
            if (
                max_records_per_type is not None
                and selected_by_type[package_type] >= max_records_per_type
            ):
                continue
            selected_by_type[package_type] += 1
            requested = int(row.get("samples_requested") or 2)
            if financial:
                hard_prefixes = HARD_TEMPLATE_PREFIXES.get(row["package_type"], ())
                hard_count = sum(
                    1
                    for template in library.templates.values()
                    if template.prefix in hard_prefixes
                )
                template_count = requested * 3 if hard_count >= requested * 3 else requested
                templates = select_templates(
                    library.templates,
                    package_type=row["package_type"],
                    count=template_count,
                    usage=usage,
                )
            else:
                templates = [
                    PromptTemplate(
                        "SYN-TEXT-HARD",
                        "SYN",
                        "自包含金融困难题",
                        SYNTHETIC_TEXT_PROMPT,
                    )
                    for _ in range(requested)
                ]

            for sample_index, template in enumerate(templates):
                key = f"{offset}:{sample_index}"
                if key in completed:
                    counters["skipped"] += 1
                    continue
                seed = stable_seed(
                    base_seed,
                    f"finance_qa:{sample_index}",
                    offset,
                )
                try:
                    if financial:
                        prompt_input = build_prompt_input(
                            bundle=row,
                            template=template,
                            library=library,
                            processor=processor,
                            project_root=project_root,
                            generation_seed=seed,
                            question_min_images=question_min_images,
                            question_max_images=question_max_images,
                        )
                    else:
                        prompt_input = build_synthetic_text_input(
                            bundle=row,
                            library=library,
                            processor=processor,
                            generation_seed=seed,
                        )
                except Exception as error:
                    prompt_input = {"_input_error": error}
                tasks.append(
                    (key, offset, sample_index, row, template, prompt_input)
                )
                if len(tasks) == batch_size:
                    target_reached = process_batch(tasks)
                    tasks = []
                if target_reached:
                    break
            if target_reached:
                break

        if tasks and not target_reached:
            process_batch(tasks)
        if stop_reason is None:
            set_stop_reason("input_exhausted")
        write_checkpoints(None)
    sync_counters()
    return counters


def _merge_kind(
    output_dir: Path,
    *,
    kind: str,
    destination: str,
    world_size: int,
    key_getter: Callable[[dict[str, Any]], str],
) -> int:
    target = output_dir / destination
    temporary = target.with_suffix(f".tmp.{os.getpid()}")
    seen = set()
    count = 0
    with temporary.open("w", encoding="utf-8", newline="\n") as output:
        for rank in range(world_size):
            part = _part_path(output_dir, kind, rank)
            repair_jsonl_tail(part)
            if not part.exists():
                continue
            with part.open(encoding="utf-8") as handle:
                for line in handle:
                    if not line.strip():
                        continue
                    row = json.loads(line)
                    key = key_getter(row)
                    if key in seen:
                        continue
                    seen.add(key)
                    output.write(_json_line(row))
                    count += 1
    temporary.replace(target)
    return count


def _worker_state(output_dir: Path, rank: int) -> dict[str, Any]:
    success = output_dir / "_status" / f"rank_{rank:04d}.success"
    if success.exists():
        try:
            return json.loads(success.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
    checkpoint = _rank_checkpoint(output_dir, rank)
    return checkpoint.get("counters") or checkpoint


def merge_parts(output_dir: Path, *, world_size: int) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    raw_question_count = _merge_kind(
        output_dir,
        kind="raw_questions",
        destination="raw_question_generations.jsonl",
        world_size=world_size,
        key_getter=lambda row: str(row["record_key"]),
    )
    question_count = _merge_kind(
        output_dir,
        kind="questions",
        destination="question_candidates.jsonl",
        world_size=world_size,
        key_getter=lambda row: str(row["record_key"]),
    )
    raw_answer_count = _merge_kind(
        output_dir,
        kind="raw_answers",
        destination="raw_answer_generations.jsonl",
        world_size=world_size,
        key_getter=lambda row: f"{row['record_key']}:{row.get('attempt', 0)}",
    )
    raw_count = _merge_kind(
        output_dir,
        kind="raw",
        destination="raw_generations.jsonl",
        world_size=world_size,
        key_getter=lambda row: str(row["record_key"]),
    )
    multi_count = _merge_kind(
        output_dir,
        kind="multi",
        destination="finance_generated_multi.jsonl",
        world_size=world_size,
        key_getter=lambda row: str(row["record_id"]),
    )
    text_count = _merge_kind(
        output_dir,
        kind="text",
        destination="finance_generated_text.jsonl",
        world_size=world_size,
        key_getter=lambda row: str(row["record_id"]),
    )
    error_count = _merge_kind(
        output_dir,
        kind="errors",
        destination="errors.jsonl",
        world_size=world_size,
        key_getter=lambda row: str(row["record_key"]),
    )
    worker_states = [_worker_state(output_dir, rank) for rank in range(world_size)]
    model_calls = sum(int(state.get("model_calls") or 0) for state in worker_states)
    worker_stop_reasons = [
        str(state.get("stop_reason"))
        for state in worker_states
        if state.get("stop_reason")
    ]
    if "max_model_calls" in worker_stop_reasons:
        stop_reason = "max_model_calls"
    elif "target_accepted" in worker_stop_reasons:
        stop_reason = "target_accepted"
    else:
        stop_reason = "input_exhausted"
    summary = {
        "raw_question_generations": raw_question_count,
        "question_candidates": question_count,
        "raw_answer_generations": raw_answer_count,
        "raw_generations": raw_count,
        "accepted_multi": multi_count,
        "accepted_text": text_count,
        "accepted_total": multi_count + text_count,
        "errors": error_count,
        "total": multi_count + text_count + error_count,
        "model_calls": model_calls,
        "stop_reason": stop_reason,
    }
    (output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return summary


class VLLMGenerator:
    def __init__(
        self,
        *,
        model: Path,
        tensor_parallel_size: int,
        top_p: float,
        question_max_tokens: int,
        answer_max_tokens: int,
        max_model_len: int,
        max_num_seqs: int,
        gpu_memory_utilization: float,
        max_images_per_prompt: int,
        question_schema: dict[str, Any],
    ) -> None:
        os.environ["VLLM_WORKER_MULTIPROC_METHOD"] = "spawn"
        os.environ["WANDB_DISABLED"] = "true"
        validate_runtime_dependencies()
        from transformers import AutoProcessor
        from vllm import LLM, SamplingParams
        from vllm.sampling_params import StructuredOutputsParams

        self.processor = AutoProcessor.from_pretrained(str(model))
        self._sampling_params = SamplingParams
        self._structured_outputs_params = StructuredOutputsParams
        self._top_p = top_p
        self._question_max_tokens = question_max_tokens
        self._answer_max_tokens = answer_max_tokens
        self._question_schema = question_schema
        self._llm = LLM(
            model=str(model),
            tensor_parallel_size=tensor_parallel_size,
            dtype="auto",
            max_model_len=max_model_len,
            max_num_seqs=max_num_seqs,
            gpu_memory_utilization=gpu_memory_utilization,
            limit_mm_per_prompt={"image": max_images_per_prompt, "video": 0},
            mm_processor_cache_gb=0,
            generation_config="vllm",
        )

    def _build_sampling_params(
        self,
        inputs: Sequence[dict[str, Any]],
        seeds: Sequence[int],
        temperatures: Sequence[float],
    ) -> list[Any]:
        params = []
        for item, seed, temperature in zip(inputs, seeds, temperatures):
            stage = str(item.get("_stage") or "answer")
            kwargs: dict[str, Any] = {
                "n": 1,
                "temperature": temperature,
                "top_p": self._top_p,
                "max_tokens": (
                    self._question_max_tokens
                    if stage == "question"
                    else self._answer_max_tokens
                ),
                "seed": seed,
            }
            if stage == "question":
                schema = copy.deepcopy(self._question_schema)
                schema["required"] = [
                    field
                    for field in schema.get("required") or []
                    if field not in SCRIPT_MANAGED_QUESTION_FIELDS
                ]
                for field in SCRIPT_MANAGED_QUESTION_FIELDS:
                    (schema.get("properties") or {}).pop(field, None)
                schema.pop("not", None)
                schema["additionalProperties"] = False
                if (
                    (item.get("_resolved_bundle") or {}).get("package_type")
                    == "synthetic_text"
                ):
                    schema["properties"]["media_paths"]["minItems"] = 0
                    schema["properties"]["media_paths"]["maxItems"] = 0
                    schema["properties"]["chart_text_alignment"]["minItems"] = 0
                    schema["properties"]["hardness"]["properties"]["page_count"][
                        "minimum"
                    ] = 0
                kwargs["structured_outputs"] = self._structured_outputs_params(
                    json=schema
                )
            params.append(self._sampling_params(**kwargs))
        return params

    def generate_batch(
        self,
        inputs: Sequence[dict[str, Any]],
        seeds: Sequence[int],
        temperatures: Sequence[float] | None = None,
    ) -> list[str]:
        clean_inputs = [
            {
                key: value
                for key, value in item.items()
                if not key.startswith("_")
            }
            for item in inputs
        ]
        if temperatures is None:
            temperatures = [0.6 for _ in seeds]
        params = self._build_sampling_params(inputs, seeds, temperatures)
        outputs = self._llm.generate(
            clean_inputs,
            sampling_params=params,
            use_tqdm=False,
        )
        return [
            GeneratedText(
                output.outputs[0].text,
                finish_reason=output.outputs[0].finish_reason,
                stop_reason=output.outputs[0].stop_reason,
            )
            for output in outputs
        ]


def run_worker(args: argparse.Namespace) -> dict[str, int]:
    project_root = Path(args.root)
    input_path = Path(args.input)
    prompt_path = Path(args.prompts)
    output_dir = Path(args.output_dir)
    schema_root = prompt_path.parent.parent / "schemas"
    sample_schema_path = schema_root / "financial_multimodal_sample.schema.json"
    question_schema_path = schema_root / "financial_question_candidate.schema.json"
    config = {
        "model": str(Path(args.model)),
        "input": str(input_path),
        "prompts": str(prompt_path),
        "sample_schema": str(sample_schema_path),
        "question_schema": str(question_schema_path),
        "input_sha256": _sha256_file(input_path),
        "prompts_sha256": _sha256_file(prompt_path),
        "sample_schema_sha256": _sha256_file(sample_schema_path),
        "question_schema_sha256": _sha256_file(question_schema_path),
        "generator_sha256": _sha256_file(Path(__file__)),
        "world_size": args.world_size,
        "tensor_parallel_size": args.tensor_parallel_size,
        "question_temperature": args.question_temperature,
        "answer_temperature": args.answer_temperature,
        "top_p": args.top_p,
        "question_max_tokens": args.question_max_tokens,
        "answer_max_tokens": args.answer_max_tokens,
        "max_model_len": args.max_model_len,
        "max_num_seqs": args.max_num_seqs,
        "question_min_images": args.question_min_images,
        "question_max_images": args.question_max_images,
        "base_seed": args.seed,
        "target_accepted": args.target_accepted,
        "max_model_calls": args.max_model_calls,
    }
    ensure_run_config(output_dir, config)
    status_dir = output_dir / "_status"
    status_dir.mkdir(parents=True, exist_ok=True)
    success = status_dir / f"rank_{args.rank:04d}.success"
    failed = status_dir / f"rank_{args.rank:04d}.failed.json"
    heartbeat = status_dir / f"rank_{args.rank:04d}.heartbeat"
    success.unlink(missing_ok=True)
    failed.unlink(missing_ok=True)
    heartbeat.touch()
    try:
        if not input_path.is_file():
            raise FileNotFoundError(f"input does not exist: {input_path}")
        if not prompt_path.is_file():
            raise FileNotFoundError(f"prompt library does not exist: {prompt_path}")
        library = parse_prompt_library(prompt_path)
        generator = VLLMGenerator(
            model=Path(args.model),
            tensor_parallel_size=args.tensor_parallel_size,
            top_p=args.top_p,
            question_max_tokens=args.question_max_tokens,
            answer_max_tokens=args.answer_max_tokens,
            max_model_len=args.max_model_len,
            max_num_seqs=args.max_num_seqs,
            gpu_memory_utilization=args.gpu_memory_utilization,
            max_images_per_prompt=args.question_max_images,
            question_schema=json.loads(
                question_schema_path.read_text(encoding="utf-8")
            ),
        )
        counters = process_shard(
            input_path=input_path,
            project_root=project_root,
            output_dir=output_dir,
            rank=args.rank,
            world_size=args.world_size,
            library=library,
            processor=generator.processor,
            generate_batch=generator.generate_batch,
            batch_size=args.batch_size,
            base_seed=args.seed,
            max_records=args.max_records,
            max_records_per_type=args.max_records_per_type,
            target_accepted=args.target_accepted,
            heartbeat_callback=heartbeat.touch,
            question_temperature=args.question_temperature,
            answer_temperature=args.answer_temperature,
            max_model_calls=args.max_model_calls,
            question_min_images=args.question_min_images,
            question_max_images=args.question_max_images,
        )
        success.write_text(
            json.dumps(counters, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        return counters
    except Exception as error:
        failed.write_text(
            json.dumps(
                {
                    "rank": args.rank,
                    "error_type": type(error).__name__,
                    "error": str(error),
                    "traceback": traceback.format_exc(),
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        raise


def run_merge(args: argparse.Namespace) -> dict[str, Any]:
    output_dir = Path(args.output_dir)
    wait_for_workers(
        output_dir,
        world_size=args.world_size,
        timeout_seconds=args.wait_timeout,
        poll_seconds=args.poll_seconds,
        startup_timeout_seconds=args.startup_timeout,
        stale_timeout_seconds=args.stale_timeout,
    )
    return merge_parts(output_dir, world_size=args.world_size)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate hard financial multimodal QA records"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    worker = subparsers.add_parser("worker")
    worker.add_argument("--root", default=DEFAULT_ROOT)
    worker.add_argument("--model", default=DEFAULT_MODEL)
    worker.add_argument("--input", default=DEFAULT_INPUT)
    worker.add_argument("--prompts", default=DEFAULT_PROMPTS)
    worker.add_argument("--output-dir", default=DEFAULT_OUTPUT)
    worker.add_argument("--rank", type=int, required=True)
    worker.add_argument("--world-size", type=int, required=True)
    worker.add_argument("--tensor-parallel-size", type=int, default=8)
    worker.add_argument("--question-temperature", type=float, default=0.9)
    worker.add_argument("--answer-temperature", type=float, default=0.6)
    worker.add_argument("--top-p", type=float, default=0.95)
    worker.add_argument("--question-max-tokens", type=int, default=9216)
    worker.add_argument("--answer-max-tokens", type=int, default=16384)
    worker.add_argument("--max-model-len", type=int, default=65536)
    worker.add_argument("--max-num-seqs", type=int, default=4)
    worker.add_argument("--question-min-images", type=int, default=6)
    worker.add_argument("--question-max-images", type=int, default=10)
    worker.add_argument("--gpu-memory-utilization", type=float, default=0.9)
    worker.add_argument("--batch-size", type=int, default=4)
    worker.add_argument("--seed", type=int, default=42)
    worker.add_argument("--max-records", type=int)
    worker.add_argument("--max-records-per-type", type=int)
    worker.add_argument("--target-accepted", type=int)
    worker.add_argument("--max-model-calls", type=int)

    merge = subparsers.add_parser("merge")
    merge.add_argument("--output-dir", default=DEFAULT_OUTPUT)
    merge.add_argument("--world-size", type=int, required=True)
    merge.add_argument("--wait-timeout", type=float, default=0)
    merge.add_argument("--poll-seconds", type=float, default=10)
    merge.add_argument("--startup-timeout", type=float, default=600)
    merge.add_argument("--stale-timeout", type=float, default=7200)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    os.environ["WANDB_DISABLED"] = "true"
    args = build_parser().parse_args(argv)
    if args.command == "worker":
        run_worker(args)
    elif args.command == "merge":
        run_merge(args)
    else:
        raise ValueError(f"unsupported command: {args.command}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
