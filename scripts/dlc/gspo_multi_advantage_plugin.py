"""Outcome-anchored multi-advantage credit assignment for Reasoning RL.

Final-answer GRPO advantage is the primary signal over the whole completion.
Visual and reasoning advantages are auxiliary, answer-conditioned residuals:

    A_token = A_answer
              + lambda_v * w_visual(token) * DeltaA_visual
              + lambda_r * w_reason(token) * DeltaA_reason

DeltaA_visual and DeltaA_reason are normalized separately inside the
answer-correct and answer-wrong rollout buckets.  On rows where A_answer is
non-zero, auxiliary residuals are capped so they cannot reverse the final
outcome direction.  When the group has no usable outcome advantage (for
example all-correct/all-wrong), process/visual variation can still provide
learning signal.
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
    "reasoning_terminal_support": 2.0,
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
            if any(
                isinstance(item, Mapping) and item.get("type") == "image"
                for item in content
            ):
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


def _bucket_channel_signal(
    rows: Sequence[dict[str, Any]],
    *,
    channel: str,
    eps: float,
) -> dict[int, float]:
    """Normalize one auxiliary channel inside answer-correct/wrong buckets."""

    signal = {int(row["global_index"]): 0.0 for row in rows}
    for answer_correct in (False, True):
        bucket = [
            row
            for row in rows
            if bool(row.get("answer_correct")) is answer_correct
            and not bool(row.get("gold_injected"))
        ]
        if len(bucket) <= 1:
            continue

        names = sorted(
            {
                str(name)
                for row in bucket
                for name in (row.get("criteria") or {})
                if _criterion_weight(str(name), channel) > 0
            }
        )
        bucket_signal = {int(row["global_index"]): 0.0 for row in bucket}
        total_weight = 0.0

        for name in names:
            values: list[float] = []
            valid = True
            for row in bucket:
                value = (row.get("criteria") or {}).get(name)
                if isinstance(value, bool) or not isinstance(value, (int, float)):
                    valid = False
                    break
                value = float(value)
                if not math.isfinite(value):
                    valid = False
                    break
                values.append(value)
            if not valid or len(values) != len(bucket):
                continue

            mean_value = sum(values) / len(values)
            variance = sum(
                (value - mean_value) ** 2 for value in values
            ) / len(values)
            learnability = min(1.0, 4.0 * variance)
            weight = _criterion_weight(name, channel) * learnability
            if weight <= eps:
                continue

            std = math.sqrt(variance + eps)
            total_weight += weight
            for row, value in zip(bucket, values):
                bucket_signal[int(row["global_index"])] += (
                    weight * ((value - mean_value) / std)
                )

        if total_weight <= eps:
            continue

        bucket_signal = {
            key: value / total_weight
            for key, value in bucket_signal.items()
        }
        max_abs = max((abs(value) for value in bucket_signal.values()), default=0.0)
        if max_abs <= eps:
            continue

        for key, value in bucket_signal.items():
            signal[key] = max(-1.0, min(1.0, value / max_abs))

    return signal


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
    rows: list[dict[str, Any]] = []
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
        rows.append(
            {
                "rank": rank,
                "local_index": local_index,
                "group_id": str(
                    extra.get("sample_id")
                    or getattr(sample, "prompt_id", "")
                    or f"{rank}:{local_index // max(1, int(self.num_generations))}"
                ),
                "answer_correct": bool(raw_score >= 1.0 and not gold_injected),
                "gold_injected": gold_injected,
                "criteria": dict(process.get("criteria") or {}),
                "answer_start_char": process.get("answer_start_char"),
            }
        )
    return rows


def _compute_local_channels(self, samples: Sequence[Any]) -> list[dict[str, Any]]:
    from accelerate.utils import gather_object

    local_rows = _local_rows(self, samples)
    all_rows = list(gather_object(local_rows))
    for global_index, row in enumerate(all_rows):
        row["global_index"] = global_index

    groups: dict[str, list[dict[str, Any]]] = {}
    for row in all_rows:
        groups.setdefault(str(row["group_id"]), []).append(row)

    eps = float(os.environ.get("GSPO_MULTI_ADV_EPS", "1e-6"))
    expected = int(self.num_generations)
    perception: dict[int, float] = {}
    reasoning: dict[int, float] = {}

    for rows in groups.values():
        rows.sort(key=lambda row: int(row["global_index"]))
        if len(rows) != expected:
            for row in rows:
                idx = int(row["global_index"])
                perception[idx] = 0.0
                reasoning[idx] = 0.0
            continue
        perception.update(
            _bucket_channel_signal(rows, channel="perception", eps=eps)
        )
        reasoning.update(
            _bucket_channel_signal(rows, channel="reasoning", eps=eps)
        )

    rank = int(getattr(self.accelerator, "process_index", 0))
    local_output: list[dict[str, Any]] = []
    for row in all_rows:
        if int(row["rank"]) != rank:
            continue
        idx = int(row["global_index"])
        local_output.append(
            {
                **row,
                "perception_advantage": float(perception.get(idx, 0.0)),
                "reasoning_advantage": float(reasoning.get(idx, 0.0)),
            }
        )

    local_output.sort(key=lambda row: int(row["local_index"]))
    if len(local_output) != len(samples):
        raise RuntimeError(
            f"multi-advantage gather mismatch: local={len(samples)} "
            f"recovered={len(local_output)}"
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
            f"multi-advantage batch mismatch: {len(gas_chunks)} "
            f"vs {len(batch_encoded_inputs)}"
        )

    for batch, batch_encoded in zip(gas_chunks, batch_encoded_inputs):
        grpo_batch = batch_encoded["grpo_batch"]
        device = grpo_batch.advantages.device
        dtype = grpo_batch.advantages.dtype
        seq_len = int(grpo_batch.advantages.shape[-1])
        batch_rows = rows[cursor : cursor + len(batch)]
        cursor += len(batch)

        perception_adv = torch.tensor(
            [float(row["perception_advantage"]) for row in batch_rows],
            dtype=dtype,
            device=device,
        )
        reasoning_adv = torch.tensor(
            [float(row["reasoning_advantage"]) for row in batch_rows],
            dtype=dtype,
            device=device,
        )

        token_index = torch.arange(seq_len, device=device).view(1, -1)
        answer_start_tokens = torch.tensor(
            [
                _token_index_for_char(
                    self,
                    sample,
                    row.get("answer_start_char"),
                )
                for sample, row in zip(batch, batch_rows)
            ],
            dtype=torch.long,
            device=device,
        )
        reasoning_region_mask = (
            token_index < answer_start_tokens.view(-1, 1)
        ).to(dtype=dtype)

        grpo_batch.gspo_base_answer_advantages = grpo_batch.advantages.clone()
        grpo_batch.gspo_perception_advantages = perception_adv
        grpo_batch.gspo_reasoning_advantages = reasoning_adv
        grpo_batch.gspo_reasoning_region_mask = reasoning_region_mask

        # k=0/k=8 are normally skipped by the curriculum.  If answer-conditioned
        # process/visual criteria still distinguish rollouts, allow those rows to
        # train on the auxiliary residual while the outcome baseline stays zero.
        base_row_weights = getattr(grpo_batch, "gspo_rl_row_weights", None)
        if base_row_weights is None:
            base_row_weights = torch.ones(
                len(batch), dtype=torch.float32, device=device
            )
        else:
            base_row_weights = base_row_weights.to(
                device=device, dtype=torch.float32
            )

        gold_rows = torch.tensor(
            [bool(row.get("gold_injected")) for row in batch_rows],
            dtype=torch.bool,
            device=device,
        )
        auxiliary_active = (
            (perception_adv.abs() > 1e-12)
            | (reasoning_adv.abs() > 1e-12)
        ) & (~gold_rows)
        grpo_batch.gspo_rl_row_weights = torch.where(
            auxiliary_active,
            torch.ones_like(base_row_weights),
            base_row_weights,
        )


GSPOGRPOTrainer._postprocess_batch = _postprocess_batch_multi_advantage


_original_get_per_token = GSPOGRPOTrainer._get_per_token_logps_and_entropies


def _counterfactual_visual_weights(
    self,
    model,
    model_inputs,
    grpo_batch,
    per_token_logps,
):
    import torch

    completion_mask = grpo_batch.completion_mask.to(
        dtype=per_token_logps.dtype
    )
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

    delta = (
        per_token_logps.detach().float()
        - masked_logps.detach().float()
    ).abs()
    delta = delta * completion_mask.float()
    denom = completion_mask.float().sum(
        dim=-1, keepdim=True
    ).clamp(min=1.0)
    mean_delta = delta.sum(dim=-1, keepdim=True) / denom
    weights = torch.where(
        mean_delta > 1e-8,
        (
            delta / (2.0 * mean_delta.clamp(min=1e-8))
        ).clamp(min=0.0, max=1.0),
        torch.zeros_like(delta),
    )

    # Keep the existing VGPO-style temporal compensation: later generated
    # tokens receive slightly more visual credit at equal dependency strength.
    length = weights.shape[-1]
    position = torch.linspace(
        0.0,
        1.0,
        steps=max(length, 1),
        device=weights.device,
        dtype=weights.dtype,
    ).view(1, -1)
    temporal = 0.75 + 0.5 * position
    return (weights * temporal).clamp(max=1.0).to(
        dtype=per_token_logps.dtype
    )


def _get_per_token_multi_advantage(self, *args, **kwargs):
    import torch

    per_token_logps, entropies = _original_get_per_token(
        self, *args, **kwargs
    )

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

    base_adv = getattr(
        grpo_batch, "gspo_base_answer_advantages", None
    )
    perception_adv = getattr(
        grpo_batch, "gspo_perception_advantages", None
    )
    reasoning_adv = getattr(
        grpo_batch, "gspo_reasoning_advantages", None
    )
    reasoning_region_mask = getattr(
        grpo_batch, "gspo_reasoning_region_mask", None
    )
    if any(
        value is None
        for value in (
            base_adv,
            perception_adv,
            reasoning_adv,
            reasoning_region_mask,
        )
    ):
        return per_token_logps, entropies

    completion_mask = grpo_batch.completion_mask.to(
        dtype=per_token_logps.dtype
    )
    visual_weights = _counterfactual_visual_weights(
        self,
        model,
        model_inputs,
        grpo_batch,
        per_token_logps,
    )
    reasoning_weights = (
        1.0 - 0.75 * visual_weights
    ).clamp(min=0.25, max=1.0)
    reasoning_weights = reasoning_weights * reasoning_region_mask

    lambda_perception = float(
        os.environ.get("GSPO_PERCEPTION_ADV_COEF", "0.25")
    )
    lambda_reasoning = float(
        os.environ.get("GSPO_REASONING_ADV_COEF", "0.25")
    )
    raw_aux = (
        lambda_perception
        * perception_adv.view(-1, 1)
        * visual_weights
        + lambda_reasoning
        * reasoning_adv.view(-1, 1)
        * reasoning_weights
    )

    # Outcome remains the anchor.  Where a non-zero final-answer advantage
    # exists, auxiliary process signals may strengthen/weaken it but cannot
    # flip its sign.  If outcome advantage is zero, retain the auxiliary signal
    # so all-correct/all-wrong groups can still learn from process variation.
    cap_ratio = max(
        0.0,
        min(
            0.99,
            float(
                os.environ.get(
                    "GSPO_AUX_TO_OUTCOME_CAP",
                    "0.75",
                )
            ),
        ),
    )
    base_abs = base_adv.abs()
    limit = cap_ratio * base_abs
    capped_aux = torch.maximum(
        torch.minimum(raw_aux, limit),
        -limit,
    )
    aux = torch.where(base_abs > 1e-8, capped_aux, raw_aux)

    combined = base_adv + aux
    grpo_batch.advantages = combined * completion_mask

    active = completion_mask.sum().clamp(min=1.0)
    zero_outcome_rows = (
        base_abs.max(dim=-1).values <= 1e-8
    ).to(dtype=torch.float32)
    aux_active_rows = (
        raw_aux.abs().max(dim=-1).values > 1e-8
    ).to(dtype=torch.float32)

    self._gspo_multi_adv_metrics = {
        "visual_dependency_mean": float(
            (visual_weights * completion_mask).sum().detach().item()
            / active.detach().item()
        ),
        "answer_adv_abs_mean": float(
            (base_abs * completion_mask).sum().detach().item()
            / active.detach().item()
        ),
        "perception_adv_abs_mean": float(
            perception_adv.abs().mean().detach().item()
        ),
        "reasoning_adv_abs_mean": float(
            reasoning_adv.abs().mean().detach().item()
        ),
        "aux_token_abs_mean": float(
            (aux.abs() * completion_mask).sum().detach().item()
            / active.detach().item()
        ),
        "zero_outcome_aux_row_ratio": float(
            (zero_outcome_rows * aux_active_rows).mean().detach().item()
        ),
    }
    return per_token_logps, entropies


GSPOGRPOTrainer._get_per_token_logps_and_entropies = (
    _get_per_token_multi_advantage
)


_original_update_metrics = GSPOGRPOTrainer._update_metrics


def _update_metrics_multi_advantage(self, metrics_data):
    _original_update_metrics(self, metrics_data)
    values = self.__dict__.pop("_gspo_multi_adv_metrics", None)
    if not values:
        return
    mode = metrics_data["mode"]
    for key, value in values.items():
        self._metrics[mode][f"multi_adv/{key}"].append(
            float(value)
        )


GSPOGRPOTrainer._update_metrics = _update_metrics_multi_advantage
