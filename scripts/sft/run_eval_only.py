"""Run one Pass@8 evaluation against an SFT checkpoint."""

from __future__ import annotations

import os
from contextlib import nullcontext
from pathlib import Path
from typing import Any

from scripts.sft.pass_at_8_eval import run_distributed_evaluation
from scripts.sft.swift_sft_plugin import suspend_sequence_parallel

try:
    from swift.utils import unwrap_model_for_generation
except ImportError:  # pragma: no cover - only used by lightweight unit tests
    from contextlib import contextmanager

    @contextmanager
    def unwrap_model_for_generation(model, accelerator):
        yield model


def evaluate_once(*, model: Any, processor: Any, template: Any, accelerator: Any,
                  benchmark_path: Path, project_root: Path, output_dir: Path,
                  judge_url: str, max_samples: int | None) -> dict[str, Any]:
    unwrap_context = (nullcontext(model) if accelerator is None
                      else unwrap_model_for_generation(model, accelerator))
    with unwrap_context as model_wrapped:
        with template.generate_context():
            with suspend_sequence_parallel():
                return run_distributed_evaluation(
                    model=model_wrapped, processor=processor, template=template,
                    benchmark_path=benchmark_path, project_root=project_root,
                    output_dir=output_dir, step=0, judge_url=judge_url,
                    max_samples=max_samples,
                )


def main() -> None:
    from swift.arguments import InferArguments
    from swift.pipelines.utils import prepare_model_template
    from swift.utils import parse_args

    args, remaining = parse_args(InferArguments)
    if remaining:
        raise ValueError(f"remaining_argv: {remaining}")
    model, template = prepare_model_template(args)
    try:
        from accelerate import Accelerator

        accelerator = Accelerator()
    except ImportError:  # pragma: no cover - dependency is present on DSW
        accelerator = getattr(args, "accelerator", None)
    root = Path(os.environ.get("QWEN3VL_ROOT", "/mnt/nas/bihaoran/qwen3vl"))
    benchmark = Path(os.environ.get("SFT_BENCHMARK", str(root / "data/benchmark/my_benchmark/all.jsonl")))
    output_dir = Path(os.environ.get("SFT_EVAL_OUTPUT", "output/sft_eval/eval"))
    evaluate_once(
        model=model, processor=getattr(template, "processor", None), template=template,
        accelerator=accelerator, benchmark_path=benchmark,
        project_root=root, output_dir=output_dir,
        judge_url=os.environ.get("SFT_JUDGE_URL", "http://127.0.0.1:8001"),
        max_samples=int(os.environ.get("SFT_EVAL_MAX_SAMPLES", "1")) or None,
    )


if __name__ == "__main__":
    main()
