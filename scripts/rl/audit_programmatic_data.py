"""Classify programmatic RL records as clean, suspicious, or broken before GSPO."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any, Mapping

from .prepare_gspo_data import _FORMAT_TO_VERIFIER, RejectedRecord, prepare_record, validate_program_metadata


def audit_record(row: Mapping[str, Any], line_number: int) -> dict[str, Any] | None:
    verifier_type = _FORMAT_TO_VERIFIER.get(row.get("output_format"), "model_judge")
    if verifier_type == "model_judge":
        return None
    sample_id = str((row.get("_pass_at_k") or {}).get("result_index") or f"line:{line_number}")
    reasons: list[str] = []
    status = "clean"
    try:
        _, conflict = validate_program_metadata(row)
        if conflict:
            raise RejectedRecord(conflict)
        prepared = prepare_record(row, line_number)
    except RejectedRecord as exc:
        status = "broken"
        reasons.append(str(exc))
        prepared = None
    except Exception as exc:
        status = "broken"
        reasons.append(f"prepare_error:{exc}")
        prepared = None
    metadata = row.get("metadata") or {}
    pass_at_k = row.get("_pass_at_k") or {}
    has_independent_verifier = any(
        metadata.get(key) not in (None, "")
        for key in ("program", "official_answer", "gold_execution_answer", "gold_readable_answer")
    )
    if status == "clean" and int(pass_at_k.get("correct_count", -1)) == 0 and not has_independent_verifier:
        status = "suspicious"
        reasons.append("hard_negative_without_independent_verifier")
    if status == "clean" and metadata.get("program") and not any(
        metadata.get(key) not in (None, "") for key in ("official_answer", "gold_readable_answer")
    ):
        status = "suspicious"
        reasons.append("program_has_no_independent_reference")
    return {
        "line": line_number,
        "sample_id": sample_id,
        "status": status,
        "reasons": reasons,
        "source": row.get("source", ""),
        "verifier_type": verifier_type,
        "gold_numeric": (prepared or {}).get("gold_numeric", []),
    }


def audit_jsonl(input_path: str | Path, output_dir: str | Path) -> dict[str, Any]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    handles = {status: (output_dir / f"{status}.jsonl").open("w", encoding="utf-8") for status in ("clean", "suspicious", "broken")}
    counts: Counter[str] = Counter()
    source_counts: Counter[str] = Counter()
    try:
        with open(input_path, encoding="utf-8") as source:
            for line_number, line in enumerate(source, 1):
                if not line.strip():
                    continue
                row = json.loads(line)
                result = audit_record(row, line_number)
                if result is None:
                    continue
                counts[result["status"]] += 1
                source_counts[f"{result['status']}::{result['source']}"] += 1
                handles[result["status"]].write(json.dumps({"audit": result, "record": row}, ensure_ascii=False) + "\n")
    finally:
        for handle in handles.values():
            handle.close()
    report = {
        "input": str(input_path),
        "programmatic_total": sum(counts.values()),
        "counts": dict(counts),
        "counts_by_status_source": dict(source_counts),
        "outputs": {status: str(output_dir / f"{status}.jsonl") for status in handles},
    }
    (output_dir / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input")
    parser.add_argument("output_dir")
    args = parser.parse_args()
    print(json.dumps(audit_jsonl(args.input, args.output_dir), ensure_ascii=False))


if __name__ == "__main__":
    main()
