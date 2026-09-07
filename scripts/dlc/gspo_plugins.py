"""Combined external plugin entrypoint for reward and evaluation callbacks."""

from scripts.dlc.gspo_reward_plugin import GSPOReward
from scripts.dlc.gspo_trainer_plugin import GSPOEvalCallback

# Side-effect patches: concise W&B metrics and raw-policy diagnostics.
import scripts.dlc.gspo_wandb_plugin  # noqa: F401,E402

# Reasoning-policy controls are applied after W&B so they can replace the legacy
# fixed-set evaluation path while keeping the W&B/trainer diagnostics above.
import scripts.dlc.gspo_reasoning_policy_plugin  # noqa: F401,E402

# Apply CUDA cleanup last so it wraps the final three-seed reasoning evaluator.
import scripts.dlc.gspo_eval_cuda_cleanup_plugin  # noqa: F401,E402
