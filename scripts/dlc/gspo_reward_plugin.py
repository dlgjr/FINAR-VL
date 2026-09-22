"""ms-swift reward plugin for the full mixed GSPO run."""

from __future__ import annotations

import json
import math
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


def _generation_point_scores(payload: Mapping[str, Any], rubric: Mapping[str, Any]) -> dict[str, int] | None:
    points = rubric.get("points")
    scored = payload.get("point_scores")
    if not isinstance(points, list) or not points or not isinstance(scored, list):
        return None

    expected = [str(point.get("id") or "") for point in points if isinstance(point, Mapping)]
    if expected != [f"P{index}" for index in range(1, len(points) + 1)]:
        return None

    scores: dict[str, int] = {}
    for item in scored:
        if not isinstance(item, Mapping):
            return None
        point_id = str(item.get("id") or "")
        score = item.get("score")
        if point_id not in expected or point_id in scores:
            return None
        if isinstance(score, bool) or not isinstance(score, (int, float)) or float(score) not in {0.0, 1.0}:
            return None
        scores[point_id] = int(score)
    return scores if set(scores) == set(expected) else None


def _criterion_policy_signal(
    indices: Sequence[int],
    records: Sequence[dict[str, Any]],
) -> tuple[dict[int, float], dict[str, Any]]:
    """GDPO/POW3R-inspired criterion-normalize-then-aggregate signal.

    Each binary rubric criterion is normalized independently inside the rollout
    group. Static rubric importance determines evaluation value; current-policy
    learnability 4p(1-p) down-weights criteria that are almost always passed or
    almost always failed. Dimension budgets stay fixed so teacher-chosen rubric
    granularity cannot silently change the task-level reward mixture.
    """

    first = records[indices[0]]
    rubric = first.get("generation_rubric")
    if not isinstance(rubric, Mapping):
        raise ValueError("Generation criterion reward requires generation_rubric")

    points = rubric.get("points")
    scoring = rubric.get("scoring") or {}
    importance_weights = scoring.get("importance_weights") or {
        "core": 3.0,
        "important": 2.0,
        "optional": 1.0,
    }
    dimension_weights = scoring.get("dimension_weights") or {
        "fact": 0.50,
        "relation": 0.25,
        "synthesis": 0.15,
        "completeness": 0.10,
    }
    if not isinstance(points, list) or not points:
        raise ValueError("Generation criterion reward requires rubric points")
    if not isinstance(importance_weights, Mapping) or not isinstance(dimension_weights, Mapping):
        raise ValueError("invalid Generation rubric aggregation weights")

    point_meta: dict[str, tuple[str, float]] = {}
    for point in points:
        if not isinstance(point, Mapping):
            raise ValueError("invalid Generation rubric point")
        point_id = str(point.get("id") or "")
        dimension = str(point.get("dimension") or "")
        importance = str(point.get("importance") or "")
        if dimension not in dimension_weights or importance not in importance_weights:
            raise ValueError("unknown Generation rubric dimension/importance")
        static_weight = float(importance_weights[importance])
        if static_weight <= 0 or float(dimension_weights[dimension]) <= 0:
            raise ValueError("Generation rubric weights must be positive")
        point_meta[point_id] = (dimension, static_weight)

    rows: dict[int, dict[str, int]] = {}
    for index in indices:
        payload = _judge_payload(records[index])
        current_rubric = records[index].get("generation_rubric")
        if not isinstance(current_rubric, Mapping):
            raise ValueError("missing Generation rubric in rollout group")
        scores = _generation_point_scores(payload, current_rubric)
        if scores is None or set(scores) != set(point_meta):
            raise ValueError("invalid or inconsistent Generation point scores")
        rows[index] = scores

    learnability_power = float(os.environ.get("GSPO_GENERATION_LEARNABILITY_POWER", "1.0"))
    if learnability_power < 0:
        raise ValueError("GSPO_GENERATION_LEARNABILITY_POWER must be non-negative")
    eps = float(os.environ.get("GSPO_GENERATION_CRITERION_EPS", "1e-6"))
    if eps <= 0:
        raise ValueError("GSPO_GENERATION_CRITERION_EPS must be positive")

    criterion_stats: dict[str, dict[str, float | str]] = {}
    dimension_numerators: dict[str, dict[int, float]] = {}
    dimension_denominators: dict[str, float] = {}
    dimension_static_totals: dict[str, float] = {}
    dimension_learnability_totals: dict[str, float] = {}

    group_size = len(indices)
    for point_id, (dimension, static_weight) in point_meta.items():
        values = [rows[index][point_id] for index in indices]
        pass_rate = sum(values) / group_size
        variance = pass_rate * (1.0 - pass_rate)
        learnability = 4.0 * variance
        learnability_weight = learnability ** learnability_power if learnability > 0 else 0.0
        criterion_stats[point_id] = {
            "dimension": dimension,
            "pass_rate": pass_rate,
            "learnability": learnability,
            "static_weight": static_weight,
        }
        dimension_static_totals[dimension] = dimension_static_totals.get(dimension, 0.0) + static_weight
        dimension_learnability_totals[dimension] = (
            dimension_learnability_totals.get(dimension, 0.0)
            + static_weight * learnability_weight
        )
        if learnability_weight <= eps:
            continue

        std = math.sqrt(variance + eps)
        combined_weight = static_weight * learnability_weight
        dimension_denominators[dimension] = dimension_denominators.get(dimension, 0.0) + combined_weight
        bucket = dimension_numerators.setdefault(dimension, {index: 0.0 for index in indices})
        for index, value in zip(indices, values):
            bucket[index] += combined_weight * ((value - pass_rate) / std)

    dimension_train_weights: dict[str, float] = {}
    for dimension, denominator in dimension_denominators.items():
        static_total = dimension_static_totals.get(dimension, 0.0)
        if denominator <= eps or static_total <= eps:
            continue
        mean_learnability = dimension_learnability_totals[dimension] / static_total
        train_weight = float(dimension_weights[dimension]) * mean_learnability
        if train_weight > eps:
            dimension_train_weights[dimension] = train_weight

    signal = {index: 0.0 for index in indices}
    train_weight_total = sum(dimension_train_weights.values())
    if train_weight_total > eps:
        for dimension, train_weight in dimension_train_weights.items():
            denominator = dimension_denominators[dimension]
            for index in indices:
                dimension_signal = dimension_numerators[dimension][index] / denominator
                signal[index] += train_weight * dimension_signal
        for index in indices:
            signal[index] /= train_weight_total

    max_abs = max((abs(value) for value in signal.values()), default=0.0)
    if max_abs > eps:
        signal = {index: max(-1.0, min(1.0, value / max_abs)) for index, value in signal.items()}
    else:
        signal = {index: 0.0 for index in indices}

    active_criteria = sum(float(item["learnability"]) > eps for item in criterion_stats.values())
    mean_learnability = (
        sum(float(item["learnability"]) for item in criterion_stats.values()) / len(criterion_stats)
        if criterion_stats else 0.0
    )
    diagnostics = {
        "criterion_stats": criterion_stats,
        "active_criteria": active_criteria,
        "criterion_count": len(criterion_stats),
        "active_criterion_ratio": active_criteria / len(criterion_stats) if criterion_stats else 0.0,
        "mean_learnability": mean_learnability,
        "dimension_train_weights": dimension_train_weights,
    }
    return signal, diagnostics


def _apply_generation_reward_policy(
    rewards: Sequence[float],
    records: Sequence[dict[str, Any]],
) -> list[float]:
    """Apply an absolute quality gate plus policy-aware rubric shaping.

    Absolute q is retained only for acceptance calibration:
        accepted = no_hard_fail and q >= threshold

    Inside a mixed group, criterion scores are normalized independently before
    aggregation (GDPO-style), and criteria receive current-policy learnability
    weights 4p(1-p) (POW3R/EvoRubric-style). The resulting relative signal is
    mapped to [0,1] and placed behind a G-sized acceptance anchor:

        reward = (G * accepted + policy_quality) / (G + 1)

    Therefore, in every mixed group, accepted rows cannot receive a negative
    group-relative advantage and rejected/hard-failed rows cannot receive a
    positive one. All-rejected and all-accepted groups remain constants for
    dynamic resampling / zero-advantage skipping.
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
        rubric = record.get("generation_rubric")
        point_scores = _generation_point_scores(payload, rubric) if isinstance(rubric, Mapping) else None
        valid = (
            not isinstance(quality, bool)
            and isinstance(quality, (int, float))
            and 0.0 <= float(quality) <= 1.0
            and isinstance(accepted, bool)
            and isinstance(hard_fail, bool)
            and point_scores is not None
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
            "point_scores": point_scores or {},
        }
        groups.setdefault(str(record.get("sample_id", f"batch:{index}")), []).append(index)

    for sample_id, indices in groups.items():
        accepted_count = sum(bool(records[index]["_generation_reward"]["accepted"]) for index in indices)
        complete_group = len(indices) == generations

        if complete_group and accepted_count == 0:
            for index in indices:
                output[index] = 0.0
                records[index]["_generation_reward"]["group_policy"] = "all_rejected_zero"
                records[index]["_generation_reward"]["policy_signal"] = 0.0
                records[index]["_generation_reward"]["policy_quality"] = 0.5
        elif complete_group and accepted_count == generations:
            for index in indices:
                output[index] = 1.0
                records[index]["_generation_reward"]["group_policy"] = "all_accepted_one"
                records[index]["_generation_reward"]["policy_signal"] = 0.0
                records[index]["_generation_reward"]["policy_quality"] = 0.5
        else:
            diagnostics: dict[str, Any] = {}
            if complete_group:
                try:
                    signals, diagnostics = _criterion_policy_signal(indices, records)
                    group_policy = "mixed_criterion_normalized"
                except Exception as error:
                    signals = {
                        index: 2.0 * float(records[index]["_generation_reward"]["quality_score"]) - 1.0
                        for index in indices
                    }
                    diagnostics = {"criterion_error": str(error)}
                    group_policy = "mixed_quality_fallback"
            else:
                # A callback that does not expose a complete prompt group cannot
                # estimate criterion pass rates. Keep the old q-based shaping,
                # but make the fallback explicit in reward-pool diagnostics.
                signals = {
                    index: 2.0 * float(records[index]["_generation_reward"]["quality_score"]) - 1.0
                    for index in indices
                }
                group_policy = "incomplete_group_quality_fallback"

            for index in indices:
                detail = records[index]["_generation_reward"]
                policy_signal = max(-1.0, min(1.0, float(signals[index])))
                policy_quality = 0.5 * (policy_signal + 1.0)
                accepted_flag = int(bool(detail["accepted"]))
                output[index] = (generations * accepted_flag + policy_quality) / (generations + 1.0)
                detail["group_policy"] = group_policy
                detail["policy_signal"] = policy_signal
                detail["policy_quality"] = policy_quality
                if diagnostics:
                    compact_diagnostics = {
                        key: value
                        for key, value in diagnostics.items()
                        if key != "criterion_stats"
                    }
                    detail["group_criterion_diagnostics"] = compact_diagnostics
                    if index == indices[0] and "criterion_stats" in diagnostics:
                        detail["group_criterion_stats"] = diagnostics["criterion_stats"]

            if complete_group:
                group_mean = sum(output[index] for index in indices) / len(indices)
                accepted_rewards = [
                    output[index]
                    for index in indices
                    if records[index]["_generation_reward"]["accepted"]
                ]
                rejected_rewards = [
                    output[index]
                    for index in indices
                    if not records[index]["_generation_reward"]["accepted"]
                ]
                if accepted_rewards and min(accepted_rewards) + 1e-12 < group_mean:
                    raise RuntimeError("accepted Generation rollout received negative group-relative sign")
                if rejected_rewards and max(rejected_rewards) - 1e-12 > group_mean:
                    raise RuntimeError("rejected Generation rollout received positive group-relative sign")

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
        criterion_diagnostics = [
            item.get("group_criterion_diagnostics")
            for item in generation_groups.values()
            if isinstance(item.get("group_criterion_diagnostics"), Mapping)
            and "criterion_error" not in item.get("group_criterion_diagnostics", {})
        ]
        criterion_active_ratios = [
            float(item.get("active_criterion_ratio", 0.0))
            for item in criterion_diagnostics
        ]
        criterion_learnabilities = [
            float(item.get("mean_learnability", 0.0))
            for item in criterion_diagnostics
        ]
        criterion_fallbacks = [
            item for item in generation_groups.values()
            if "fallback" in str(item.get("group_policy", ""))
        ]

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
            "generation/criterion_active_ratio": (
                mean(criterion_active_ratios) if criterion_active_ratios else 0.0
            ),
            "generation/criterion_learnability_mean": (
                mean(criterion_learnabilities) if criterion_learnabilities else 0.0
            ),
            "generation/criterion_fallback_ratio": (
                len(criterion_fallbacks) / len(generation_groups)
                if generation_groups else 0.0
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
                    "generation/criterion_active_ratio",
                    "generation/criterion_learnability_mean",
                    "generation/criterion_fallback_ratio",
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
