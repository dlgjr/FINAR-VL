"""三级采样计划生成器：模态 -> task -> task 内样本。

以固定 seed 预生成全局采样计划：每 steps_per_block(500) 个 optimizer step
一个 block，block 大小 = steps_per_block x global_batch_size。模态配额全程
50:50；模态内部按 p_t ~ n_t^alpha x b_t 分配 task 配额，应用占比上限后
重新归一化；task 内随机无放回抽样、耗尽后重新洗牌；不足 100 条的 task
合并为 tiny_task_pool，单样本全程最多重复 TINY_MAX_REPEAT 次。

输出：每 block 一个 block_{block_id:04d}.jsonl（全局有序，含
block/micro_step/position_in_micro_step/modality/task/index），以及
meta.json（N_multi/N_text/max_steps/total_blocks 与每 block 配额统计）。
不传 --max-steps 时按 (5 x N_multi + N_text) // global_batch_size 计算，
与原来 full 训练一轮的样本访问量相当。
"""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path
from typing import Any


ALPHA_SCHEDULE = ((0, 1000, 0.70), (1000, 3000, 0.50), (3000, float("inf"), 0.35))

HEAD_DOWNWEIGHT = {
    "chart_qa": 0.6,
    "table_math_qa": 0.6,
    "financial_multiple_choice": 0.5,
    "financial_headline_classification": 0.7,
    "financial_event_extraction": 0.7,
    "stock_movement_prediction": 0.7,
}

BENCHMARK_UPWEIGHT = {
    "basic_arithmetic_metrics": 1.5,
    "candlestick_ohlc_analysis": 1.5,
    "entity_extraction_classification": 1.5,
    "evidence_retrieval": 1.4,
    "long_document_cross_page_qa": 1.4,
    "document_finance_numeric_qa": 1.3,
    "table_math_reasoning": 1.3,
    "financial_chart_qa": 1.3,
    "compliance_safety_suitability": 1.5,
    "risk_sentiment_policy": 1.5,
    "investment_advice_strategy": 1.5,
    "portfolio_and_risk_management": 1.4,
    "financial_audit_and_controls": 1.5,
    "table_statistics_and_comparison": 1.4,
    "multi_table_reasoning": 1.4,
    "single_table_qa": 1.3,
    "financial_causal_event_reasoning": 1.4,
    "multimodal_financial_knowledge": 1.5,
    "financial_numerical_reasoning": 1.3,
    "financial_relation_extraction": 1.3,
    "long_document_cross_page": 1.4,
}

MAX_TASK_RATIO = 0.08
SMALL_TASK_MIN_N = 100
SMALL_TASK_MAX_N = 499
SMALL_TASK_RATIO = 0.02
TINY_TASK_MAX_N = 100  # 样本数不足 100 的 task 进 tiny pool
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


def alpha_for_step(step: int) -> float:
    for start, end, alpha in ALPHA_SCHEDULE:
        if start <= step < end:
            return alpha
    raise ValueError(f"step {step} outside alpha schedule")


def scan_task_index(path: Path) -> tuple[dict[str, list[int]], int]:
    """流式扫描 JSONL，返回 {task: [0-based 行号]} 与总行数。"""
    task_index: dict[str, list[int]] = {}
    total = 0
    with path.open(encoding="utf-8") as handle:
        for line_no, line in enumerate(handle):
            row = json.loads(line)
            task = str(row.get("task") or UNKNOWN_TASK)
            task_index.setdefault(task, []).append(line_no)
            total += 1
    return task_index, total


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
) -> tuple[dict[str, int], int, list[str]]:
    """按 n_t^alpha x b_t 分配模态内配额，超上限截断后重新归一化。

    返回 (普通 task 配额, tiny pool 配额, tiny task 列表)，三者之和等于 quota。
    """
    tiny_tasks = sorted(task for task, count in counts.items() if count < TINY_TASK_MAX_N)
    weights: dict[str, float] = {}
    for task, count in counts.items():
        weights[task] = (count**alpha) * task_b_weight(task)
    if tiny_tasks:
        weights[_TINY_POOL_KEY] = sum(weights[task] for task in tiny_tasks)

    def cap_fn(task: str) -> float:
        if task == _TINY_POOL_KEY:
            return max(1, int(quota * TINY_POOL_RATIO))
        return float(task_cap(counts[task], quota))

    pending = dict(weights)
    final_float: dict[str, float] = {}
    remaining = float(quota)
    for _ in range(len(weights) + 1):
        total_weight = sum(pending.values())
        if total_weight <= 0 or remaining <= 1e-9:
            break
        for task in list(pending):
            raw = remaining * pending[task] / total_weight
            cap = cap_fn(task)
            take = min(raw, cap)
            final_float[task] = final_float.get(task, 0.0) + take
            if raw >= cap - 1e-9:
                del pending[task]
        remaining = quota - sum(final_float.values())
        if remaining <= 1e-9:
            break

    floors = {task: int(value) for task, value in final_float.items()}
    deficit = quota - sum(floors.values())
    order = sorted(
        final_float,
        key=lambda task: (final_float[task] - int(final_float[task]), task),
        reverse=True,
    )
    for task in order:
        if deficit <= 0:
            break
        floors[task] += 1
        deficit -= 1
    if deficit > 0:
        raise ValueError(
            f"unable to allocate quota={quota}: task caps sum to "
            f"{sum(floors.values())} which is below quota; check task size distribution"
        )

    tiny_quota = int(floors.pop(_TINY_POOL_KEY, 0))
    return floors, tiny_quota, tiny_tasks


def sample_task_indices(indices: list[int], quota: int, rng: random.Random) -> list[int]:
    """task 内无放回抽样；配额超过 task 大小时耗尽后重新洗牌。"""
    pool = list(indices)
    rng.shuffle(pool)
    if quota <= len(pool):
        return pool[:quota]
    full, remainder = divmod(quota, len(pool))
    return pool * full + rng.sample(pool, remainder)


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
    """tiny pool 内按 task 权重抽样；单样本全程最多重复 TINY_MAX_REPEAT 次。"""
    picked: list[int] = []
    picked_set: set[int] = set()
    attempts = quota * 4 + 10
    for _ in range(attempts):
        if len(picked) >= quota:
            break
        candidates: list[int] = []
        candidate_weights: list[float] = []
        for task in tiny_tasks:
            weight = (len(task_index[task]) ** alpha) * task_b_weight(task)
            for index in task_index[task]:
                if usage.get((modality, index), 0) < TINY_MAX_REPEAT and index not in picked_set:
                    candidates.append(index)
                    candidate_weights.append(weight)
        if not candidates:
            break
        picked.append(rng.choices(candidates, weights=candidate_weights, k=1)[0])
        picked_set.add(picked[-1])
    for index in picked:
        usage[(modality, index)] = usage.get((modality, index), 0) + 1
    return picked


def _split_uneven(count: int, parts: int) -> list[int]:
    base, extra = divmod(count, parts)
    return [base + 1 if index < extra else base for index in range(parts)]


def _sample_modality(
    task_index: dict[str, list[int]],
    quota: int,
    alpha: float,
    usage: dict[tuple[str, int], int],
    rng: random.Random,
    *,
    modality: str,
) -> tuple[list[tuple[int, str]], dict[str, int]]:
    counts = {task: len(indices) for task, indices in task_index.items()}
    allocations, tiny_quota, tiny_tasks = allocate_quotas(counts, quota, alpha)
    samples: list[tuple[int, str]] = []
    for task in sorted(allocations):
        for index in sample_task_indices(task_index[task], allocations[task], rng):
            samples.append((index, task))
    for index in sample_tiny_pool(
        tiny_tasks, task_index, tiny_quota, alpha, usage, rng, modality=modality
    ):
        samples.append((index, _TINY_POOL_KEY))
    shortfall = quota - len(samples)
    if shortfall > 0:
        # tiny pool 可用样本不足时，余量按权重转给未达上限的非 tiny task
        capacities = {
            task: max(0, task_cap(counts[task], quota) - allocations[task])
            for task in allocations
        }
        if sum(capacities.values()) < shortfall:
            raise ValueError(
                f"cannot cover tiny shortfall {shortfall}: remaining capacity "
                f"{sum(capacities.values())} below quota {quota}"
            )
        pending_weights = {
            task: (counts[task] ** alpha) * task_b_weight(task)
            for task, capacity in capacities.items()
            if capacity > 0
        }
        extra: dict[str, int] = {}
        remaining = shortfall
        while remaining > 0 and pending_weights:
            total_weight = sum(pending_weights.values())
            if total_weight <= 0:
                break
            for task in list(pending_weights):
                if remaining <= 0:
                    break
                raw = remaining * pending_weights[task] / total_weight
                take = min(max(1, int(raw)), capacities[task], remaining)
                extra[task] = extra.get(task, 0) + take
                capacities[task] -= take
                remaining -= take
                if capacities[task] <= 0:
                    del pending_weights[task]
        if remaining > 0:
            raise ValueError(f"cannot cover tiny shortfall {shortfall} fully")
        for task in sorted(extra):
            for index in sample_task_indices(task_index[task], extra[task], rng):
                samples.append((index, task))
            allocations[task] += extra[task]
    rng.shuffle(samples)
    quotas = dict(allocations)
    quotas[_TINY_POOL_KEY] = tiny_quota
    return samples, quotas


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
    multi_index: dict[str, list[int]],
    text_index: dict[str, list[int]],
    tiny_usage: dict[tuple[str, int], int],
) -> tuple[list[dict[str, Any]], dict[str, Any], dict[int, int]]:
    """生成一个 block 的全局计划条目；微步内全局保持多模态/纯文本各半。"""
    rng = random.Random(seed * 100_000 + block_id)
    alpha = alpha_for_step(start_step)
    samples_total = steps * global_batch_size
    multi_quota = samples_total // 2
    text_quota = samples_total - multi_quota

    multi_samples, multi_quotas = _sample_modality(
        multi_index, multi_quota, alpha, tiny_usage, rng, modality="multi"
    )
    text_samples, text_quotas = _sample_modality(
        text_index, text_quota, alpha, tiny_usage, rng, modality="text"
    )

    micro_steps = steps * grad_acc
    per_micro = dp_world_size * per_device_batch
    # 每 step 该模态样本数 = global_batch_size // 2
    samples_per_step = global_batch_size // 2
    multi_sizes = _split_uneven(samples_per_step, grad_acc)
    entries: list[dict[str, Any]] = []
    multi_pos = text_pos = 0
    for micro_index in range(micro_steps):
        take_multi = multi_sizes[micro_index % grad_acc]
        take_text = per_micro - take_multi
        micro: list[tuple[tuple[int, str], str]] = []
        micro.extend(
            ((index, task), "multi")
            for index, task in multi_samples[multi_pos : multi_pos + take_multi]
        )
        micro.extend(
            ((index, task), "text")
            for index, task in text_samples[text_pos : text_pos + take_text]
        )
        multi_pos += take_multi
        text_pos += take_text
        rng.shuffle(micro)
        for position, ((index, task), modality) in enumerate(micro):
            entries.append(
                {
                    "block": block_id,
                    "micro_step": start_step * grad_acc + micro_index,
                    "position_in_micro_step": position,
                    "modality": modality,
                    "task": task,
                    "index": index,
                }
            )

    block_info: dict[str, Any] = {
        "block_id": block_id,
        "start_step": start_step,
        "steps": steps,
        "alpha": alpha,
        "quotas": {"multi": multi_quotas, "text": text_quotas},
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
    max_steps: int | None = None,
    epochs: int = 1,
    steps_per_block: int = 500,
) -> dict[str, Any]:
    if global_batch_size != dp_world_size * per_device_batch * grad_acc:
        raise ValueError(
            "global_batch_size must equal dp_world_size * per_device_batch * grad_acc "
            f"got {global_batch_size} vs {dp_world_size} * {per_device_batch} * {grad_acc}"
        )
    multi_index, n_multi = scan_task_index(train_multi)
    text_index, n_text = scan_task_index(train_text)
    if max_steps is None:
        max_steps = (5 * n_multi + n_text) * epochs // global_batch_size
    total_blocks = (max_steps + steps_per_block - 1) // steps_per_block
    output_dir.mkdir(parents=True, exist_ok=True)

    tiny_usage: dict[tuple[str, int], int] = {}
    blocks: list[dict[str, Any]] = []
    for block_id in range(total_blocks):
        start_step = block_id * steps_per_block
        steps = min(steps_per_block, max_steps - start_step)
        entries, block_info, tiny_usage = build_block(
            block_id=block_id,
            start_step=start_step,
            steps=steps,
            global_batch_size=global_batch_size,
            dp_world_size=dp_world_size,
            per_device_batch=per_device_batch,
            grad_acc=grad_acc,
            seed=seed,
            multi_index=multi_index,
            text_index=text_index,
            tiny_usage=tiny_usage,
        )
        block_path = output_dir / f"block_{block_id:04d}.jsonl"
        with block_path.open("w", encoding="utf-8") as handle:
            for entry in entries:
                handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
        blocks.append(block_info)

    meta: dict[str, Any] = {
        "max_steps": max_steps,
        "total_blocks": total_blocks,
        "steps_per_block": steps_per_block,
        "N_multi": n_multi,
        "N_text": n_text,
        "global_batch_size": global_batch_size,
        "dp_world_size": dp_world_size,
        "per_device_batch": per_device_batch,
        "grad_acc": grad_acc,
        "seed": seed,
        "epochs": epochs,
        "blocks": blocks,
        "tiny_usage": {
            f"{modality}:{index}": count for (modality, index), count in tiny_usage.items()
        },
    }
    meta_path = output_dir / "meta.json"
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (output_dir / ".ready").write_text("ready\n", encoding="utf-8")
    return meta


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="生成三级采样计划")
    parser.add_argument("--train-multi", type=Path, required=True)
    parser.add_argument("--train-text", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--global-batch-size", type=int, default=24)
    parser.add_argument("--dp-world-size", type=int, default=12)
    parser.add_argument("--per-device-batch", type=int, default=1)
    parser.add_argument("--grad-acc", type=int, default=2)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--max-steps", type=int, default=None)
    parser.add_argument("--epochs", type=int, default=1)
    parser.add_argument("--steps-per-block", type=int, default=500)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    meta = generate_plan(
        train_multi=args.train_multi,
        train_text=args.train_text,
        output_dir=args.output_dir,
        global_batch_size=args.global_batch_size,
        dp_world_size=args.dp_world_size,
        per_device_batch=args.per_device_batch,
        grad_acc=args.grad_acc,
        seed=args.seed,
        max_steps=args.max_steps,
        epochs=args.epochs,
        steps_per_block=args.steps_per_block,
    )
    print(
        f"sample_plan n_multi={meta['N_multi']} n_text={meta['N_text']} "
        f"max_steps={meta['max_steps']} blocks={meta['total_blocks']} "
        f"dir={args.output_dir}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
