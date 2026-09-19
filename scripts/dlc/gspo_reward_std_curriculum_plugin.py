"""Keep strict Pass@k success while using reward variance to gate k=0 GRPO."""

from __future__ import annotations

import json
import os

import scripts.dlc.gspo_direct_curriculum_plugin as curriculum
from scripts.dlc.gspo_trainer_plugin import GSPOGRPOTrainer


def _strict_success_mask(rewards):
    """Compare in float64 so a threshold just below 1.0 stays below 1.0."""
    return rewards.double() > float(curriculum._SUCCESS_THRESHOLD)


def _strict_group_correct_counts(self, rewards_per_func):
    import torch

    rewards = self._weighted_rewards(rewards_per_func).float()
    generations = int(self.num_generations)
    if generations != 8:
        raise RuntimeError(f"direct curriculum requires num_generations=8, got {generations}")
    if rewards.numel() % generations:
        raise RuntimeError(
            f"Pass@8 rewards must be divisible by {generations}, got {rewards.numel()}"
        )
    grouped = rewards.view(-1, generations)
    finite = torch.isfinite(grouped).all(dim=1)
    counts = _strict_success_mask(grouped).sum(dim=1).long()
    return grouped, finite, counts


# The strict threshold is set to 0.999999999999 by the distributed fix. A
# float32 comparison rounds that scalar to 1.0 and makes `1.0 > threshold`
# false. Replace the shared group counter with an identical float64 comparison.
curriculum._group_correct_counts = _strict_group_correct_counts


def _group_has_reward_signal(group_rewards) -> bool:
    return bool(group_rewards.float().std(unbiased=False).item() > 0.0)


def _group_rl_weight(k: int, group_rewards) -> float:
    if k == 0 and _group_has_reward_signal(group_rewards):
        return 1.0
    return curriculum._group_rl_weight(k)


def _initial_rollout_metrics(self, rewards_per_func):
    import torch

    grouped, finite, counts = curriculum._group_correct_counts(self, rewards_per_func)
    grouped = grouped[finite]
    counts = counts[finite]
    if counts.numel() == 0:
        metrics = {
            "rollout/pass8": 0.0,
            "rollout/positive_per_8": 0.0,
            "rollout/all8": 0.0,
            "group/k_mean": 0.0,
            "group/rl_effective_ratio": 0.0,
        }
        metrics.update({f"group/k{k}": 0.0 for k in range(9)})
        return metrics

    rl_active = torch.tensor(
        [
            _group_rl_weight(int(k), group_rewards) > 0
            for k, group_rewards in zip(counts.tolist(), grouped)
        ],
        dtype=torch.float32,
        device=counts.device,
    )
    metrics = {
        "rollout/pass8": float((counts > 0).float().mean().item()),
        "rollout/positive_per_8": float(counts.float().mean().item()),
        "rollout/all8": float((counts == 8).float().mean().item()),
        "group/k_mean": float(counts.float().mean().item()),
        "group/rl_effective_ratio": float(rl_active.mean().item()),
    }
    for k in range(9):
        metrics[f"group/k{k}"] = float((counts == k).float().mean().item())
    return metrics


def _annotate_and_inject_gold(self, all_samples, rewards_per_func):
    import torch

    samples = list(all_samples)
    weighted = self._weighted_rewards(rewards_per_func)
    grouped, finite, counts = curriculum._group_correct_counts(self, rewards_per_func)
    generations = int(self.num_generations)
    inject_enabled = os.environ.get("GSPO_GOLD_INJECT", "true").lower() == "true"

    injected = 0
    injected_weight_sum = 0.0
    for group_index, k_tensor in enumerate(counts):
        start = group_index * generations
        end = start + generations

        if not bool(finite[group_index]):
            for sample in samples[start:end]:
                sample.extra["_gspo_group_k"] = -1
                sample.extra["_gspo_rl_weight"] = 0.0
                sample.extra["_gspo_gold_sft_weight"] = 0.0
            continue

        k = int(k_tensor.item())
        rl_weight = _group_rl_weight(k, grouped[group_index])
        sft_weight = curriculum._gold_sft_weight(k) if inject_enabled else 0.0
        for sample in samples[start:end]:
            sample.extra["_gspo_group_k"] = k
            sample.extra["_gspo_rl_weight"] = rl_weight
            sample.extra["_gspo_gold_sft_weight"] = 0.0

        if sft_weight <= 0:
            continue

        group_rewards = weighted[start:end]
        failed = torch.nonzero(
            ~_strict_success_mask(group_rewards),
            as_tuple=False,
        ).flatten()
        target_rel = int(failed[0].item()) if failed.numel() else 0
        target = start + target_rel
        gold = curriculum._direct_gold_sample(samples[target], sft_weight=sft_weight)
        if gold is None:
            raise RuntimeError(
                f"hard Pass@8 group k={k} has no gold_final_answer for auxiliary SFT"
            )
        gold.extra["_gspo_group_k"] = k
        samples[target] = gold
        injected += 1
        injected_weight_sum += sft_weight

    groups = int(counts.numel())
    return samples, {
        "gold/inject_ratio": injected / groups if groups else 0.0,
        "gold/sft_weight_mean": injected_weight_sum / groups if groups else 0.0,
    }


def _dynamic_sampling(self, samples, rewards_per_func):
    """Retry only strict 0/8 groups with zero reward variance."""
    import torch

    local_size = len(samples)
    all_samples = self._gather_samples_equal_size(samples)
    selected_rewards = rewards_per_func

    grouped, finite, initial_counts = curriculum._group_correct_counts(self, rewards_per_func)
    reward_signal = grouped.float().std(dim=1, unbiased=False) > 0
    zero_groups = finite & (initial_counts == 0) & (~reward_signal)
    zero_ratio = (
        float(zero_groups.float().mean().item())
        if zero_groups.numel()
        else 0.0
    )
    resample_rounds = 0

    if bool(zero_groups.any()) and int(self.max_resample_times) > 0:
        reroll_local = curriculum._clone_for_reroll(samples)
        reroll_local = self._generate_completions(reroll_local)
        reroll_rewards = self._compute_rewards_per_func(reroll_local)
        reroll_all = self._gather_samples_equal_size(reroll_local)

        generations = int(self.num_generations)
        chosen_samples = list(all_samples)
        chosen_rewards = rewards_per_func.clone()
        for group_index, use_reroll in enumerate(zero_groups.tolist()):
            if not use_reroll:
                continue
            start = group_index * generations
            end = start + generations
            chosen_samples[start:end] = reroll_all[start:end]
            chosen_rewards[start:end] = reroll_rewards[start:end]

        all_samples = chosen_samples
        selected_rewards = chosen_rewards
        resample_rounds = 1

    annotated_samples, gold_metrics = _annotate_and_inject_gold(
        self,
        all_samples,
        selected_rewards,
    )
    metrics = _initial_rollout_metrics(self, selected_rewards)
    metrics["sampling/resample_rounds"] = float(resample_rounds)
    metrics["sampling/zero_resample_ratio"] = zero_ratio
    metrics.update(gold_metrics)
    self._record_concise_train_metrics(metrics)

    if self.accelerator.is_main_process:
        print(
            "[GSPO-TRAIN-CORE] "
            + json.dumps(metrics, ensure_ascii=False, sort_keys=True),
            flush=True,
        )

    process_slice = slice(
        self.accelerator.process_index * local_size,
        (self.accelerator.process_index + 1) * local_size,
    )
    return annotated_samples[process_slice], selected_rewards


curriculum._initial_rollout_metrics = _initial_rollout_metrics
curriculum._annotate_and_inject_gold = _annotate_and_inject_gold
curriculum._dynamic_sampling = _dynamic_sampling
GSPOGRPOTrainer._initial_rollout_metrics = _initial_rollout_metrics
GSPOGRPOTrainer._dynamic_sampling = _dynamic_sampling
