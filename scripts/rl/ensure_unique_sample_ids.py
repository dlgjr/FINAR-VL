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


def _merge_shape(shape: Any, value: Any) -> Any:
    if isinstance(value, dict):
        shape = shape if isinstance(shape, dict) else {}
        for key, item in value.items():
            shape[key] = _merge_shape(shape.get(key), item)
        return shape
    if isinstance(value, list):
        shape = shape if isinstance(shape, list) else [None]
        for item in value:
            shape[0] = _merge_shape(shape[0], item)
        return shape
    return shape


def _normalize_shape(value: Any, shape: Any) -> Any:
    if isinstance(shape, dict):
        source = value if isinstance(value, dict) else {}
        return {key: _normalize_shape(source.get(key), child) for key, child in shape.items()}
    if isinstance(shape, list) and isinstance(value, list):
        return [_normalize_shape(item, shape[0]) for item in value]
    return value


def _harmonize_mopd_sources(output_path: Path) -> None:
    if output_path.name not in {"reasoning.unique_source.jsonl", "generation.unique_source.jsonl"}:
        return
    paths = [output_path.parent / "reasoning.unique_source.jsonl", output_path.parent / "generation.unique_source.jsonl"]
    if not all(path.is_file() for path in paths):
        return

    shape: Any = None
    for path in paths:
        with path.open(encoding="utf-8") as source:
            for line in source:
                if line.strip():
                    shape = _merge_shape(shape, json.loads(line))

    for path in paths:
        temp = path.with_suffix(path.suffix + ".tmp")
        with path.open(encoding="utf-8") as source, temp.open("w", encoding="utf-8") as target:
            for line in source:
                if line.strip():
                    target.write(json.dumps(_normalize_shape(json.loads(line), shape), ensure_ascii=False) + "\n")
        temp.replace(path)
    print("[GSPO_DATA] harmonized MOPD source schemas")


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

    _harmonize_mopd_sources(output_path)
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
