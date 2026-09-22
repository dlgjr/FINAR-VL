"""Multi-advantage Reasoning RL for FINAR-VL.

This plugin keeps outcome, perception, and reasoning signals separate until the
per-token policy-gradient stage.

Design:
- mixed Pass@8 groups use a strict binary outcome advantage;
- perception and reasoning criteria are normalized independently by group;
- rejected rollouts preserve the verified-good prefix and receive negative
  outcome/process pressure only from the first verifiable error onward;
- visual credit uses a soft image-counterfactual token dependency rather than
  treating <perception> membership as a hard visual-token label.

The implementation is intentionally disabled outside the Reasoning route.
"""

from __future__ import annotations

import json
import math
import os
from typing import Any, Mapping, Sequence

from scripts.dlc.gspo_trainer_plugin import GSPOGRPOTrainer
from scripts.rl.gspo_reward import score_programmatic_answer
from scripts.rl.reasoning_process_verifier import verify_reasoning_process

try:
    from swift.rlhf_trainers import GRPOTrainer
except ImportError:  # pragma: no cover - DLC supplies ms-swift
    GRPOTrainer = None  # type: ignore[assignment]


_PERCEPTION_WEIGHTS = {
    "perception_sufficiency": 2.0,
    "perception_productive": 1.0,
    "perception_nonredundant": 0.5,
    "grounding_consistency": 2.0,
}
_REASONING_WEIGHTS = {
    "reasoning_arithmetic_valid": 2.0,
    "reasoning_step_coverage": 2.0,
    "format": 0.25,
}


def _completion_text(sample: Any) -> str:
    messages = getattr(sample, "messages", None) or []
    if messages and isinstance(messages[-1], Mapping) and messages[-1].get("role") == "assistant":
        content = messages[-1].get("content", "")
        if isinstance(content, str):
            return content
        if isinstance(content, Sequence) and not isinstance(content, (str, bytes)):
            return "".join(
                str(item.get("text", ""))
                for item in content
                if isinstance(item, Mapping) and item.get("type") == "text"
            )
    return ""


def _has_image(sample: Any) -> bool:
    for message in getattr(sample, "messages", None) or []:
        if not isinstance(message, Mapping):
            continue
        content = message.get("content")
        if isinstance(content, Sequence) and not isinstance(content, (str, bytes)):
            if any(isinstance(item, Mapping) and item.get("type") == "image" for item in content):
                return True
    return bool((getattr(sample, "extra", {}) or {}).get("images"))


def _json_mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return dict(value)
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return {}
        return dict(parsed) if isinstance(parsed, Mapping) else {}
    return {}


def _json_list(value: Any) -> list[Any]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return list(value)
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return [value]
        return list(parsed) if isinstance(parsed, list) else [parsed]
    return []


def _record_from_sample(sample: Any) -> dict[str, Any]:
    extra = dict(getattr(sample, "extra", {}) or {})
    return {
        "sample_id": extra.get("sample_id", getattr(sample, "prompt_id", "")),
        "question": extra.get("question", ""),
        "verifier_type": extra.get("verifier_type", ""),
        "gold_atoms": _json_list(extra.get("gold_atoms", [])),
        "gold_numeric": _json_list(extra.get("gold_numeric", [])),
        "metadata": _json_mapping(extra.get("metadata", {})),
        "images": ["present"] if _has_image(sample) else [],
    }


def _criterion_weight(name: str, channel: str) -> float:
    if channel == "perception":
        if name.startswith("visual_fact:"):
            return 2.0
        return float(_PERCEPTION_WEIGHTS.get(name, 0.0))
    return float(_REASONING_WEIGHTS.get(name, 0.0))


def _channel_signal(
    rows: Sequence[dict[str, Any]],
    *,
    channel: str,
    eps: float,
) -> dict[int, float]:
    signal = {int(row["global_index"]): 0.0 for row in rows}
    if not rows:
        return signal

    names = sorted(
        {
            str(name)
            for row in rows
            for name in (row.get("criteria") or {})
            if _criterion_weight(str(name), channel) > 0
        }
    )
    total_weight = 0.0
    for name in names:
        values = []
        valid = True
        for row in rows:
            value = (row.get("criteria") or {}).get(name)
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                valid = False
                break
            value = float(value)
            if not math.isfinite(value):
                valid = False
                break
            values.append(value)
        if not valid or not values:
            continue

        mean_value = sum(values) / len(values)
        variance = sum((value - mean_value) ** 2 for value in values) / len(values)
        learnability = min(1.0, 4.0 * variance)
        static_weight = _criterion_weight(name, channel)
        weight = static_weight * learnability
        if weight <= eps:
            continue

        std = math.sqrt(variance + eps)
        total_weight += weight
        for row, value in zip(rows, values):
            signal[int(row["global_index"])] += weight * ((value - mean_value) / std)

    if total_weight <= eps:
        return {key: 0.0 for key in signal}

    signal = {key: value / total_weight for key, value in signal.items()}
    max_abs = max((abs(value) for value in signal.values()), default=0.0)
    if max_abs <= eps:
        return {key: 0.0 for key in signal}
    return {
        key: max(-1.0, min(1.0, value / max_abs))
        for key, value in signal.items()
    }


def _strict_outcome_signal(rows: Sequence[dict[str, Any]], eps: float) -> dict[int, float]:
    values = [1.0 if row["strict_success"] else 0.0 for row in rows]
    mean_value = sum(values) / len(values)
    variance = sum((value - mean_value) ** 2 for value in values) / len(values)
    if variance <= eps:
        return {int(row["global_index"]): 0.0 for row in rows}
    std = math.sqrt(variance + eps)
    return {
        int(row["global_index"]): (value - mean_value) / std
        for row, value in zip(rows, values)
    }


def _token_index_for_char(self, sample: Any, char_pos: int | None) -> int:
    ids = list(getattr(sample, "response_token_ids", None) or [])
    if char_pos is None:
        return len(ids)
    if char_pos <= 0 or not ids:
        return 0

    tokenizer = getattr(getattr(self, "template", None), "tokenizer", None)
    if tokenizer is None:
        text = _completion_text(sample)
        if not text:
            return 0
        return min(len(ids), max(0, round(len(ids) * char_pos / len(text))))

    lo, hi = 0, len(ids)
    while lo < hi:
        mid = (lo + hi) // 2
        decoded = tokenizer.decode(ids[:mid], skip_special_tokens=False)
        if len(decoded) >= char_pos:
            hi = mid
        else:
            lo = mid + 1
    return min(len(ids), lo)


def _local_rows(self, samples: Sequence[Any]) -> list[dict[str, Any]]:
    rank = int(getattr(self.accelerator, "process_index", 0))
    rows = []
    for local_index, sample in enumerate(samples):
        record = _record_from_sample(sample)
        text = _completion_text(sample)
        verifier_type = str(record.get("verifier_type") or "")
        process = verify_reasoning_process(text, record)
        raw_score = score_programmatic_answer(
            text,
            record.get("gold_atoms", []),
            verifier_type,
            str(record.get("question", "")),
            record.get("gold_numeric", []),
        )
        extra = getattr(sample, "extra", {}) or {}
        gold_injected = bool(extra.get("_gold_injected"))
        strict_success = bool(
            raw_score >= 1.0
            and process.get("status") != "fail"
            and not gold_injected
        )
        first_error_char = process.get("first_error_char")
        if not strict_success and first_error_char is None:
            first_error_char = process.get("answer_start_char")
        rows.append(
            {
                "rank": rank,
                "local_index": local_index,
                "group_id": str(
                    extra.get("sample_id")
                    or getattr(sample, "prompt_id", "")
                    or f"{rank}:{local_index // max(1, int(self.num_generations))}"
                ),
                "strict_success": strict_success,
                "gold_injected": gold_injected,
                "criteria": dict(process.get("criteria") or {}),
                "first_error_char": first_error_char,
                "process_status": str(process.get("status") or ""),
                "group_k": int(extra.get("_gspo_group_k", -1)),
                "rl_weight": float(extra.get("_gspo_rl_weight", 1.0)),
            }
        )
    return rows


def _compute_local_channels(self, samples: Sequence[Any]) -> list[dict[str, Any]]:
    from accelerate.utils import gather_object

    local_rows = _local_rows(self, samples)
    gathered = gather_object(local_rows)
    all_rows = list(gathered)
    for global_index, row in enumerate(all_rows):
        row["global_index"] = global_index

    eps = float(os.environ.get("GSPO_MULTI_ADV_EPS", "1e-6"))
    groups: dict[str, list[dict[str, Any]]] = {}
    for row in all_rows:
        groups.setdefault(str(row["group_id"]), []).append(row)

    outcome: dict[int, float] = {}
    perception: dict[int, float] = {}
    reasoning: dict[int, float] = {}
    expected = int(self.num_generations)

    for rows in groups.values():
        rows.sort(key=lambda row: int(row["global_index"]))
        annotated_k = {int(row.get("group_k", -1)) for row in rows}
        annotated_k.discard(-1)
        k = (
            next(iter(annotated_k))
            if len(annotated_k) == 1
            else sum(bool(row["strict_success"]) for row in rows)
        )
        complete = len(rows) == expected

        if complete and 0 < k < expected:
            outcome.update(_strict_outcome_signal(rows, eps))
            perception.update(_channel_signal(rows, channel="perception", eps=eps))
            reasoning.update(_channel_signal(rows, channel="reasoning", eps=eps))
        else:
            for row in rows:
                idx = int(row["global_index"])
                outcome[idx] = float("nan")  # keep parent outcome channel for k=0
                perception[idx] = 0.0
                reasoning[idx] = 0.0

    rank = int(getattr(self.accelerator, "process_index", 0))
    local_output = []
    for row in all_rows:
        if int(row["rank"]) != rank:
            continue
        idx = int(row["global_index"])
        local_output.append(
            {
                **row,
                "outcome_advantage": outcome.get(idx, float("nan")),
                "perception_advantage": perception.get(idx, 0.0),
                "reasoning_advantage": reasoning.get(idx, 0.0),
            }
        )
    local_output.sort(key=lambda row: int(row["local_index"]))
    if len(local_output) != len(samples):
        raise RuntimeError(
            f"multi-advantage gather mismatch: local={len(samples)} recovered={len(local_output)}"
        )
    return local_output


_original_postprocess_batch = GSPOGRPOTrainer._postprocess_batch


def _postprocess_batch_multi_advantage(self, samples, batch_encoded_inputs):
    import torch

    _original_postprocess_batch(self, samples, batch_encoded_inputs)
    if os.environ.get("GSPO_ROUTE_MODE", "mixed") != "reasoning":
        return
    if os.environ.get("GSPO_MULTI_ADVANTAGE", "true").lower() != "true":
        return

    rows = _compute_local_channels(self, samples)
    gas_chunks = self.split_by_mini_batches(samples)
    cursor = 0
    if len(gas_chunks) != len(batch_encoded_inputs):
        raise RuntimeError(
            f"multi-advantage batch mismatch: {len(gas_chunks)} vs {len(batch_encoded_inputs)}"
        )

    for batch, batch_encoded in zip(gas_chunks, batch_encoded_inputs):
        grpo_batch = batch_encoded["grpo_batch"]
        device = grpo_batch.advantages.device
        dtype = grpo_batch.advantages.dtype
        batch_rows = rows[cursor : cursor + len(batch)]
        cursor += len(batch)

        parent_advantages = grpo_batch.advantages.clone()
        for row_index, row in enumerate(batch_rows):
            rl_weight = float(row["rl_weight"])
            k = int(row["group_k"])
            if 0 < k < int(self.num_generations) and rl_weight > 0:
                outcome_value = float(row["outcome_advantage"]) * rl_weight
                parent_advantages[row_index] = outcome_value

        perception_adv = torch.tensor(
            [float(row["perception_advantage"]) * float(row["rl_weight"]) for row in batch_rows],
            dtype=dtype,
            device=device,
        )
        reasoning_adv = torch.tensor(
            [float(row["reasoning_advantage"]) * float(row["rl_weight"]) for row in batch_rows],
            dtype=dtype,
            device=device,
        )
        strict_success = torch.tensor(
            [bool(row["strict_success"]) for row in batch_rows],
            dtype=torch.bool,
            device=device,
        )
        cutoff_tokens = torch.tensor(
            [
                _token_index_for_char(
                    self,
                    sample,
                    row["first_error_char"],
                )
                for sample, row in zip(batch, batch_rows)
            ],
            dtype=torch.long,
            device=device,
        )

        grpo_batch.advantages = parent_advantages
        grpo_batch.gspo_perception_advantages = perception_adv
        grpo_batch.gspo_reasoning_advantages = reasoning_adv
        grpo_batch.gspo_strict_success = strict_success
        grpo_batch.gspo_error_cutoff_tokens = cutoff_tokens


GSPOGRPOTrainer._postprocess_batch = _postprocess_batch_multi_advantage


_original_get_per_token = GSPOGRPOTrainer._get_per_token_logps_and_entropies


def _counterfactual_visual_weights(self, model, model_inputs, grpo_batch, per_token_logps):
    import torch

    completion_mask = grpo_batch.completion_mask.to(dtype=per_token_logps.dtype)
    if GRPOTrainer is None:
        return torch.zeros_like(per_token_logps)

    masked_inputs = dict(model_inputs)
    visual_keys = []
    for key, value in model_inputs.items():
        if "pixel_values" in str(key) and isinstance(value, torch.Tensor):
            masked_inputs[key] = torch.zeros_like(value)
            visual_keys.append(key)
    if not visual_keys:
        return torch.zeros_like(per_token_logps)

    with torch.no_grad():
        masked_logps, _ = GRPOTrainer._get_per_token_logps_and_entropies(
            self,
            model,
            masked_inputs,
            grpo_batch,
            compute_entropy=False,
        )

    delta = (per_token_logps.detach().float() - masked_logps.detach().float()).abs()
    delta = delta * completion_mask.float()
    denom = completion_mask.float().sum(dim=-1, keepdim=True).clamp(min=1.0)
    mean_delta = delta.sum(dim=-1, keepdim=True) / denom
    weights = torch.where(
        mean_delta > 1e-8,
        (delta / (2.0 * mean_delta.clamp(min=1e-8))).clamp(min=0.0, max=1.0),
        torch.zeros_like(delta),
    )

    # VGPO-style temporal compensation: later reasoning tokens receive a
    # slightly larger visual-dependency expectation to counter visual forgetting.
    length = weights.shape[-1]
    position = torch.linspace(
        0.0,
        1.0,
        steps=max(length, 1),
        device=weights.device,
        dtype=weights.dtype,
    ).view(1, -1)
    temporal = 0.75 + 0.5 * position
    return (weights * temporal).clamp(max=1.0).to(dtype=per_token_logps.dtype)


def _signed_prefix_mask(values, strict_success, cutoff_tokens, completion_mask):
    import torch

    token_index = torch.arange(
        completion_mask.shape[-1],
        device=completion_mask.device,
    ).view(1, -1)
    cutoff = cutoff_tokens.view(-1, 1)
    prefix = token_index < cutoff
    suffix = ~prefix
    positive = values.view(-1, 1) >= 0
    rejected_mask = torch.where(positive, prefix, suffix)
    active = torch.where(strict_success.view(-1, 1), torch.ones_like(rejected_mask), rejected_mask)
    return active.to(dtype=completion_mask.dtype) * completion_mask


def _get_per_token_multi_advantage(self, *args, **kwargs):
    import torch

    per_token_logps, entropies = _original_get_per_token(self, *args, **kwargs)

    if os.environ.get("GSPO_ROUTE_MODE", "mixed") != "reasoning":
        return per_token_logps, entropies
    if os.environ.get("GSPO_MULTI_ADVANTAGE", "true").lower() != "true":
        return per_token_logps, entropies

    if len(args) >= 3:
        model, model_inputs, grpo_batch = args[:3]
    else:
        model = kwargs.get("model")
        model_inputs = kwargs.get("model_inputs")
        grpo_batch = kwargs.get("grpo_batch")
    if model is None or model_inputs is None or grpo_batch is None:
        return per_token_logps, entropies

    perception_adv = getattr(grpo_batch, "gspo_perception_advantages", None)
    reasoning_adv = getattr(grpo_batch, "gspo_reasoning_advantages", None)
    strict_success = getattr(grpo_batch, "gspo_strict_success", None)
    cutoff_tokens = getattr(grpo_batch, "gspo_error_cutoff_tokens", None)
    if any(value is None for value in (perception_adv, reasoning_adv, strict_success, cutoff_tokens)):
        return per_token_logps, entropies

    completion_mask = grpo_batch.completion_mask.to(dtype=per_token_logps.dtype)
    visual_weights = _counterfactual_visual_weights(
        self,
        model,
        model_inputs,
        grpo_batch,
        per_token_logps,
    )
    reasoning_weights = (1.0 - 0.75 * visual_weights).clamp(min=0.25, max=1.0)

    perception_mask = _signed_prefix_mask(
        perception_adv,
        strict_success,
        cutoff_tokens,
        completion_mask,
    )
    reasoning_mask = _signed_prefix_mask(
        reasoning_adv,
        strict_success,
        cutoff_tokens,
        completion_mask,
    )

    outcome = grpo_batch.advantages.clone()
    token_index = torch.arange(
        completion_mask.shape[-1],
        device=completion_mask.device,
    ).view(1, -1)
    suffix = token_index >= cutoff_tokens.view(-1, 1)
    rejected = (~strict_success).view(-1, 1)
    # Save-the-Good-Prefix: a rejected trajectory's negative strict-outcome
    # signal starts at the first verifiable error (or at <answer> when the
    # process is clean but the final answer is wrong).
    outcome = torch.where(
        rejected & (~suffix),
        torch.zeros_like(outcome),
        outcome,
    )

    lambda_perception = float(os.environ.get("GSPO_PERCEPTION_ADV_COEF", "0.35"))
    lambda_reasoning = float(os.environ.get("GSPO_REASONING_ADV_COEF", "0.35"))
    combined = (
        outcome
        + lambda_perception
        * perception_adv.view(-1, 1)
        * visual_weights
        * perception_mask
        + lambda_reasoning
        * reasoning_adv.view(-1, 1)
        * reasoning_weights
        * reasoning_mask
    )
    grpo_batch.advantages = combined * completion_mask

    self._gspo_multi_adv_metrics = {
        "visual_dependency_mean": float(
            (visual_weights * completion_mask).sum().detach().item()
            / completion_mask.sum().clamp(min=1.0).detach().item()
        ),
        "perception_adv_abs_mean": float(perception_adv.abs().mean().detach().item()),
        "reasoning_adv_abs_mean": float(reasoning_adv.abs().mean().detach().item()),
    }
    return per_token_logps, entropies


GSPOGRPOTrainer._get_per_token_logps_and_entropies = _get_per_token_multi_advantage


_original_update_metrics = GSPOGRPOTrainer._update_metrics


def _update_metrics_multi_advantage(self, metrics_data):
    _original_update_metrics(self, metrics_data)
    values = self.__dict__.pop("_gspo_multi_adv_metrics", None)
    if not values:
        return
    mode = metrics_data["mode"]
    for key, value in values.items():
        self._metrics[mode][f"multi_adv/{key}"].append(float(value))


GSPOGRPOTrainer._update_metrics = _update_metrics_multi_advantage
