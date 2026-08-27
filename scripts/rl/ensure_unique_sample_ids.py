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


def _compact_mopd_row(row: Mapping[str, Any], line_number: int) -> dict[str, Any] | None:
    from .prepare_gspo_data import RejectedRecord, prepare_record

    try:
        prepared = prepare_record(row, line_number)
    except RejectedRecord:
        return None
    return {
        "messages": row.get("messages") or [],
        "images": row.get("images") or [],
        "solution": prepared["solution"],
        "sample_id": prepared["sample_id"],
        "reward_type": "judge",
        "verifier_type": "model_judge",
    }


def rewrite_unique_ids(input_path: str | Path, output_path: str | Path) -> tuple[int, int]:
    input_path = Path(input_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    mopd_source = output_path.name in {"reasoning.unique_source.jsonl", "generation.unique_source.jsonl"}

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
                renamed += 1

            row["sample_id"] = sample_id
            seen.add(sample_id)
            if mopd_source:
                row = _compact_mopd_row(row, line_number)
                if row is None:
                    continue
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
