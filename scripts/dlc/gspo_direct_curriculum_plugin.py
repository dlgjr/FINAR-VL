"""Direct-answer GRPO curriculum driven by each live Pass@8 rollout group.

This plugin keeps the dataset immutable: k/8 is recomputed from the current
policy's verifier rewards every generation batch. It adds three interventions:

1. Same-prompt retry once for groups that are 0/8 on the first draw.
2. Per-group GRPO advantage weighting: 0/8 and 8/8 skip RL, 6/8 and 7/8 are
   down-weighted, and 1/8..5/8 keep full GRPO weight.
3. One direct-answer gold target for k<=2, trained with an auxiliary CE term.
   The gold target never receives synthetic GRPO reward and never contributes
   policy advantage; its SFT weight is a local learning-rate multiplier.
"""

from __future__ import annotations

import copy
import json
import os

from scripts.dlc.gspo_trainer_plugin import GSPOGRPOTrainer


_SUCCESS_THRESHOLD = 0.5


def _group_correct_counts(self, rewards_per_func):
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
    counts = (grouped > _SUCCESS_THRESHOLD).sum(dim=1).long()
    return grouped, finite, counts


def _group_rl_weight(k: int) -> float:
    defaults = {
        0: 0.0,
        1: 1.0,
        2: 1.0,
        3: 1.0,
        4: 1.0,
        5: 1.0,
        6: 0.7,
        7: 0.35,
        8: 0.0,
    }
    return float(os.environ.get(f"GSPO_GROUP_WEIGHT_K{k}", str(defaults[k])))


def _gold_sft_weight(k: int) -> float:
    max_correct = int(os.environ.get("GSPO_GOLD_SFT_MAX_CORRECT", "2"))
    if k > max_correct:
        return 0.0
    defaults = {0: 2.0, 1: 1.0, 2: 0.5}
    return float(
        os.environ.get(
            f"GSPO_GOLD_SFT_WEIGHT_K{k}",
            str(defaults.get(k, 0.0)),
        )
    )


def _initial_rollout_metrics(self, rewards_per_func):
    import torch

    _grouped, finite, counts = _group_correct_counts(self, rewards_per_func)
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
        [_group_rl_weight(int(k)) > 0 for k in counts.tolist()],
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


# Replace the trainer's older >0 / synthetic-gold rollout metrics with the live
# verifier-success definition used by the new curriculum.
GSPOGRPOTrainer._initial_rollout_metrics = _initial_rollout_metrics


def _direct_gold_sample(sample, *, sft_weight: float):
    final_answer = str((getattr(sample, "extra", {}) or {}).get("gold_final_answer") or "").strip()
    if not final_answer:
        final_answer = str((getattr(sample, "extra", {}) or {}).get("answer") or "").strip()
    if not final_answer:
        return None

    gold = copy.deepcopy(sample)
    if gold.messages and gold.messages[-1].get("role") == "assistant":
        gold.messages[-1] = {"role": "assistant", "content": final_answer}
    else:
        gold.messages.append({"role": "assistant", "content": final_answer})

    gold.response_token_ids = []
    gold.response_loss_mask = []
    gold.rollout_logprobs = []
    gold.finish_reason = "stop"
    gold.add_eos = False
    gold.encoded = None
    gold.routed_experts = None
    gold.rollout_infos = {}
    gold.extra["_gold_injected"] = True
    gold.extra["_gspo_gold_sft_weight"] = float(sft_weight)
    # Gold is supervised-only: never let it consume an on-policy advantage.
    gold.extra["_gspo_rl_weight"] = 0.0
    return gold


def _clone_for_reroll(samples):
    reroll = copy.deepcopy(samples)
    for sample in reroll:
        sample.response_token_ids = []
        sample.response_loss_mask = []
        sample.rollout_logprobs = []
        sample.finish_reason = None
        sample.add_eos = False
        sample.encoded = None
        sample.routed_experts = None
        sample.rollout_infos = {}
        for key in (
            "_gold_injected",
            "_gspo_gold_sft_weight",
            "_gspo_rl_weight",
            "_gspo_group_k",
        ):
            sample.extra.pop(key, None)
    return reroll


def _annotate_and_inject_gold(self, all_samples, rewards_per_func):
    import torch

    samples = list(all_samples)
    weighted = self._weighted_rewards(rewards_per_func)
    _grouped, finite, counts = _group_correct_counts(self, rewards_per_func)
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
        rl_weight = _group_rl_weight(k)
        sft_weight = _gold_sft_weight(k) if inject_enabled else 0.0
        for sample in samples[start:end]:
            sample.extra["_gspo_group_k"] = k
            sample.extra["_gspo_rl_weight"] = rl_weight
            sample.extra["_gspo_gold_sft_weight"] = 0.0

        if sft_weight <= 0:
            continue

        # Replace a failed completion so every correct online rollout survives.
        group_rewards = weighted[start:end]
        failed = torch.nonzero(
            group_rewards <= _SUCCESS_THRESHOLD,
            as_tuple=False,
        ).flatten()
        target_rel = int(failed[0].item()) if failed.numel() else 0
        target = start + target_rel
        gold = _direct_gold_sample(samples[target], sft_weight=sft_weight)
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
        # Average over all groups so this metric reflects both injection
        # frequency and local SFT multiplier.
        "gold/sft_weight_mean": injected_weight_sum / groups if groups else 0.0,
    }


def _dynamic_sampling(self, samples, rewards_per_func):
    """Retry first-draw 0/8 prompts once, then apply live k/8 curriculum."""
    import torch

    local_size = len(samples)
    all_samples = self._gather_samples_equal_size(samples)
    selected_rewards = rewards_per_func

    _grouped, finite, initial_counts = _group_correct_counts(self, rewards_per_func)
    zero_groups = finite & (initial_counts == 0)
    zero_ratio = (
        float(zero_groups.float().mean().item())
        if zero_groups.numel()
        else 0.0
    )
    resample_rounds = 0

    # Every rank rerolls its same local prompts when any global group is 0/8.
    # This keeps the collective vLLM call shape identical on all four ranks.
    if bool(zero_groups.any()) and int(self.max_resample_times) > 0:
        reroll_local = _clone_for_reroll(samples)
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


GSPOGRPOTrainer._dynamic_sampling = _dynamic_sampling


# Parent GRPO expands scalar group advantages to [B,T]. Apply our curriculum
# weights after that expansion, and pass gold-SFT row weights to loss compute.
_original_postprocess_batch = GSPOGRPOTrainer._postprocess_batch


def _postprocess_batch_with_curriculum(self, samples, batch_encoded_inputs):
    import torch

    _original_postprocess_batch(self, samples, batch_encoded_inputs)
    gas_chunks = self.split_by_mini_batches(samples)
    if len(gas_chunks) != len(batch_encoded_inputs):
        raise RuntimeError(
            f"curriculum batch mismatch: {len(gas_chunks)} vs {len(batch_encoded_inputs)}"
        )

    for batch, batch_encoded in zip(gas_chunks, batch_encoded_inputs):
        grpo_batch = batch_encoded["grpo_batch"]
        device = grpo_batch.completion_mask.device
        rl_weights = torch.tensor(
            [
                float(
                    (getattr(sample, "extra", {}) or {}).get(
                        "_gspo_rl_weight",
                        1.0,
                    )
                )
                for sample in batch
            ],
            dtype=grpo_batch.advantages.dtype,
            device=device,
        )
        grpo_batch.advantages = grpo_batch.advantages * rl_weights.unsqueeze(-1)
        grpo_batch.gspo_gold_sft_weights = torch.tensor(
            [
                float(
                    (getattr(sample, "extra", {}) or {}).get(
                        "_gspo_gold_sft_weight",
                        0.0,
                    )
                )
                for sample in batch
            ],
            dtype=torch.float32,
            device=device,
        )


GSPOGRPOTrainer._postprocess_batch = _postprocess_batch_with_curriculum


# Keep a second handle to the current-policy token log-probs. The trainer's
# existing entropy wrapper consumes its own handle before this outer loss patch
# gets control back.
_original_get_per_token = GSPOGRPOTrainer._get_per_token_logps_and_entropies


def _get_per_token_with_gold_handle(self, *args, **kwargs):
    per_token_logps, entropies = _original_get_per_token(self, *args, **kwargs)
    self._gspo_gold_policy_logps_tensor = per_token_logps
    return per_token_logps, entropies


GSPOGRPOTrainer._get_per_token_logps_and_entropies = _get_per_token_with_gold_handle


_original_compute_loss = GSPOGRPOTrainer._compute_loss_and_metrics


def _compute_loss_with_gold_ce(self, model, model_inputs, grpo_batch):
    loss, metrics_data = _original_compute_loss(
        self,
        model,
        model_inputs,
        grpo_batch,
    )
    current_logps = self.__dict__.pop("_gspo_gold_policy_logps_tensor", None)
    gold_weights = getattr(grpo_batch, "gspo_gold_sft_weights", None)
    if current_logps is None or gold_weights is None:
        return loss, metrics_data

    gold_weights = gold_weights.to(
        device=current_logps.device,
        dtype=current_logps.dtype,
    )
    if not bool((gold_weights > 0).any()):
        return loss, metrics_data

    completion_mask = metrics_data["completion_mask"].to(dtype=current_logps.dtype)
    weighted_mask = completion_mask * gold_weights.unsqueeze(-1)
    gold_token_mask = completion_mask * (gold_weights > 0).to(
        dtype=current_logps.dtype
    ).unsqueeze(-1)
    token_count = gold_token_mask.sum().clamp(min=1.0)

    # Divide by UNWEIGHTED gold-token count so k0/k1/k2 weights genuinely scale
    # the supervised gradient, i.e. act like a per-hardness SFT learning rate.
    gold_ce = -(current_logps * weighted_mask).sum() / token_count
    coef = float(os.environ.get("GSPO_GOLD_SFT_COEF", "1.0"))
    loss = loss + coef * gold_ce

    gathered = self.accelerator.gather_for_metrics(gold_ce.detach())
    metrics_data["gspo_gold_ce_loss"] = float(gathered.nanmean().item())
    return loss, metrics_data


GSPOGRPOTrainer._compute_loss_and_metrics = _compute_loss_with_gold_ce


_original_update_metrics = GSPOGRPOTrainer._update_metrics


def _update_metrics_with_gold_ce(self, metrics_data):
    _original_update_metrics(self, metrics_data)
    value = metrics_data.get("gspo_gold_ce_loss")
    if value is not None:
        mode = metrics_data["mode"]
        self._metrics[mode]["gold/ce_loss"].append(float(value))


GSPOGRPOTrainer._update_metrics = _update_metrics_with_gold_ce
