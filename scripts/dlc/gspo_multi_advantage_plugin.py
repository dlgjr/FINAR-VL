"""Process-localized multi-advantage credit assignment for Reasoning RL.

This plugin targets two common math-RL failure modes directly:

1. final answer correct, reasoning contains a hard error;
2. final answer wrong, but earlier verified steps are correct.

Outcome, process, and perception stay separate until token-level optimization.
Final-answer advantage is never broadcast blindly across the whole CoT.

For each rollout:

    A_token =
        A_answer * M_outcome
        + lambda_step * A_step(token)
        - lambda_suffix * M_error_suffix
        + lambda_visual * A_visual * w_visual(token)

where:
- A_answer is strict 0/1 group-relative advantage;
- M_outcome rewards verified-correct reasoning spans + the answer for a correct
  final result, and penalizes only the hard-error suffix + answer for an
  incorrect final result;
- A_step is a hard-verifier local step advantage (+ correct / - incorrect);
- M_error_suffix starts at the first verifiable process error;
- w_visual is an image-counterfactual token dependency score.

Unknown/unverifiable reasoning receives no process credit.
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


def _perception_criterion_weight(name: str) -> float:
    if name.startswith("visual_fact:"):
        return 2.0
    return float(_PERCEPTION_WEIGHTS.get(name, 0.0))


def _strict_answer_advantage(
    rows: Sequence[dict[str, Any]],
    eps: float,
) -> dict[int, float]:
    """Group-normalize strict final correctness only."""

    active = [row for row in rows if not bool(row.get("gold_injected"))]
    output = {int(row["global_index"]): 0.0 for row in rows}
    if len(active) <= 1:
        return output

    values = [1.0 if bool(row.get("answer_correct")) else 0.0 for row in active]
    mean_value = sum(values) / len(values)
    variance = sum((value - mean_value) ** 2 for value in values) / len(values)
    if variance <= eps:
        return output

    std = math.sqrt(variance + eps)
    for row, value in zip(active, values):
        output[int(row["global_index"])] = (value - mean_value) / std
    return output


def _perception_advantage(
    rows: Sequence[dict[str, Any]],
    eps: float,
) -> dict[int, float]:
    """Normalize visual quality inside answer-correct/wrong buckets."""

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
                if _perception_criterion_weight(str(name)) > 0
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
            weight = _perception_criterion_weight(name) * learnability
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


def _step_advantages(
    rows: Sequence[dict[str, Any]],
    eps: float,
) -> dict[int, list[dict[str, Any]]]:
    """Center hard step correctness inside each prompt group.

    If every verified step has the same label, retain a small absolute signal:
    all-correct steps get +1 and all-incorrect steps get -1. This lets a
    k=0/k=8 group still improve process quality when outcome variance is zero.
    """

    output: dict[int, list[dict[str, Any]]] = {
        int(row["global_index"]): [] for row in rows
    }
    flat: list[tuple[dict[str, Any], Mapping[str, Any], float]] = []
    for row in rows:
        if bool(row.get("gold_injected")):
            continue
        for step in row.get("reasoning_steps") or []:
            score = step.get("score")
            if bool(step.get("terminal")) and not bool(row.get("answer_correct")):
                # A self-consistent formula that produces a wrong final answer
                # is not a correct terminal reasoning step.
                score = 0.0
            if isinstance(score, bool) or not isinstance(score, (int, float)):
                continue
            score = float(score)
            if not math.isfinite(score):
                continue
            flat.append((row, step, score))

    if not flat:
        return output

    values = [score for _row, _step, score in flat]
    mean_value = sum(values) / len(values)
    variance = sum((value - mean_value) ** 2 for value in values) / len(values)

    if variance > eps:
        std = math.sqrt(variance + eps)

        def normalize(value: float) -> float:
            return max(-2.0, min(2.0, (value - mean_value) / std))
    else:
        def normalize(value: float) -> float:
            return 1.0 if value >= 0.5 else -1.0

    for row, step, score in flat:
        item = dict(step)
        item["advantage"] = float(normalize(score))
        output[int(row["global_index"])].append(item)
    return output


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
        answer_correct = bool(raw_score >= 1.0 and not gold_injected)
        reasoning_steps = list(process.get("reasoning_steps") or [])
        first_error_char = process.get("first_error_char")
        if not answer_correct:
            terminal_starts = [
                int(step["char_start"])
                for step in reasoning_steps
                if bool(step.get("terminal")) and step.get("char_start") is not None
            ]
            if terminal_starts:
                terminal_error = min(terminal_starts)
                first_error_char = (
                    terminal_error
                    if first_error_char is None
                    else min(int(first_error_char), terminal_error)
                )

        rows.append(
            {
                "rank": rank,
                "local_index": local_index,
                "group_id": str(
                    extra.get("sample_id")
                    or getattr(sample, "prompt_id", "")
                    or f"{rank}:{local_index // max(1, int(self.num_generations))}"
                ),
                "answer_correct": answer_correct,
                "gold_injected": gold_injected,
                "criteria": dict(process.get("criteria") or {}),
                "reasoning_steps": reasoning_steps,
                "first_error_char": first_error_char,
                "answer_start_char": process.get("answer_start_char"),
                "answer_end_char": process.get("answer_end_char"),
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
    answer_adv: dict[int, float] = {}
    perception_adv: dict[int, float] = {}
    step_adv: dict[int, list[dict[str, Any]]] = {}

    for rows in groups.values():
        rows.sort(key=lambda row: int(row["global_index"]))
        if len(rows) != expected:
            for row in rows:
                idx = int(row["global_index"])
                answer_adv[idx] = 0.0
                perception_adv[idx] = 0.0
                step_adv[idx] = []
            continue

        answer_adv.update(_strict_answer_advantage(rows, eps))
        perception_adv.update(_perception_advantage(rows, eps))
        step_adv.update(_step_advantages(rows, eps))

    rank = int(getattr(self.accelerator, "process_index", 0))
    local_output: list[dict[str, Any]] = []
    for row in all_rows:
        if int(row["rank"]) != rank:
            continue
        idx = int(row["global_index"])
        local_output.append(
            {
                **row,
                "answer_advantage": float(answer_adv.get(idx, 0.0)),
                "perception_advantage": float(perception_adv.get(idx, 0.0)),
                "step_advantages": list(step_adv.get(idx, [])),
            }
        )

    local_output.sort(key=lambda row: int(row["local_index"]))
    if len(local_output) != len(samples):
        raise RuntimeError(
            f"multi-advantage gather mismatch: local={len(samples)} "
            f"recovered={len(local_output)}"
        )
    return local_output


def _span_mask(
    self,
    sample: Any,
    start_char: int | None,
    end_char: int | None,
    *,
    seq_len: int,
    device,
    dtype,
):
    import torch

    start = _token_index_for_char(self, sample, start_char)
    end = _token_index_for_char(self, sample, end_char)
    start = max(0, min(seq_len, int(start)))
    end = max(start, min(seq_len, int(end)))
    if end == start and start < seq_len:
        end = start + 1
    index = torch.arange(seq_len, device=device)
    return ((index >= start) & (index < end)).to(dtype=dtype)


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

        answer_adv = torch.tensor(
            [float(row["answer_advantage"]) for row in batch_rows],
            dtype=dtype,
            device=device,
        )
        perception_adv = torch.tensor(
            [float(row["perception_advantage"]) for row in batch_rows],
            dtype=dtype,
            device=device,
        )
        answer_correct = torch.tensor(
            [bool(row["answer_correct"]) for row in batch_rows],
            dtype=torch.bool,
            device=device,
        )
        gold_rows = torch.tensor(
            [bool(row["gold_injected"]) for row in batch_rows],
            dtype=torch.bool,
            device=device,
        )

        answer_mask = torch.zeros((len(batch), seq_len), dtype=dtype, device=device)
        verified_good_mask = torch.zeros_like(answer_mask)
        error_suffix_mask = torch.zeros_like(answer_mask)
        step_offset = torch.zeros_like(answer_mask)

        for row_index, (sample, row) in enumerate(zip(batch, batch_rows)):
            answer_start = row.get("answer_start_char")
            answer_end = row.get("answer_end_char")
            if answer_start is None:
                # Malformed output: keep terminal outcome local instead of
                # broadcasting it over the whole completion.
                ids = list(getattr(sample, "response_token_ids", None) or [])
                start_token = max(0, len(ids) - 1)
                answer_mask[row_index, start_token : start_token + 1] = 1.0
                answer_start_token = start_token
            else:
                answer_span = _span_mask(
                    self,
                    sample,
                    int(answer_start),
                    int(answer_end) if answer_end is not None else int(answer_start) + 1,
                    seq_len=seq_len,
                    device=device,
                    dtype=dtype,
                )
                answer_mask[row_index] = answer_span
                answer_start_token = _token_index_for_char(
                    self, sample, int(answer_start)
                )

            first_error = row.get("first_error_char")
            for step in row.get("step_advantages") or []:
                step_start = int(step.get("char_start", 0))
                span = _span_mask(
                    self,
                    sample,
                    step_start,
                    int(step.get("char_end", step.get("char_start", 0))),
                    seq_len=seq_len,
                    device=device,
                    dtype=dtype,
                )
                value = float(step.get("advantage", 0.0))
                # Save-the-Good-Prefix rule: once a hard error is observed,
                # later self-consistent calculations are no longer eligible
                # for positive process credit because they may depend on the
                # erroneous state.
                if (
                    value > 0
                    and first_error is not None
                    and step_start >= int(first_error)
                ):
                    value = 0.0
                current = step_offset[row_index]
                # A verified error dominates an overlapping positive step.
                if value < 0:
                    step_offset[row_index] = torch.where(
                        span > 0,
                        torch.minimum(
                            current,
                            torch.full_like(current, value),
                        ),
                        current,
                    )
                elif value > 0:
                    step_offset[row_index] = torch.where(
                        (span > 0) & (current >= 0),
                        torch.maximum(
                            current,
                            torch.full_like(current, value),
                        ),
                        current,
                    )
                    verified_good_mask[row_index] = torch.maximum(
                        verified_good_mask[row_index],
                        span,
                    )

            if first_error is not None:
                error_start_token = _token_index_for_char(
                    self, sample, int(first_error)
                )
                error_start_token = max(
                    0, min(int(answer_start_token), int(error_start_token))
                )
                if answer_start_token > error_start_token:
                    error_suffix_mask[
                        row_index,
                        error_start_token:answer_start_token,
                    ] = 1.0

        # Strict final correctness only supplies terminal/outcome credit.
        # Correct answers reinforce verified-good process spans + answer.
        # Wrong answers penalize the hard-error suffix + answer; if no process
        # error is found, only the answer is penalized.
        correct_outcome_mask = torch.maximum(
            verified_good_mask,
            answer_mask,
        )
        wrong_outcome_mask = torch.maximum(
            error_suffix_mask,
            answer_mask,
        )
        outcome_mask = torch.where(
            answer_correct.view(-1, 1),
            correct_outcome_mask,
            wrong_outcome_mask,
        )

        grpo_batch.gspo_answer_advantages = answer_adv
        grpo_batch.gspo_answer_outcome_mask = outcome_mask
        grpo_batch.gspo_perception_advantages = perception_adv
        grpo_batch.gspo_process_step_offsets = step_offset
        grpo_batch.gspo_error_suffix_mask = error_suffix_mask
        grpo_batch.gspo_reasoning_region_mask = (
            1.0 - answer_mask
        ).clamp(min=0.0, max=1.0)

        base_row_weights = getattr(grpo_batch, "gspo_rl_row_weights", None)
        if base_row_weights is None:
            base_row_weights = torch.ones(
                len(batch), dtype=torch.float32, device=device
            )
        else:
            base_row_weights = base_row_weights.to(
                device=device, dtype=torch.float32
            )

        process_active = (
            (step_offset.abs().max(dim=-1).values > 1e-12)
            | (error_suffix_mask.max(dim=-1).values > 0)
            | (perception_adv.abs() > 1e-12)
            | (answer_adv.abs() > 1e-12)
        ) & (~gold_rows)
        grpo_batch.gspo_rl_row_weights = torch.where(
            process_active,
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

    # Later tokens get a mild compensation for visual forgetting, while the
    # actual dependency still comes from the counterfactual image ablation.
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

    answer_adv = getattr(grpo_batch, "gspo_answer_advantages", None)
    outcome_mask = getattr(grpo_batch, "gspo_answer_outcome_mask", None)
    perception_adv = getattr(grpo_batch, "gspo_perception_advantages", None)
    process_step = getattr(grpo_batch, "gspo_process_step_offsets", None)
    error_suffix = getattr(grpo_batch, "gspo_error_suffix_mask", None)
    reasoning_region = getattr(grpo_batch, "gspo_reasoning_region_mask", None)
    if any(
        value is None
        for value in (
            answer_adv,
            outcome_mask,
            perception_adv,
            process_step,
            error_suffix,
            reasoning_region,
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

    lambda_step = float(os.environ.get("GSPO_PROCESS_STEP_COEF", "0.35"))
    lambda_suffix = float(os.environ.get("GSPO_PROCESS_SUFFIX_COEF", "0.20"))
    lambda_visual = float(os.environ.get("GSPO_PERCEPTION_ADV_COEF", "0.20"))

    outcome = answer_adv.view(-1, 1) * outcome_mask
    process = lambda_step * process_step
    suffix_penalty = -lambda_suffix * error_suffix
    visual = (
        lambda_visual
        * perception_adv.view(-1, 1)
        * visual_weights
        * reasoning_region
    )

    combined = (
        outcome
        + process
        + suffix_penalty
        + visual
    ) * completion_mask
    grpo_batch.advantages = combined

    active = completion_mask.sum().clamp(min=1.0)
    self._gspo_multi_adv_metrics = {
        "visual_dependency_mean": float(
            (visual_weights * completion_mask).sum().detach().item()
            / active.detach().item()
        ),
        "answer_adv_abs_mean": float(
            answer_adv.abs().mean().detach().item()
        ),
        "process_offset_abs_mean": float(
            (process.abs() * completion_mask).sum().detach().item()
            / active.detach().item()
        ),
        "perception_adv_abs_mean": float(
            perception_adv.abs().mean().detach().item()
        ),
        "prefix_rows": float(
            (outcome_mask.sum(dim=-1) > 0).float().mean().detach().item()
        ),
        "error_rows": float(
            (error_suffix.sum(dim=-1) > 0).float().mean().detach().item()
        ),
        "process_active_rows": float(
            (process_step.abs().max(dim=-1).values > 1e-12)
            .float().mean().detach().item()
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
        self._metrics[mode][f"multi_adv/{key}"].append(float(value))


GSPOGRPOTrainer._update_metrics = _update_metrics_multi_advantage
