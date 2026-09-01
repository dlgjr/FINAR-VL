#!/usr/bin/env python3
"""Unify train_text SFT JSONL columns for strict dataset loaders.

Every output row uses the same column order:
messages, source, split, task, _pass_at_k.
Missing source/task become null, missing split becomes "train", and
_pass_at_k is normalized to -1 (meaning none) so its type is uniform.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


COLUMNS = ("messages", "source", "split", "task", "_pass_at_k")
DEFAULT_SPLIT = "train"
NO_PASS_AT_K = -1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    written = 0
    filled = 0
    with args.input.open("r", encoding="utf-8-sig") as source, args.output.open(
        "w", encoding="utf-8", newline="\n"
    ) as output:
        for line in source:
            raw = line.strip()
            if not raw:
                continue
            record = json.loads(raw)
            if "source" not in record or "task" not in record:
                filled += 1
            record.setdefault("source", None)
            record.setdefault("task", None)
            record.setdefault("split", DEFAULT_SPLIT)
            record["_pass_at_k"] = NO_PASS_AT_K
            output.write(
                json.dumps(
                    {column: record[column] for column in COLUMNS},
                    ensure_ascii=False,
                    separators=(",", ":"),
                )
                + "\n"
            )
            written += 1

    report = {
        "input": str(args.input),
        "output": str(args.output),
        "written": written,
        "rows_with_missing_source_or_task": filled,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
