"""Combined external plugin entrypoint for reward and evaluation callbacks."""

from scripts.dlc.gspo_reward_plugin import GSPOReward
from scripts.dlc.gspo_trainer_plugin import GSPOEvalCallback

# Side-effect patches: concise W&B metrics, fixed rl_test evaluation routing,
# entropy dashboard metrics, and eval Pass@k logging.
import scripts.dlc.gspo_wandb_plugin  # noqa: F401,E402
