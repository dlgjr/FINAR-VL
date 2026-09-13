"""Publish per-seed fixed-eval Pass@1/Pass@8 metrics to W&B."""

from __future__ import annotations

import json
from pathlib import Path

import scripts.dlc.gspo_wandb_timeseries_fix as wandb_timeseries
from scripts.dlc.gspo_trainer_plugin import GSPOEvalCallback


_original_eval_run = GSPOEvalCallback._run


def _eval_run_with_seed_metrics(self, state, control=None, *, force: bool = False):
    step = int(state.global_step)
    previous_step = self.last_eval_step
    result = _original_eval_run(self, state, control, force=force)

    actually_ran = self.last_eval_step == step and previous_step != step
    if not actually_ran or not getattr(state, "is_world_process_zero", True):
        return result

    summary_path = (
        Path(self.args.output_dir)
        / "eval"
        / f"step-{step:06d}"
        / "summary.json"
    )
    if not summary_path.is_file():
        return result

    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    per_seed = summary.get("per_seed", [])
    if not per_seed:
        return result

    try:
        import wandb
    except ImportError:
        return result

    run = wandb_timeseries._configure_axis(wandb)
    if run is None:
        return result

    payload = {"_gspo_step": wandb_timeseries._logical_wandb_step(step)}
    for row in per_seed:
        seed = int(row["seed"])
        pass1_key = f"eval/seed_{seed}/pass_at_1"
        pass8_key = f"eval/seed_{seed}/pass_at_8"
        run.define_metric(
            pass1_key,
            step_metric="_gspo_step",
            step_sync=True,
            overwrite=True,
        )
        run.define_metric(
            pass8_key,
            step_metric="_gspo_step",
            step_sync=True,
            overwrite=True,
        )
        payload[pass1_key] = float(row.get("pass_at_1", 0.0))
        payload[pass8_key] = float(row.get("pass_at_8", 0.0))

    run.log(payload)
    return result


_eval_run_with_seed_metrics._gspo_eval_seed_wandb = True
GSPOEvalCallback._run = _eval_run_with_seed_metrics
