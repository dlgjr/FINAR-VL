"""Post-selection exactness and length reward shaping for reasoning rollouts."""

from __future__ import annotations

import json
import os
from decimal import ROUND_HALF_UP, Decimal

import scripts.dlc.gspo_wandb_plugin as wandb_plugin
from scripts.dlc.gspo_trainer_plugin import GSPOGRPOTrainer
import scripts.rl.gspo_reward as reward_module


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


def _equal_numeric(left: Decimal, right: Decimal, places: int | None) -> bool:
    if places is None:
        return left == right
    quantum = Decimal(1).scaleb(-places)
    return left.quantize(quantum, rounding=ROUND_HALF_UP) == right.quantize(
        quantum, rounding=ROUND_HALF_UP
    )


def _numeric_exact_match(pred, gold, question: str) -> bool:
    places = reward_module._requested_decimal_places(question)

    # Preserve the verifier's existing presentation compatibility while making
    # the numerical comparison exact rather than using the +/-2 precision window.
    if gold.dimension == "scalar" and gold.unit == "":
        return _equal_numeric(pred.value, gold.value, places)

    if pred.dimension == "scalar" and pred.unit == "":
        if _equal_numeric(pred.value, gold.value, places):
            return True
        return _equal_numeric(pred.value / gold.factor, gold.value, places)

    if pred.dimension != gold.dimension:
        return False

    pred_in_gold_unit = pred.base_value / gold.factor
    return _equal_numeric(pred_in_gold_unit, gold.value, places)


def _sample_exact_numeric(sample) -> tuple[bool, bool]:
    extra = getattr(sample, "extra", {}) or {}
    if extra.get("_gold_injected"):
        return False, False

    verifier_type = str(extra.get("verifier_type", ""))
    if verifier_type not in _NUMERIC_VERIFIERS:
        return False, False

    completion = wandb_plugin._completion_text(sample)
    answer = reward_module.extract_final_answer(completion, verifier_type)
    if not answer:
        return True, False

    try:
        pred_values = [
            reward_module._parse_numeric(atom)
            for atom in reward_module._numeric_atoms(answer)
        ]
        gold_numeric = _list_value(extra.get("gold_numeric"))
        if gold_numeric:
            gold_specs = []
            for item in gold_numeric:
                primary = reward_module._structured_numeric(item)
                aliases = [
                    reward_module._structured_numeric(alias)
                    for alias in item.get("aliases", []) or []
                ]
                gold_specs.append((primary, aliases))
        else:
            gold_specs = [
                (reward_module._parse_numeric(str(atom)), [])
                for atom in _list_value(extra.get("gold_atoms"))
            ]
    except (TypeError, ValueError, json.JSONDecodeError):
        return True, False

    if not pred_values or len(pred_values) != len(gold_specs):
        return True, False

    question = str(extra.get("question", ""))
    matched_gold: set[int] = set()
    for pred in pred_values:
        for index, (gold, aliases) in enumerate(gold_specs):
            if index in matched_gold:
                continue
            if any(
                _numeric_exact_match(pred, candidate, question)
                for candidate in (gold, *aliases)
            ):
                matched_gold.add(index)
                break
        else:
            return True, False

    return True, len(matched_gold) == len(gold_specs)


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

        # A tolerance-window hit remains correct at 1.0. Exact numeric agreement
        # receives +0.2 without changing the underlying verifier/eval semantics.
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
