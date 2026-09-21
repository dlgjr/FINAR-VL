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


def _gather_rewards(rewards: Sequence[float]) -> list[float]:
    import torch.distributed as dist

    local = [float(value) for value in rewards]
    if not dist.is_available() or not dist.is_initialized() or dist.get_world_size() == 1:
        return local
    gathered: list[list[float] | None] = [None] * dist.get_world_size()
    dist.all_gather_object(gathered, local)
    return [value for rank_rewards in gathered if rank_rewards is not None for value in rank_rewards]


def _judge_payload(record: Mapping[str, Any]) -> dict[str, Any]:
    raw = record.get("_judge_json")
    if isinstance(raw, Mapping):
        return dict(raw)
    if isinstance(raw, str):
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            return {}
        return dict(payload) if isinstance(payload, Mapping) else {}
    return {}


def _apply_generation_reward_policy(
    rewards: Sequence[float],
    records: Sequence[dict[str, Any]],
) -> list[float]:
    """Turn Generation rubric quality into an accept-anchored group reward.

    q is a dense quality score in [0,1]. A rollout is accepted only when q is
    above the calibrated threshold and the factual hard-veto is clear.

    For a mixed group of size G:
        reward = (G * accepted + q) / (G + 1)

    This makes every accepted rollout outrank every rejected rollout while
    preserving dense ordering inside each side. All-rejected and all-accepted
    groups are collapsed to constants so ms-swift dynamic sampling can
    resample/skip groups without useful acceptance variance.
    """

    output = [float(value) for value in rewards]
    if os.environ.get("GSPO_ROUTE_MODE", "mixed") != "generation":
        return output

    generations = int(os.environ.get("GSPO_NUM_GENERATIONS", "8"))
    groups: dict[str, list[int]] = {}
    for index, record in enumerate(records):
        if not (record.get("reward_type") == "judge" or record.get("verifier_type") == "model_judge"):
            continue

        payload = _judge_payload(record)
        quality = payload.get("quality_score")
        accepted = payload.get("accepted")
        hard_fail = payload.get("hard_fail")
        valid = (
            not isinstance(quality, bool)
            and isinstance(quality, (int, float))
            and 0.0 <= float(quality) <= 1.0
            and isinstance(accepted, bool)
            and isinstance(hard_fail, bool)
        )
        if valid:
            quality_score = float(quality)
            accepted_flag = bool(accepted)
            hard_fail_flag = bool(hard_fail)
        else:
            # Judge/schema errors must never create a positive rollout.
            quality_score = 0.0
            accepted_flag = False
            hard_fail_flag = True

        record["_generation_reward"] = {
            "quality_score": quality_score,
            "accepted": accepted_flag,
            "hard_fail": hard_fail_flag,
            "accept_threshold": payload.get("accept_threshold"),
            "judge_valid": valid,
        }
        groups.setdefault(str(record.get("sample_id", f"batch:{index}")), []).append(index)

    for sample_id, indices in groups.items():
        accepted_count = sum(bool(records[index]["_generation_reward"]["accepted"]) for index in indices)
        complete_group = len(indices) == generations

        if complete_group and accepted_count == 0:
            for index in indices:
                output[index] = 0.0
                records[index]["_generation_reward"]["group_policy"] = "all_rejected_zero"
        elif complete_group and accepted_count == generations:
            for index in indices:
                output[index] = 1.0
                records[index]["_generation_reward"]["group_policy"] = "all_accepted_one"
        else:
            for index in indices:
                detail = records[index]["_generation_reward"]
                quality_score = float(detail["quality_score"])
                accepted_flag = int(bool(detail["accepted"]))
                output[index] = (generations * accepted_flag + quality_score) / (generations + 1.0)
                detail["group_policy"] = "mixed_lexicographic" if complete_group else "incomplete_group_fallback"

        for index in indices:
            detail = records[index]["_generation_reward"]
            detail["group_sample_id"] = sample_id
            detail["group_size"] = len(indices)
            detail["expected_group_size"] = generations
            detail["group_accept_count"] = accepted_count
            detail["final_reward"] = output[index]

    return output


def records_from_kwargs(kwargs: Mapping[str, Any], count: int) -> list[dict[str, Any]]:
    supplied = kwargs.get("records", kwargs.get("data"))
    if isinstance(supplied, Sequence) and not isinstance(supplied, (str, bytes)) and supplied and isinstance(supplied[0], Mapping):
        return [dict(supplied[index]) if index < len(supplied) else {} for index in range(count)]
    records = []
    for index in range(count):
        def value(name: str, default: Any) -> Any:
            item = _column(kwargs, name, index, default)
            if isinstance(item, str) and name == "generation_rubric":
                return json.loads(item)
            if isinstance(item, str) and name in {"images", "gold_atoms", "gold_numeric", "gold_claims", "gold_claim_details", "metadata"}:
                try:
                    return json.loads(item)
                except json.JSONDecodeError:
                    return [item]
            return item

        records.append(
            {
                "sample_id": value("sample_id", f"batch:{index}"),
                "source": value("source", ""),
                "task": value("task", ""),
                "metadata": value("metadata", {}),
                "reward_type": value("reward_type", ""),
                "reward_subtype": value("reward_subtype", ""),
                "verifier_type": value("verifier_type", "model_judge"),
                "images": value("images", []),
                "gold_atoms": value("gold_atoms", []),
                "gold_numeric": value("gold_numeric", []),
                "gold_claims": value("gold_claims", []),
                "gold_claim_details": value("gold_claim_details", []),
                "judge_reference": value("judge_reference", ""),
                "judge_reference_mode": value("judge_reference_mode", ""),
                "generation_rubric": value("generation_rubric", {}),
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
        self.completed_by_route = {"rule": 0, "judge": 0}

    def __call__(self, completions, **kwargs) -> list[float]:
        started = time.perf_counter()
        records = records_from_kwargs(kwargs, len(completions))
        scorer = MixedReward(judge=judge_from_record)
        rewards = scorer(completions, records=records)
        rewards = _apply_generation_reward_policy(rewards, records)

        self.completed += len(completions)
        route_counts = {"rule": 0, "judge": 0}
        for record in records:
            route = "judge" if record.get("reward_type") == "judge" or record.get("verifier_type") == "model_judge" else "rule"
            route_counts[route] += 1
            self.completed_by_route[route] += 1

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
                                "reward_type": record.get("reward_type", ""),
                                "reward_subtype": record.get("reward_subtype", ""),
                                "completion": str(completion),
                                "reward": float(reward),
                                "verifier_type": record.get("verifier_type"),
                                "gold_atoms": record.get("gold_atoms", []),
                                "gold_numeric": record.get("gold_numeric", []),
                                "gold_claims": record.get("gold_claims", []),
                                "gold_claim_details": record.get("gold_claim_details", []),
                                "judge_reference_mode": record.get("judge_reference_mode", ""),
                                "solution": record.get("solution", ""),
                                "question": record.get("question", ""),
                                "parser_result": record.get("_parser_result"),
                                "process_result": record.get("_process_result"),
                                "judge_json": record.get("_judge_json"),
                                "generation_reward": record.get("_generation_reward"),
                            },
                            ensure_ascii=False,
                        )
                        + "\n"
                    )

        lengths = [len(str(completion)) for completion in completions]
        process_results = [
            record.get("_process_result")
            for record in records
            if isinstance(record.get("_process_result"), Mapping)
        ]
        process_checked = [item for item in process_results if item.get("status") in {"pass", "fail", "unknown"}]
        process_failures = [item for item in process_checked if item.get("status") == "fail"]
        process_unknown = [item for item in process_checked if item.get("status") == "unknown"]

        generation_details = [
            record["_generation_reward"]
            for record in records
            if isinstance(record.get("_generation_reward"), Mapping)
        ]
        quality_scores = [float(item["quality_score"]) for item in generation_details]
        accepted_flags = [bool(item["accepted"]) for item in generation_details]
        hard_fail_flags = [bool(item["hard_fail"]) for item in generation_details]
        generation_groups: dict[str, dict[str, Any]] = {}
        for item in generation_details:
            group_id = str(item.get("group_sample_id", ""))
            generation_groups[group_id] = item
        group_accept_counts = [int(item.get("group_accept_count", 0)) for item in generation_groups.values()]
        group_sizes = [int(item.get("group_size", 0)) for item in generation_groups.values()]

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
            "gspo/rule_samples": route_counts["rule"],
            "gspo/judge_samples": route_counts["judge"],
            "gspo/process_checked_ratio": len(process_checked) / len(rewards) if rewards else 0.0,
            "gspo/process_veto_ratio": len(process_failures) / len(rewards) if rewards else 0.0,
            "gspo/process_unknown_ratio": len(process_unknown) / len(rewards) if rewards else 0.0,
            "generation/quality_mean": mean(quality_scores) if quality_scores else 0.0,
            "generation/accept_ratio": sum(accepted_flags) / len(accepted_flags) if accepted_flags else 0.0,
            "generation/hard_fail_ratio": sum(hard_fail_flags) / len(hard_fail_flags) if hard_fail_flags else 0.0,
            "generation/group_all_rejected_ratio": (
                sum(count == 0 for count in group_accept_counts) / len(group_accept_counts)
                if group_accept_counts else 0.0
            ),
            "generation/group_all_accepted_ratio": (
                sum(count == size and size > 0 for count, size in zip(group_accept_counts, group_sizes))
                / len(group_accept_counts)
                if group_accept_counts else 0.0
            ),
            "generation/group_mixed_accept_ratio": (
                sum(0 < count < size for count, size in zip(group_accept_counts, group_sizes))
                / len(group_accept_counts)
                if group_accept_counts else 0.0
            ),
        }

        global_rewards = _gather_rewards(rewards)
        generations = int(os.environ.get("GSPO_NUM_GENERATIONS", "16"))
        groups = [global_rewards[index : index + generations] for index in range(0, len(global_rewards), generations)]
        positive_counts = [sum(value > 0 for value in group) for group in groups]
        summary["gspo/group_all_zero_ratio"] = sum(count == 0 for count in positive_counts) / len(groups) if groups else 0.0
        summary["gspo/group_all_success_ratio"] = sum(all(value >= 1 for value in group) for group in groups) / len(groups) if groups else 0.0
        summary["gspo/group_mixed_ratio"] = sum(len(set(group)) > 1 for group in groups) / len(groups) if groups else 0.0
        summary["gspo/group_positive_count_mean"] = mean(positive_counts) if positive_counts else 0.0
        summary["gspo/group_positive_count_min"] = min(positive_counts) if positive_counts else 0.0
        summary["gspo/group_positive_count_max"] = max(positive_counts) if positive_counts else 0.0

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
                "completed_rule": self.completed_by_route["rule"],
                "completed_judge": self.completed_by_route["judge"],
                "remaining": max(0, planned - self.completed) if planned else 0,
                "errors": len(scorer.errors),
                "heartbeat": time.time(),
                "throughput": len(completions) / max(time.perf_counter() - started, 1e-6),
            }
            with open(os.path.join(status_dir, f"rank_{rank}.json"), "w", encoding="utf-8") as handle:
                json.dump(status, handle, ensure_ascii=False, indent=2)

        live_keys = [
            "gspo/reward_mean",
            "gspo/reward_std",
            "gspo/group_all_zero_ratio",
            "gspo/group_mixed_ratio",
        ]
        if generation_details:
            live_keys.extend(
                [
                    "generation/quality_mean",
                    "generation/accept_ratio",
                    "generation/hard_fail_ratio",
                    "generation/group_mixed_accept_ratio",
                ]
            )
        live_summary = {key: summary[key] for key in live_keys}
        print("[GSPO_REWARD]", json.dumps(live_summary, ensure_ascii=False), flush=True)

        if os.environ.get("WANDB_MODE") not in {"disabled", "offline-disabled"}:
            try:
                import wandb

                wandb.log(summary)
            except Exception:
                pass
        return rewards


orms["gspo_mixed"] = GSPOReward
