"""Keep resume state only in the newest step checkpoint.

Regular checkpoint model weights are retained. Optimizer/scheduler/RNG/trainer
state is kept only for the newest ``checkpoint-N`` so a crash can resume without
multiplying state-storage cost across every saved model checkpoint.
"""

from __future__ import annotations

from pathlib import Path

from scripts.dlc.gspo_trainer_plugin import GSPOEvalCallback


_STATE_PATTERNS = (
    "optimizer.pt",
    "optimizer.bin",
    "scheduler.pt",
    "scheduler.bin",
    "scaler.pt",
    "trainer_state.json",
    "training_args.bin",
    "rng_state*.pth",
)


def _remove_resume_state(checkpoint: Path) -> bool:
    removed = False
    if not checkpoint.is_dir():
        return removed
    for pattern in _STATE_PATTERNS:
        for target in checkpoint.glob(pattern):
            if target.is_file():
                target.unlink()
                removed = True
    return removed


def _checkpoint_step(path: Path) -> int | None:
    prefix = "checkpoint-"
    if not path.name.startswith(prefix):
        return None
    suffix = path.name[len(prefix):]
    return int(suffix) if suffix.isdigit() else None


def _on_save_keep_latest_state(self, args, state, control, **kwargs):
    # Preserve the existing save-triggered fixed evaluation.
    self._run(state, control, force=True)

    if getattr(state, "is_world_process_zero", True):
        current_step = int(state.global_step)
        output_dir = Path(args.output_dir)
        removed_from = []
        for checkpoint in output_dir.glob("checkpoint-*"):
            step = _checkpoint_step(checkpoint)
            if step is None or step >= current_step:
                continue
            if _remove_resume_state(checkpoint):
                removed_from.append(checkpoint.name)
        if removed_from:
            print(
                f"[GSPO_CHECKPOINT_STATE] latest=checkpoint-{current_step} "
                f"removed_previous={','.join(sorted(removed_from))}",
                flush=True,
            )
    return control


GSPOEvalCallback.on_save = _on_save_keep_latest_state
