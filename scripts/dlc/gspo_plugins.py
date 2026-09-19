"""Combined external plugin entrypoint for direct-answer token-level GRPO."""

from scripts.dlc.gspo_reward_plugin import GSPOReward
from scripts.dlc.gspo_trainer_plugin import GSPOEvalCallback

# Core live k/8 curriculum must patch the trainer before observability wrappers
# snapshot those methods.
import scripts.dlc.gspo_direct_curriculum_plugin  # noqa: F401,E402
# Gold auxiliary CE can be present on only one rank in a micro-step. Install the
# distributed-safe loss wrapper before W&B snapshots _compute_loss_and_metrics.
import scripts.dlc.gspo_direct_curriculum_distributed_fix  # noqa: F401,E402
# Keep strict Pass@k success, but preserve GRPO on strict 0/8 groups whenever
# partial verifier rewards still have non-zero variance.
import scripts.dlc.gspo_reward_std_curriculum_plugin  # noqa: F401,E402

# Concise W&B sink + fixed-set evaluation plumbing.
import scripts.dlc.gspo_wandb_plugin as wandb_plugin  # noqa: F401,E402

# Online rollout/eval prompt policy: minimal direct answer, same distribution in
# training and fixed 50-row evaluation.
import scripts.dlc.gspo_reasoning_policy_plugin  # noqa: F401,E402

# Apply CUDA cleanup after the three-seed evaluator is installed.
import scripts.dlc.gspo_eval_cuda_cleanup_plugin  # noqa: F401,E402

# Final eval-only guards: exact clean 50-row set + terminal numeric verifier.
import scripts.dlc.gspo_reasoning_eval_fix_plugin  # noqa: F401,E402

# W&B history-axis and compatibility patches.
import scripts.dlc.gspo_wandb_timeseries_fix  # noqa: F401,E402
import scripts.dlc.gspo_wandb_run_compat_plugin  # noqa: F401,E402
# Publish Pass@1/Pass@8 for each of the three fixed eval seeds.
import scripts.dlc.gspo_eval_seed_wandb_plugin  # noqa: F401,E402

# Final rollout-success threshold and concise console output.
import scripts.dlc.gspo_console_plugin as console_plugin  # noqa: F401,E402

# Keep full resume state only in the newest step checkpoint.
import scripts.dlc.gspo_latest_state_plugin  # noqa: F401,E402


# Direct-answer runs do not publish response/reasoning-length series. The old
# synthetic-gold metric is replaced by the auxiliary-SFT metrics below.
_REMOVED_WANDB_KEYS = {
    "reasoning/too_short_ratio",
    "completions/min_length",
    "completions/mean_length",
    "completions/max_length",
    "completions/clipped_ratio",
    "intervention/gold_group_ratio",
}
wandb_plugin.TRAIN_WANDB_KEYS.difference_update(_REMOVED_WANDB_KEYS)
wandb_plugin.TRAIN_WANDB_KEYS.update(
    {
        "group/k_mean",
        *(f"group/k{k}" for k in range(9)),
        "group/rl_effective_ratio",
        "gold/inject_ratio",
        "gold/sft_weight_mean",
        "gold/ce_loss",
        "sampling/resample_rounds",
        "sampling/zero_resample_ratio",
    }
)

# Keep stdout aligned with the same direct-answer diagnostics. This does not
# affect Trainer state; it only changes the concise console view.
if hasattr(console_plugin, "_CONSOLE_TRAIN_KEYS"):
    console_plugin._CONSOLE_TRAIN_KEYS.difference_update(_REMOVED_WANDB_KEYS)
    console_plugin._CONSOLE_TRAIN_KEYS.update(
        {
            "group/k_mean",
            *(f"group/k{k}" for k in range(9)),
            "group/rl_effective_ratio",
            "gold/inject_ratio",
            "gold/sft_weight_mean",
            "gold/ce_loss",
            "sampling/resample_rounds",
            "sampling/zero_resample_ratio",
        }
    )
