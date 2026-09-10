"""W&B Run compatibility and rank-0-only eval stdout for GSPO."""

from __future__ import annotations

import io
from contextlib import redirect_stdout

import scripts.dlc.gspo_wandb_timeseries_fix as timeseries_fix
from scripts.dlc.gspo_trainer_plugin import GSPOEvalCallback


# Recent W&B Run objects reject arbitrary attribute assignment. Keep the
# per-run configured marker in this module instead of writing it onto Run.
_CONFIGURED_RUN_IDS: set[int] = set()


def _configure_axis_compat(wandb_module):
    run = getattr(wandb_module, "run", None)
    if run is None:
        return None

    run_id = id(run)
    if run_id in _CONFIGURED_RUN_IDS:
        return run

    run.define_metric("_gspo_step", hidden=True, summary="none", overwrite=True)
    for raw_key in timeseries_fix.wandb_plugin.TRAIN_WANDB_KEYS:
        run.define_metric(
            f"train/{timeseries_fix._wandb_key(raw_key)}",
            step_metric="_gspo_step",
            step_sync=True,
            overwrite=True,
        )
    for key in ("eval/pass_at_1", "eval/pass_at_8"):
        run.define_metric(
            key,
            step_metric="_gspo_step",
            step_sync=True,
            overwrite=True,
        )

    run.config.update(
        {
            "gspo/generation_batch_size": int(timeseries_fix.os.environ.get("GSPO_GENERATION_BATCH_SIZE", "0")),
            "gspo/steps_per_generation": int(timeseries_fix.os.environ.get("GSPO_STEPS_PER_GENERATION", "0")),
            "gspo/num_iterations": int(timeseries_fix.os.environ.get("GSPO_NUM_ITERATIONS", "0")),
            "gspo/max_resample_times": int(timeseries_fix.os.environ.get("GSPO_MAX_RESAMPLE_TIMES", "0")),
            "gspo/gold_mode": "fallback_after_resample",
            "gspo/reasoning_short_metric_tokens": int(timeseries_fix.os.environ.get("GSPO_REASONING_DIRECT_TOKENS", "100")),
            "gspo/wandb_step_offset": timeseries_fix._wandb_step_offset(),
        },
        allow_val_change=True,
    )
    _CONFIGURED_RUN_IDS.add(run_id)
    return run


timeseries_fix._configure_axis = _configure_axis_compat


# Evaluation must execute on every rank, but the callback's final summary print
# should appear only once. Suppress only non-main stdout; distributed work is unchanged.
_original_eval_run = GSPOEvalCallback._run


def _eval_run_rank0_stdout(self, state, control=None, *, force: bool = False):
    if getattr(state, "is_world_process_zero", True):
        return _original_eval_run(self, state, control, force=force)
    with redirect_stdout(io.StringIO()):
        return _original_eval_run(self, state, control, force=force)


GSPOEvalCallback._run = _eval_run_rank0_stdout
