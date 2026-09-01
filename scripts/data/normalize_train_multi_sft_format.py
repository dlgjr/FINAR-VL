#!/usr/bin/env python3
"""统一 train_multi SFT JSONL 格式并原地重写。

每行输出字段顺序固定为 messages, source, split, images, task；split 固定为
"train"；删除其余全部字段。有效监督token 按仓库约定：最后一条消息为
assistant 且 content 去掉 <answer> 标签后非空。子任务标签为 task，为空时
依序回退 task_original -> target_subtask -> task_raw -> task_group -> source。
无法恢复的记录写入同目录 train_multi_sft_error.jsonl（原始记录）。
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path


OUTPUT_KEYS = ("messages", "source", "split", "images", "task")
ERROR_NAME = "train_multi_sft_error.jsonl"
DEFAULT_SPLIT = "train"
TASK_FALLBACK_KEYS = ("task_original", "target_subtask", "task_raw", "task_group", "source")


def strip_answer_tags(text: str) -> str:
    return text.replace("<answer>", "").replace("</answer>", "")


def normalize_record(record: dict) -> tuple[dict | None, str | None]:
    messages = record.get("messages")
    if not isinstance(messages, list) or not messages:
        return None, "missing_assistant"
    assistant = messages[-1]
    if not isinstance(assistant, dict) or assistant.get("role") != "assistant":
        return None, "missing_assistant"
    if not strip_answer_tags(str(assistant.get("content") or "")).strip():
        return None, "empty_supervision"

    task = record.get("task")
    if not task:
        task = next((record.get(key) for key in TASK_FALLBACK_KEYS if record.get(key)), None)
    if not task:
        return None, "empty_task"

    return {
        "messages": messages,
        "source": record.get("source"),
        "split": DEFAULT_SPLIT,
        "images": record.get("images"),
        "task": task,
    }, None


def verify_file(path: Path) -> tuple[int, list[str]]:
    issues: list[str] = []
    count = 0
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            raw = line.strip()
            if not raw:
                continue
            count += 1
            try:
                record = json.loads(raw)
            except json.JSONDecodeError:
                issues.append(f"line {line_no}: parse error")
                continue
            if tuple(record.keys()) != OUTPUT_KEYS:
                issues.append(f"line {line_no}: keys mismatch {tuple(record.keys())}")
                continue
            messages = record["messages"]
            if (
                not isinstance(messages, list)
                or len(messages) != 2
                or messages[0].get("role") != "user"
                or messages[1].get("role") != "assistant"
            ):
                issues.append(f"line {line_no}: messages shape invalid")
                continue
            if not strip_answer_tags(str(messages[1].get("content") or "")).strip():
                issues.append(f"line {line_no}: empty supervision")
                continue
            images = record["images"]
            if not isinstance(images, list) or not images:
                issues.append(f"line {line_no}: images empty")
                continue
            if not record.get("task") or not record.get("source"):
                issues.append(f"line {line_no}: task/source empty")
                continue
            if record["split"] != DEFAULT_SPLIT:
                issues.append(f"line {line_no}: split != {DEFAULT_SPLIT}")
    return count, issues


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    args = parser.parse_args()

    input_path = args.input.resolve()
    temp_path = input_path.with_name(input_path.name + ".tmp")
    error_path = input_path.with_name(ERROR_NAME)

    report: dict = {"input": str(input_path), "read": 0, "written": 0, "errors": 0, "error_kinds": {}}
    with input_path.open("r", encoding="utf-8-sig") as source, temp_path.open(
        "w", encoding="utf-8", newline="\n"
    ) as output:
        for raw in source:
            raw = raw.strip()
            if not raw:
                continue
            report["read"] += 1
            try:
                record = json.loads(raw)
            except json.JSONDecodeError:
                report["errors"] += 1
                report["error_kinds"]["parse_error"] = report["error_kinds"].get("parse_error", 0) + 1
                continue
            converted, issue = normalize_record(record)
            if issue is not None:
                report["errors"] += 1
                report["error_kinds"][issue] = report["error_kinds"].get(issue, 0) + 1
                continue
            output.write(
                json.dumps({key: converted[key] for key in OUTPUT_KEYS}, ensure_ascii=False, separators=(",", ":"))
                + "\n"
            )
            report["written"] += 1

    verified, issues = verify_file(temp_path)
    report["verified"] = verified
    if issues:
        print("\n".join(issues[:20]))
        temp_path.unlink()
        return 1

    if report["errors"]:
        with error_path.open("w", encoding="utf-8", newline="\n") as error_handle:
            with input_path.open("r", encoding="utf-8-sig") as source:
                for raw in source:
                    raw = raw.strip()
                    if not raw:
                        continue
                    try:
                        record = json.loads(raw)
                    except json.JSONDecodeError:
                        error_handle.write(raw + "\n")
                        continue
                    _, issue = normalize_record(record)
                    if issue is not None:
                        error_handle.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")
    else:
        error_path.unlink(missing_ok=True)

    os.replace(temp_path, input_path)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
