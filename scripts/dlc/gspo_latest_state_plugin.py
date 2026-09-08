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


def _has_complete_resume_state(checkpoint: Path) -> bool:
    if not checkpoint.is_dir():
        return False
    has_optimizer = any((checkpoint / name).is_file() for name in ("optimizer.pt", "optimizer.bin"))
    has_scheduler = any((checkpoint / name).is_file() for name in ("scheduler.pt", "scheduler.bin"))
    has_trainer_state = (checkpoint / "trainer_state.json").is_file()
    has_rng_state = any(checkpoint.glob("rng_state*.pth"))
    return has_optimizer and has_scheduler and has_trainer_state and has_rng_state


# Ensure regular Trainer checkpoint saves include optimizer/scheduler/RNG/trainer
# state so the newest step checkpoint can resume exactly.
_original_on_train_begin = GSPOEvalCallback.on_train_begin


def _on_train_begin_enable_resume_state(self, args, state, control, **kwargs):
    args.save_only_model = False
    self.trainer.args.save_only_model = False
    return _original_on_train_begin(self, args, state, control, **kwargs)


GSPOEvalCallback.on_train_begin = _on_train_begin_enable_resume_state


def _on_save_keep_latest_state(self, args, state, control, **kwargs):
    # Transformers invokes on_save only after checkpoint-N has been written.
    # Keep the existing save-triggered fixed evaluation before touching old state.
    self._run(state, control, force=True)

    if getattr(state, "is_world_process_zero", True):
        current_step = int(state.global_step)
        output_dir = Path(args.output_dir)
        current_checkpoint = output_dir / f"checkpoint-{current_step}"

        # Never delete the previous resume state until the newly saved checkpoint
        # is visibly complete on disk.
        if not _has_complete_resume_state(current_checkpoint):
            print(
                f"[GSPO_CHECKPOINT_STATE] current={current_checkpoint.name} "
                "state_incomplete=true keep_previous=true",
                flush=True,
            )
            return control

        removed_from = []
        for checkpoint in output_dir.glob("checkpoint-*"):
            step = _checkpoint_step(checkpoint)
            if step is None or step >= current_step:
                continue
            if _remove_resume_state(checkpoint):
                removed_from.append(checkpoint.name)

        print(
            f"[GSPO_CHECKPOINT_STATE] latest={current_checkpoint.name} "
            f"state_verified=true removed_previous={','.join(sorted(removed_from)) or 'none'}",
            flush=True,
        )
    return control


GSPOEvalCallback.on_save = _on_save_keep_latest_state
