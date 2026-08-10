"""Derive evidence-backed entity disambiguation rows from financial announcements."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

import orjson

from scripts.data.select_benchmark_aligned_tasks import (
    _benchmark_hashes,
    _content_hash,
    assess_row,
    review_alignment,
)


STOCK_PATTERNS = (
    re.compile(r"证券代码\s*[:：]?\s*(\d{6})\s+证券简称\s*[:：]?\s*([^\s<]+)"),
    re.compile(r"证券简称\s*[:：]?\s*([^\s<]+)\s+证券代码\s*[:：]?\s*(\d{6})"),
)
COMPANY_PATTERN = re.compile(
    r"(?<![\u4e00-\u9fff])([\u4e00-\u9fffA-Za-z0-9*ＳＴST]{2,32}(?:股份有限公司|有限责任公司|有限公司))"
)
PERSON_PATTERN = re.compile(
    r"(?:(?:控股股东|股东|自然人)\s*)?([\u4e00-\u9fff]{2,4})(?:先生|女士)"
)


def _question(target: str, entity_type: str, context: str, answer: str) -> dict[str, Any]:
    return {
        "messages": [
            {
                "role": "user",
                "content": (
                    f"你是一个实体消岐助手。请指出以下内容中提及的“{target}”是不是{entity_type}。"
                    f"请给出正确选项。\n{context.strip()}\nA. 是\nB. 不是\nC. 不确定"
                ),
            },
            {"role": "assistant", "content": answer},
        ],
        "split": "derived",
        "task": "entity_extraction_classification",
        "task_original": "announcement_structural_entity_evidence",
        "target_capability": "entity_extraction_classification",
    }


def _context_line(text: str, target: str, limit: int = 1000) -> str:
    lines = [line.strip() for line in text.splitlines() if target in line and line.strip()]
    context = lines[0] if lines else text.strip()
    return context[:limit]


def derive_entity_rows(row: dict[str, Any], line_number: int) -> list[dict[str, Any]]:
    questions = [
        str(message.get("content", ""))
        for message in row.get("messages", [])
        if message.get("role") == "user"
    ]
    if len(questions) != 1:
        return []
    text = questions[0]
    derived: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()

    for pattern_index, pattern in enumerate(STOCK_PATTERNS):
        match = pattern.search(text)
        if not match:
            continue
        code, short_name = match.groups() if pattern_index == 0 else (match.group(2), match.group(1))
        source_context = _context_line(text, short_name)
        if code in source_context:
            context = f"证券简称：{short_name.strip()}（证券代码：{code}）发布公告。"
            derived.append(_question(short_name.strip(), "股票", context, "A"))
            seen.add((short_name.strip(), "股票"))
        break

    for match in COMPANY_PATTERN.finditer(text):
        company = match.group(1).strip()
        key = (company, "公司")
        if key in seen:
            continue
        derived.append(_question(company, "公司", _context_line(text, company), "A"))
        seen.add(key)
        break

    for match in PERSON_PATTERN.finditer(text):
        person = match.group(1).strip()
        key = (person, "公司")
        if key in seen or person in {"公司", "股东", "控股股东"}:
            continue
        context = _context_line(text, person)
        if f"{person}先生" not in context and f"{person}女士" not in context:
            continue
        derived.append(_question(person, "公司", context, "B"))
        seen.add(key)
        break

    for item in derived:
        item["source"] = f"derived_entity:{row.get('source', 'announcement')}"
        item["derived_from"] = {
            "source": str(row.get("source", "")),
            "line_number": line_number,
            "evidence_rule": "explicit_stock_code_company_suffix_or_person_title",
        }
    return derived


def generate(input_path: Path, output_path: Path, count: int, benchmark_path: Path) -> int:
    benchmark_hashes = _benchmark_hashes(benchmark_path)
    seen: set[str] = set()
    written = 0
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with input_path.open("rb") as input_handle, output_path.open(
        "w", encoding="utf-8", buffering=1
    ) as output_handle:
        for line_number, line in enumerate(input_handle, 1):
            if not line.strip():
                continue
            row = orjson.loads(line)
            for derived in derive_entity_rows(row, line_number):
                content_hash = _content_hash(derived)
                if content_hash in seen or content_hash in benchmark_hashes:
                    continue
                decision = assess_row(derived, "entity_extraction_classification")
                reviewed, _ = review_alignment(
                    derived,
                    "entity_extraction_classification",
                    decision,
                )
                if not decision.accepted or not reviewed:
                    continue
                output_handle.write(json.dumps(derived, ensure_ascii=False) + "\n")
                seen.add(content_hash)
                written += 1
                if written >= count:
                    return written
    return written


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=Path("data/train_text_sft.jsonl"))
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/external_multimodal/derived_entity_candidates.jsonl"),
    )
    parser.add_argument("--count", type=int, default=2000)
    parser.add_argument(
        "--benchmark",
        type=Path,
        default=Path("data/benchmark/my_benchmark/all.jsonl"),
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    written = generate(args.input, args.output, args.count, args.benchmark)
    print(json.dumps({"rows": written}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
