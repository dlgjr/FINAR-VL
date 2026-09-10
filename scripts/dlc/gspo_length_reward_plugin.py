"""Post-selection exactness and length reward shaping for reasoning rollouts."""

from __future__ import annotations

import json
import os

import scripts.dlc.gspo_wandb_plugin as wandb_plugin
from scripts.dlc.gspo_trainer_plugin import GSPOGRPOTrainer
from scripts.rl.gspo_reward import numeric_gold_from_text, score_programmatic_answer


_NUMERIC_VERIFIERS = {"numeric", "numeric_final", "composite_numeric"}

# Expose the two new shaping diagnostics through the existing concise Trainer -> W&B sink.
wandb_plugin.TRAIN_WANDB_KEYS.update(
    {
        "reward/exact_numeric_ratio",
        "reasoning/longest_correct_bonus_ratio",
    }
)


def _list_value(value):
    if isinstance(value, str):
        return json.loads(value)
    return value or []


def _exact_numeric_gold(extra):
    gold_numeric = _list_value(extra.get("gold_numeric"))
    if not gold_numeric:
        gold_numeric = []
        for atom in _list_value(extra.get("gold_atoms")):
            gold_numeric.extend(numeric_gold_from_text(str(atom)))

    exact = []
    for item in gold_numeric:
        spec = dict(item)
        spec["abs_tol"] = "0"
        spec["rel_tol"] = "0"
        spec["aliases"] = [
            {**dict(alias), "abs_tol": "0", "rel_tol": "0"}
            for alias in item.get("aliases", []) or []
        ]
        exact.append(spec)
    return exact


def _sample_exact_numeric(sample) -> tuple[bool, bool]:
    extra = getattr(sample, "extra", {}) or {}
    if extra.get("_gold_injected"):
        return False, False

    verifier_type = str(extra.get("verifier_type", ""))
    if verifier_type not in _NUMERIC_VERIFIERS:
        return False, False

    try:
        exact_gold = _exact_numeric_gold(extra)
    except (TypeError, ValueError, json.JSONDecodeError):
        return True, False
    if not exact_gold:
        return True, False

    score = score_programmatic_answer(
        wandb_plugin._completion_text(sample),
        [],
        verifier_type,
        question=str(extra.get("question", "")),
        gold_numeric=exact_gold,
    )
    return True, score == 1.0


if not getattr(GSPOGRPOTrainer._dynamic_sampling, "_gspo_post_selection_length_shaping", False):
    _original_dynamic_sampling = GSPOGRPOTrainer._dynamic_sampling

    def _dynamic_sampling_with_length_shaping(self, samples, rewards_per_func):
        import torch

        selected_samples, rewards = _original_dynamic_sampling(
            self, samples, rewards_per_func
        )

        long_tokens = int(os.environ.get("GSPO_REASONING_LONG_TOKENS", "400"))
        penalty = float(os.environ.get("GSPO_REASONING_LENGTH_PENALTY", "0.3"))
        exact_bonus = float(os.environ.get("GSPO_EXACT_NUMERIC_BONUS", "0.2"))
        longest_bonus = float(os.environ.get("GSPO_REASONING_LONGEST_CORRECT_BONUS", "0.1"))

        local_lengths = torch.tensor(
            [wandb_plugin._reasoning_token_count(self, sample) for sample in selected_samples],
            dtype=torch.long,
            device=self.accelerator.device,
        )
        lengths = self.accelerator.gather_for_metrics(local_lengths).reshape(-1)

        local_numeric = []
        local_exact = []
        local_injected = []
        for sample in selected_samples:
            is_numeric, is_exact = _sample_exact_numeric(sample)
            local_numeric.append(is_numeric)
            local_exact.append(is_exact)
            local_injected.append(bool((getattr(sample, "extra", {}) or {}).get("_gold_injected")))

        numeric_mask = self.accelerator.gather_for_metrics(
            torch.tensor(local_numeric, dtype=torch.bool, device=self.accelerator.device)
        ).reshape(-1)
        exact_mask = self.accelerator.gather_for_metrics(
            torch.tensor(local_exact, dtype=torch.bool, device=self.accelerator.device)
        ).reshape(-1)
        injected_mask = self.accelerator.gather_for_metrics(
            torch.tensor(local_injected, dtype=torch.bool, device=self.accelerator.device)
        ).reshape(-1)

        shaped = rewards.clone()
        base_correct = rewards[:, 0] == 1.0
        generations = int(self.num_generations)
        grouped_lengths = lengths.view(-1, generations)

        # Preserve the existing anti-collapse / anti-verbosity boundaries.
        shortest_three = torch.zeros_like(grouped_lengths, dtype=torch.bool)
        shortest_three.scatter_(
            1,
            torch.argsort(grouped_lengths, dim=1)[:, :3],
            True,
        )
        shaped[shortest_three.reshape(-1), 0] -= penalty
        shaped[lengths > long_tokens, 0] -= penalty

        # A tolerance-window hit remains correct at 1.0. Only an exact numeric
        # match under zero abs/rel tolerance receives the extra precision bonus.
        exact_bonus_mask = base_correct & exact_mask & ~injected_mask
        shaped[exact_bonus_mask, 0] += exact_bonus

        # Replace the old shortest-correct bonus with one longest correct online
        # response per Pass@8 group, capped at the existing 400-token boundary.
        eligible = (
            base_correct & ~injected_mask & (lengths <= long_tokens)
        ).view(-1, generations)
        masked_lengths = grouped_lengths.masked_fill(~eligible, -1)
        longest_correct = torch.zeros_like(eligible, dtype=torch.bool)
        longest_index = masked_lengths.argmax(dim=1, keepdim=True)
        longest_correct.scatter_(1, longest_index, True)
        longest_correct &= eligible.any(dim=1, keepdim=True)
        longest_bonus_mask = longest_correct.reshape(-1)
        shaped[longest_bonus_mask, 0] += longest_bonus

        online_numeric = numeric_mask & ~injected_mask
        numeric_count = int(online_numeric.sum().item())
        self._record_concise_train_metrics(
            {
                "reward/exact_numeric_ratio": (
                    float((exact_mask & online_numeric).sum().item()) / numeric_count
                    if numeric_count
                    else 0.0
                ),
                "reasoning/longest_correct_bonus_ratio": float(
                    longest_bonus_mask.float().mean().item()
                ),
            }
        )

        return selected_samples, shaped

    _dynamic_sampling_with_length_shaping._gspo_post_selection_length_shaping = True
    GSPOGRPOTrainer._dynamic_sampling = _dynamic_sampling_with_length_shaping
