#!/usr/bin/env python3
"""统计统一后 train_multi SFT JSONL 的子任务分布，控制台表格输出。"""

from __future__ import annotations

import argparse
import collections
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    args = parser.parse_args()

    counts: collections.Counter[str] = collections.Counter()
    total = 0
    with args.input.open("r", encoding="utf-8-sig") as handle:
        for raw in handle:
            raw = raw.strip()
            if not raw:
                continue
            record = json.loads(raw)
            task = str(record.get("task") or "unknown")
            counts[task] += 1
            total += 1

    width = max(len("子任务"), max((len(task) for task in counts), default=0))
    print(f"{'子任务':<{width}}  {'样本数':>8}  {'占比':>8}")
    print("-" * (width + 22))
    for task, count in counts.most_common():
        ratio = count / total * 100 if total else 0.0
        print(f"{task:<{width}}  {count:>8}  {ratio:>7.2f}%")
    print("-" * (width + 22))
    print(f"{'合计':<{width}}  {total:>8}  {'100.00%':>8}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
