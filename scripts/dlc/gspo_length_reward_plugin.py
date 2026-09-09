"""Post-selection length reward shaping for reasoning rollouts."""

from __future__ import annotations

import os

import scripts.dlc.gspo_wandb_plugin as wandb_plugin
from scripts.dlc.gspo_trainer_plugin import GSPOGRPOTrainer


if not getattr(GSPOGRPOTrainer._dynamic_sampling, "_gspo_post_selection_length_shaping", False):
    _original_dynamic_sampling = GSPOGRPOTrainer._dynamic_sampling

    def _dynamic_sampling_with_length_shaping(self, samples, rewards_per_func):
        import torch

        selected_samples, rewards = _original_dynamic_sampling(
            self, samples, rewards_per_func
        )

        long_tokens = int(os.environ.get("GSPO_REASONING_LONG_TOKENS", "400"))
        penalty = float(os.environ.get("GSPO_REASONING_LENGTH_PENALTY", "0.3"))
        shortest_bonus = float(os.environ.get("GSPO_REASONING_SHORTEST_BONUS", "0.1"))

        local_lengths = torch.tensor(
            [wandb_plugin._reasoning_token_count(self, sample) for sample in selected_samples],
            dtype=torch.long,
            device=self.accelerator.device,
        )
        lengths = self.accelerator.gather_for_metrics(local_lengths).reshape(-1)

        shaped = rewards.clone()
        base_correct = shaped[:, 0] == 1.0
        generations = int(self.num_generations)
        grouped_lengths = lengths.view(-1, generations)

        shortest_three = torch.zeros_like(grouped_lengths, dtype=torch.bool)
        shortest_three.scatter_(
            1,
            torch.argsort(grouped_lengths, dim=1)[:, :3],
            True,
        )
        shaped[shortest_three.reshape(-1), 0] -= penalty
        shaped[lengths > long_tokens, 0] -= penalty

        eligible = (base_correct & (lengths <= long_tokens)).view(-1, generations)
        masked_lengths = grouped_lengths.masked_fill(
            ~eligible, torch.iinfo(torch.long).max
        )
        shortest_correct = eligible & (
            grouped_lengths == masked_lengths.min(dim=1, keepdim=True).values
        )
        shaped[shortest_correct.reshape(-1), 0] += shortest_bonus

        return selected_samples, shaped

    _dynamic_sampling_with_length_shaping._gspo_post_selection_length_shaping = True
    GSPOGRPOTrainer._dynamic_sampling = _dynamic_sampling_with_length_shaping
