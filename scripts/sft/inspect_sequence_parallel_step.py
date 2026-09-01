"""还原 DSW 调试阶段 SequenceParallelSampler 的固定步样本摘要。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _read_rows(path: Path, source: str) -> list[dict[str, Any]]:
    rows = []
    with path.open(encoding="utf-8") as handle:
        for index, line in enumerate(handle):
            if line.strip():
                rows.append({"source": source, "index": index, "row": json.loads(line)})
    return rows


def _length(row: dict[str, Any], length_fn=None) -> tuple[int, str]:
    if length_fn is not None:
        return int(length_fn(row)), "encoded_estimated"
    value = row.get("length", row.get("token_length"))
    if value is not None:
        return int(value), "encoded_estimated"
    messages = row.get("messages", [])
    return sum(len(str(message.get("content", ""))) for message in messages), "estimated"


def inspect_steps(*, train_multi: Path, train_text: Path, steps: list[int], seed: int = 42,
                  dp_world_size: int = 12, grad_acc: int = 1, length_fn=None) -> dict[str, Any]:
    if grad_acc < 1:
        raise ValueError(f"grad_acc must be positive: {grad_acc}")
    rows = _read_rows(train_multi, "train_multi") + _read_rows(train_text, "train_text")
    import torch

    generator = torch.Generator().manual_seed(seed)
    permutation = torch.randperm(len(rows), generator=generator).tolist()
    reports = []
    for step in steps:
        if step < 1:
            raise ValueError(f"step must be positive: {step}")
        start = (step - 1) * grad_acc * dp_world_size
        indices = permutation[start:start + dp_world_size]
        if not indices:
            raise ValueError(f"step {step} is outside epoch range")
        while len(indices) < dp_world_size:
            indices.append(indices[len(indices) % len(indices)])
        samples = []
        for index in indices:
            length, length_kind = _length(rows[index]["row"], length_fn)
            samples.append({"source": rows[index]["source"], "index": rows[index]["index"],
                            "length": length, "length_kind": length_kind})
        reports.append({"step": step, "samples": samples})
    return {"seed": seed, "dp_world_size": dp_world_size, "grad_acc": grad_acc, "steps": reports}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--train-multi", type=Path, required=True)
    parser.add_argument("--train-text", type=Path, required=True)
    parser.add_argument("--step", type=int, action="append", required=True)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--dp-world-size", type=int, default=12)
    parser.add_argument("--grad-acc", type=int, default=1)
    parser.add_argument("--model", type=str, default=None,
                        help="可选 Hugging Face processor，用编码长度替代字符估计")
    parser.add_argument("--image-max-token-num", type=int, default=256)
    args = parser.parse_args()
    length_fn = None
    if args.model:
        from transformers import AutoProcessor

        processor = AutoProcessor.from_pretrained(args.model, trust_remote_code=True)

        def length_fn(row):
            text_length = len(processor.apply_chat_template(row["messages"], tokenize=True,
                                                             add_generation_prompt=False))
            return text_length + len(row.get("images", [])) * args.image_max_token_num

    print(json.dumps(inspect_steps(train_multi=args.train_multi, train_text=args.train_text,
                                   steps=args.step, seed=args.seed,
                                   dp_world_size=args.dp_world_size,
                                   grad_acc=args.grad_acc,
                                   length_fn=length_fn), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
