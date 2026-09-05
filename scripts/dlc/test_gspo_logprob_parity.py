#!/usr/bin/env python3
"""CPU/GPU-independent same-logits parity tests for the vLLM patch."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def run_same_logits_tests() -> dict[str, object]:
    import torch

    from vllm.v1.sample.sampler import Sampler

    generator = torch.Generator(device="cpu").manual_seed(20260905)
    cases = []
    for rows in (1, 5, 17):
        for vocab_size in (127, 151936):
            logits = torch.randn(rows, vocab_size, generator=generator).to(torch.bfloat16)
            token_ids = torch.randint(vocab_size, (rows,), generator=generator)
            for temperature_value in (0.7, 1.0, 1.3):
                temperature = torch.full((rows,), temperature_value, dtype=torch.bfloat16)
                expected_logits = logits.clone()
                expected_logits.div_(temperature.unsqueeze(1))
                expected = torch.nn.functional.log_softmax(expected_logits, dim=-1)
                actual = Sampler.compute_logprobs(logits, temperature)
                expected_selected = expected.gather(1, token_ids[:, None]).float()
                actual_selected = actual.gather(1, token_ids[:, None]).float()
                if not torch.equal(expected_selected, actual_selected):
                    raise AssertionError(
                        f"same-logits mismatch rows={rows} vocab={vocab_size} temperature={temperature_value}"
                    )
                cases.append(
                    {
                        "rows": rows,
                        "vocab_size": vocab_size,
                        "temperature": temperature_value,
                        "max_abs_error": 0.0,
                    }
                )
    return {"torch_equal": True, "max_abs_error": 0.0, "cases": cases}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = {"same_logits": run_same_logits_tests()}
    payload = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    print(payload, end="")


if __name__ == "__main__":
    main()
