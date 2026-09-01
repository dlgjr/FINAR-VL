#!/usr/bin/env python3
"""Merge correct pass@k JSONL shards into SFT JSONL files."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Iterable


DEFAULT_CORRECT_INDICES = (0, 1, 2, 3)


def training_key(record: dict[str, Any]) -> str:
    payload = {
        "messages": record.get("messages"),
        "images": record.get("images") or [],
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def merge_correct_files(
    input_dir: Path,
    output_path: Path,
    *,
    correct_indices: Iterable[int] = DEFAULT_CORRECT_INDICES,
) -> dict[str, Any]:
    input_paths = [input_dir / f"correct_{index}.jsonl" for index in correct_indices]
    for path in input_paths:
        if not path.is_file():
            raise FileNotFoundError(f"missing input file: {path}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    seen: set[str] = set()
    report: dict[str, Any] = {
        "input_dir": str(input_dir),
        "output": str(output_path),
        "inputs": [str(path) for path in input_paths],
        "read": 0,
        "written": 0,
        "duplicates_removed": 0,
    }

    with output_path.open("w", encoding="utf-8", newline="\n") as output:
        for path in input_paths:
            with path.open("r", encoding="utf-8-sig") as source:
                for line_number, line in enumerate(source, start=1):
                    raw = line.strip()
                    if not raw:
                        continue
                    try:
                        record = json.loads(raw)
                    except json.JSONDecodeError as exc:
                        raise ValueError(f"invalid JSON in {path}:{line_number}: {exc}") from exc
                    report["read"] += 1
                    key = training_key(record)
                    if key in seen:
                        report["duplicates_removed"] += 1
                        continue
                    seen.add(key)
                    output.write(raw + "\n")
                    report["written"] += 1
    return report


def merge_default_outputs(project_root: Path) -> dict[str, Any]:
    data_root = project_root / "data"
    reports = {
        "train_text_sft": merge_correct_files(
            data_root / "train_text",
            data_root / "train_text" / "train_text_sft.jsonl",
        ),
        "train_multi_sft": merge_correct_files(
            data_root / "train_multi",
            data_root / "train_multi" / "train_multi_sft.jsonl",
        ),
    }
    return reports


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    args = parser.parse_args(argv)
    reports = merge_default_outputs(args.project_root.resolve())
    print(json.dumps(reports, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
