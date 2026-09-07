"""Combined external plugin entrypoint for reward and evaluation callbacks."""

from scripts.dlc.gspo_reward_plugin import GSPOReward
from scripts.dlc.gspo_trainer_plugin import GSPOEvalCallback

# Side-effect patches: concise W&B metrics and raw-policy diagnostics.
import scripts.dlc.gspo_wandb_plugin  # noqa: F401,E402

# Reasoning-policy controls are applied last so they can override the old fixed-20
# evaluation wrapper while keeping the W&B/trainer diagnostics above.
import scripts.dlc.gspo_reasoning_policy_plugin  # noqa: F401,E402
