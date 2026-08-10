"""Evaluation/checkpoint callback for the full GSPO run.

Evaluation artifacts are written to disk and are intentionally not passed to
``trainer.log``; only the reward plugin emits training W&B metrics.
"""

from __future__ import annotations

import json
import os
from contextlib import nullcontext
from pathlib import Path
from typing import Any

try:
    from swift.callbacks import TrainerCallback, callbacks_map
except ImportError:  # pragma: no cover - DLC supplies ms-swift
    class TrainerCallback:  # type: ignore[no-redef]
        def __init__(self, *args, **kwargs):
            pass

    callbacks_map: dict[str, type] = {}  # type: ignore[no-redef]

from scripts.rl.gspo_audit import build_audit_records
from scripts.sft.pass_at_8_eval import run_distributed_evaluation


class GSPOEvalCallback(TrainerCallback):
    def __init__(self, args, trainer):
        super().__init__()
        self.args = args
        self.trainer = trainer
        self.last_eval_step: int | None = None

    @staticmethod
    def _cleanup_checkpoint(path: Path) -> None:
        state_names = {
            "optimizer.pt",
            "optimizer.bin",
            "scheduler.pt",
            "scheduler.bin",
            "rng_state.pth",
            "trainer_state.json",
            "training_args.bin",
        }
        for name in state_names:
            target = path / name
            if target.is_file():
                target.unlink()
        remaining = [str(target) for target in path.iterdir() if target.name in state_names] if path.is_dir() else []
        if remaining:
            raise RuntimeError(f"GSPO checkpoint contains trainer state: {remaining}")

    def _run(self, state, *, force: bool = False) -> None:
        step = int(state.global_step)
        interval = int(os.environ.get("GSPO_EVAL_STEPS", "200"))
        if not force and (step == 0 or step % interval != 0):
            return
        if self.last_eval_step == step:
            return
        self.last_eval_step = step
        model = getattr(self.trainer, "model_wrapped", self.trainer.model)
        accelerator = getattr(self.trainer, "accelerator", None)
        template = getattr(self.trainer, "template", None)
        if accelerator is None:
            unwrap_context = nullcontext(model)
        else:
            try:
                from swift.utils import unwrap_model_for_generation
            except ImportError:
                unwrap_context = nullcontext(model)
            else:
                unwrap_context = unwrap_model_for_generation(model, accelerator)
        template_context = template.generate_context() if template is not None else nullcontext()
        with unwrap_context as model_wrapped, template_context:
            metrics = run_distributed_evaluation(
                model=model_wrapped,
                processor=getattr(self.trainer, "processor", None),
                template=template,
                benchmark_path=Path(os.environ["GSPO_BENCHMARK"]),
                project_root=Path(os.environ["QWEN3VL_ROOT"]),
                output_dir=Path(self.args.output_dir) / "eval",
                step=step,
                judge_url=os.environ.get("GSPO_JUDGE_URL", "http://127.0.0.1:8001"),
                max_samples=int(os.environ.get("GSPO_EVAL_MAX_SAMPLES", "0")) or None,
            )
        if int(step) > 0 and getattr(state, "is_world_process_zero", True):
            pool_path = Path(os.environ.get("GSPO_REWARD_POOL", str(Path(self.args.output_dir) / "reward_pool.jsonl")))
            if pool_path.is_file():
                pool = [json.loads(line) for line in pool_path.read_text(encoding="utf-8").splitlines() if line.strip()]
                audit = build_audit_records(pool, seed=int(os.environ.get("GSPO_AUDIT_SEED", "42")), max_completion_length=int(os.environ.get("GSPO_MAX_COMPLETION_LENGTH", "2048")))
                audit_path = Path(self.args.output_dir) / "eval" / f"step-{step:06d}" / "high_reward_audit.json"
                audit_path.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"[GSPO_EVAL] step={step} metrics={json.dumps(metrics, ensure_ascii=False)}", flush=True)

    def on_train_begin(self, args, state, control, **kwargs):
        self._run(state, force=True)
        return control

    def on_save(self, args, state, control, **kwargs):
        self._run(state, force=True)
        if getattr(state, "is_world_process_zero", True):
            checkpoint = Path(args.output_dir) / f"checkpoint-{state.global_step}"
            self._cleanup_checkpoint(checkpoint)
        return control

    def on_epoch_end(self, args, state, control, **kwargs):
        if getattr(state, "is_world_process_zero", True):
            epoch = int(round(float(state.epoch or 0)))
            checkpoint = Path(args.output_dir) / f"checkpoint-epoch-{epoch}"
            self.trainer.save_model(str(checkpoint))
            self._cleanup_checkpoint(checkpoint)
        return control

    def on_train_end(self, args, state, control, **kwargs):
        if getattr(state, "is_world_process_zero", True):
            checkpoint = Path(args.output_dir) / "final"
            self.trainer.save_model(str(checkpoint))
            self._cleanup_checkpoint(checkpoint)
            self._cleanup_checkpoint(Path(args.output_dir))
        self.last_eval_step = None
        self._run(state, force=True)
        return control


callbacks_map["gspo_eval"] = GSPOEvalCallback
