"""Distributed-safety and pass/fail fixes for direct-answer GRPO curriculum.

The core curriculum injects at most one gold row per hard global Pass@8 group.
With per-device batch size 1, a given micro-step can therefore contain a gold
row on only one rank. Metric collectives must still be entered by every rank;
otherwise the first asymmetric gold micro-step deadlocks DDP.

Pass@k counts must also reflect full verifier success, not merely a partial
Jaccard reward. A reward of 1.0 is a pass; fractional rewards remain failures
for k/8 routing while still contributing normally to GRPO where that group is
kept.
"""

from __future__ import annotations

import os

import scripts.dlc.gspo_direct_curriculum_plugin as curriculum
from scripts.dlc.gspo_trainer_plugin import GSPOGRPOTrainer


# The curriculum uses `reward > _SUCCESS_THRESHOLD`.  Put the threshold just
# below one so only a full verifier reward (1.0, up to floating-point noise)
# counts toward k/8.  This matters for composite/choice rewards where partial
# matches can be > 0.5 without being correct.
curriculum._SUCCESS_THRESHOLD = float(
    os.environ.get("GSPO_SUCCESS_THRESHOLD", "0.999999999999")
)


def _compute_loss_with_distributed_gold_ce(self, model, model_inputs, grpo_batch):
    import torch

    original_completion_mask = grpo_batch.completion_mask
    rl_row_weights = getattr(grpo_batch, "gspo_rl_row_weights", None)
    if rl_row_weights is not None:
        # k=0 and k=8 are true RL skips. Gold rows also have RL weight 0;
        # their supervised CE below still uses the original completion mask.
        skip_rows = rl_row_weights.to(device=original_completion_mask.device) <= 0
        if bool(skip_rows.any()):
            grpo_batch.completion_mask = original_completion_mask & (~skip_rows.unsqueeze(-1))

    try:
        loss, metrics_data = curriculum._original_compute_loss(
            self,
            model,
            model_inputs,
            grpo_batch,
        )
    finally:
        grpo_batch.completion_mask = original_completion_mask

    current_logps = self.__dict__.pop("_gspo_gold_policy_logps_tensor", None)
    gold_weights = getattr(grpo_batch, "gspo_gold_sft_weights", None)
    if current_logps is None or gold_weights is None:
        return loss, metrics_data

    gold_weights = gold_weights.to(
        device=current_logps.device,
        dtype=current_logps.dtype,
    )
    completion_mask = original_completion_mask.to(dtype=current_logps.dtype)
    weighted_mask = completion_mask * gold_weights.unsqueeze(-1)
    gold_token_mask = completion_mask * (gold_weights > 0).to(
        dtype=current_logps.dtype
    ).unsqueeze(-1)

    # Local loss: a rank without a gold row contributes exactly zero CE. DDP
    # then averages the active supervised gradient together with the other ranks.
    local_gold_tokens = gold_token_mask.sum()
    local_nll_sum = -(current_logps * weighted_mask).sum()
    local_gold_ce = local_nll_sum / local_gold_tokens.clamp(min=1.0)
    coef = float(os.environ.get("GSPO_GOLD_SFT_COEF", "1.0"))
    loss = loss + coef * local_gold_ce

    # IMPORTANT: every rank enters this collective on every micro-step. The
    # previous implementation returned early on non-gold ranks, which could
    # deadlock when only one rank owned the injected gold row.
    local_stats = torch.stack(
        [local_nll_sum.detach().float(), local_gold_tokens.detach().float()]
    ).reshape(1, 2)
    gathered_stats = self.accelerator.gather_for_metrics(local_stats)
    global_nll_sum = gathered_stats[:, 0].sum()
    global_gold_tokens = gathered_stats[:, 1].sum()
    if bool(global_gold_tokens > 0):
        metrics_data["gspo_gold_ce_loss"] = float(
            (global_nll_sum / global_gold_tokens).item()
        )

    return loss, metrics_data


# Install before the W&B wrapper snapshots _compute_loss_and_metrics.
GSPOGRPOTrainer._compute_loss_and_metrics = _compute_loss_with_distributed_gold_ce
