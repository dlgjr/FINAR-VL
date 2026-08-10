"""Fail-closed preflight for the derived RL JSONL."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
import argparse


def validate(path: str | Path, *, expected_count: int = 6624, root: str | Path | None = None) -> dict[str, Any]:
    seen: set[str] = set()
    errors: list[dict[str, Any]] = []
    count = 0
    for line_number, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        count += 1
        row = json.loads(line)
        sample_id = str(row.get("sample_id", ""))
        if not sample_id or sample_id in seen:
            errors.append({"line": line_number, "error": "missing_or_duplicate_sample_id", "sample_id": sample_id})
        seen.add(sample_id)
        if any(message.get("role") == "assistant" for message in row.get("messages", [])):
            errors.append({"line": line_number, "error": "assistant_leakage", "sample_id": sample_id})
        if row.get("verifier_type") == "model_judge" and not row.get("gold_claims"):
            errors.append({"line": line_number, "error": "missing_gold_claims", "sample_id": sample_id})
        if row.get("verifier_type") != "model_judge" and not row.get("gold_atoms"):
            errors.append({"line": line_number, "error": "missing_gold_atoms", "sample_id": sample_id})
        if not row.get("messages"):
            errors.append({"line": line_number, "error": "missing_messages", "sample_id": sample_id})
        if root is not None:
            for image in row.get("images", []) or []:
                image_path = Path(image)
                if not image_path.is_absolute():
                    image_path = Path(root) / image_path
                if not image_path.is_file():
                    errors.append({"line": line_number, "error": "missing_image", "sample_id": sample_id, "image": str(image_path)})
    count_matches = expected_count <= 0 or count == expected_count
    report = {"count": count, "expected_count": expected_count, "unique_sample_ids": len(seen), "errors": errors, "valid": count_matches and not errors}
    if not report["valid"]:
        raise ValueError(json.dumps(report, ensure_ascii=False))
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("path")
    parser.add_argument("--expected-count", type=int, default=6624)
    parser.add_argument("--root")
    args = parser.parse_args()
    print(json.dumps(validate(args.path, expected_count=args.expected_count, root=args.root), ensure_ascii=False))


if __name__ == "__main__":
    main()
