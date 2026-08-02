"""流式提取 SequenceParallelSampler 历史 step 的目标样本。

样本顺序与 ms-swift 的 SequenceParallelSampler 一致：train_multi 在前，
train_text 在后；DP sampler 使用固定 seed 的 randperm。定位过程只读取
命中的原始行，避免把整个 JSONL 数据集载入内存。
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
) -> list[dict[str, Any]]:
    """Locate rank-0/1 sequence-parallel samples for historical steps.

    ``index`` is the stable physical JSONL line number within ``source``.
    ``raw_line`` contains the selected original JSONL line; no JSON object is
    materialized while locating samples.
    """
    if dp_world_size < 1:
        raise ValueError("dp_world_size must be positive")
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
        position = (step - 1) * dp_world_size
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
                "source": source,
                "index": line_index,
                "raw_line": raw_line,
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
    args = parser.parse_args()

    records = extract_steps(
        args.train_multi,
        args.train_text,
        args.step,
        seed=args.seed,
        dp_world_size=args.dp_world_size,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    metadata_output = args.output.with_suffix(args.output.suffix + ".metadata.jsonl")
    with args.output.open("w", encoding="utf-8") as handle, metadata_output.open(
        "w", encoding="utf-8"
    ) as metadata_handle:
        for record in records:
            handle.write(record["raw_line"] + "\n")
            metadata_handle.write(
                json.dumps(
                    {key: record[key] for key in ("historical_step", "sampler_position", "seed", "dp_world_size", "source", "index")},
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
