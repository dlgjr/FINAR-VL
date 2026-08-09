#!/usr/bin/env python3
"""从 train_multi SFT JSONL 中随机筛选子任务 long 样本。

随机保留 keep 条 long 样本在原文件（保持相对顺序），其余 long 样本写入
同目录 train_multi_reasoning_sheet_rl.jsonl（保持相对顺序）。
"""

from __future__ import annotations

import argparse
import json
import os
import random
from pathlib import Path


RL_NAME = "train_multi_reasoning_sheet_rl.jsonl"
TARGET_TASK = "long"
DEFAULT_KEEP = 800
DEFAULT_SEED = 42


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--keep", type=int, default=DEFAULT_KEEP)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    args = parser.parse_args()

    input_path = args.input.resolve()
    temp_path = input_path.with_name(input_path.name + ".tmp")
    rl_path = input_path.with_name(RL_NAME)

    raw_lines: list[str] = []
    long_indexes: list[int] = []
    with input_path.open("r", encoding="utf-8") as handle:
        for raw in handle:
            raw = raw.strip()
            if not raw:
                continue
            record = json.loads(raw)
            if str(record.get("task") or "") == TARGET_TASK:
                long_indexes.append(len(raw_lines))
            raw_lines.append(raw)

    if len(long_indexes) <= args.keep:
        raise SystemExit(f"long 样本数 {len(long_indexes)} 不大于保留数 {args.keep}")

    keep_indexes = set(random.Random(args.seed).sample(long_indexes, args.keep))
    long_set = set(long_indexes)
    kept = 0
    moved = 0
    with temp_path.open("w", encoding="utf-8", newline="\n") as output, rl_path.open(
        "w", encoding="utf-8", newline="\n"
    ) as rl_output:
        for index, raw in enumerate(raw_lines):
            if index in keep_indexes:
                output.write(raw + "\n")
                kept += 1
            elif index in long_set:
                rl_output.write(raw + "\n")
                moved += 1
            else:
                output.write(raw + "\n")

    os.replace(temp_path, input_path)
    print(
        json.dumps(
            {
                "input": str(input_path),
                "rl_output": str(rl_path),
                "task": TARGET_TASK,
                "total_long": len(long_indexes),
                "kept": kept,
                "moved_to_rl": moved,
                "seed": args.seed,
                "output_total": len(raw_lines) - moved,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
