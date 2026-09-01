"""流式提取 SequenceParallelSampler 历史 step 的目标样本。

样本顺序与 ms-swift 的 SequenceParallelSampler 一致：train_multi 在前，
train_text 在后；DP sampler 使用固定 seed 的 randperm。step 为优化器步，
grad_acc 表示每个优化器步消耗的微批数，定位过程只读取命中的原始行，
避免把整个 JSONL 数据集载入内存。
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Iterable


def _nonempty_count(path: Path) -> int:
    with path.open("r", encoding="utf-8") as handle:
        return sum(1 for line in handle if line.strip())


def _find_nonempty_line(path: Path, ordinal: int) -> tuple[int, str]:
    """Return physical line index and raw JSON for a zero-based sample ordinal."""
    seen = 0
    with path.open("r", encoding="utf-8") as handle:
        for line_index, line in enumerate(handle):
            if not line.strip():
                continue
            if seen == ordinal:
                return line_index, line.rstrip("\r\n")
            seen += 1
    raise IndexError(f"sample ordinal {ordinal} is outside {path}")


def extract_steps(
    train_multi: Path,
    train_text: Path,
    steps: Iterable[int],
    *,
    seed: int = 42,
    dp_world_size: int = 12,
    grad_acc: int = 1,
) -> list[dict[str, Any]]:
    """Locate rank-0/1 sequence-parallel samples for historical steps.

    ``index`` is the stable physical JSONL line number within ``source``.
    ``raw_line`` contains the selected original JSONL line; no JSON object is
    materialized while locating samples.
    """
    if dp_world_size < 1:
        raise ValueError("dp_world_size must be positive")
    if grad_acc < 1:
        raise ValueError("grad_acc must be positive")
    requested = list(steps)
    if any(step < 1 for step in requested):
        raise ValueError("step must be positive")

    multi_len = _nonempty_count(train_multi)
    text_len = _nonempty_count(train_text)
    total_len = multi_len + text_len
    import torch

    permutation = torch.randperm(
        total_len, generator=torch.Generator().manual_seed(seed)
    ).tolist()
    records: list[dict[str, Any]] = []
    for step in requested:
        position = (step - 1) * grad_acc * dp_world_size
        if position >= total_len:
            raise ValueError(f"step {step} is outside epoch range (total={total_len})")
        global_index = permutation[position]
        if global_index < multi_len:
            source, path, local_ordinal = "train_multi", train_multi, global_index
        else:
            source, path, local_ordinal = "train_text", train_text, global_index - multi_len
        line_index, raw_line = _find_nonempty_line(path, local_ordinal)
        records.append(
            {
                "historical_step": step,
                "sampler_position": position,
                "seed": seed,
                "dp_world_size": dp_world_size,
                "grad_acc": grad_acc,
                "source": source,
                "index": line_index,
                "raw_line": raw_line,
            }
        )
    return records


def extract_plan_steps(
    plan_dir: Path,
    steps: Iterable[int],
    *,
    grad_acc: int = 2,
    rank: int = 0,
    per_device_batch: int = 1,
) -> list[dict[str, Any]]:
    """从全局采样计划提取目标 optimizer step 的 rank 微步样本。

    optimizer step s（1-based）对应 micro_step (s-1)*grad_acc .. s*grad_acc-1；
    rank r 只消费 position_in_micro_step == r 的条目。
    """
    wanted = {
        (step - 1) * grad_acc + j for step in steps for j in range(grad_acc)
    }
    entries: list[dict[str, Any]] = []
    for block_path in sorted(Path(plan_dir).glob("block_*.jsonl")):
        with block_path.open(encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                entry = json.loads(line)
                if int(entry["micro_step"]) in wanted and (
                    rank * per_device_batch
                    <= int(entry["position_in_micro_step"])
                    < (rank + 1) * per_device_batch
                ):
                    entries.append(entry)
    entries.sort(key=lambda entry: int(entry["micro_step"]))
    records: list[dict[str, Any]] = []
    for entry in entries:
        micro_step = int(entry["micro_step"])
        modality = str(entry["modality"])
        records.append(
            {
                "historical_step": micro_step // grad_acc + 1,
                "micro_step": micro_step,
                "modality": modality,
                "task": str(entry["task"]),
                "index": int(entry["index"]),
                "source": "train_multi" if modality == "multi" else "train_text",
            }
        )
    return records


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--train-multi", type=Path, required=True)
    parser.add_argument("--train-text", type=Path, required=True)
    parser.add_argument("--step", type=int, action="append", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--dp-world-size", type=int, default=12)
    parser.add_argument("--grad-acc", type=int, default=1)
    parser.add_argument("--per-device-batch", type=int, default=1)
    parser.add_argument("--plan-dir", type=Path, default=None)
    args = parser.parse_args()

    if args.plan_dir is not None:
        records = extract_plan_steps(
            args.plan_dir,
            args.step,
            grad_acc=args.grad_acc,
            per_device_batch=args.per_device_batch,
        )
        for record in records:
            path = args.train_multi if record["modality"] == "multi" else args.train_text
            _, raw_line = _find_nonempty_line(path, record["index"])
            record["raw_line"] = raw_line
        metadata_keys = ("historical_step", "micro_step", "modality", "task", "source", "index")
    else:
        records = extract_steps(
            args.train_multi,
            args.train_text,
            args.step,
            seed=args.seed,
            dp_world_size=args.dp_world_size,
            grad_acc=args.grad_acc,
        )
        metadata_keys = ("historical_step", "sampler_position", "seed", "dp_world_size", "grad_acc", "source", "index")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    metadata_output = args.output.with_suffix(args.output.suffix + ".metadata.jsonl")
    with args.output.open("w", encoding="utf-8") as handle, metadata_output.open(
        "w", encoding="utf-8"
    ) as metadata_handle:
        for record in records:
            handle.write(record["raw_line"] + "\n")
            metadata_handle.write(
                json.dumps(
                    {key: record[key] for key in metadata_keys},
                    ensure_ascii=False,
                )
                + "\n"
            )
    print(json.dumps({"output": str(args.output), "metadata": str(metadata_output), "records": [
        {key: record[key] for key in ("historical_step", "source", "index")}
        for record in records
    ]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
