"""ms-swift reward plugin for the full mixed GSPO run."""

from __future__ import annotations

import json
import os
import time
from statistics import mean, pstdev
from typing import Any, Mapping, Sequence

from scripts.rl.gspo_reward import MixedReward
from scripts.rl.judge_client import judge_from_record

try:
    from swift.rewards import ORM, orms
except ImportError:  # pragma: no cover - DLC supplies ms-swift
    class ORM:  # type: ignore[no-redef]
        pass

    orms: dict[str, Any] = {}  # type: ignore[no-redef]


def _column(kwargs: Mapping[str, Any], name: str, index: int, default: Any) -> Any:
    value = kwargs.get(name)
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return value[index] if index < len(value) else default
    return default if value is None else value


def records_from_kwargs(kwargs: Mapping[str, Any], count: int) -> list[dict[str, Any]]:
    supplied = kwargs.get("records", kwargs.get("data"))
    if isinstance(supplied, Sequence) and not isinstance(supplied, (str, bytes)) and supplied and isinstance(supplied[0], Mapping):
        return [dict(supplied[index]) if index < len(supplied) else {} for index in range(count)]
    records = []
    for index in range(count):
        def value(name: str, default: Any) -> Any:
            item = _column(kwargs, name, index, default)
            if isinstance(item, str) and name in {"gold_atoms", "gold_numeric", "gold_claims", "gold_claim_details"}:
                try:
                    return json.loads(item)
                except json.JSONDecodeError:
                    return [item]
            return item

        records.append(
            {
                "sample_id": value("sample_id", f"batch:{index}"),
                "source": value("source", ""),
                "verifier_type": value("verifier_type", "model_judge"),
                "gold_atoms": value("gold_atoms", []),
                "gold_numeric": value("gold_numeric", []),
                "gold_claims": value("gold_claims", []),
                "gold_claim_details": value("gold_claim_details", []),
                "question": value("question", ""),
                "solution": value("solution", ""),
                "estimated_cost": value("estimated_cost", 0),
            }
        )
    return records


class GSPOReward(ORM):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.completed = 0

    def __call__(self, completions, **kwargs) -> list[float]:
        started = time.perf_counter()
        records = records_from_kwargs(kwargs, len(completions))
        scorer = MixedReward(judge=judge_from_record)
        rewards = scorer(completions, records=records)
        self.completed += len(completions)
        pool_path = os.environ.get("GSPO_REWARD_POOL")
        if pool_path:
            os.makedirs(os.path.dirname(pool_path) or ".", exist_ok=True)
            with open(pool_path, "a", encoding="utf-8") as handle:
                for completion, record, reward in zip(completions, records, rewards):
                    handle.write(
                        json.dumps(
                            {
                                "sample_id": str(record.get("sample_id", "")),
                                "source": record.get("source", ""),
                                "completion": str(completion),
                                "reward": float(reward),
                                "verifier_type": record.get("verifier_type"),
                                "gold_atoms": record.get("gold_atoms", []),
                                "gold_numeric": record.get("gold_numeric", []),
                                "gold_claims": record.get("gold_claims", []),
                                "gold_claim_details": record.get("gold_claim_details", []),
                                "solution": record.get("solution", ""),
                                "question": record.get("question", ""),
                                "parser_result": record.get("_parser_result"),
                                "judge_json": record.get("_judge_json"),
                            },
                            ensure_ascii=False,
                        )
                        + "\n"
                    )
        lengths = [len(str(completion)) for completion in completions]
        summary = {
            "gspo/reward_mean": mean(rewards) if rewards else 0.0,
            "gspo/reward_std": pstdev(rewards) if len(rewards) > 1 else 0.0,
            "gspo/reward_nonzero_ratio": sum(value > 0 for value in rewards) / len(rewards) if rewards else 0.0,
            "gspo/reward_partial_ratio": sum(0 < value < 1 for value in rewards) / len(rewards) if rewards else 0.0,
            "gspo/completion_length": mean(lengths) if lengths else 0.0,
            "gspo/resample_count": float(kwargs.get("resample_count", 0) or 0),
            "gspo/throughput": float(kwargs.get("throughput", 0) or 0),
            "gspo/gradient_norm": float(kwargs.get("gradient_norm", 0) or 0),
            "gspo/nonfinite": float(bool(kwargs.get("nonfinite", False))),
        }
        generations = int(os.environ.get("GSPO_NUM_GENERATIONS", "16"))
        groups = [rewards[index : index + generations] for index in range(0, len(rewards), generations)]
        summary["gspo/valid_group_ratio"] = sum(len(set(group)) > 1 for group in groups) / len(groups) if groups else 0.0
        errors_path = os.environ.get("GSPO_REWARD_ERRORS")
        if errors_path and scorer.errors:
            os.makedirs(os.path.dirname(errors_path) or ".", exist_ok=True)
            with open(errors_path, "a", encoding="utf-8") as handle:
                for error in scorer.errors:
                    handle.write(json.dumps(error, ensure_ascii=False) + "\n")
        status_dir = os.environ.get("GSPO_STATUS_DIR")
        if status_dir:
            os.makedirs(status_dir, exist_ok=True)
            planned = int(os.environ.get("GSPO_PLANNED_ROLLOUTS", "0"))
            rank = os.environ.get("RANK", os.environ.get("LOCAL_RANK", "0"))
            status = {
                "rank": rank,
                "planned": planned,
                "completed": self.completed,
                "remaining": max(0, planned - self.completed) if planned else 0,
                "errors": len(scorer.errors),
                "heartbeat": time.time(),
                "throughput": len(completions) / max(time.perf_counter() - started, 1e-6),
            }
            with open(os.path.join(status_dir, f"rank_{rank}.json"), "w", encoding="utf-8") as handle:
                json.dump(status, handle, ensure_ascii=False, indent=2)
        print("[GSPO_REWARD]", json.dumps(summary, ensure_ascii=False), flush=True)
        if os.environ.get("WANDB_MODE") not in {"disabled", "offline-disabled"}:
            try:
                import wandb

                wandb.log(summary)
            except Exception:
                pass
        return rewards


orms["gspo_mixed"] = GSPOReward
