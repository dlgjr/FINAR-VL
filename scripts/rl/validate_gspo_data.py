"""Fail-closed preflight for the derived RL JSONL."""

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
    path: str | Path, *, expected_count: int = 0, root: str | Path | None = None, fail_on_unverified: bool = False
) -> dict[str, Any]:
    seen: set[str] = set()
    errors: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
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
        if any(message.get("role") == "assistant" for message in messages):
            _add(errors, line_number, sample_id, "assistant_leakage")
        if not messages:
            _add(errors, line_number, sample_id, "missing_messages")

        gold_atoms = row.get("gold_atoms") or []
        if verifier_type == "model_judge":
            if not row.get("gold_claims"):
                _add(errors, line_number, sample_id, "missing_gold_claims")
        elif verifier_type == "numeric":
            gold_numeric = row.get("gold_numeric")
            if gold_atoms:
                _add(errors, line_number, sample_id, "numeric_has_stale_gold_atoms")
            if not gold_numeric:
                _add(errors, line_number, sample_id, "missing_gold_numeric")
            elif not isinstance(gold_numeric, list) or len(gold_numeric) != 1:
                _add(
                    errors,
                    line_number,
                    sample_id,
                    "numeric_requires_single_gold",
                    gold_count=len(gold_numeric) if isinstance(gold_numeric, list) else None,
                )
            else:
                try:
                    item = gold_numeric[0]
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
            _add(errors, line_number, sample_id, "program_metadata_conflict", detail=conflict)

        verification = row.get("gold_verification") or {}
        if verifier_type != "model_judge":
            status = verification.get("status")
            if status not in {"verified", "source_only", "hard_negative_unverified"}:
                _add(errors, line_number, sample_id, "missing_or_invalid_gold_verification", status=status)
            elif status != "verified":
                warning = {
                    "line": line_number,
                    "sample_id": sample_id,
                    "warning": status,
                    "source": row.get("source", ""),
                }
                warnings.append(warning)
                if fail_on_unverified:
                    _add(
                        errors,
                        line_number,
                        sample_id,
                        "unverified_gold_blocked",
                        status=status,
                        source=row.get("source", ""),
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
    report = {
        "count": count,
        "expected_count": expected_count,
        "unique_sample_ids": len(seen),
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
    parser.add_argument("--fail-on-unverified", action="store_true")
    args = parser.parse_args()
    print(
        json.dumps(
            validate(
                args.path,
                expected_count=args.expected_count,
                root=args.root,
                fail_on_unverified=args.fail_on_unverified,
            ),
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
