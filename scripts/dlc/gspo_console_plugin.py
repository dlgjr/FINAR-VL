"""Final rollout-success threshold and concise training console output."""

from __future__ import annotations

import os

from scripts.dlc.gspo_trainer_plugin import GSPOGRPOTrainer


# Keep the existing rollout metric names, but count a completion as successful
# only when it receives a full verifier reward. Fractional Jaccard/partial
# rewards are useful GRPO signal but are not a Pass@k success.
_original_initial_rollout_metrics = GSPOGRPOTrainer._initial_rollout_metrics


def _initial_rollout_metrics_success_full(self, rewards_per_func):
    import torch

    metrics = _original_initial_rollout_metrics(self, rewards_per_func)
    grouped = self._weighted_rewards(rewards_per_func).float().view(-1, 8)
    grouped = grouped[torch.isfinite(grouped).all(dim=1)]
    if grouped.numel() == 0:
        metrics["rollout/pass8"] = 0.0
        metrics["rollout/positive_per_8"] = 0.0
        return metrics

    threshold = float(os.environ.get("GSPO_SUCCESS_THRESHOLD", "0.999999999999"))
    positive_count = (grouped > threshold).sum(dim=1).float()
    metrics["rollout/pass8"] = float((positive_count > 0).float().mean().item())
    metrics["rollout/positive_per_8"] = float(positive_count.mean().item())
    return metrics


GSPOGRPOTrainer._initial_rollout_metrics = _initial_rollout_metrics_success_full


# Filter only the stdout/logging.jsonl view. Trainer metrics and W&B still
# receive the original full log dictionary.
_CONSOLE_TRAIN_KEYS = {
    "reward",
    "reward_std",
    "rollout/raw_reward_mean",
    "rollout/pass8",
    "rollout/positive_per_8",
    "rollout/raw_zero_std_group_ratio",
    "sampling/resample_rounds",
    "reasoning/too_short_ratio",
    "intervention/gold_group_ratio",
    "kl",
    "ess/ratio",
    "clip_ratio/region_mean",
    "entropy/mean",
    "completions/mean_length",
    "completions/clipped_ratio",
}


def _console_logs(logs):
    return {
        key: value
        for key, value in (logs or {}).items()
        if key.removeprefix("train/") in _CONSOLE_TRAIN_KEYS
    }


import swift.trainers.patcher as swift_patcher


def _patch_console_callback(callback_cls):
    original_on_log = callback_cls.on_log

    def _concise_on_log(self, args, state, control, logs=None, **kwargs):
        return original_on_log(
            self,
            args,
            state,
            control,
            logs=_console_logs(logs),
            **kwargs,
        )

    callback_cls.on_log = _concise_on_log


_patch_console_callback(swift_patcher.ProgressCallbackNew)
_patch_console_callback(swift_patcher.PrinterCallbackNew)
