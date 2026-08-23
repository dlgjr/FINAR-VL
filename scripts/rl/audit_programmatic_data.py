"""Audit programmatic RL records for objective verifier conflicts before GSPO."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any, Mapping

from .prepare_gspo_data import _FORMAT_TO_VERIFIER, RejectedRecord, prepare_record


def _has_independent_reference(row: Mapping[str, Any], verifier_type: str) -> bool:
    metadata = row.get("metadata") or {}
    if verifier_type == "page_numbers":
        return bool(metadata.get("evidence_pages"))
    if verifier_type in {"numeric", "numeric_final", "composite_numeric"}:
        return any(
            metadata.get(key) not in (None, "")
            for key in ("gold_readable_answer", "official_answer", "official_program", "original_program")
        )
    return False


def audit_record(row: Mapping[str, Any], line_number: int) -> dict[str, Any] | None:
    verifier_type = str(row.get("verifier_type") or row.get("reward_subtype") or _FORMAT_TO_VERIFIER.get(row.get("output_format"), "model_judge"))
    if verifier_type == "model_judge":
        return None
    sample_id = str((row.get("_pass_at_k") or {}).get("result_index") or f"line:{line_number}")
    reasons: list[str] = []
    status = "clean"
    try:
        prepared = prepare_record(row, line_number)
        if "program_conflict:" in str(prepared.get("gold_source") or ""):
            status = "suspicious"
            reasons.append(str(prepared["gold_source"]).rsplit("program_conflict:", 1)[1])
    except RejectedRecord as exc:
        status = "broken"
        reasons.append(str(exc))
        prepared = None
    except Exception as exc:
        status = "broken"
        reasons.append(f"prepare_error:{exc}")
        prepared = None
    return {
        "line": line_number,
        "sample_id": str((prepared or {}).get("sample_id") or sample_id),
        "status": status,
        "reasons": reasons,
        "source": row.get("source", ""),
        "verifier_type": verifier_type,
        "has_independent_reference": _has_independent_reference(row, verifier_type),
        "gold_source": (prepared or {}).get("gold_source", ""),
        "gold_verification": (prepared or {}).get("gold_verification", {}),
        "gold_numeric": (prepared or {}).get("gold_numeric", []),
        "gold_atoms": (prepared or {}).get("gold_atoms", []),
    }


def audit_jsonl(input_path: str | Path, output_dir: str | Path) -> dict[str, Any]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    handles = {status: (output_dir / f"{status}.jsonl").open("w", encoding="utf-8") for status in ("clean", "suspicious", "broken")}
    counts: Counter[str] = Counter()
    source_counts: Counter[str] = Counter()
    reason_counts: Counter[str] = Counter()
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
                for reason in result["reasons"]:
                    reason_counts[reason] += 1
                handles[result["status"]].write(json.dumps({"audit": result, "record": row}, ensure_ascii=False) + "\n")
    finally:
        for handle in handles.values():
            handle.close()
    report = {
        "input": str(input_path),
        "programmatic_total": sum(counts.values()),
        "counts": dict(counts),
        "counts_by_status_source": dict(source_counts),
        "counts_by_reason": dict(reason_counts),
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
