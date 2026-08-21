"""Convert the immutable mixed training JSONL into GSPO-ready records."""

from __future__ import annotations

import argparse
import copy
import json
import re
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
}
_PROGRAM_CALL_RE = re.compile(r"(add|subtract|multiply|divide)\(([^()]*)\)")


class RejectedRecord(ValueError):
    """A data-quality rejection that should be dropped and reported, not crash preparation."""


def _assistant_solution(messages: Sequence[Mapping[str, Any]]) -> str:
    for message in reversed(messages):
        if message.get("role") == "assistant":
            content = message.get("content", "")
            return content if isinstance(content, str) else str(content)
    raise ValueError("record has no assistant solution")


def _question(messages: Sequence[Mapping[str, Any]]) -> str:
    return "\n".join(str(m.get("content", "")) for m in messages if m.get("role") == "user")


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
    if token.startswith("#"):
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


def execute_financial_program(program: str) -> Decimal:
    values: list[Decimal] = []
    matches = list(_PROGRAM_CALL_RE.finditer(program or ""))
    if not matches:
        raise RejectedRecord("empty_or_unsupported_program")
    remainder = _PROGRAM_CALL_RE.sub("", program).replace(",", "").strip()
    if remainder:
        raise RejectedRecord(f"unsupported_program_syntax:{remainder}")
    for match in matches:
        operation = match.group(1)
        args = [part.strip() for part in match.group(2).split(",")]
        if len(args) != 2:
            raise RejectedRecord(f"invalid_program_arity:{operation}")
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
    unit = Decimal(10) ** Decimal(-decimals)
    candidates = [(value, unit)]
    if percent:
        candidates.append((value / Decimal(100), unit / Decimal(100)))
    return any(abs(execution - expected) <= tolerance + Decimal("1e-12") for expected, tolerance in candidates)


def _close_decimal(left: Decimal, right: Decimal) -> bool:
    delta = abs(left - right)
    return delta <= Decimal("1e-10") + max(abs(left), abs(right)) * Decimal("1e-10")


def validate_program_metadata(row: Mapping[str, Any]) -> tuple[Decimal | None, str | None]:
    metadata = row.get("metadata") or {}
    program = metadata.get("program")
    if not program:
        return None, None
    execution = execute_financial_program(str(program))
    operation_count = metadata.get("operation_count")
    if operation_count is not None and int(operation_count) != len(_PROGRAM_CALL_RE.findall(str(program))):
        return execution, "operation_count_mismatch"
    value = metadata.get("program_execution_result")
    if value not in (None, ""):
        parsed = _first_decimal(value)
        if parsed is not None and not _close_decimal(execution, parsed[0]):
            return execution, "program_execution_result_mismatch"
    for key in ("gold_execution_answer", "official_answer"):
        value = metadata.get(key)
        if value not in (None, "") and not _display_consistent(execution, value):
            return execution, f"{key}_mismatch"
    readable = metadata.get("gold_readable_answer")
    if readable not in (None, "") and not _display_consistent(execution, readable):
        return execution, "gold_readable_answer_mismatch"
    return execution, None


def _numeric_gold(row: Mapping[str, Any], solution: str) -> tuple[list[dict[str, str]], str]:
    metadata = row.get("metadata") or {}
    execution, conflict = validate_program_metadata(row)
    if conflict:
        raise RejectedRecord(conflict)
    if execution is not None:
        return [{"value": str(execution), "unit": ""}], "metadata.program"
    for key in ("gold_execution_answer", "official_answer"):
        value = metadata.get(key)
        if value not in (None, ""):
            return numeric_gold_from_text(str(value)), f"metadata.{key}"
    candidate = _canonical_solution(solution)
    return numeric_gold_from_text(candidate), "assistant.final_answer"


def prepare_record(row: Mapping[str, Any], line_number: int, claims: Sequence[Any] | None = None) -> dict[str, Any]:
    messages = row.get("messages") or []
    solution = _assistant_solution(messages)
    question = _question(messages)
    output_format = row.get("output_format")
    verifier_type = _FORMAT_TO_VERIFIER.get(output_format, "model_judge")
    if verifier_type == "model_judge" and not claims:
        raise ValueError(f"open answer requires cached gold_claims at line {line_number}")
    claim_ids, claim_details = _normalize_claims(claims or [])
    canonical_solution = _canonical_solution(solution)
    gold_numeric: list[dict[str, str]] = []
    gold_source = "assistant.final_answer"
    if verifier_type == "numeric":
        gold_numeric, gold_source = _numeric_gold(row, solution)
        gold_atoms: list[str] = []
    elif verifier_type == "model_judge":
        gold_atoms = []
    else:
        gold_atoms = _split_atoms(canonical_solution, verifier_type)
    sample_id = (row.get("_pass_at_k") or {}).get("result_index") or f"line:{line_number}"
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
            "verifier_type": verifier_type,
            "gold_atoms": gold_atoms,
            "gold_numeric": gold_numeric,
            "gold_source": gold_source,
            "gold_claims": claim_ids,
            "gold_claim_details": claim_details,
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


def prepare_jsonl(input_path: str | Path, output_path: str | Path, audit_path: str | Path, claims_by_id: Mapping[str, Sequence[str]] | None = None) -> dict[str, Any]:
    claims_by_id = claims_by_id or {}
    output_path, audit_path = Path(output_path), Path(audit_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    audit: dict[str, Any] = {"input": str(input_path), "total": 0, "written": 0, "rejected": [], "errors": []}
    sample_ids: set[str] = set()
    with open(input_path, encoding="utf-8") as source, open(output_path, "w", encoding="utf-8") as target:
        for line_number, line in enumerate(source, 1):
            if not line.strip():
                continue
            audit["total"] += 1
            row = json.loads(line)
            sample_id = str((row.get("_pass_at_k") or {}).get("result_index") or f"line:{line_number}")
            if sample_id in sample_ids:
                audit["errors"].append({"line": line_number, "sample_id": sample_id, "error": "duplicate_sample_id"})
                continue
            sample_ids.add(sample_id)
            try:
                prepared = prepare_record(row, line_number, claims_by_id.get(sample_id))
            except RejectedRecord as exc:
                audit["rejected"].append({"line": line_number, "sample_id": sample_id, "error": str(exc)})
                continue
            except Exception as exc:
                audit["errors"].append({"line": line_number, "sample_id": sample_id, "error": str(exc)})
                continue
            target.write(json.dumps(prepared, ensure_ascii=False) + "\n")
            audit["written"] += 1
    audit["rejected_count"] = len(audit["rejected"])
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
