"""Preflight validation for the derived RL JSONL."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from .gspo_reward import _structured_numeric
from .prepare_gspo_data import _FORMAT_TO_VERIFIER, validate_program_metadata


_CHOICE_RE = re.compile(r"^(?:[A-H]|\d+)$")


def _image_slots(messages: list[dict[str, Any]]) -> int:
    count = 0
    for message in messages:
        content = message.get("content", "")
        if isinstance(content, str):
            count += content.count("<image>")
        elif isinstance(content, list):
            count += sum(isinstance(item, dict) and item.get("type") == "image" for item in content)
    return count


def _add(errors: list[dict[str, Any]], line: int, sample_id: str, error: str, **detail: Any) -> None:
    item: dict[str, Any] = {"line": line, "error": error, "sample_id": sample_id}
    item.update(detail)
    errors.append(item)


def validate(
    path: str | Path,
    *,
    expected_count: int = 0,
    root: str | Path | None = None,
    fail_on_unverified: bool = False,
    route_mode: str = "mixed",
) -> dict[str, Any]:
    # fail_on_unverified is retained for CLI compatibility only. Source-only gold is
    # diagnostic metadata; it is not a rejection criterion. Objective structural or
    # program/reference conflicts remain hard errors below.
    del fail_on_unverified
    seen: set[str] = set()
    errors: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    reward_counts = {"rule": 0, "judge": 0}
    count = 0
    for line_number, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        count += 1
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            _add(errors, line_number, "", "invalid_json", detail=exc.msg)
            continue
        sample_id = str(row.get("sample_id", ""))
        messages = row.get("messages", []) or []
        verifier_type = row.get("verifier_type")
        reward_type = row.get("reward_type")
        output_format = row.get("output_format")
        if not sample_id or sample_id in seen:
            _add(errors, line_number, sample_id, "missing_or_duplicate_sample_id")
        seen.add(sample_id)
        if output_format in _FORMAT_TO_VERIFIER and _FORMAT_TO_VERIFIER[output_format] != verifier_type:
            _add(
                errors,
                line_number,
                sample_id,
                "verifier_type_mismatch",
                output_format=output_format,
                expected=_FORMAT_TO_VERIFIER[output_format],
                actual=verifier_type,
            )
        expected_reward_type = "judge" if verifier_type == "model_judge" else "rule"
        if reward_type != expected_reward_type:
            _add(
                errors,
                line_number,
                sample_id,
                "reward_type_mismatch",
                expected=expected_reward_type,
                actual=reward_type,
            )
        elif reward_type in reward_counts:
            reward_counts[reward_type] += 1
        if any(message.get("role") == "assistant" for message in messages):
            _add(errors, line_number, sample_id, "assistant_leakage")
        if not messages:
            _add(errors, line_number, sample_id, "missing_messages")

        gold_atoms = row.get("gold_atoms") or []
        if verifier_type == "model_judge":
            reference_mode = row.get("judge_reference_mode")
            if reference_mode != "question_only":
                _add(errors, line_number, sample_id, "invalid_judge_reference_mode", mode=reference_mode)
            if str(row.get("judge_reference") or "").strip() or row.get("gold_claims") or row.get("gold_claim_details"):
                _add(errors, line_number, sample_id, "judge_must_not_use_reference")
        elif verifier_type in {"numeric", "numeric_final", "composite_numeric"}:
            gold_numeric = row.get("gold_numeric")
            if gold_atoms:
                _add(errors, line_number, sample_id, "numeric_has_stale_gold_atoms")
            if not gold_numeric:
                _add(errors, line_number, sample_id, "missing_gold_numeric")
            elif not isinstance(gold_numeric, list) or (
                verifier_type != "composite_numeric" and len(gold_numeric) != 1
            ):
                _add(
                    errors,
                    line_number,
                    sample_id,
                    "numeric_requires_single_gold",
                    gold_count=len(gold_numeric) if isinstance(gold_numeric, list) else None,
                )
            else:
                try:
                    for item in gold_numeric:
                        if not isinstance(item, dict):
                            raise ValueError("gold_numeric item is not an object")
                        _structured_numeric(item)
                        for alias in item.get("aliases", []) or []:
                            if not isinstance(alias, dict):
                                raise ValueError("numeric alias is not an object")
                            _structured_numeric(alias)
                except Exception as exc:
                    _add(errors, line_number, sample_id, "invalid_gold_numeric", detail=str(exc))
            if not row.get("gold_source"):
                _add(errors, line_number, sample_id, "missing_gold_source")
        elif verifier_type == "page_numbers":
            if not gold_atoms:
                _add(errors, line_number, sample_id, "missing_gold_atoms")
            else:
                pages: list[int] = []
                for atom in gold_atoms:
                    if not str(atom).isdigit() or int(atom) <= 0:
                        _add(errors, line_number, sample_id, "invalid_page_atom", atom=str(atom))
                        continue
                    pages.append(int(atom))
                images = row.get("images", []) or []
                if images and any(page > len(images) for page in pages):
                    _add(errors, line_number, sample_id, "page_out_of_range", pages=pages, image_count=len(images))
        elif verifier_type == "true_false":
            if len(gold_atoms) != 1 or str(gold_atoms[0]) not in {"true", "false"}:
                _add(errors, line_number, sample_id, "invalid_true_false_gold", gold_atoms=gold_atoms)
        elif verifier_type == "single_choice":
            if len(gold_atoms) != 1 or not _CHOICE_RE.fullmatch(str(gold_atoms[0])):
                _add(errors, line_number, sample_id, "invalid_single_choice_gold", gold_atoms=gold_atoms)
        elif verifier_type in {"multiple_choice", "choice"}:
            if not gold_atoms or any(not _CHOICE_RE.fullmatch(str(atom)) for atom in gold_atoms):
                _add(errors, line_number, sample_id, "invalid_multiple_choice_gold", gold_atoms=gold_atoms)
        elif verifier_type:
            _add(errors, line_number, sample_id, "unknown_verifier_type", verifier_type=verifier_type)
        else:
            _add(errors, line_number, sample_id, "missing_verifier_type")

        images = row.get("images", []) or []
        slots = _image_slots(messages)
        if slots != len(images):
            _add(errors, line_number, sample_id, "image_slot_mismatch", image_slots=slots, images=len(images))
        try:
            _, conflict = validate_program_metadata(row)
        except Exception as exc:
            conflict = str(exc)
        if conflict:
            if "program_conflict:" in str(row.get("gold_source") or ""):
                warnings.append(
                    {
                        "line": line_number,
                        "sample_id": sample_id,
                        "warning": "program_metadata_conflict_ignored",
                        "detail": conflict,
                    }
                )
            else:
                _add(errors, line_number, sample_id, "program_metadata_conflict", detail=conflict)

        verification = row.get("gold_verification") or {}
        if verifier_type != "model_judge":
            status = verification.get("status")
            if status not in {"verified", "source_only", "hard_negative_unverified"}:
                _add(errors, line_number, sample_id, "missing_or_invalid_gold_verification", status=status)
            elif status != "verified":
                warnings.append(
                    {
                        "line": line_number,
                        "sample_id": sample_id,
                        "warning": "source_only",
                        "source": row.get("source", ""),
                    }
                )

        if root is not None:
            for image in images:
                image_path = Path(image)
                if not image_path.is_absolute():
                    image_path = Path(root) / image_path
                if not image_path.is_file():
                    _add(errors, line_number, sample_id, "missing_image", image=str(image_path))
    count_matches = expected_count <= 0 or count == expected_count
    if not count_matches:
        errors.append(
            {"line": 0, "error": "count_mismatch", "sample_id": "", "count": count, "expected_count": expected_count}
        )
    if route_mode == "generation" and (reward_counts["rule"] == 0 or reward_counts["judge"] == 0):
        errors.append({"line": 0, "error": "generation_requires_rule_and_judge_routes", "sample_id": ""})
    elif route_mode == "reasoning" and reward_counts["judge"]:
        errors.append({"line": 0, "error": "reasoning_must_be_programmatic_only", "sample_id": ""})
    report = {
        "count": count,
        "expected_count": expected_count,
        "unique_sample_ids": len(seen),
        "reward_counts": reward_counts,
        "warnings": warnings,
        "errors": errors,
        "valid": not errors,
    }
    if not report["valid"]:
        raise ValueError(json.dumps(report, ensure_ascii=False))
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("path")
    parser.add_argument("--expected-count", type=int, default=0)
    parser.add_argument("--root")
    parser.add_argument("--fail-on-unverified", action="store_true", help="deprecated; retained for compatibility")
    parser.add_argument("--route-mode", choices=("mixed", "generation", "reasoning"), default="mixed")
    parser.add_argument("--report")
    args = parser.parse_args()
    report = validate(
        args.path,
        expected_count=args.expected_count,
        root=args.root,
        fail_on_unverified=args.fail_on_unverified,
        route_mode=args.route_mode,
    )
    if args.report:
        Path(args.report).write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    summary = {key: value for key, value in report.items() if key not in {"warnings", "errors"}}
    summary["warning_count"] = len(report["warnings"])
    summary["error_count"] = len(report["errors"])
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
