#!/usr/bin/env python3
"""Build the 24-task reasoning benchmark from the current 240-row benchmark.

The only semantic change is replacing the 10 open-ended
``financial_visual_description`` items with deterministic
``financial_visual_data_reasoning`` items using the same images.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
from collections import Counter
from pathlib import Path
from typing import Any


TARGET_TASK = "financial_visual_data_reasoning"
SOURCE_TASK = "financial_visual_description"

# Questions are derived from facts already present in the original MME-Finance
# reference captions, but force image reading plus a deterministic calculation
# or count. Answers are intentionally numeric so the existing programmatic judge
# can score them without an LLM-as-judge.
_REPLACEMENTS: dict[str, tuple[str, str]] = {
    "MME-Finance/Image Caption/763": (
        "根据图中列出的四只超跌绩优股及其年内跌幅，计算四者年内跌幅的简单平均值。"
        "仅输出百分比，保留两位小数。",
        "38.44%",
    ),
    "MME-Finance/Image Caption/319": (
        "根据图中数据，计算田中精机与创新新材涨幅的差值。"
        "仅输出数值，单位为个百分点，保留两位小数。",
        "9.91",
    ),
    "MME-Finance/Image Caption/0": (
        "根据图中2024年3月13日苹果公司的最高价和最低价，计算当日日内价差。"
        "仅输出数值，保留三位小数。",
        "2.425",
    ),
    "MME-Finance/Image Caption/565": (
        "根据图中的上涨股票数和下跌股票数，计算净上涨家数（上涨数减下跌数）。"
        "仅输出整数。",
        "1962",
    ),
    "MME-Finance/Image Caption/140": (
        "根据图中的BOLL上轨和下轨最新值，计算BOLL带宽（上轨减下轨）。"
        "仅输出数值，保留三位小数。",
        "15.886",
    ),
    "MME-Finance/Image Caption/1013": (
        "根据图中深圳成指的开盘价和当前价，计算当前价较开盘价低多少点。"
        "仅输出数值，保留两位小数。",
        "9.41",
    ),
    "MME-Finance/Image Caption/775": (
        "根据图中文字，统计被明确点名为“大涨”或“跟涨”的一体成型电感概念股数量。"
        "仅输出整数。",
        "5",
    ),
    "MME-Finance/Image Caption/333": (
        "根据图中股票数据表的表头，统计明确列出的字段数量。"
        "仅输出整数。",
        "5",
    ),
    "MME-Finance/Image Caption/1": (
        "根据图中2024年6月25日苹果公司的最高价和最低价，计算当日日内价差。"
        "仅输出数值，保留两位小数。",
        "2.77",
    ),
    "MME-Finance/Image Caption/579": (
        "根据图中四个中国股指的当日涨跌幅，计算最大涨幅与最小涨幅之间的差值。"
        "仅输出数值，单位为个百分点，保留两位小数。",
        "0.96",
    ),
}


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_number}: invalid JSON: {exc}") from exc
            if not isinstance(row, dict):
                raise TypeError(f"{path}:{line_number}: row must be a JSON object")
            rows.append(row)
    return rows


def _validate_shape(rows: list[dict[str, Any]], *, stage: str) -> Counter[str]:
    if len(rows) != 240:
        raise ValueError(f"{stage}: expected 240 rows, got {len(rows)}")
    counts = Counter(str(row.get("task") or "") for row in rows)
    if len(counts) != 24 or set(counts.values()) != {10}:
        raise ValueError(f"{stage}: expected 24 tasks x 10 rows, got {dict(counts)}")
    for index, row in enumerate(rows, 1):
        messages = row.get("messages") or []
        if not messages or messages[0].get("role") != "user" or messages[-1].get("role") != "assistant":
            raise ValueError(f"{stage}: row {index} has invalid messages")
        prompt = str(messages[0].get("content") or "")
        images = list(row.get("images") or [])
        if prompt.count("<image>") != len(images):
            raise ValueError(
                f"{stage}: row {index} image marker mismatch: "
                f"{prompt.count('<image>')} markers vs {len(images)} images"
            )
    return counts


def transform(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    input_counts = _validate_shape(rows, stage="input")
    if input_counts.get(SOURCE_TASK) != 10:
        raise ValueError(
            f"input: expected exactly 10 {SOURCE_TASK!r} rows, "
            f"got {input_counts.get(SOURCE_TASK, 0)}"
        )

    seen: set[str] = set()
    output: list[dict[str, Any]] = []
    for row in rows:
        if str(row.get("task") or "") != SOURCE_TASK:
            output.append(row)
            continue

        source = str(row.get("source") or "")
        replacement = _REPLACEMENTS.get(source)
        if replacement is None:
            raise ValueError(f"unexpected {SOURCE_TASK} source: {source!r}")
        if source in seen:
            raise ValueError(f"duplicate {SOURCE_TASK} source: {source!r}")
        seen.add(source)

        question, answer = replacement
        updated = copy.deepcopy(row)
        updated["messages"] = [
            {"role": "user", "content": "<image>" + question},
            {"role": "assistant", "content": answer},
        ]
        updated["source"] = f"derived/{source}/visual_data_reasoning"
        updated["task"] = TARGET_TASK
        output.append(updated)

    missing = sorted(set(_REPLACEMENTS) - seen)
    if missing:
        raise ValueError(f"missing expected visual-description sources: {missing}")

    output_counts = _validate_shape(output, stage="output")
    if SOURCE_TASK in output_counts:
        raise ValueError(f"output still contains {SOURCE_TASK}")
    if output_counts.get(TARGET_TASK) != 10:
        raise ValueError(f"output: expected 10 {TARGET_TASK} rows")
    return output


def _write_jsonl_atomic(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp.{os.getpid()}")
    try:
        with temporary.open("w", encoding="utf-8") as handle:
            for row in rows:
                handle.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    rows = transform(_load_jsonl(args.input))
    _write_jsonl_atomic(args.output, rows)
    counts = Counter(str(row["task"]) for row in rows)
    print(
        f"wrote {args.output}: rows={len(rows)} tasks={len(counts)} "
        f"{TARGET_TASK}={counts[TARGET_TASK]}"
    )


if __name__ == "__main__":
    main()
