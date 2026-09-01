#!/usr/bin/env python3
"""Rebalance reasoning RL data and derive medium variants from existing multi-step numeric rows.

The input JSONL is never modified. Existing ``multi_step_numerical_reasoning``
rows are downsampled to a configurable count. Medium variants are created only
from the dropped numeric rows by keeping the original question/images/gold
answer and adding:
  1) a short operation hint; and
  2) four numeric candidate results containing the original gold value.

This lowers retrieval/search difficulty without changing the verifier target.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import re
from collections import Counter, defaultdict
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from typing import Any

DEFAULT_ROOT = Path("/mnt/nas/bihaoran/qwen3vl")
DEFAULT_INPUT = DEFAULT_ROOT / "data/train_multi/train_rl_reasoning.jsonl"
DEFAULT_OUTPUT = DEFAULT_ROOT / "data/train_multi/train_rl_reasoning_medium_rebalanced.jsonl"
DEFAULT_AUDIT = DEFAULT_ROOT / "data/train_multi/train_rl_reasoning_medium_rebalanced.audit.json"

TARGET_TASK = "multi_step_numerical_reasoning"
_NUMBER_RE = re.compile(r"[-+]?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?")
_CJK_RE = re.compile(r"[\u3400-\u9fff]")
_ANSWER_MARKER_RE = re.compile(r"(?:答案|answer)\s*[:：]\s*", re.IGNORECASE)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def stable_hash(row: dict[str, Any], seed: int, salt: str) -> str:
    routing = row.get("_reward_routing") or {}
    identity = (
        row.get("sample_id")
        or row.get("id")
        or routing.get("source_line")
        or row.get("question")
        or user_text(row)
    )
    payload = f"{seed}\0{salt}\0{row.get('source', '')}\0{identity}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def user_text(row: dict[str, Any]) -> str:
    return "\n".join(
        str(message.get("content", ""))
        for message in row.get("messages", [])
        if message.get("role") == "user"
    ).strip()


def reference_text(row: dict[str, Any]) -> str:
    explicit = row.get("solution")
    if explicit not in (None, ""):
        return str(explicit).strip()
    for message in reversed(row.get("messages", [])):
        if message.get("role") == "assistant":
            return str(message.get("content", "")).strip()
    return str(row.get("reference") or "").strip()


def final_answer_text(row: dict[str, Any]) -> str:
    value = reference_text(row)
    markers = list(_ANSWER_MARKER_RE.finditer(value))
    if markers:
        value = value[markers[-1].end() :].strip()
    lines = [line.strip() for line in value.splitlines() if line.strip()]
    return lines[-1] if lines else value


def parse_numeric_answer(row: dict[str, Any]) -> tuple[Decimal, str, int] | None:
    if str(row.get("verifier_type", "")) not in {"numeric", "numeric_final"}:
        return None
    answer = final_answer_text(row)
    matches = list(_NUMBER_RE.finditer(answer))
    if not matches:
        return None
    match = matches[-1]
    token = match.group(0)
    try:
        value = Decimal(token.replace(",", ""))
    except InvalidOperation:
        return None
    decimals = len(token.split(".", 1)[1]) if "." in token else 0
    suffix = answer[match.end() :].strip()
    suffix_match = re.match(r"^(%|％|[^\s,，。;；:：]{1,12})", suffix)
    unit = suffix_match.group(1) if suffix_match else ""
    return value, unit, decimals


def render_number(value: Decimal, decimals: int, unit: str) -> str:
    quant = Decimal(1).scaleb(-decimals)
    rounded = value.quantize(quant, rounding=ROUND_HALF_UP)
    if decimals == 0:
        number = f"{rounded:.0f}"
    else:
        number = f"{rounded:.{decimals}f}"
    return f"{number}{unit}"


def candidate_values(
    gold: Decimal,
    decimals: int,
    unit: str,
    *,
    row: dict[str, Any],
    seed: int,
) -> list[str]:
    step = Decimal(1).scaleb(-decimals)
    magnitude = max(abs(gold), step)
    deltas = [
        max(step, magnitude * Decimal("0.10")),
        max(step, magnitude * Decimal("0.20")),
        max(step, magnitude * Decimal("0.05")),
        max(step, magnitude * Decimal("0.15")),
    ]
    raw = [
        gold - deltas[0],
        gold + deltas[0],
        gold - deltas[1],
        gold + deltas[1],
        gold - deltas[2],
        gold + deltas[2],
        -gold if gold != 0 else step,
    ]
    distractors: list[Decimal] = []
    seen = {render_number(gold, decimals, unit)}
    for value in raw:
        rendered = render_number(value, decimals, unit)
        if rendered in seen:
            continue
        seen.add(rendered)
        distractors.append(value)
        if len(distractors) == 3:
            break
    if len(distractors) < 3:
        for multiplier in (Decimal("0.5"), Decimal("1.5"), Decimal("2")):
            value = gold * multiplier
            rendered = render_number(value, decimals, unit)
            if rendered not in seen:
                seen.add(rendered)
                distractors.append(value)
            if len(distractors) == 3:
                break
    if len(distractors) < 3:
        for offset in (step, -step, step * 2, -step * 2, step * 5, -step * 5):
            value = gold + offset
            rendered = render_number(value, decimals, unit)
            if rendered not in seen:
                seen.add(rendered)
                distractors.append(value)
            if len(distractors) == 3:
                break
    if len(distractors) != 3:
        raise ValueError("unable to create three numeric distractors")

    values = [gold, *distractors]
    values.sort(
        key=lambda value: hashlib.sha256(
            f"{seed}\0options\0{stable_hash(row, seed, 'option')}\0{value}".encode("utf-8")
        ).hexdigest()
    )
    return [render_number(value, decimals, unit) for value in values]


def operation_hint(question: str, chinese: bool) -> str:
    lower = question.casefold()
    # Prefer the operation explicitly requested by the question. Metric names
    # such as "净利润增速" must not override "计算绝对差/平均值".
    if re.search(r"算术平均|平均值|average|mean", lower):
        return (
            "提示：先把相关数值求和，再除以对应项数。"
            if chinese
            else "Hint: sum the relevant values first, then divide by the number of terms."
        )
    if re.search(r"绝对差|差值|相差|差额|absolute difference|difference between", lower):
        return (
            "提示：先定位两个目标数值，再按题意做差；若要求绝对差则取绝对值。"
            if chinese
            else "Hint: identify the two target values first, subtract them, and take the absolute value when requested."
        )
    if re.search(r"合计|总和|总计|sum|total", lower):
        return (
            "提示：只提取题目要求的项目并逐项求和。"
            if chinese
            else "Hint: extract only the requested items and sum them."
        )
    if re.search(r"多少倍|倍数|ratio|how many times|represent in relation", lower):
        return (
            "提示：先定位两个关键数值，再按“目标值 ÷ 基准值”计算比例。"
            if chinese
            else "Hint: identify the two key values, then compute target divided by baseline."
        )
    if re.search(r"同比|环比|增幅|增长率|percentage (?:increase|decrease|change)|growth rate|percent change", lower):
        return (
            "提示：先定位基准值和比较值，再求差值并除以基准值。"
            if chinese
            else "Hint: identify the baseline and comparison values, then compute the difference and divide by the baseline."
        )
    if re.search(r"占比|百分比|percentage|percent", lower):
        return (
            "提示：先定位两个关键数值，再按“目标值 ÷ 基准值”计算比例。"
            if chinese
            else "Hint: identify the two key values, then compute target divided by baseline."
        )
    if re.search(r"change|increase|decrease", lower):
        return (
            "提示：先定位两个目标数值，再按题意完成所需变化量计算。"
            if chinese
            else "Hint: identify the two target values first, then compute the requested change."
        )
    return (
        "提示：先定位与问题直接相关的关键数值，再完成必要的 1–2 步计算。"
        if chinese
        else "Hint: locate the key values directly relevant to the question, then finish the required one or two arithmetic steps."
    )


def append_to_last_user_message(row: dict[str, Any], appendix: str) -> None:
    messages = row.get("messages") or []
    for message in reversed(messages):
        if message.get("role") != "user":
            continue
        content = message.get("content", "")
        if isinstance(content, str):
            message["content"] = content.rstrip() + "\n\n" + appendix
        elif isinstance(content, list):
            content.append({"type": "text", "text": "\n\n" + appendix})
        else:
            message["content"] = str(content) + "\n\n" + appendix
        return
    raise ValueError("row has no user message")


def derive_medium(row: dict[str, Any], seed: int) -> dict[str, Any]:
    parsed = parse_numeric_answer(row)
    if parsed is None:
        raise ValueError("row does not have a numeric gold answer")
    gold, unit, decimals = parsed
    options = candidate_values(gold, decimals, unit, row=row, seed=seed)
    question = user_text(row)
    chinese = bool(_CJK_RE.search(question))
    labels = "ABCD"
    if chinese:
        appendix = (
            "难度提示（由原题简化）：\n"
            f"{operation_hint(question, True)}\n"
            "候选结果仅用于缩小计算范围，请自行核对：\n"
            + "\n".join(f"{label}. {value}" for label, value in zip(labels, options))
            + "\n最后仍直接输出正确的数值答案，不要输出选项字母。"
        )
    else:
        appendix = (
            "Difficulty hint (simplified from the original problem):\n"
            f"{operation_hint(question, False)}\n"
            "Candidate results are provided only to narrow the calculation; verify them yourself:\n"
            + "\n".join(f"{label}. {value}" for label, value in zip(labels, options))
            + "\nStill output the correct numeric answer directly, not the option letter."
        )

    derived = copy.deepcopy(row)
    original_sample_id = str(
        row.get("sample_id")
        or row.get("id")
        or (row.get("_reward_routing") or {}).get("source_line")
        or stable_hash(row, seed, "medium-id")[:16]
    )
    append_to_last_user_message(derived, appendix)
    if "question" in derived:
        derived["question"] = user_text(derived)
    derived["sample_id"] = f"{original_sample_id}:medium_v1"
    derived["_medium_derivation"] = {
        "version": "multi_step_medium_v1",
        "method": "operation_hint_plus_numeric_candidates",
        "derived_from_sample_id": original_sample_id,
        "derived_from_task": row.get("task"),
        "derived_from_source": row.get("source"),
        "candidate_count": 4,
        "gold_preserved": True,
    }
    return derived


def proportional_quotas(groups: dict[str, list[int]], count: int) -> dict[str, int]:
    total = sum(len(indices) for indices in groups.values())
    if count > total:
        raise ValueError(f"requested {count} rows from only {total} available")
    raw = {key: count * len(indices) / total for key, indices in groups.items()}
    quotas = {key: min(len(groups[key]), int(math.floor(value))) for key, value in raw.items()}
    remaining = count - sum(quotas.values())
    order = sorted(
        groups,
        key=lambda key: (-(raw[key] - math.floor(raw[key])), key),
    )
    while remaining:
        progressed = False
        for key in order:
            if quotas[key] < len(groups[key]):
                quotas[key] += 1
                remaining -= 1
                progressed = True
                if remaining == 0:
                    break
        if not progressed:
            raise RuntimeError("quota allocation stalled")
    return quotas


def stratified_indices(
    rows: list[dict[str, Any]],
    candidate_indices: list[int],
    count: int,
    seed: int,
    salt: str,
) -> set[int]:
    groups: dict[str, list[int]] = defaultdict(list)
    for index in candidate_indices:
        row = rows[index]
        key = f"{row.get('source', '')}\0{row.get('verifier_type', '')}"
        groups[key].append(index)
    quotas = proportional_quotas(groups, count)
    selected: set[int] = set()
    for key, indices in groups.items():
        indices.sort(key=lambda index: stable_hash(rows[index], seed, f"{salt}:{key}"))
        selected.update(indices[: quotas[key]])
    return selected


def build_dataset(
    rows: list[dict[str, Any]],
    *,
    keep_original_count: int,
    medium_count: int,
    seed: int,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    multi_indices = [i for i, row in enumerate(rows) if row.get("task") == TARGET_TASK]
    if len(multi_indices) < keep_original_count:
        raise ValueError(
            f"only {len(multi_indices)} {TARGET_TASK} rows found, need {keep_original_count}"
        )

    kept = stratified_indices(
        rows,
        multi_indices,
        keep_original_count,
        seed,
        "keep-original",
    )
    dropped = [index for index in multi_indices if index not in kept]
    eligible_medium = [
        index
        for index in dropped
        if parse_numeric_answer(rows[index]) is not None
    ]
    if len(eligible_medium) < medium_count:
        raise ValueError(
            f"only {len(eligible_medium)} dropped numeric rows can be mediumized, need {medium_count}"
        )
    medium_source_indices = stratified_indices(
        rows,
        eligible_medium,
        medium_count,
        seed,
        "derive-medium",
    )

    output = [
        copy.deepcopy(row)
        for index, row in enumerate(rows)
        if row.get("task") != TARGET_TASK or index in kept
    ]
    medium_rows = [
        derive_medium(rows[index], seed)
        for index in sorted(medium_source_indices)
    ]
    output.extend(medium_rows)

    audit = {
        "input_rows": len(rows),
        "input_multi_step_numerical_reasoning": len(multi_indices),
        "kept_original_multi_step_numerical_reasoning": len(kept),
        "dropped_original_multi_step_numerical_reasoning": len(dropped),
        "eligible_dropped_numeric_for_medium": len(eligible_medium),
        "added_medium_rows": len(medium_rows),
        "output_rows": len(output),
        "output_multi_step_numerical_reasoning": sum(
            row.get("task") == TARGET_TASK for row in output
        ),
        "seed": seed,
        "medium_method": "operation_hint_plus_numeric_candidates",
        "task_counts": dict(
            sorted(Counter(str(row.get("task", "")) for row in output).items())
        ),
        "kept_original_source_counts": dict(
            sorted(Counter(str(rows[index].get("source", "")) for index in kept).items())
        ),
        "medium_source_counts": dict(
            sorted(Counter(str(rows[index].get("source", "")) for index in medium_source_indices).items())
        ),
    }
    return output, audit


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--audit", type=Path, default=DEFAULT_AUDIT)
    parser.add_argument("--keep-original-count", type=int, default=3000)
    parser.add_argument("--medium-count", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=20260827)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    rows = read_jsonl(args.input)
    output, audit = build_dataset(
        rows,
        keep_original_count=args.keep_original_count,
        medium_count=args.medium_count,
        seed=args.seed,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as handle:
        for row in output:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    args.audit.parent.mkdir(parents=True, exist_ok=True)
    args.audit.write_text(
        json.dumps(audit, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(audit, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
