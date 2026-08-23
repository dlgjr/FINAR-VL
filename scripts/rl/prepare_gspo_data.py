"""Convert the immutable mixed training JSONL into GSPO-ready records."""

from __future__ import annotations

import argparse
import copy
import json
import re
from collections import Counter
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Mapping, Sequence

from .gspo_reward import (
    _numeric_atoms,
    _split_atoms,
    extract_last_answer,
    extract_prefixed_answer,
    numeric_gold_from_text,
)


_FORMAT_TO_VERIFIER = {
    "number_or_free_text": "numeric",
    "numeric_or_short_text": "numeric",
    "single_choice": "single_choice",
    "multiple_choice": "multiple_choice",
    "true_false": "true_false",
    "page_numbers": "page_numbers",
    "numeric_final": "numeric_final",
    "composite_numeric": "composite_numeric",
}
_PROGRAMMATIC_VERIFIERS = set(_FORMAT_TO_VERIFIER.values())
_PROGRAM_CALL_RE = re.compile(r"(add|subtract|multiply|divide)\(([^()]*)\)")


class RejectedRecord(ValueError):
    """A data-quality rejection that should be dropped and reported, not crash preparation."""


def _reference_solution(row: Mapping[str, Any], messages: Sequence[Mapping[str, Any]]) -> str:
    explicit = row.get("solution")
    if explicit not in (None, ""):
        return str(explicit)
    for message in reversed(messages):
        if message.get("role") == "assistant":
            content = message.get("content", "")
            return content if isinstance(content, str) else str(content)
    return str(row.get("reference") or "")


def _question(messages: Sequence[Mapping[str, Any]]) -> str:
    return "\n".join(str(m.get("content", "")) for m in messages if m.get("role") == "user")


def _sample_id(row: Mapping[str, Any], line_number: int) -> str:
    routed_line = (row.get("_reward_routing") or {}).get("source_line")
    return str(
        row.get("sample_id")
        or row.get("id")
        or (row.get("_pass_at_k") or {}).get("result_index")
        or f"line:{routed_line or line_number}"
    )


def _estimate_cost(row: Mapping[str, Any], question: str, verifier_type: str) -> float:
    images = row.get("images") or []
    pixels = row.get("image_pixels") or []
    resolution_cost = sum(float(value) for value in pixels) / 1_000_000 * 256 if pixels else len(images) * 256
    input_tokens = max(1, len(question) // 4)
    expected_completion = 2048 if verifier_type == "model_judge" else 512
    judge_calls = 4 if verifier_type == "model_judge" else 0
    return float(input_tokens + resolution_cost + expected_completion + judge_calls * 128)


def _canonical_solution(solution: str) -> str:
    tagged = extract_last_answer(solution)
    if tagged is not None:
        return tagged
    prefixed = extract_prefixed_answer(solution)
    if prefixed is not None:
        return prefixed
    try:
        payload = json.loads(solution)
    except (TypeError, json.JSONDecodeError):
        payload = None
    if isinstance(payload, Mapping) and "answer" in payload:
        return str(payload["answer"])
    lines = [line.strip() for line in solution.splitlines() if line.strip()]
    return lines[-1] if lines else solution


def _normalize_claims(claims: Sequence[Any]) -> tuple[list[str], list[dict[str, str]]]:
    ids: list[str] = []
    details: list[dict[str, str]] = []
    for index, claim in enumerate(claims, 1):
        if isinstance(claim, Mapping):
            claim_id = str(claim.get("id") or f"G{index}")
            text = str(claim.get("text") or claim.get("claim") or "")
        else:
            value = str(claim)
            match = re.match(r"^(G\d+)\s*:\s*(.*)$", value)
            claim_id, text = (match.group(1), match.group(2)) if match else (f"G{index}", value)
        if claim_id in ids or not text.strip():
            raise ValueError(f"invalid or duplicate gold claim at index {index}")
        ids.append(claim_id)
        details.append({"id": claim_id, "text": text.strip()})
    return ids, details


def _program_arg(token: str, values: Sequence[Decimal]) -> Decimal:
    token = token.strip()
    if (token.startswith("#") or token.startswith("A")) and token[1:].isdigit():
        index = int(token[1:])
        if index >= len(values):
            raise RejectedRecord(f"program references missing intermediate #{index}")
        return values[index]
    if token.startswith("const_"):
        value = token[len("const_") :]
        if value == "m1":
            return Decimal(-1)
        try:
            return Decimal(value)
        except InvalidOperation as exc:
            raise RejectedRecord(f"unsupported program constant {token}") from exc
    try:
        return Decimal(token)
    except InvalidOperation as exc:
        raise RejectedRecord(f"unsupported program operand {token}") from exc


def _program_calls(program: str) -> list[tuple[str, tuple[str, str]]]:
    matches = list(_PROGRAM_CALL_RE.finditer(program or ""))
    if not matches:
        raise RejectedRecord("empty_or_unsupported_program")
    remainder = _PROGRAM_CALL_RE.sub("", program).replace(",", "").strip()
    if remainder:
        raise RejectedRecord(f"unsupported_program_syntax:{remainder}")
    output: list[tuple[str, tuple[str, str]]] = []
    for match in matches:
        args = [part.strip() for part in match.group(2).split(",")]
        if len(args) != 2:
            raise RejectedRecord(f"invalid_program_arity:{match.group(1)}")
        normalized = tuple(("#" + arg[1:]) if arg.startswith("A") and arg[1:].isdigit() else arg for arg in args)
        output.append((match.group(1), (normalized[0], normalized[1])))
    return output


def _program_is_prefix(program: str, reference_program: str) -> bool:
    current = _program_calls(program)
    reference = _program_calls(reference_program)
    return len(current) <= len(reference) and current == reference[: len(current)]


def execute_financial_program(program: str) -> Decimal:
    values: list[Decimal] = []
    calls = _program_calls(program)
    for operation, args in calls:
        left, right = (_program_arg(arg, values) for arg in args)
        if operation == "add":
            result = left + right
        elif operation == "subtract":
            result = left - right
        elif operation == "multiply":
            result = left * right
        else:
            if right == 0:
                raise RejectedRecord("program_division_by_zero")
            result = left / right
        values.append(result)
    return values[-1]


def _first_decimal(text: Any) -> tuple[Decimal, bool, int] | None:
    atoms = _numeric_atoms(str(text))
    if not atoms:
        return None
    atom = atoms[-1]
    number_match = re.search(
        r"[-+]?(?:(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.(\d+))?|\.(\d+))(?:[eE][-+]?\d+)?",
        atom,
    )
    if not number_match:
        return None
    value = Decimal(number_match.group(0).replace(",", ""))
    percent = "%" in atom or "％" in atom
    decimals = len((number_match.group(1) or number_match.group(2) or ""))
    return value, percent, decimals


def _display_consistent(execution: Decimal, display: Any) -> bool:
    parsed = _first_decimal(display)
    if parsed is None:
        return True
    value, percent, decimals = parsed
    precision = Decimal(10) ** Decimal(-decimals)
    candidates = [(value, precision)]
    if percent:
        candidates.append((value / Decimal(100), precision / Decimal(100)))
    return any(abs(execution - expected) <= tolerance + Decimal("1e-12") for expected, tolerance in candidates)


def _close_decimal(left: Decimal, right: Decimal) -> bool:
    delta = abs(left - right)
    return delta <= Decimal("1e-10") + max(abs(left), abs(right)) * Decimal("1e-10")


def validate_program_metadata(row: Mapping[str, Any]) -> tuple[Decimal | None, str | None]:
    metadata = row.get("metadata") or {}
    program = metadata.get("program")
    if not program:
        return None, None
    program = str(program)
    execution = execute_financial_program(program)
    operation_count = metadata.get("operation_count")
    if operation_count is not None and int(operation_count) != len(_program_calls(program)):
        return execution, "operation_count_mismatch"
    original_program = metadata.get("original_program")
    if original_program and not _program_is_prefix(program, str(original_program)):
        return execution, "original_program_prefix_mismatch"
    official_program = metadata.get("official_program")
    if official_program and _program_calls(program) != _program_calls(str(official_program)):
        return execution, "official_program_mismatch"
    value = metadata.get("program_execution_result")
    if value not in (None, ""):
        parsed = _first_decimal(value)
        if parsed is not None and not _close_decimal(execution, parsed[0]):
            return execution, "program_execution_result_mismatch"
    value = metadata.get("gold_execution_answer")
    if value not in (None, "") and not _display_consistent(execution, value):
        return execution, "gold_execution_answer_mismatch"
    value = metadata.get("official_answer")
    if value not in (None, "") and not _display_consistent(execution, value):
        return execution, "official_answer_mismatch"
    readable = metadata.get("gold_readable_answer")
    if readable not in (None, "") and not _display_consistent(execution, readable):
        return execution, "gold_readable_answer_mismatch"
    return execution, None


def _numeric_gold(row: Mapping[str, Any], solution: str) -> tuple[list[dict[str, Any]], str]:
    metadata = row.get("metadata") or {}
    execution, conflict = validate_program_metadata(row)
    if conflict:
        if conflict != "gold_readable_answer_mismatch":
            raise RejectedRecord(conflict)
        for key in ("gold_readable_answer", "official_answer", "gold_execution_answer"):
            value = metadata.get(key)
            if value not in (None, ""):
                return numeric_gold_from_text(str(value)), f"metadata.{key}+program_conflict:{conflict}"
        raise RejectedRecord(conflict)
    if execution is not None:
        # Program execution verifies the arithmetic. Prefer an independently sourced
        # human-readable/official presentation so unit and scale are explicit.
        for key in ("gold_readable_answer", "official_answer", "gold_execution_answer"):
            value = metadata.get(key)
            if value not in (None, ""):
                try:
                    gold: list[dict[str, Any]] = numeric_gold_from_text(str(value))
                except ValueError as exc:
                    raise RejectedRecord(f"invalid_{key}") from exc
                primary = gold[0]
                execution_alias = {"value": str(execution), "unit": ""}
                if primary["unit"] != "" or Decimal(primary["value"]) != execution:
                    primary["aliases"] = [execution_alias]
                return gold, f"metadata.{key}+program_verified"
        return [{"value": str(execution), "unit": ""}], "metadata.program"
    for key in ("official_answer", "gold_readable_answer", "gold_execution_answer"):
        value = metadata.get(key)
        if value not in (None, ""):
            return numeric_gold_from_text(str(value)), f"metadata.{key}"
    candidate = _canonical_solution(solution)
    return numeric_gold_from_text(candidate), "assistant.final_answer"


def _page_gold(row: Mapping[str, Any], canonical_solution: str) -> tuple[list[str], str]:
    assistant_pages = _split_atoms(canonical_solution, "page_numbers")
    evidence_pages = (row.get("metadata") or {}).get("evidence_pages")
    if evidence_pages not in (None, ""):
        try:
            pages = list(dict.fromkeys(str(int(page)) for page in evidence_pages))
        except (TypeError, ValueError) as exc:
            raise RejectedRecord("invalid_evidence_pages") from exc
        if not pages:
            raise RejectedRecord("empty_evidence_pages")
        if set(assistant_pages) != set(pages):
            raise RejectedRecord("evidence_pages_answer_mismatch")
        return pages, "metadata.evidence_pages"
    return assistant_pages, "assistant.final_answer"


def _composite_numeric_gold(canonical_solution: str) -> list[dict[str, str]]:
    gold: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for atom in _numeric_atoms(canonical_solution):
        item = numeric_gold_from_text(atom)[0]
        key = (item["value"], item["unit"])
        if key not in seen:
            seen.add(key)
            gold.append(item)
    if not gold:
        raise RejectedRecord("missing_composite_numeric_gold")
    return gold


def _gold_verification(row: Mapping[str, Any], verifier_type: str, gold_source: str) -> dict[str, Any]:
    metadata = row.get("metadata") or {}
    pass_at_k = row.get("_pass_at_k") or {}
    independent = False
    if verifier_type == "page_numbers":
        independent = bool(metadata.get("evidence_pages"))
    elif verifier_type in {"numeric", "numeric_final", "composite_numeric"}:
        independent = any(
            metadata.get(key) not in (None, "")
            for key in ("gold_readable_answer", "official_answer", "official_program", "original_program")
        )
    if "program_conflict:" in gold_source:
        independent = False
    status = "verified" if independent else "source_only"
    if int(pass_at_k.get("correct_count", -1)) == 0 and not independent:
        status = "hard_negative_unverified"
    return {"status": status, "independent": independent, "gold_source": gold_source}


def prepare_record(row: Mapping[str, Any], line_number: int, claims: Sequence[Any] | None = None) -> dict[str, Any]:
    messages = row.get("messages") or []
    solution = _reference_solution(row, messages)
    question = _question(messages) or str(row.get("question") or "")
    output_format = row.get("output_format")
    reward_type = str(row.get("reward_type") or "")
    verifier_type = str(row.get("verifier_type") or row.get("reward_subtype") or _FORMAT_TO_VERIFIER.get(output_format, "model_judge"))
    if verifier_type not in _PROGRAMMATIC_VERIFIERS | {"model_judge"}:
        raise ValueError(f"unknown verifier_type {verifier_type!r} at line {line_number}")
    expected_reward_type = "judge" if verifier_type == "model_judge" else "rule"
    if reward_type and reward_type != expected_reward_type:
        raise ValueError(f"reward_type/verifier_type mismatch at line {line_number}")
    reward_type = expected_reward_type
    if verifier_type != "model_judge" and not solution.strip():
        raise ValueError(f"programmatic answer requires a reference solution at line {line_number}")
    explicit_claims = claims if claims is not None else row.get("gold_claim_details") or row.get("gold_claims") or []
    claim_ids, claim_details = _normalize_claims(explicit_claims)
    canonical_solution = _canonical_solution(solution)
    gold_numeric: list[dict[str, Any]] = []
    gold_source = "assistant.final_answer"
    judge_reference = ""
    judge_reference_mode = ""
    if verifier_type in {"numeric", "numeric_final"}:
        try:
            gold_numeric, gold_source = _numeric_gold(row, solution)
        except RejectedRecord:
            raise
        except ValueError:
            if verifier_type != "numeric_final":
                raise
            gold_numeric = numeric_gold_from_text(solution)
            gold_source = "assistant.last_numeric"
        gold_atoms: list[str] = []
    elif verifier_type == "composite_numeric":
        gold_numeric = _composite_numeric_gold(canonical_solution)
        gold_atoms = []
    elif verifier_type == "page_numbers":
        gold_atoms, gold_source = _page_gold(row, canonical_solution)
    elif verifier_type == "model_judge":
        gold_atoms = []
        judge_reference = str(row.get("reference") or solution or "").strip()
        routed_mode = str((row.get("_reward_routing") or {}).get("reference_mode") or "")
        if claim_ids:
            judge_reference_mode = "gold_claims"
            gold_source = "gold_claims"
        elif routed_mode == "question_only" or not judge_reference:
            judge_reference_mode = "question_only"
            judge_reference = ""
            gold_source = "question_only"
        else:
            judge_reference_mode = "reference"
            gold_source = "reference"
    else:
        gold_atoms = _split_atoms(canonical_solution, verifier_type)
        if not gold_atoms:
            raise RejectedRecord(f"missing_{verifier_type}_gold")
    sample_id = _sample_id(row, line_number)
    input_messages = [copy.deepcopy(message) for message in messages if message.get("role") != "assistant"]
    instruction = "\n请在回复最后一行按“答案：具体答案”的格式给出最终答案。"
    for message in reversed(input_messages):
        if message.get("role") != "user":
            continue
        content = message.get("content", "")
        if isinstance(content, str):
            message["content"] = content + instruction
        elif isinstance(content, list):
            content.append({"type": "text", "text": instruction})
        break
    prepared = {key: value for key, value in row.items() if key != "messages"}
    prepared.update(
        {
            "messages": input_messages,
            "solution": solution,
            "sample_id": str(sample_id),
            "reward_type": reward_type,
            "reward_subtype": str(row.get("reward_subtype") or verifier_type),
            "verifier_type": verifier_type,
            "gold_atoms": gold_atoms,
            "gold_numeric": gold_numeric,
            "gold_source": gold_source,
            "gold_verification": _gold_verification(row, verifier_type, gold_source),
            "gold_claims": claim_ids,
            "gold_claim_details": claim_details,
            "judge_reference": judge_reference,
            "judge_reference_mode": judge_reference_mode,
            "question": question,
            "estimated_cost": _estimate_cost(row, question, verifier_type),
            "estimated_cost_breakdown": {
                "input_tokens": max(1, len(question) // 4),
                "image_count": len(row.get("images") or []),
                "image_pixels": sum(row.get("image_pixels") or []),
                "expected_completion_tokens": 2048 if verifier_type == "model_judge" else 512,
                "judge_calls": 4 if verifier_type == "model_judge" else 0,
            },
        }
    )
    return prepared


def prepare_jsonl(
    input_path: str | Path,
    output_path: str | Path,
    audit_path: str | Path,
    claims_by_id: Mapping[str, Sequence[str]] | None = None,
) -> dict[str, Any]:
    claims_by_id = claims_by_id or {}
    output_path, audit_path = Path(output_path), Path(audit_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    audit: dict[str, Any] = {"input": str(input_path), "total": 0, "written": 0, "rejected": [], "errors": []}
    sample_ids: set[str] = set()
    rejected_reasons: Counter[str] = Counter()
    with open(input_path, encoding="utf-8") as source, open(output_path, "w", encoding="utf-8") as target:
        for line_number, line in enumerate(source, 1):
            if not line.strip():
                continue
            audit["total"] += 1
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                audit["errors"].append({"line": line_number, "error": f"invalid_json:{exc.msg}"})
                continue
            sample_id = _sample_id(row, line_number)
            if sample_id in sample_ids:
                audit["errors"].append({"line": line_number, "sample_id": sample_id, "error": "duplicate_sample_id"})
                continue
            sample_ids.add(sample_id)
            try:
                prepared = prepare_record(row, line_number, claims_by_id.get(sample_id))
            except RejectedRecord as exc:
                reason = str(exc)
                rejected_reasons[reason] += 1
                audit["rejected"].append(
                    {"line": line_number, "sample_id": sample_id, "source": row.get("source", ""), "error": reason}
                )
                continue
            except Exception as exc:
                audit["errors"].append({"line": line_number, "sample_id": sample_id, "error": str(exc)})
                continue
            target.write(json.dumps(prepared, ensure_ascii=False) + "\n")
            audit["written"] += 1
    audit["rejected_count"] = len(audit["rejected"])
    audit["rejected_by_reason"] = dict(rejected_reasons)
    audit["unique_sample_ids"] = len(sample_ids)
    audit_path.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    if audit["errors"]:
        raise RuntimeError(f"GSPO data preparation failed for {len(audit['errors'])} records; see {audit_path}")
    return audit


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input")
    parser.add_argument("output")
    parser.add_argument("audit")
    parser.add_argument("--claims-json", help="JSON object mapping sample_id to claim ID lists")
    args = parser.parse_args()
    claims = json.loads(Path(args.claims_json).read_text(encoding="utf-8")) if args.claims_json else None
    prepare_jsonl(args.input, args.output, args.audit, claims)


if __name__ == "__main__":
    main()
