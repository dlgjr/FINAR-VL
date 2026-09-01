#!/usr/bin/env python3
"""Reclassify reward routing for the two finance RL source datasets."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Any


_CHOICE_RE = re.compile(r"^(?:[A-H]+|[A-H](?:\s*[,，、/;；]\s*[A-H])+)$", re.IGNORECASE)
_TRUE_FALSE_RE = re.compile(r"^(?:正确|错误|对|错|是|否|true|false|yes|no)$", re.IGNORECASE)
_NUMBER_RE = re.compile(
    r"[-+]?(?:(?:\d{1,3}(?:[,，]\d{3})+|\d+)(?:\.\d+)?|\.\d+)(?:[eE][-+]?\d+)?"
)
_ANSWER_RE = re.compile(r"<answer>\s*(.*?)\s*</answer>", re.IGNORECASE | re.DOTALL)
_ANSWER_PREFIX_RE = re.compile(r"(?:最终答案|答案|Answer)\s*[:：][ \t]*([^\r\n]*)", re.IGNORECASE)
_OPTION_RE = re.compile(r"(?m)^\s*([A-H])\s*[.、:：)]\s*(.*?)\s*$", re.IGNORECASE)

_DIRECT_FORMATS = {
    "number_or_free_text": "numeric",
    "numeric_or_short_text": "numeric",
    "single_choice": "single_choice",
    "multiple_choice": "multiple_choice",
    "true_false": "true_false",
    "page_numbers": "page_numbers",
}

_COMPOSITE_TASKS = {"long"}


def _assistant_solution(row: dict[str, Any]) -> str:
    for message in reversed(row.get("messages") or []):
        if message.get("role") == "assistant":
            return str(message.get("content", ""))
    return str(row.get("solution") or row.get("reference") or "")


def _question(row: dict[str, Any]) -> str:
    if row.get("question"):
        return str(row["question"])
    return "\n".join(
        str(message.get("content", ""))
        for message in row.get("messages") or []
        if message.get("role") == "user"
    )


def _canonical_answer(solution: str) -> str:
    tagged = _ANSWER_RE.findall(solution)
    if tagged:
        return tagged[-1].strip()
    prefixed = _ANSWER_PREFIX_RE.findall(solution)
    if prefixed:
        return prefixed[-1].strip()
    return solution.strip()


def _choice_subtype(answer: str) -> str | None:
    compact = answer.strip().strip(".。:：()（）[]【】")
    if not _CHOICE_RE.fullmatch(compact):
        return None
    letters = re.findall(r"[A-H]", compact.upper())
    return "multiple_choice" if len(set(letters)) > 1 else "single_choice"


def _normalize_option_text(value: str) -> str:
    value = unicodedata.normalize("NFKC", value).casefold()
    return "".join(char for char in value if not unicodedata.category(char).startswith(("P", "Z")))


def _recover_choice(question: str, answer: str) -> list[str]:
    options = {label.upper(): text.strip() for label, text in _OPTION_RE.findall(question) if text.strip()}
    if not options:
        return []

    compact = answer.strip().strip(".。:：()（）[]【】")
    if _CHOICE_RE.fullmatch(compact):
        labels = list(dict.fromkeys(re.findall(r"[A-H]", compact.upper())))
        return labels if all(label in options for label in labels) else []

    leading = re.match(r"^\s*([A-H])\s*[.、:：)]", answer, re.IGNORECASE)
    if leading and leading.group(1).upper() in options:
        return [leading.group(1).upper()]

    normalized_options = {_normalize_option_text(text): label for label, text in options.items()}
    whole = normalized_options.get(_normalize_option_text(answer))
    if whole:
        return [whole]

    pieces = [part.strip() for part in re.split(r"[;；,，、]", answer) if part.strip()]
    labels = [normalized_options.get(_normalize_option_text(part)) for part in pieces]
    if pieces and all(labels):
        return list(dict.fromkeys(str(label) for label in labels))
    return []


def _canonical_boolean(answer: str) -> str | None:
    normalized = answer.strip().strip(".。!！?？:：").casefold()
    if not _TRUE_FALSE_RE.fullmatch(normalized):
        return None
    return "true" if normalized in {"正确", "对", "是", "true", "yes"} else "false"


def _set_route(
    row: dict[str, Any], *, reward_type: str, subtype: str, reason: str, reference_mode: str = ""
) -> None:
    row["reward_type"] = reward_type
    row["reward_subtype"] = subtype
    row["verifier_type"] = "model_judge" if reward_type == "judge" else subtype
    previous = row.get("_reward_routing") or {}
    route = {"version": "finance_rl_route_v2", "reason": reason}
    for key in ("source_dataset", "original_source_line"):
        if key in previous:
            route[key] = previous[key]
    if reference_mode:
        route["reference_mode"] = reference_mode
    row["_reward_routing"] = route


def classify_generation(row: dict[str, Any]) -> tuple[str, str]:
    fmt = str(row.get("output_format") or "")
    solution = str(row.get("solution") or "").strip()
    reference = str(row.get("reference") or "").strip()
    assistant_gold = _assistant_solution(row).strip()
    question = _question(row)

    if fmt in _DIRECT_FORMATS and solution:
        subtype = _DIRECT_FORMATS[fmt]
        _set_route(row, reward_type="rule", subtype=subtype, reason=f"declared_{fmt}")
        return "rule", subtype

    reference_labels = _recover_choice(question, reference)
    reference_choice = "multiple_choice" if len(reference_labels) > 1 else "single_choice" if reference_labels else None
    if reference_choice:
        row["solution"] = "".join(reference_labels)
        row["output_format"] = reference_choice
        _set_route(
            row,
            reward_type="rule",
            subtype=reference_choice,
            reason="objective_choice_recovered_from_reference",
        )
        return "rule", reference_choice

    if reference and reference.casefold() != "nan":
        if not solution:
            row["solution"] = reference
    elif assistant_gold:
        row["solution"] = assistant_gold
        row["reference"] = assistant_gold
    _set_route(
        row,
        reward_type="judge",
        subtype="free_text",
        reason="semantic_finance_answer",
        reference_mode="question_only",
    )
    return "judge", "free_text"


def classify_reasoning(row: dict[str, Any]) -> tuple[str, str]:
    fmt = str(row.get("output_format") or "")
    task = str(row.get("task") or "")
    question = _question(row)
    solution = _assistant_solution(row)
    answer = _canonical_answer(solution)

    if fmt in _DIRECT_FORMATS:
        subtype = _DIRECT_FORMATS[fmt]
        _set_route(row, reward_type="rule", subtype=subtype, reason=f"declared_{fmt}")
        return "rule", subtype

    choice_labels = _recover_choice(question, answer)
    if choice_labels:
        choice_subtype = "multiple_choice" if len(choice_labels) > 1 else "single_choice"
        row["solution"] = "".join(choice_labels)
        row["output_format"] = choice_subtype
        _set_route(row, reward_type="rule", subtype=choice_subtype, reason="choice_recovered_from_answer")
        return "rule", choice_subtype

    boolean = _canonical_boolean(answer)
    if boolean:
        row["solution"] = boolean
        row["output_format"] = "true_false"
        _set_route(row, reward_type="rule", subtype="true_false", reason="boolean_recovered_from_answer")
        return "rule", "true_false"

    numbers = _NUMBER_RE.findall(answer)
    if task in _COMPOSITE_TASKS and numbers:
        subtype = "composite_numeric"
        reason = "multi_field_financial_computation"
    elif numbers:
        subtype = "numeric" if len(numbers) <= 1 else "numeric_final"
        reason = "objective_financial_computation"
    else:
        row["solution"] = answer
        row["reference"] = answer
        _set_route(
            row,
            reward_type="judge",
            subtype="free_text",
            reason="semantic_answer_requires_model_judge",
            reference_mode="question_only",
        )
        return "judge", "free_text"

    _set_route(row, reward_type="rule", subtype=subtype, reason=reason)
    return "rule", subtype


def _load_rows(path: Path, kind: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as source:
        for line_number, line in enumerate(source, 1):
            if not line.strip():
                continue
            row = json.loads(line)
            if kind == "generation":
                classify_generation(row)
            else:
                classify_reasoning(row)
            row["_reward_routing"]["source_line"] = line_number
            rows.append(row)
    return rows


def _report(path: Path, kind: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    route_counts = Counter(f"{row['reward_type']}:{row['reward_subtype']}" for row in rows)
    reason_counts = Counter(str(row["_reward_routing"]["reason"]) for row in rows)
    return {
        "path": str(path),
        "kind": kind,
        "records": len(rows),
        "route_counts": dict(route_counts),
        "reason_counts": dict(reason_counts),
        "unclassified": 0,
    }


def _write_rows(path: Path, rows: list[dict[str, Any]], backup_suffix: str) -> str:
    backup = path.with_name(path.name + backup_suffix)
    if not backup.exists():
        shutil.copy2(path, backup)
    temporary = path.with_name(path.name + ".route_tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as target:
        for row in rows:
            target.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")
    temporary.replace(path)
    return str(backup)


def rebalance(
    generation_path: Path, reasoning_path: Path, *, write: bool, backup_suffix: str
) -> list[dict[str, Any]]:
    generation_rows = _load_rows(generation_path, "generation")
    reasoning_rows = _load_rows(reasoning_path, "reasoning")
    kept_reasoning: list[dict[str, Any]] = []
    moved_to_generation: list[dict[str, Any]] = []
    for row in reasoning_rows:
        if row["reward_type"] == "judge":
            original_line = int(row["_reward_routing"]["source_line"])
            row.setdefault("sample_id", f"reasoning:{original_line}")
            row["_reward_routing"]["source_dataset"] = reasoning_path.name
            row["_reward_routing"]["original_source_line"] = original_line
            moved_to_generation.append(row)
        else:
            kept_reasoning.append(row)

    generation_rows.extend(moved_to_generation)
    for line_number, row in enumerate(generation_rows, 1):
        row["_reward_routing"]["source_line"] = line_number
    for line_number, row in enumerate(kept_reasoning, 1):
        row["_reward_routing"]["source_line"] = line_number

    reports = [
        _report(generation_path, "generation", generation_rows),
        _report(reasoning_path, "reasoning", kept_reasoning),
    ]
    reports[0]["moved_from_reasoning"] = len(moved_to_generation)
    reports[1]["moved_to_generation"] = len(moved_to_generation)
    if write:
        reports[0]["backup"] = _write_rows(generation_path, generation_rows, backup_suffix)
        reports[1]["backup"] = _write_rows(reasoning_path, kept_reasoning, backup_suffix)
    return reports


def process(path: Path, kind: str, *, write: bool, backup_suffix: str) -> dict[str, Any]:
    rows = _load_rows(path, kind)
    report = _report(path, kind, rows)
    if not write:
        return report

    report["backup"] = _write_rows(path, rows, backup_suffix)
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--generation", type=Path, required=True)
    parser.add_argument("--reasoning", type=Path, required=True)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--backup-suffix", default=".before_question_only_judge_20260823")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()

    reports = rebalance(
        args.generation,
        args.reasoning,
        write=args.write,
        backup_suffix=args.backup_suffix,
    )
    payload = {"version": "finance_rl_route_v2", "datasets": reports}
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
