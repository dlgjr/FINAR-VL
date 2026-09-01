#!/usr/bin/env python3
"""Normalize the finance reasoning RL JSONL and audit every appended record.

The records appended at source line 4580 and later come from benchmark
sources.  They are routed only after their concrete answer structure has been
validated.  SpreadsheetBench records are excluded because their final JSON
targets exceed the RL rollout budget.  The rewrite is atomic and gives every
row the same top-level schema.  Pass@k selection metadata is intentionally
removed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from collections import Counter
from pathlib import Path
from typing import Any, Mapping

from scripts.rl.gspo_reward import (
    _numeric_atoms,
    _split_atoms,
    extract_last_answer,
    extract_prefixed_answer,
)


APPENDED_START_LINE = 4580
PASS_FIELDS = {"_pass_at_k", "pass_at_k", "passk", "pass_at_k_used"}
CANONICAL_FIELDS = (
    "sample_id",
    "messages",
    "source",
    "split",
    "images",
    "task",
    "output_format",
    "solution",
    "metadata",
    "reward_type",
    "reward_subtype",
    "verifier_type",
    "_reward_routing",
)
FORMAT_BY_VERIFIER = {
    "numeric": "number_or_free_text",
    "numeric_final": "numeric_final",
    "composite_numeric": "composite_numeric",
    "page_numbers": "page_numbers",
    "true_false": "true_false",
    "single_choice": "single_choice",
    "multiple_choice": "multiple_choice",
}
LEGACY_METADATA_FIELDS = (
    "difficulty",
    "task_raw",
    "task_group",
    "task_needs_review",
    "task_normalization_version",
    "task_original",
    "_manual_verification_review",
)


def _scrub_pass_fields(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {
            key: _scrub_pass_fields(item)
            for key, item in value.items()
            if str(key).casefold() not in PASS_FIELDS
        }
    if isinstance(value, list):
        return [_scrub_pass_fields(item) for item in value]
    return value


def _assistant_solution(row: Mapping[str, Any]) -> str:
    for message in reversed(row.get("messages") or []):
        if message.get("role") == "assistant":
            return str(message.get("content", ""))
    return str(row.get("solution") or "")


def _canonical_answer(solution: str) -> str:
    tagged = extract_last_answer(solution)
    if tagged is not None:
        return tagged
    prefixed = extract_prefixed_answer(solution)
    if prefixed is not None:
        return prefixed
    english = re.findall(r"Answer\s*[:：][ \t]*([^\r\n]*)", solution, re.IGNORECASE)
    if english:
        return english[-1].strip()
    lines = [line.strip() for line in solution.splitlines() if line.strip()]
    return lines[-1] if lines else solution.strip()


def _sample_id(row: Mapping[str, Any], line_number: int) -> str:
    pass_at_k = row.get("_pass_at_k") or {}
    routing = row.get("_reward_routing") or {}
    return str(
        row.get("sample_id")
        or row.get("id")
        or pass_at_k.get("result_index")
        or (
            f"{routing.get('source_dataset')}:{routing.get('original_source_line')}"
            if routing.get("source_dataset") and routing.get("original_source_line")
            else ""
        )
        or f"reasoning:{line_number}"
    )


def _audit_appended(row: Mapping[str, Any], line_number: int) -> tuple[str, str, str]:
    source = str(row.get("source") or "")
    output_format = str(row.get("output_format") or "")
    solution = _assistant_solution(row)
    answer = _canonical_answer(solution)
    metadata = row.get("metadata") or {}

    if output_format in {"number_or_free_text", "numeric_final"}:
        atoms = _numeric_atoms(answer)
        if len(atoms) != 1:
            raise ValueError(f"line {line_number}: numeric final answer has {len(atoms)} numeric atoms")
        official = metadata.get("official_answer")
        if official not in (None, "") and len(_numeric_atoms(str(official))) != 1:
            raise ValueError(f"line {line_number}: official numeric answer is not singular")
        verifier = "numeric_final" if source == "FinChart-Bench" else "numeric"
        return verifier, "objective_financial_numeric_answer", "single_final_numeric_and_official_gold"

    if output_format == "page_numbers":
        pages = set(_split_atoms(answer, "page_numbers"))
        evidence_pages = metadata.get("evidence_pages")
        if not pages or not isinstance(evidence_pages, list):
            raise ValueError(f"line {line_number}: page answer or evidence_pages is missing")
        official_pages = {str(int(page)) for page in evidence_pages}
        if pages != official_pages:
            raise ValueError(f"line {line_number}: assistant pages do not match evidence_pages")
        if row.get("images") and any(int(page) > len(row["images"]) for page in pages):
            raise ValueError(f"line {line_number}: evidence page exceeds image count")
        return "page_numbers", "objective_evidence_page_set", "assistant_pages_match_metadata_evidence_pages"

    raise ValueError(
        f"line {line_number}: appended record is not safely program-verifiable "
        f"(source={source!r}, output_format={output_format!r})"
    )


def _normalize_row(row: dict[str, Any], line_number: int) -> dict[str, Any]:
    sample_id = _sample_id(row, line_number)
    metadata = dict(row.get("metadata") or {})
    for key in LEGACY_METADATA_FIELDS:
        if key in row and row[key] is not None:
            target = "manual_verification_review" if key == "_manual_verification_review" else key
            metadata.setdefault(target, row[key])
    metadata = _scrub_pass_fields(metadata)

    if line_number >= APPENDED_START_LINE:
        verifier, reason, basis = _audit_appended(row, line_number)
        previous = row.get("_reward_routing") or {}
        routing = {
            "version": "finance_rl_route_v3",
            "reason": reason,
            "verification_basis": basis,
            "program_verification_checked": True,
            "original_source_line": int(previous.get("original_source_line") or line_number),
            "source_line": line_number,
        }
    else:
        verifier = str(row.get("verifier_type") or row.get("reward_subtype") or "")
        if verifier not in FORMAT_BY_VERIFIER:
            raise ValueError(f"line {line_number}: unsupported existing verifier {verifier!r}")
        previous = row.get("_reward_routing") or {}
        routing = {
            "version": "finance_rl_route_v3",
            "reason": str(previous.get("reason") or "existing_programmatic_route"),
            "source_line": line_number,
        }
        for key in ("source_dataset", "original_source_line", "reference_mode"):
            if previous.get(key) not in (None, ""):
                routing[key] = previous[key]

    explicit_solution = row.get("solution")
    normalized = {
        "sample_id": sample_id,
        "messages": _scrub_pass_fields(row.get("messages") or []),
        "source": str(row.get("source") or ""),
        "split": str(row.get("split") or "train"),
        "images": list(row.get("images") or []),
        "task": str(row.get("task") or ""),
        "output_format": FORMAT_BY_VERIFIER[verifier],
        "solution": explicit_solution if explicit_solution not in (None, "") else None,
        "metadata": metadata,
        "reward_type": "rule",
        "reward_subtype": verifier,
        "verifier_type": verifier,
        "_reward_routing": routing,
    }
    if tuple(normalized) != CANONICAL_FIELDS:
        raise AssertionError("canonical field order drifted")
    return normalized


def normalize(path: Path, *, write: bool) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    route_counts: Counter[str] = Counter()
    source_counts: Counter[str] = Counter()
    seen_lines: set[bytes] = set()
    duplicates_removed: list[dict[str, Any]] = []
    spreadsheet_removed: list[dict[str, Any]] = []
    appended_records_audited = 0
    with path.open(encoding="utf-8") as source:
        for line_number, line in enumerate(source, 1):
            if not line.strip():
                continue
            raw_row = json.loads(line)
            if raw_row.get("source") == "SpreadsheetBench-v2":
                spreadsheet_removed.append(
                    {"original_source_line": line_number, "sample_id": _sample_id(raw_row, line_number)}
                )
                continue
            fingerprint = hashlib.sha256(line.strip().encode("utf-8")).digest()
            if fingerprint in seen_lines:
                duplicates_removed.append(
                    {"original_source_line": line_number, "sample_id": _sample_id(raw_row, line_number)}
                )
                continue
            seen_lines.add(fingerprint)
            row = _normalize_row(raw_row, line_number)
            row["_reward_routing"]["source_line"] = len(rows) + 1
            rows.append(row)
            route_counts[row["verifier_type"]] += 1
            if line_number >= APPENDED_START_LINE:
                appended_records_audited += 1
                source_counts[row["source"]] += 1

    ids = [row["sample_id"] for row in rows]
    if len(ids) != len(set(ids)):
        duplicates = [sample_id for sample_id, count in Counter(ids).items() if count > 1]
        raise ValueError(f"duplicate sample_id values: {duplicates[:10]}")
    if any(tuple(row) != CANONICAL_FIELDS for row in rows):
        raise AssertionError("top-level schemas are not uniform")
    serialized = [json.dumps(row, ensure_ascii=False, separators=(",", ":")) for row in rows]
    if any(re.search(r'"(?:_?pass_?at_?k|passk|pass_at_k_used)"\s*:', line, re.IGNORECASE) for line in serialized):
        raise AssertionError("pass@k field survived normalization")

    if write:
        temporary = path.with_name(path.name + ".normalize_tmp")
        try:
            with temporary.open("w", encoding="utf-8", newline="\n") as target:
                target.write("\n".join(serialized) + "\n")
            os.replace(temporary, path)
        finally:
            if temporary.exists():
                temporary.unlink()

    return {
        "path": str(path),
        "records": len(rows),
        "appended_records_audited": appended_records_audited,
        "duplicates_removed": duplicates_removed,
        "spreadsheet_records_removed": len(spreadsheet_removed),
        "uniform_fields": list(CANONICAL_FIELDS),
        "route_counts": dict(route_counts),
        "appended_source_counts": dict(source_counts),
        "pass_fields_remaining": 0,
        "written": write,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", type=Path)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    print(json.dumps(normalize(args.path, write=args.write), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
