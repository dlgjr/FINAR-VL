"""Drive dynamic resampling from raw verifier rewards only."""

from __future__ import annotations

import os

from scripts.dlc.gspo_trainer_plugin import GSPOGRPOTrainer


# Snapshot the reward tensor immediately after the verifier returns it. Later
# reward shaping/penalties must not decide whether a Pass@8 group is resampled.
if not getattr(GSPOGRPOTrainer._compute_rewards_per_func, "_gspo_raw_reward_snapshot", False):
    _original_compute_rewards_per_func = GSPOGRPOTrainer._compute_rewards_per_func

    def _compute_rewards_with_raw_snapshot(self, samples):
        rewards = _original_compute_rewards_per_func(self, samples)
        self._gspo_raw_rewards_per_func = rewards.detach().clone()
        return rewards

    _compute_rewards_with_raw_snapshot._gspo_raw_reward_snapshot = True
    GSPOGRPOTrainer._compute_rewards_per_func = _compute_rewards_with_raw_snapshot


# Keep groups only when the original verifier reward has non-zero within-group
# variance. At the final attempt, Gold injection is allowed to create variance
# for final selection. Increase the retry budget from 3 to 4.
if not getattr(GSPOGRPOTrainer._dynamic_sampling, "_gspo_raw_reward_resampling", False):
    _original_dynamic_sampling = GSPOGRPOTrainer._dynamic_sampling

    def _dynamic_sampling_with_raw_rewards(self, samples, rewards_per_func):
        import torch

        original_compute_std = self.compute_std
        original_max_resample_times = self.max_resample_times

        def _raw_reward_std(samples_for_std, rewards_for_std):
            raw_rewards = getattr(self, "_gspo_raw_rewards_per_func", None)
            if raw_rewards is None or raw_rewards.shape != rewards_for_std.shape:
                return original_compute_std(samples_for_std, rewards_for_std)

            # Gold injection happens only on the final attempt and raises one
            # reward above its raw verifier value. Use that injected tensor for
            # final selection so Gold keeps its existing fallback semantics.
            if bool(torch.any(rewards_for_std > raw_rewards + 1e-12)):
                return original_compute_std(samples_for_std, rewards_for_std)
            return original_compute_std(samples_for_std, raw_rewards)

        self.compute_std = _raw_reward_std
        self.max_resample_times = int(os.environ.get("GSPO_RAW_MAX_RESAMPLE_TIMES", "4"))
        try:
            return _original_dynamic_sampling(self, samples, rewards_per_func)
        finally:
            self.compute_std = original_compute_std
            self.max_resample_times = original_max_resample_times

    _dynamic_sampling_with_raw_rewards._gspo_raw_reward_resampling = True
    GSPOGRPOTrainer._dynamic_sampling = _dynamic_sampling_with_raw_rewards
