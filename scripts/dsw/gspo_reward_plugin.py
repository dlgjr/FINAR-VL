"""DSW import path for the same pure mixed reward implementation used on DLC."""

from scripts.dlc.gspo_reward_plugin import GSPOReward, records_from_kwargs
from swift.rewards import orms

orms["gspo_mixed"] = GSPOReward

