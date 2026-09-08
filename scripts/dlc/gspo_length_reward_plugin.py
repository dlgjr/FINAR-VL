"""Length-based reward shaping for reasoning rollouts."""

from __future__ import annotations

import os

import scripts.dlc.gspo_wandb_plugin as wandb_plugin
from scripts.dlc.gspo_trainer_plugin import GSPOGRPOTrainer


if not getattr(GSPOGRPOTrainer._compute_rewards_per_func, "_gspo_length_reward_shaping", False):
    _original_compute_rewards_per_func = GSPOGRPOTrainer._compute_rewards_per_func

    def _compute_rewards_with_length_shaping(self, samples):
        import torch

        rewards = _original_compute_rewards_per_func(self, samples)
        direct_tokens = int(os.environ.get("GSPO_REASONING_DIRECT_TOKENS", "100"))
        long_tokens = int(os.environ.get("GSPO_REASONING_LONG_TOKENS", "400"))
        penalty = float(os.environ.get("GSPO_REASONING_LENGTH_PENALTY", "0.3"))
        shortest_bonus = float(os.environ.get("GSPO_REASONING_SHORTEST_BONUS", "0.1"))
        all_short_longest_bonus = float(
            os.environ.get("GSPO_REASONING_ALL_SHORT_LONGEST_BONUS", "0.2")
        )

        local_lengths = torch.tensor(
            [wandb_plugin._reasoning_token_count(self, sample) for sample in samples],
            dtype=torch.long,
            device=self.accelerator.device,
        )
        lengths = self.accelerator.gather_for_metrics(local_lengths).reshape(-1)
        if rewards.shape[0] != lengths.numel():
            raise RuntimeError(
                "length reward alignment mismatch: "
                f"rewards={rewards.shape[0]} reasoning_lengths={lengths.numel()}"
            )

        rewards = rewards.clone()
        base_correct = rewards[:, 0] == 1.0
        rewards[lengths < direct_tokens, 0] -= penalty
        rewards[lengths > long_tokens, 0] -= penalty

        generations = int(self.num_generations)
        grouped_lengths = lengths.view(-1, generations)

        eligible = (
            base_correct & (lengths >= direct_tokens) & (lengths <= long_tokens)
        ).view(-1, generations)
        masked_lengths = grouped_lengths.masked_fill(
            ~eligible, torch.iinfo(torch.long).max
        )
        shortest = eligible & (
            grouped_lengths == masked_lengths.min(dim=1, keepdim=True).values
        )
        rewards[shortest.reshape(-1), 0] += shortest_bonus

        all_short = (grouped_lengths < direct_tokens).all(dim=1)
        all_short_longest = torch.zeros_like(grouped_lengths, dtype=torch.bool)
        short_rows = torch.nonzero(all_short, as_tuple=False).reshape(-1)
        if short_rows.numel():
            longest_index = grouped_lengths[short_rows].argmax(dim=1)
            all_short_longest[short_rows, longest_index] = True
            rewards[all_short_longest.reshape(-1), 0] += all_short_longest_bonus

        return rewards

    _compute_rewards_with_length_shaping._gspo_length_reward_shaping = True
    GSPOGRPOTrainer._compute_rewards_per_func = _compute_rewards_with_length_shaping
