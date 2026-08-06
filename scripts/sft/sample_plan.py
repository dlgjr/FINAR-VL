"""Deterministic task sampling plans for SFT."""

from __future__ import annotations

import argparse
import json
import os
import random
from pathlib import Path
from typing import Any


DEFAULT_MULTI_RATIO = 0.45
ALPHA_SCHEDULE = ((0, 1000, 0.45), (1000, 3000, 0.40), (3000, float("inf"), 0.35))
HEAD_DOWNWEIGHT = {
    "chart_qa": 0.30,
    "table_math_qa": 0.35,
    "financial_multiple_choice": 0.25,
    "financial_headline_classification": 0.40,
    "financial_event_extraction": 0.60,
    "stock_movement_prediction": 0.40,
    "general_dialogue": 0.35,
}
BENCHMARK_UPWEIGHT = {
    "basic_arithmetic_metrics": 1.3,
    "candlestick_trend_analysis": 1.5,
    "candlestick_ohlc_analysis": 1.6,
    "financial_chart_qa": 1.8,
    "document_ocr_qa": 1.3,
    "ocr_qa": 1.2,
    "entity_extraction_classification": 1.5,
    "evidence_retrieval": 2.5,
    "long_document_cross_page_qa": 2.5,
    "long_document_cross_page": 2.5,
    "financial_multipage_qa": 2.0,
    "document_finance_numeric_qa": 2.0,
    "table_math_reasoning": 2.2,
    "financial_numerical_reasoning": 2.2,
    "multi_table_reasoning": 2.5,
    "single_table_qa": 1.5,
    "table_statistics_and_comparison": 1.8,
    "compliance_safety_suitability": 1.6,
    "risk_sentiment_policy": 1.8,
    "investment_advice_strategy": 1.6,
    "portfolio_and_risk_management": 1.6,
    "financial_audit_and_controls": 1.6,
    "multimodal_financial_knowledge": 1.8,
    "financial_causal_event_reasoning": 1.8,
    "financial_causal_explanation": 1.8,
    "financial_relation_extraction": 2.2,
}
TASK_TO_FAMILY = {
    "chart_qa": "chart_understanding",
    "financial_chart_qa": "chart_understanding",
    "figure_qa": "chart_understanding",
    "candlestick_trend_analysis": "candlestick",
    "candlestick_ohlc_analysis": "candlestick",
    "table_math_qa": "single_table_reasoning",
    "table_math_reasoning": "single_table_reasoning",
    "single_table_qa": "single_table_reasoning",
    "hierarchical_table_qa": "single_table_reasoning",
    "table_statistics_and_comparison": "single_table_reasoning",
    "multi_table_reasoning": "multi_table_reasoning",
    "document_ocr_qa": "ocr",
    "ocr_qa": "ocr",
    "span_extraction": "ocr",
    "multi_span_extraction": "ocr",
    "table_structure_detection": "ocr",
    "long_document_cross_page_qa": "cross_page",
    "financial_multipage_qa": "cross_page",
    "long_document_cross_page": "cross_page",
    "evidence_retrieval": "evidence_retrieval",
}
FAMILY_CAP = {
    "chart_understanding": 0.12,
    "candlestick": 0.08,
    "single_table_reasoning": 0.12,
    "multi_table_reasoning": 0.04,
    "ocr": 0.10,
    "cross_page": 0.08,
    "evidence_retrieval": 0.08,
}
MAX_TASK_RATIO = 0.08
SMALL_TASK_MIN_N = 100
SMALL_TASK_MAX_N = 499
SMALL_TASK_RATIO = 0.02
TINY_TASK_MAX_N = 100
TINY_POOL_RATIO = 0.005
TINY_MAX_REPEAT = 2
UNKNOWN_TASK = "__unknown__"
_TINY_POOL_KEY = "__tiny_pool__"


def task_b_weight(task: str) -> float:
    if task in HEAD_DOWNWEIGHT:
        return HEAD_DOWNWEIGHT[task]
    if task in BENCHMARK_UPWEIGHT:
        return BENCHMARK_UPWEIGHT[task]
    return 1.0


def family_for_task(task: str) -> str:
    return TASK_TO_FAMILY.get(task, task)


def alpha_for_step(step: int) -> float:
    for start, end, alpha in ALPHA_SCHEDULE:
        if start <= step < end:
            return alpha
    raise ValueError(f"step {step} outside alpha schedule")


def scan_task_index(path: Path) -> tuple[dict[str, list[int]], int]:
    task_index: dict[str, list[int]] = {}
    total = 0
    with path.open(encoding="utf-8") as handle:
        for line_no, line in enumerate(handle):
            row = json.loads(line)
            task = str(row.get("task") or UNKNOWN_TASK)
            task_index.setdefault(task, []).append(line_no)
            total += 1
    return task_index, total


def _load_training_template(model: str, model_type: str, max_length: int):
    from swift.model import get_model_processor
    from swift.template import get_template

    _, processor = get_model_processor(model, model_type=model_type, load_model=False)
    # ms-swift represents the SFT `delete` strategy as template-level `raise`;
    # scan_encoded_index drops the resulting MaxLengthError rows.
    template = get_template(
        processor,
        max_length=max_length,
        truncation_strategy="raise",
        loss_scale="default",
    )
    template.set_mode("train")
    return template


def _supervision_tokens(template, row: dict[str, Any]) -> int:
    encoded = template.encode(row)
    if isinstance(encoded, list):
        raise ValueError("truncation produced multiple encoded rows")
    labels = encoded.get("labels")
    if labels is None:
        return 0
    if hasattr(labels, "reshape"):
        labels = labels.reshape(-1)
    if hasattr(labels, "tolist"):
        labels = labels.tolist()
    if isinstance(labels, list):
        values = labels
        while values and isinstance(values[0], list):
            values = [item for nested in values for item in nested]
    else:
        values = [labels]
    return sum(int(value != -100) for value in values)


def scan_encoded_index(
    path: Path,
    *,
    modality: str,
    model: str | None,
    model_type: str = "qwen3_vl",
    max_length: int = 49152,
) -> tuple[dict[str, list[dict[str, Any]]], int, int, list[dict[str, Any]], dict[str, int]]:
    template = _load_training_template(model, model_type, max_length) if model else None
    task_index: dict[str, list[dict[str, Any]]] = {}
    cache_rows: list[dict[str, Any]] = []
    stats = {"raw": 0, "retained": 0, "eligible": 0, "deleted": 0, "encoding_failed": 0, "zero_supervision": 0}
    with path.open(encoding="utf-8") as handle:
        for raw_index, line in enumerate(handle):
            if not line.strip():
                continue
            stats["raw"] += 1
            row = json.loads(line)
            task = str(row.get("task") or UNKNOWN_TASK)
            if template is None:
                token_count = 1
            else:
                try:
                    token_count = _supervision_tokens(template, row)
                except Exception as exc:
                    try:
                        from swift.template import MaxLengthError
                    except ImportError:
                        MaxLengthError = ()
                    if MaxLengthError and isinstance(exc, MaxLengthError):
                        stats["deleted"] += 1
                    else:
                        stats["encoding_failed"] += 1
                    continue
            dataset_index = stats["retained"]
            stats["retained"] += 1
            family = family_for_task(task)
            cache_row = {
                "modality": modality,
                "dataset_index": dataset_index,
                "raw_index": raw_index,
                "task": task,
                "family": family,
                "assistant_token_count": int(token_count),
                "eligible": bool(token_count > 0),
            }
            cache_rows.append(cache_row)
            if token_count <= 0:
                stats["zero_supervision"] += 1
                continue
            stats["eligible"] += 1
            task_index.setdefault(task, []).append(
                {
                    "index": dataset_index,
                    "raw_index": raw_index,
                    "task": task,
                    "family": family,
                    "assistant_token_count": int(token_count),
                }
            )
    return task_index, stats["retained"], stats["eligible"], cache_rows, stats


def task_cap(count: int, quota: int) -> int:
    if count < TINY_TASK_MAX_N:
        return max(1, int(quota * TINY_POOL_RATIO))
    if SMALL_TASK_MIN_N <= count <= SMALL_TASK_MAX_N:
        ratio = SMALL_TASK_RATIO
    else:
        ratio = MAX_TASK_RATIO
    return max(1, int(quota * ratio))


def allocate_quotas(
    counts: dict[str, int],
    quota: int,
    alpha: float,
    means: dict[str, float] | None = None,
) -> tuple[dict[str, int], int, list[str]]:
    means = means or {task: 1.0 for task in counts}
    tiny_tasks = sorted(task for task, count in counts.items() if count < TINY_TASK_MAX_N)
    sampling_weights = {
        task: (count**alpha) * task_b_weight(task) / means[task]
        for task, count in counts.items()
        if task not in tiny_tasks
    }
    if tiny_tasks:
        sampling_weights[_TINY_POOL_KEY] = sum(
            (counts[task]**alpha) * task_b_weight(task) / means[task]
            for task in tiny_tasks
        )

    def cap_fn(task: str) -> int:
        if task == _TINY_POOL_KEY:
            return quota if not any(task_name not in tiny_tasks for task_name in counts) else max(1, int(quota * TINY_POOL_RATIO))
        return task_cap(counts[task], quota)

    pending = dict(sampling_weights)
    values: dict[str, float] = {}
    remaining = float(quota)
    for _ in range(len(pending) + 1):
        total = sum(pending.values())
        if total <= 0 or remaining <= 1e-9:
            break
        for task in list(pending):
            raw = remaining * pending[task] / total
            take = min(raw, cap_fn(task))
            values[task] = values.get(task, 0.0) + take
            if raw >= cap_fn(task) - 1e-9:
                del pending[task]
        remaining = quota - sum(values.values())
    floors = {task: int(value) for task, value in values.items()}
    deficit = quota - sum(floors.values())
    order = sorted(values, key=lambda task: (values[task] - int(values[task]), task), reverse=True)
    for task in order:
        if deficit <= 0:
            break
        if floors[task] < cap_fn(task):
            floors[task] += 1
            deficit -= 1
    if deficit > 0:
        raise ValueError(f"unable to allocate quota={quota}: task caps sum below quota")
    tiny_quota = int(floors.pop(_TINY_POOL_KEY, 0))
    return floors, tiny_quota, tiny_tasks


def sample_task_indices(indices: list[int], quota: int, rng: random.Random) -> list[int]:
    pool = list(indices)
    rng.shuffle(pool)
    if not pool or quota <= 0:
        return []
    result: list[int] = []
    while len(result) < quota:
        if not pool:
            pool = list(indices)
            rng.shuffle(pool)
        result.append(pool.pop())
    return result


class PersistentCursor:
    def __init__(self, seed: int):
        self.seed = seed
        self.states: dict[tuple[str, str], dict[str, Any]] = {}

    def _state(self, modality: str, task: str, entries: list[dict[str, Any]]) -> dict[str, Any]:
        key = (modality, task)
        state = self.states.get(key)
        if state is None:
            state = {"pool": list(entries), "cursor": 0, "pending": []}
            stable = sum((index + 1) * ord(char) for index, char in enumerate(f"{modality}:{task}"))
            random.Random(self.seed + stable).shuffle(state["pool"])
            self.states[key] = state
        return state

    def peek(self, modality: str, task: str, entries: list[dict[str, Any]]) -> dict[str, Any]:
        state = self._state(modality, task, entries)
        if state["pending"]:
            return state["pending"][0]
        if state["cursor"] >= len(state["pool"]):
            state["pool"] = list(entries)
            state["cursor"] = 0
            random.Random(self.seed + len(state["pool"]) + state.get("reshuffles", 0)).shuffle(state["pool"])
            state["reshuffles"] = state.get("reshuffles", 0) + 1
        return state["pool"][state["cursor"]]

    def draw(self, modality: str, task: str, entries: list[dict[str, Any]], count: int) -> list[dict[str, Any]]:
        state = self._state(modality, task, entries)
        picked = []
        for _ in range(count):
            if state["pending"]:
                picked.append(state["pending"].pop(0))
            else:
                picked.append(self.peek(modality, task, entries))
                state["cursor"] += 1
        return picked

    def put_back(self, modality: str, task: str, entries: list[dict[str, Any]], entry: dict[str, Any]) -> None:
        self._state(modality, task, entries)["pending"].insert(0, entry)


def _sample_tiny_pool(
    tiny_tasks: list[str],
    task_index: dict[str, list[dict[str, Any]]],
    quota: int,
    means: dict[str, float],
    usage: dict[tuple[str, int], int],
    rng: random.Random,
    *,
    modality: str,
    alpha: float,
) -> list[dict[str, Any]]:
    picked: list[dict[str, Any]] = []
    eligible = {
        task: [entry for entry in task_index[task] if usage.get((modality, entry["index"]), 0) < TINY_MAX_REPEAT]
        for task in tiny_tasks
    }
    eligible = {task: rows for task, rows in eligible.items() if rows}
    while len(picked) < quota and eligible:
        tasks = sorted(eligible)
        weights = [len(task_index[task]) ** alpha * task_b_weight(task) / means[task] for task in tasks]
        task = rng.choices(tasks, weights=weights, k=1)[0]
        entry = rng.choice(eligible[task])
        eligible[task].remove(entry)
        if not eligible[task]:
            del eligible[task]
        picked.append(entry)
    for entry in picked:
        key = (modality, entry["index"])
        usage[key] = usage.get(key, 0) + 1
    return picked


def sample_tiny_pool(
    tiny_tasks: list[str],
    task_index: dict[str, list[int]],
    quota: int,
    alpha: float,
    usage: dict[tuple[str, int], int],
    rng: random.Random,
    *,
    modality: str,
) -> list[int]:
    rows = {
        task: [
            {
                "index": index,
                "raw_index": index,
                "task": task,
                "family": family_for_task(task),
                "assistant_token_count": 1,
            }
            for index in indices
        ]
        for task, indices in task_index.items()
    }
    result = _sample_tiny_pool(
        tiny_tasks, rows, quota, {task: 1.0 for task in tiny_tasks}, usage, rng,
        modality=modality, alpha=alpha,
    )
    return [entry["index"] for entry in result]


def _distribution(samples: list[dict[str, Any]]) -> dict[str, Any]:
    tasks: dict[str, dict[str, int]] = {}
    families: dict[str, dict[str, int]] = {}
    for entry in samples:
        token = int(entry["assistant_token_count"])
        task = entry["task"]
        family = entry["family"]
        tasks.setdefault(task, {"samples": 0, "assistant_tokens": 0})
        families.setdefault(family, {"samples": 0, "assistant_tokens": 0})
        tasks[task]["samples"] += 1
        tasks[task]["assistant_tokens"] += token
        families[family]["samples"] += 1
        families[family]["assistant_tokens"] += token
    total_samples = len(samples)
    total_tokens = sum(v["assistant_tokens"] for v in tasks.values())
    for grouped in (tasks, families):
        for values in grouped.values():
            values["sample_ratio"] = values["samples"] / total_samples if total_samples else 0.0
            values["token_ratio"] = values["assistant_tokens"] / total_tokens if total_tokens else 0.0
    return {
        "samples": total_samples,
        "assistant_tokens": total_tokens,
        "sample_ratio": 1.0 if total_samples else 0.0,
        "token_ratio": 1.0 if total_tokens else 0.0,
        "tasks": tasks,
        "families": families,
    }


def _family_violation(samples: list[dict[str, Any]]) -> tuple[str | None, float, float]:
    total = sum(int(entry["assistant_token_count"]) for entry in samples)
    if total <= 0:
        return None, 0.0, 0.0
    grouped: dict[str, list[dict[str, Any]]] = {}
    for entry in samples:
        grouped.setdefault(entry["family"], []).append(entry)
    violations = []
    for family, rows in grouped.items():
        cap = FAMILY_CAP.get(family)
        if cap is None:
            continue
        tokens = sum(int(row["assistant_token_count"]) for row in rows)
        excess = tokens - cap * total
        tolerance = max(int(row["assistant_token_count"]) for row in rows)
        if excess > tolerance:
            violations.append((excess, family, tolerance))
    if not violations:
        return None, 0.0, 0.0
    excess, family, tolerance = max(violations, key=lambda value: (value[0], value[1]))
    return family, excess, tolerance


def _repair_family_caps(
    samples: list[dict[str, Any]],
    task_index: dict[str, list[dict[str, Any]]],
    quotas: dict[str, int],
    tiny_tasks: set[str],
    tiny_quota: int,
    cursor: PersistentCursor,
    *,
    modality: str,
    usage: dict[tuple[str, int], int],
) -> list[dict[str, Any]]:
    selected = {(entry["index"], entry["task"]) for entry in samples}
    while True:
        family, excess, tolerance = _family_violation(samples)
        if family is None:
            return samples
        candidates: list[tuple[float, str, int, dict[str, Any], dict[str, Any]]] = []
        old_rows = [row for row in samples if row["family"] == family]
        total_tokens = sum(int(row["assistant_token_count"]) for row in samples)
        family_tokens = sum(int(row["assistant_token_count"]) for row in old_rows)
        cap_ratio = FAMILY_CAP[family]
        for old in sorted(old_rows, key=lambda row: (-int(row["assistant_token_count"]), row["task"], row["index"])):
            old_tokens = int(old["assistant_token_count"])
            old_pool = old["task"] in tiny_tasks
            for task in sorted(task_index):
                if (task in tiny_tasks) != old_pool:
                    continue
                cap = tiny_quota if old_pool else task_cap(len(task_index[task]), len(samples))
                if task != old["task"] and quotas.get(task, 0) >= cap:
                    continue
                if task == old["task"] and quotas.get(task, 0) > cap:
                    continue
                if task in tiny_tasks:
                    rows = [row for row in task_index[task] if usage.get((modality, row["index"]), 0) < TINY_MAX_REPEAT]
                    rows = [row for row in rows if (row["index"], row["task"]) not in selected]
                    if not rows:
                        continue
                    candidate = min(rows, key=lambda row: (int(row["assistant_token_count"]), row["task"], row["index"]))
                else:
                    candidate = cursor.peek(modality, task, task_index[task])
                    if (candidate["index"], candidate["task"]) in selected:
                        continue
                candidate_tokens = int(candidate["assistant_token_count"])
                candidate_in_family = candidate["family"] == family
                new_total = total_tokens - old_tokens + candidate_tokens
                new_family_tokens = family_tokens - old_tokens + (candidate_tokens if candidate_in_family else 0)
                new_excess = new_family_tokens - cap_ratio * new_total
                score = excess - max(0.0, new_excess)
                if score > 0:
                    candidates.append((score, task, int(candidate["index"]), old, candidate))
        if not candidates:
            if excess <= tolerance:
                return samples
            raise ValueError(f"family cap cannot be satisfied for family={family}")
        best_score = max(item[0] for item in candidates)
        _, task, _, old, candidate = min(
            (item for item in candidates if item[0] == best_score),
            key=lambda item: (item[1], item[2]),
        )
        if candidate["task"] in tiny_tasks:
            candidate = dict(candidate, tiny_pool=True)
        samples[samples.index(old)] = candidate
        quotas[old["task"]] = quotas.get(old["task"], 0) - 1
        quotas[candidate["task"]] = quotas.get(candidate["task"], 0) + 1
        selected.remove((old["index"], old["task"]))
        selected.add((candidate["index"], candidate["task"]))
        if old["task"] in tiny_tasks:
            old_key = (modality, old["index"])
            usage[old_key] = max(0, usage.get(old_key, 0) - 1)
        if candidate["task"] in tiny_tasks:
            candidate_key = (modality, candidate["index"])
            usage[candidate_key] = usage.get(candidate_key, 0) + 1
        if candidate["task"] not in tiny_tasks:
            cursor.draw(modality, candidate["task"], task_index[candidate["task"]], 1)
            cursor.put_back(modality, old["task"], task_index[old["task"]], old)


def _sample_modality(
    task_index: dict[str, list[dict[str, Any]]],
    quota: int,
    alpha: float,
    means: dict[str, float],
    usage: dict[tuple[str, int], int],
    rng: random.Random,
    cursor: PersistentCursor,
    *,
    modality: str,
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    counts = {task: len(rows) for task, rows in task_index.items()}
    allocations, tiny_quota, tiny_tasks = allocate_quotas(counts, quota, alpha, means)
    samples: list[dict[str, Any]] = []
    for task in sorted(allocations):
        samples.extend(cursor.draw(modality, task, task_index[task], allocations[task]))
    tiny_samples = _sample_tiny_pool(
        tiny_tasks, task_index, tiny_quota, means, usage, rng, modality=modality, alpha=alpha
    )
    tiny_samples = [dict(row, tiny_pool=True) for row in tiny_samples]
    samples.extend(tiny_samples)
    quotas = dict(allocations)
    quotas[_TINY_POOL_KEY] = tiny_quota
    shortfall = quota - len(samples)
    if shortfall > 0:
        capacities = {
            task: max(0, task_cap(counts[task], quota) - allocations[task])
            for task in allocations
        }
        pending = {
            task: counts[task] ** alpha * task_b_weight(task) / means[task]
            for task, capacity in capacities.items()
            if capacity > 0
        }
        while shortfall > 0 and pending:
            total = sum(pending.values())
            if total <= 0:
                break
            for task in list(pending):
                if shortfall <= 0:
                    break
                take = min(
                    capacities[task],
                    shortfall,
                    max(1, int(shortfall * pending[task] / total)),
                )
                samples.extend(cursor.draw(modality, task, task_index[task], take))
                quotas[task] = quotas.get(task, 0) + take
                capacities[task] -= take
                shortfall -= take
                if capacities[task] <= 0:
                    del pending[task]
        if shortfall > 0:
            raise ValueError(f"cannot cover tiny shortfall {shortfall}")
    _repair_family_caps(
        samples,
        task_index,
        quotas,
        set(tiny_tasks),
        tiny_quota,
        cursor,
        modality=modality,
        usage=usage,
    )
    rng.shuffle(samples)
    return samples, quotas


def _split_uneven(count: int, parts: int) -> list[int]:
    base, extra = divmod(count, parts)
    return [base + 1 if index < extra else base for index in range(parts)]


def build_block(
    *,
    block_id: int,
    start_step: int,
    steps: int,
    global_batch_size: int,
    dp_world_size: int,
    per_device_batch: int,
    grad_acc: int,
    seed: int,
    multi_ratio: float = DEFAULT_MULTI_RATIO,
    multi_index: dict[str, list[dict[str, Any]]] | dict[str, list[int]],
    text_index: dict[str, list[dict[str, Any]]] | dict[str, list[int]],
    tiny_usage: dict[tuple[str, int], int],
    cursor: PersistentCursor | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any], dict[tuple[str, int], int]]:
    rng = random.Random(seed * 100_000 + block_id)
    cursor = cursor or PersistentCursor(seed * 100_000)
    alpha = alpha_for_step(start_step)

    def normalize(index: dict[str, list[Any]], modality: str) -> dict[str, list[dict[str, Any]]]:
        return {
            task: [
                row if isinstance(row, dict) else {
                    "index": int(row),
                    "raw_index": int(row),
                    "task": task,
                    "family": family_for_task(task),
                    "assistant_token_count": 1,
                }
                for row in rows
            ]
            for task, rows in index.items()
        }

    multi_index = normalize(multi_index, "multi")
    text_index = normalize(text_index, "text")
    multi_quota = int(steps * global_batch_size * multi_ratio + 0.5)
    text_quota = steps * global_batch_size - multi_quota
    multi_means = {task: sum(row["assistant_token_count"] for row in rows) / len(rows) for task, rows in multi_index.items()}
    text_means = {task: sum(row["assistant_token_count"] for row in rows) / len(rows) for task, rows in text_index.items()}
    multi_samples, multi_quotas = _sample_modality(multi_index, multi_quota, alpha, multi_means, tiny_usage, rng, cursor, modality="multi")
    text_samples, text_quotas = _sample_modality(text_index, text_quota, alpha, text_means, tiny_usage, rng, cursor, modality="text")

    micro_steps = steps * grad_acc
    per_micro = dp_world_size * per_device_batch
    multi_sizes: list[int] = []
    for step_multi in _split_uneven(multi_quota, steps):
        step_sizes = _split_uneven(step_multi, grad_acc)
        rng.shuffle(step_sizes)
        multi_sizes.extend(step_sizes)
    entries: list[dict[str, Any]] = []
    multi_pos = text_pos = 0
    for micro_index in range(micro_steps):
        take_multi = multi_sizes[micro_index]
        micro = [(row, "multi") for row in multi_samples[multi_pos:multi_pos + take_multi]]
        micro.extend((row, "text") for row in text_samples[text_pos:text_pos + per_micro - take_multi])
        multi_pos += take_multi
        text_pos += per_micro - take_multi
        rng.shuffle(micro)
        for position, (row, modality) in enumerate(micro):
            entries.append({
                "block": block_id,
                "micro_step": start_step * grad_acc + micro_index,
                "position_in_micro_step": position,
                "modality": modality,
                "task": row["task"],
                "family": row["family"],
                "index": row["index"],
                "raw_index": row.get("raw_index", row["index"]),
                "assistant_token_count": int(row["assistant_token_count"]),
                "tiny_pool": bool(row.get("tiny_pool", False)),
                "pool": _TINY_POOL_KEY if row.get("tiny_pool", False) else "regular",
            })
    block_info = {
        "block_id": block_id,
        "start_step": start_step,
        "steps": steps,
        "alpha": alpha,
        "quotas": {"multi": multi_quotas, "text": text_quotas},
        "planned": {
            "multi": _distribution([entry for entry in entries if entry["modality"] == "multi"]),
            "text": _distribution([entry for entry in entries if entry["modality"] == "text"]),
        },
    }
    return entries, block_info, tiny_usage


def generate_plan(
    *,
    train_multi: Path,
    train_text: Path,
    output_dir: Path,
    global_batch_size: int,
    dp_world_size: int,
    per_device_batch: int = 1,
    grad_acc: int,
    seed: int,
    multi_ratio: float = DEFAULT_MULTI_RATIO,
    max_steps: int | None = None,
    epochs: int = 1,
    steps_per_block: int = 500,
    model: str | None = None,
    model_type: str = "qwen3_vl",
    max_length: int = 49152,
) -> dict[str, Any]:
    if not 0.0 < multi_ratio < 1.0:
        raise ValueError(f"multi_ratio must be between 0 and 1, got {multi_ratio}")
    if global_batch_size != dp_world_size * per_device_batch * grad_acc:
        raise ValueError("global_batch_size must equal dp_world_size * per_device_batch * grad_acc")
    if per_device_batch != 1:
        raise ValueError("sample plan actual accounting requires per_device_batch=1")
    output_dir.mkdir(parents=True, exist_ok=True)
    multi_index, dataset_n_multi, eligible_n_multi, multi_cache, multi_stats = scan_encoded_index(
        train_multi, modality="multi", model=model, model_type=model_type, max_length=max_length
    )
    text_index, dataset_n_text, eligible_n_text, text_cache, text_stats = scan_encoded_index(
        train_text, modality="text", model=model, model_type=model_type, max_length=max_length
    )
    (output_dir / "token_cache_multi.jsonl").write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in multi_cache), encoding="utf-8"
    )
    (output_dir / "token_cache_text.jsonl").write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in text_cache), encoding="utf-8"
    )
    if max_steps is None:
        max_steps = (5 * eligible_n_multi + eligible_n_text) * epochs // global_batch_size
    total_blocks = (max_steps + steps_per_block - 1) // steps_per_block
    tiny_usage: dict[tuple[str, int], int] = {}
    cursor = PersistentCursor(seed * 100_000)
    blocks: list[dict[str, Any]] = []
    for block_id in range(total_blocks):
        start_step = block_id * steps_per_block
        steps = min(steps_per_block, max_steps - start_step)
        entries, block_info, tiny_usage = build_block(
            block_id=block_id, start_step=start_step, steps=steps,
            global_batch_size=global_batch_size, dp_world_size=dp_world_size,
            per_device_batch=per_device_batch, grad_acc=grad_acc, seed=seed,
            multi_ratio=multi_ratio, multi_index=multi_index, text_index=text_index,
            tiny_usage=tiny_usage, cursor=cursor,
        )
        with (output_dir / f"block_{block_id:04d}.jsonl").open("w", encoding="utf-8") as handle:
            for entry in entries:
                handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
        blocks.append(block_info)
    meta = {
        "max_steps": max_steps, "total_blocks": total_blocks, "steps_per_block": steps_per_block,
        "N_multi": dataset_n_multi, "N_text": dataset_n_text,
        "eligible_N_multi": eligible_n_multi, "eligible_N_text": eligible_n_text,
        "dataset_stats": {"multi": multi_stats, "text": text_stats},
        "global_batch_size": global_batch_size, "dp_world_size": dp_world_size,
        "per_device_batch": per_device_batch, "grad_acc": grad_acc, "seed": seed,
        "epochs": epochs, "multi_ratio": multi_ratio, "text_ratio": 1.0 - multi_ratio,
        "model": model, "model_type": model_type, "max_length": max_length,
        "truncation_strategy": "delete",
        "image_max_token_num": os.environ.get("IMAGE_MAX_TOKEN_NUM", "512"),
        "family_cap": FAMILY_CAP, "blocks": blocks,
        "tiny_usage": {f"{modality}:{index}": count for (modality, index), count in tiny_usage.items()},
    }
    (output_dir / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (output_dir / ".ready").write_text("ready\n", encoding="utf-8")
    return meta


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="generate deterministic SFT sampling plan")
    parser.add_argument("--train-multi", type=Path, required=True)
    parser.add_argument("--train-text", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--global-batch-size", type=int, default=24)
    parser.add_argument("--dp-world-size", type=int, default=12)
    parser.add_argument("--per-device-batch", type=int, default=1)
    parser.add_argument("--grad-acc", type=int, default=2)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--multi-ratio", type=float, default=DEFAULT_MULTI_RATIO)
    parser.add_argument("--max-steps", type=int, default=None)
    parser.add_argument("--epochs", type=int, default=1)
    parser.add_argument("--steps-per-block", type=int, default=500)
    parser.add_argument("--model", "--base-model", dest="model", type=str, default=None)
    parser.add_argument("--model-type", "--model_type", dest="model_type", type=str, default="qwen3_vl")
    parser.add_argument("--max-length", "--max_length", dest="max_length", type=int, default=49152)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    meta = generate_plan(
        train_multi=args.train_multi, train_text=args.train_text, output_dir=args.output_dir,
        global_batch_size=args.global_batch_size, dp_world_size=args.dp_world_size,
        per_device_batch=args.per_device_batch, grad_acc=args.grad_acc, seed=args.seed,
        multi_ratio=args.multi_ratio, max_steps=args.max_steps, epochs=args.epochs,
        steps_per_block=args.steps_per_block, model=args.model, model_type=args.model_type,
        max_length=args.max_length,
    )
    print(
        f"sample_plan n_multi={meta['N_multi']} n_text={meta['N_text']} "
        f"eligible_multi={meta['eligible_N_multi']} eligible_text={meta['eligible_N_text']} "
        f"max_steps={meta['max_steps']} blocks={meta['total_blocks']} dir={args.output_dir}", flush=True
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
