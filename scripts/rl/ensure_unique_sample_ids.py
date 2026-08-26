#!/usr/bin/env python3
"""Rewrite a GSPO JSONL so every record has a unique sample_id."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping


def _base_sample_id(row: Mapping[str, Any], line_number: int) -> str:
    routed_line = (row.get("_reward_routing") or {}).get("source_line")
    return str(
        row.get("sample_id")
        or row.get("id")
        or (row.get("_pass_at_k") or {}).get("result_index")
        or f"line:{routed_line or line_number}"
    )


def rewrite_unique_ids(input_path: str | Path, output_path: str | Path) -> tuple[int, int]:
    input_path = Path(input_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    seen: set[str] = set()
    total = 0
    renamed = 0

    with input_path.open(encoding="utf-8") as source, output_path.open("w", encoding="utf-8") as target:
        for line_number, line in enumerate(source, 1):
            if not line.strip():
                continue
            row = json.loads(line)
            total += 1

            base_id = _base_sample_id(row, line_number)
            sample_id = base_id
            if sample_id in seen:
                sample_id = f"{base_id}:dup:{line_number}"
                suffix = 2
                while sample_id in seen:
                    sample_id = f"{base_id}:dup:{line_number}:{suffix}"
                    suffix += 1
                row["_original_sample_id"] = base_id
                renamed += 1

            row["sample_id"] = sample_id
            seen.add(sample_id)
            target.write(json.dumps(row, ensure_ascii=False) + "\n")

    return total, renamed


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input")
    parser.add_argument("output")
    args = parser.parse_args()
    total, renamed = rewrite_unique_ids(args.input, args.output)
    print(f"[GSPO_DATA] unique sample_id rewrite: total={total}, renamed_duplicates={renamed}")


if __name__ == "__main__":
    main()
