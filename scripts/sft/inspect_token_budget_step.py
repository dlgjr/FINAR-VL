"""根据旧运行的长度扫描结果还原动态 batch 中指定优化步。"""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path
from typing import Any


BUCKETS = (("short", 8192, 2), ("medium", 32768, 1), ("long", 81920, 1))


def _read_lengths(results_dir: Path) -> list[int]:
    values: dict[int, int] = {}
    errors = []
    for path in sorted(results_dir.glob("rank_*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        errors.extend(payload.get("errors", []))
        for index, length in payload.get("lengths", []):
            index = int(index)
            if index in values:
                raise ValueError(f"duplicate dataset index: {index}")
            values[index] = int(length)
    if errors:
        raise ValueError(f"length scan contains errors: {errors[0]}")
    if not values:
        raise ValueError(f"no length results found in {results_dir}")
    expected = list(range(max(values) + 1))
    if sorted(values) != expected:
        missing = next(index for index in expected if index not in values)
        raise ValueError(f"missing dataset index: {missing}")
    return [values[index] for index in expected]


def _batches_for_epoch(lengths: list[int], *, seed: int, dp_world_size: int) -> list[list[int]]:
    buckets = {name: [] for name, _, _ in BUCKETS}
    for index, length in enumerate(lengths):
        for name, maximum, _ in BUCKETS:
            if length <= maximum:
                buckets[name].append(index)
                break
    generator = random.Random(seed)
    batches = []
    for name, _, local_batch_size in BUCKETS:
        indices = buckets[name]
        generator.shuffle(indices)
        global_batch_size = local_batch_size * dp_world_size
        for offset in range(0, len(indices), global_batch_size):
            batch = indices[offset:offset + global_batch_size]
            original = list(batch)
            while len(batch) < global_batch_size:
                batch.append(original[len(batch) % len(original)])
            batches.append(batch)
    generator.shuffle(batches)
    return batches


def inspect_steps(*, results_dir: Path, steps: list[int], seed: int, dp_world_size: int, sp_size: int,
                  global_ranks: list[int]) -> dict[str, Any]:
    lengths = _read_lengths(results_dir)
    batches = _batches_for_epoch(lengths, seed=seed, dp_world_size=dp_world_size)
    rank_mapping = {str(rank): rank // sp_size for rank in global_ranks}
    reports = []
    for step in steps:
        if not 1 <= step <= len(batches):
            raise ValueError(f"step {step} is outside epoch-0 range 1..{len(batches)}")
        batch = batches[step - 1]
        local_size = len(batch) // dp_world_size
        dp_batches = {}
        for dp_rank in range(dp_world_size):
            indices = batch[dp_rank * local_size:(dp_rank + 1) * local_size]
            dp_batches[str(dp_rank)] = {"indices": indices, "lengths": [lengths[i] for i in indices]}
        reports.append({"step": step, "global_batch_indices": batch, "global_batch_size": len(batch),
                        "dp_batches": dp_batches})
    return {"seed": seed, "dp_world_size": dp_world_size, "sp_size": sp_size,
            "rank_mapping": rank_mapping, "epoch_batches": len(batches), "steps": reports}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-dir", type=Path, required=True)
    parser.add_argument("--step", type=int, action="append", required=True)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--dp-world-size", type=int, default=12)
    parser.add_argument("--sp-size", type=int, default=2)
    parser.add_argument("--global-rank", type=int, action="append", default=[])
    args = parser.parse_args()
    print(json.dumps(inspect_steps(results_dir=args.results_dir, steps=args.step, seed=args.seed,
                                   dp_world_size=args.dp_world_size, sp_size=args.sp_size,
                                   global_ranks=args.global_rank), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
