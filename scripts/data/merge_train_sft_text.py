#!/usr/bin/env python3
"""Merge four train_text JSONL files into one unified SFT JSONL file.

Every output row uses the same column order:
messages, source, split, task, _pass_at_k, task_original, task_group,
output_format, task_needs_review, task_normalization_version.

Rows with an empty subtask label or empty supervised tokens (assistant
content after removing <answer> tags) are moved to merge_error.jsonl.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


OUTPUT_NAME = "train_sft_text_final.jsonl"
ERROR_NAME = "merge_error.jsonl"
TASK_NORMALIZATION_VERSION = "text_task_taxonomy_v3_semantic_merge"
OUTPUT_COLUMNS = (
    "messages",
    "source",
    "split",
    "task",
    "_pass_at_k",
    "task_original",
    "task_group",
    "output_format",
    "task_needs_review",
    "task_normalization_version",
)
DEFAULT_TASK_TAXONOMY = {
    "long_context_citation_grounded_qa": ("document_qa_and_retrieval", "free_text"),
    "statistics_comparison_ranking": ("table_reasoning", "free_text"),
    "multi_step_numerical_reasoning": ("numerical_reasoning", "number_or_free_text"),
    "industry_trend_inference": ("financial_reasoning", "free_text"),
}
FALLBACK_TAXONOMY = ("other", "free_text")

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INPUTS = (
    PROJECT_ROOT / "data" / "train_text" / "train_text_sft_supplement_final_5000.jsonl",
    PROJECT_ROOT / "data" / "train_text" / "train_text_sft_official_manual_v2.jsonl",
    PROJECT_ROOT
    / "data"
    / "train_text"
    / "train_text_123_benchmark_aligned_expanded_3000_cfinbench.jsonl",
    PROJECT_ROOT / "data" / "train_text" / "train_sft_text_v1.jsonl",
)
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "data" / "train_text"


def strip_answer_tags(text: str) -> str:
    return text.replace("<answer>", "").replace("</answer>", "")


def build_task_taxonomy(v1_path: Path) -> dict[str, tuple[str, str]]:
    taxonomy: dict[str, tuple[str, str]] = {}
    with v1_path.open("r", encoding="utf-8-sig") as handle:
        for line in handle:
            raw = line.strip()
            if not raw:
                continue
            record = json.loads(raw)
            task = record.get("task")
            task_group = record.get("task_group")
            output_format = record.get("output_format")
            if task and task_group and output_format and task not in taxonomy:
                taxonomy[task] = (task_group, output_format)
    return taxonomy


def convert_record(
    record: dict[str, Any],
    index: int,
    taxonomy: dict[str, tuple[str, str]],
) -> tuple[dict[str, Any] | None, str | None]:
    task = record.get("task")
    if not task:
        return None, "empty_task"

    messages = record.get("messages")
    if not isinstance(messages, list) or not messages:
        return None, "missing_assistant"
    assistant = messages[-1]
    if not isinstance(assistant, dict) or assistant.get("role") != "assistant":
        return None, "missing_assistant"
    if not strip_answer_tags(str(assistant.get("content") or "")).strip():
        return None, "empty_supervision"

    converted_messages = []
    for message in messages:
        item = dict(message)
        if item.get("role") == "assistant":
            item["content"] = strip_answer_tags(str(item.get("content") or ""))
        converted_messages.append(item)

    task_group = record.get("task_group")
    output_format = record.get("output_format")
    if not task_group or not output_format:
        fallback = (
            taxonomy.get(task)
            or DEFAULT_TASK_TAXONOMY.get(task)
            or FALLBACK_TAXONOMY
        )
        if not task_group:
            task_group = fallback[0]
        if not output_format:
            output_format = fallback[1]

    target = {
        "messages": converted_messages,
        "source": record.get("source"),
        "split": record.get("split"),
        "task": task,
        "_pass_at_k": {
            "k": 8,
            "correct_count": 0,
            "dataset": "train_text",
            "result_index": f"train_text:{index}",
        },
        "task_original": record.get("task_original") or task,
        "task_group": task_group,
        "output_format": output_format,
        "task_needs_review": False,
        "task_normalization_version": TASK_NORMALIZATION_VERSION,
    }
    return target, None


def merge_train_text_files(
    inputs: tuple[Path, ...],
    output_dir: Path,
) -> dict[str, Any]:
    if len(inputs) != 4:
        raise ValueError("exactly 4 input files are required")
    taxonomy = build_task_taxonomy(inputs[3])

    output_path = output_dir / OUTPUT_NAME
    error_path = output_dir / ERROR_NAME
    output_dir.mkdir(parents=True, exist_ok=True)

    report: dict[str, Any] = {
        "output": str(output_path),
        "errors": str(error_path),
        "files": {},
        "written": 0,
        "errors_total": 0,
        "error_kinds": {},
    }
    index = 0
    with output_path.open("w", encoding="utf-8", newline="\n") as output, error_path.open(
        "w", encoding="utf-8", newline="\n"
    ) as error:
        for path in inputs:
            file_report = {"read": 0, "written": 0, "errors": 0}
            with path.open("r", encoding="utf-8-sig") as source:
                for line in source:
                    raw = line.strip()
                    if not raw:
                        continue
                    file_report["read"] += 1
                    try:
                        record = json.loads(raw)
                    except json.JSONDecodeError:
                        error.write(raw + "\n")
                        file_report["errors"] += 1
                        report["errors_total"] += 1
                        report["error_kinds"]["parse_error"] = (
                            report["error_kinds"].get("parse_error", 0) + 1
                        )
                        continue
                    converted, issue = convert_record(record, index, taxonomy)
                    if issue is not None:
                        error.write(
                            json.dumps(record, ensure_ascii=False, separators=(",", ":"))
                            + "\n"
                        )
                        file_report["errors"] += 1
                        report["errors_total"] += 1
                        report["error_kinds"][issue] = (
                            report["error_kinds"].get(issue, 0) + 1
                        )
                        continue
                    output.write(
                        json.dumps(
                            {column: converted[column] for column in OUTPUT_COLUMNS},
                            ensure_ascii=False,
                            separators=(",", ":"),
                        )
                        + "\n"
                    )
                    file_report["written"] += 1
                    report["written"] += 1
                    index += 1
            report["files"][str(path)] = file_report
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--inputs",
        nargs="+",
        type=Path,
        default=list(DEFAULT_INPUTS),
        help="4 input JSONL files; the 4th must be train_sft_text_v1.jsonl",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="directory for train_sft_text_final.jsonl and merge_error.jsonl",
    )
    args = parser.parse_args(argv)
    if len(args.inputs) != 4:
        parser.error("exactly 4 input files are required")
    report = merge_train_text_files(tuple(args.inputs), args.output_dir)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
