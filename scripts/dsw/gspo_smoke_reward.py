from typing import List

from swift.rewards import ORM, orms


class GSPOSmokeReward(ORM):

    def __call__(
        self,
        completions,
        **kwargs,
    ) -> List[float]:
        rewards = [
            float(index % 2)
            for index in range(len(completions))
        ]

        print(
            "[GSPO_SMOKE_REWARD]",
            "count=",
            len(completions),
            "rewards=",
            rewards,
            flush=True,
        )
        return rewards


orms["gspo_smoke"] = GSPOSmokeReward
