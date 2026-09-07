"""Combined external plugin entrypoint for reward and evaluation callbacks."""

from scripts.dlc.gspo_reward_plugin import GSPOReward
from scripts.dlc.gspo_trainer_plugin import GSPOEvalCallback

# Side-effect patches: concise W&B metrics and raw-policy diagnostics.
import scripts.dlc.gspo_wandb_plugin  # noqa: F401,E402

# Reasoning-policy controls are applied after W&B so they can replace the legacy
# fixed-set evaluation path while keeping the W&B/trainer diagnostics above.
import scripts.dlc.gspo_reasoning_policy_plugin  # noqa: F401,E402
import scripts.dlc.gspo_length_reward_plugin  # noqa: F401,E402

# Apply CUDA cleanup after the final three-seed reasoning evaluator is installed.
import scripts.dlc.gspo_eval_cuda_cleanup_plugin  # noqa: F401,E402

# Final eval-only guards: force the exact clean 50-row set and relax only
# presentation units omitted by the benchmark reference. Training reward is unchanged.
import scripts.dlc.gspo_reasoning_eval_fix_plugin  # noqa: F401,E402
