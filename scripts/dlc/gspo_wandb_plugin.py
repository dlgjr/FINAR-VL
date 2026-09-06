"""Keep GSPO W&B focused and make fixed-set evaluation metrics reproducible.

This module is imported for side effects by ``gspo_plugins.py``.  It deliberately
leaves Trainer/stdout/checkpoint behavior alone and only changes what is emitted
to W&B, plus the fixed 20-row RL evaluation routing.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from scripts.dlc.gspo_reward_plugin import GSPOReward
import scripts.dlc.gspo_trainer_plugin as trainer_plugin
from scripts.dlc.gspo_trainer_plugin import GSPOEvalCallback, GSPOGRPOTrainer


# One metric per training concept.  In particular, do not mirror
# rewards/gspo_mixed/{mean,std} when reward/reward_std already exist.
TRAIN_WANDB_KEYS = {
    "loss",
    "grad_norm",
    "reward",
    "reward_std",
    "frac_reward_zero_std",
    "kl",
    "clip_ratio/region_mean",
    "entropy/regularized_mean",
    "entropy/regularization_loss",
    "entropy/coef",
    "ess/ratio",
    "rollout/pass8",
    "rollout/positive_per_8",
    "intervention/gold_group_ratio",
}


def _configure_fixed_eval() -> None:
    """Route the in-training callback to the fixed rl_test.jsonl set."""
    eval_data = os.environ.get("GSPO_EVAL_DATA")
    if not eval_data:
        return
    eval_path = Path(eval_data)
    os.environ["GSPO_BENCHMARK"] = str(eval_path)
    os.environ["GSPO_BENCHMARK_ALLOWLIST"] = "finmmr"
    os.environ["GSPO_EVAL_MAX_SAMPLES"] = "20"
    # rl_test.jsonl contains paths such as assets/finmmr/xxx.png, so its parent
    # data/benchmark is the correct root (not data/benchmark/assets).
    os.environ["SFT_BENCHMARK_ROOT"] = str(eval_path.parent)


_configure_fixed_eval()


# The callback used QWEN3VL_ROOT as the image root.  Override only the evaluation
# call so assets/finmmr/... resolves under data/benchmark.
_original_run_distributed_evaluation = trainer_plugin.run_distributed_evaluation


def _fixed_run_distributed_evaluation(*args, **kwargs):
    eval_data = os.environ.get("GSPO_EVAL_DATA")
    if eval_data:
        kwargs["benchmark_path"] = Path(eval_data)
        kwargs["project_root"] = Path(
            os.environ.get("SFT_BENCHMARK_ROOT", str(Path(eval_data).parent))
        )
        kwargs["max_samples"] = 20
    return _original_run_distributed_evaluation(*args, **kwargs)


trainer_plugin.run_distributed_evaluation = _fixed_run_distributed_evaluation


# The reward ORM used to call wandb.log() independently from Trainer.  Suppress
# that second stream while preserving its stdout/reward-pool diagnostics.
if not getattr(GSPOReward.__call__, "_gspo_wandb_suppressed", False):
    _original_reward_call = GSPOReward.__call__

    def _reward_call_without_wandb(self, *args, **kwargs):
        old_mode = os.environ.get("WANDB_MODE")
        os.environ["WANDB_MODE"] = "offline-disabled"
        try:
            return _original_reward_call(self, *args, **kwargs)
        finally:
            if old_mode is None:
                os.environ.pop("WANDB_MODE", None)
            else:
                os.environ["WANDB_MODE"] = old_mode

    _reward_call_without_wandb._gspo_wandb_suppressed = True
    GSPOReward.__call__ = _reward_call_without_wandb


# The active V11 methods override an earlier entropy implementation.  Populate
# the three dashboard keys from the entropy term that is actually added to loss.
if not getattr(GSPOGRPOTrainer._compute_loss_and_metrics, "_gspo_entropy_wandb", False):
    _original_compute_loss_and_metrics = GSPOGRPOTrainer._compute_loss_and_metrics

    def _compute_loss_and_metrics_with_entropy_metrics(self, model, model_inputs, grpo_batch):
        loss, metrics_data = _original_compute_loss_and_metrics(
            self, model, model_inputs, grpo_batch
        )
        entropy_mean = metrics_data.get("concise_entropy_mean")
        if entropy_mean is not None:
            coef = float(os.environ.get("GSPO_ENTROPY_COEF", "0.02"))
            metrics_data["gspo_entropy_regularization"] = {
                "coef": coef,
                "mean": float(entropy_mean),
                "loss": -coef * float(entropy_mean),
            }
        return loss, metrics_data

    _compute_loss_and_metrics_with_entropy_metrics._gspo_entropy_wandb = True
    GSPOGRPOTrainer._compute_loss_and_metrics = _compute_loss_and_metrics_with_entropy_metrics


if not getattr(GSPOGRPOTrainer._update_metrics, "_gspo_entropy_wandb", False):
    _original_update_metrics = GSPOGRPOTrainer._update_metrics

    def _update_metrics_with_entropy_metrics(self, metrics_data):
        _original_update_metrics(self, metrics_data)
        regularization = metrics_data.get("gspo_entropy_regularization")
        if regularization is None:
            return
        mode = metrics_data["mode"]
        # regularized_mean is the useful entropy gauge.  Remove the synonymous
        # entropy/mean series so W&B has one entropy-mean chart, not two.
        self._metrics[mode].pop("entropy/mean", None)
        self._metrics[mode]["entropy/regularized_mean"].append(regularization["mean"])
        self._metrics[mode]["entropy/regularization_loss"].append(regularization["loss"])
        self._metrics[mode]["entropy/coef"].append(regularization["coef"])

    _update_metrics_with_entropy_metrics._gspo_entropy_wandb = True
    GSPOGRPOTrainer._update_metrics = _update_metrics_with_entropy_metrics


# rollout/all8 is redundant for the training decisions we care about.  Keep it
# in the stdout diagnostic payload, but do not add it to Trainer/W&B metrics.
if not getattr(GSPOGRPOTrainer._record_concise_train_metrics, "_gspo_no_all8", False):
    _original_record_concise_train_metrics = GSPOGRPOTrainer._record_concise_train_metrics

    def _record_concise_train_metrics_without_all8(self, metrics):
        concise = dict(metrics)
        concise.pop("rollout/all8", None)
        return _original_record_concise_train_metrics(self, concise)

    _record_concise_train_metrics_without_all8._gspo_no_all8 = True
    GSPOGRPOTrainer._record_concise_train_metrics = _record_concise_train_metrics_without_all8


# Replace only Transformers' W&B on_log sink.  Trainer still computes/logs its
# full diagnostics to stdout/state, while W&B receives the small whitelist above.
# This also prevents automatic train/global_step and removes lr/step_time/epoch.
try:
    from transformers.integrations.integration_utils import WandbCallback
except ImportError:  # pragma: no cover
    from transformers.integrations import WandbCallback


if not getattr(WandbCallback.on_log, "_gspo_concise_wandb", False):
    def _concise_wandb_on_log(self, args, state, control, model=None, logs=None, **kwargs):
        if self._wandb is None:
            return control
        if not self._initialized:
            self.setup(args, state, model, **kwargs)
        if not state.is_world_process_zero:
            return control

        payload: dict[str, Any] = {}
        for key, value in (logs or {}).items():
            raw_key = key.removeprefix("train/")
            if raw_key in TRAIN_WANDB_KEYS:
                payload[f"train/{raw_key}"] = value
        if payload:
            self._wandb.log(payload)
        return control

    _concise_wandb_on_log._gspo_concise_wandb = True
    WandbCallback.on_log = _concise_wandb_on_log


# After each completed fixed-set evaluation, publish only Pass@1 and Pass@8.
# Coverage/errors/timing remain in summary.json/stdout rather than cluttering W&B.
if not getattr(GSPOEvalCallback._run, "_gspo_eval_passk_wandb", False):
    _original_eval_run = GSPOEvalCallback._run

    def _run_with_passk_wandb(self, state, control=None, *, force: bool = False):
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

        try:
            import wandb
        except ImportError:
            return result
        if wandb.run is not None:
            wandb.log(
                {
                    "eval/pass_at_1": float(summary.get("pass_at_1", 0.0)),
                    "eval/pass_at_8": float(summary.get("pass_at_8", 0.0)),
                }
            )
        return result

    _run_with_passk_wandb._gspo_eval_passk_wandb = True
    GSPOEvalCallback._run = _run_with_passk_wandb
