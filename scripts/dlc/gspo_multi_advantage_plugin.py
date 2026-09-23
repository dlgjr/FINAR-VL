"""Decoupled answer/process/perception credit assignment for Reasoning RL.

The two target failure modes are handled explicitly:

1. correct final answer + wrong process:
   the answer span keeps positive outcome advantage while the first verifiable
   process error receives a local negative offset;
2. wrong final answer + mostly correct process:
   only the answer span receives negative outcome advantage, while verified
   good-prefix steps receive positive process credit and the first hard error
   receives a local penalty.

The design combines the decoupled step-wise advantage idea from SRaR with the
verified-good-prefix idea from Verifiable Prefix Policy Optimization (VPPO).
Perception remains a separate soft token channel based on image-counterfactual
log-probability sensitivity.
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


def _outcome_signal(rows: Sequence[dict[str, Any]], eps: float) -> dict[int, float]:
    """Standard GRPO normalization on final-answer correctness only."""

    values = [1.0 if row["answer_correct"] else 0.0 for row in rows]
    mean_value = sum(values) / len(values)
    variance = sum((value - mean_value) ** 2 for value in values) / len(values)
    if variance <= eps:
        return {int(row["global_index"]): 0.0 for row in rows}
    std = math.sqrt(variance + eps)
    return {
        int(row["global_index"]): (value - mean_value) / std
        for row, value in zip(rows, values)
    }


def _perception_signal(rows: Sequence[dict[str, Any]], eps: float) -> dict[int, float]:
    """Group-normalized perception criteria; zero-variance criteria are silent."""

    signal = {int(row["global_index"]): 0.0 for row in rows}
    usable = [row for row in rows if not row.get("gold_injected")]
    if len(usable) <= 1:
        return signal

    names = sorted(
        {
            str(name)
            for row in usable
            for name in (row.get("criteria") or {})
            if name.startswith("visual_fact:") or name in _PERCEPTION_WEIGHTS
        }
    )
    total_weight = 0.0
    for name in names:
        values: list[float] = []
        valid_rows: list[dict[str, Any]] = []
        for row in usable:
            value = (row.get("criteria") or {}).get(name)
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                continue
            value = float(value)
            if not math.isfinite(value):
                continue
            values.append(value)
            valid_rows.append(row)
        if len(values) <= 1:
            continue

        mean_value = sum(values) / len(values)
        variance = sum((value - mean_value) ** 2 for value in values) / len(values)
        learnability = min(1.0, 4.0 * variance)
        static_weight = 2.0 if name.startswith("visual_fact:") else float(_PERCEPTION_WEIGHTS[name])
        weight = static_weight * learnability
        if weight <= eps:
            continue

        std = math.sqrt(variance + eps)
        total_weight += weight
        for row, value in zip(valid_rows, values):
            signal[int(row["global_index"])] += weight * ((value - mean_value) / std)

    if total_weight <= eps:
        return signal

    signal = {key: value / total_weight for key, value in signal.items()}
    max_abs = max((abs(value) for value in signal.values()), default=0.0)
    if max_abs <= eps:
        return {key: 0.0 for key in signal}
    return {key: max(-1.0, min(1.0, value / max_abs)) for key, value in signal.items()}


def _step_relative_offsets(
    rows: Sequence[dict[str, Any]],
    eps: float,
) -> dict[tuple[int, int], float]:
    """SRaR-style cross-rollout normalization for aligned reasoning-step ordinals."""

    by_step: dict[int, list[tuple[int, float]]] = {}
    for row in rows:
        if row.get("gold_injected"):
            continue
        first_error = row.get("first_error_char")
        for step in row.get("reasoning_steps") or []:
            # Downstream arithmetic after a hard error may be locally valid but
            # semantically conditioned on a corrupted state. Do not reinforce it.
            if first_error is not None and int(step.get("char_start", 0)) > int(first_error):
                continue
            status = str(step.get("status") or "")
            if status not in {"correct", "wrong"}:
                continue
            raw = 1.0 if status == "correct" else -1.0
            by_step.setdefault(int(step.get("index", 0)), []).append(
                (int(row["global_index"]), raw)
            )

    offsets: dict[tuple[int, int], float] = {}
    for step_index, items in by_step.items():
        if len(items) <= 1:
            continue
        values = [value for _, value in items]
        mean_value = sum(values) / len(values)
        variance = sum((value - mean_value) ** 2 for value in values) / len(values)
        if variance <= eps:
            continue
        std = math.sqrt(variance + eps)
        for global_index, value in items:
            offsets[(global_index, step_index)] = max(
                -2.0,
                min(2.0, (value - mean_value) / std),
            )
    return offsets


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
                # Gold CE rows replace a failed on-policy row. Treat them as
                # outcome-failures for group statistics and exclude them from
                # process/perception normalization.
                "answer_correct": bool(raw_score >= 1.0 and not gold_injected),
                "gold_injected": gold_injected,
                "criteria": dict(process.get("criteria") or {}),
                "reasoning_steps": list(process.get("reasoning_steps") or []),
                "process_status": str(process.get("status") or ""),
                "first_error_char": process.get("first_error_char"),
                "first_error_end_char": process.get("first_error_end_char"),
                "answer_start_char": process.get("answer_start_char"),
                "answer_end_char": process.get("answer_end_char"),
                "group_k": int(extra.get("_gspo_group_k", -1)),
                "answer_rl_weight": float(extra.get("_gspo_rl_weight", 1.0)),
            }
        )
    return rows


def _compute_local_channels(self, samples: Sequence[Any]) -> list[dict[str, Any]]:
    from accelerate.utils import gather_object

    local_rows = _local_rows(self, samples)
    all_rows = list(gather_object(local_rows))
    for global_index, row in enumerate(all_rows):
        row["global_index"] = global_index

    eps = float(os.environ.get("GSPO_MULTI_ADV_EPS", "1e-6"))
    groups: dict[str, list[dict[str, Any]]] = {}
    for row in all_rows:
        groups.setdefault(str(row["group_id"]), []).append(row)

    outcome: dict[int, float] = {}
    perception: dict[int, float] = {}
    step_offsets: dict[tuple[int, int], float] = {}

    for rows in groups.values():
        rows.sort(key=lambda row: int(row["global_index"]))
        outcome.update(_outcome_signal(rows, eps))
        perception.update(_perception_signal(rows, eps))
        step_offsets.update(_step_relative_offsets(rows, eps))

    rank = int(getattr(self.accelerator, "process_index", 0))
    local_output: list[dict[str, Any]] = []
    for row in all_rows:
        if int(row["rank"]) != rank:
            continue
        idx = int(row["global_index"])
        row_steps = []
        for step in row.get("reasoning_steps") or []:
            copied = dict(step)
            copied["relative_offset"] = float(
                step_offsets.get((idx, int(step.get("index", 0))), 0.0)
            )
            row_steps.append(copied)
        local_output.append(
            {
                **row,
                "reasoning_steps": row_steps,
                "outcome_advantage": float(outcome.get(idx, 0.0)),
                "perception_advantage": float(perception.get(idx, 0.0)),
            }
        )

    local_output.sort(key=lambda row: int(row["local_index"]))
    if len(local_output) != len(samples):
        raise RuntimeError(
            f"multi-advantage gather mismatch: local={len(samples)} recovered={len(local_output)}"
        )
    return local_output


def _token_span_for_chars(
    self,
    sample: Any,
    start_char: int | None,
    end_char: int | None,
) -> tuple[int, int]:
    """Map verifier character spans to the generated-token axis.

    This follows SRaR's offset-mapping approach and falls back to a monotone
    character-ratio mapping when tokenizer offsets do not align one-to-one with
    the sampled response token ids.
    """

    ids = list(getattr(sample, "response_token_ids", None) or [])
    total_tokens = len(ids)
    if total_tokens == 0:
        return 0, 0

    text = _completion_text(sample)
    total_chars = len(text)
    if start_char is None:
        return max(0, total_tokens - 1), total_tokens
    start_char = max(0, int(start_char))
    end_char = max(start_char, int(end_char if end_char is not None else start_char + 1))

    def linear() -> tuple[int, int]:
        if total_chars <= 0:
            return 0, total_tokens
        start = min(total_tokens, int(start_char / total_chars * total_tokens))
        end = min(
            total_tokens,
            max(start + 1, math.ceil(end_char / total_chars * total_tokens)),
        )
        return start, end

    tokenizer = getattr(getattr(self, "template", None), "tokenizer", None)
    if tokenizer is None or not getattr(tokenizer, "is_fast", False):
        return linear()

    try:
        encoded = tokenizer(
            text,
            add_special_tokens=False,
            return_offsets_mapping=True,
        )
        offsets = encoded["offset_mapping"]
    except Exception:
        return linear()
    if len(offsets) != total_tokens:
        return linear()

    import bisect

    token_ends = [int(end) for _start, end in offsets]
    start = bisect.bisect_right(token_ends, start_char)
    if end_char > start_char:
        end = bisect.bisect_right(token_ends, max(end_char - 1, start_char)) + 1
    else:
        end = start + 1
    start = max(0, min(start, total_tokens))
    end = max(start + 1, min(end, total_tokens))
    return start, end


def _process_offset_tensor(
    self,
    sample: Any,
    row: Mapping[str, Any],
    seq_len: int,
    *,
    device,
    dtype,
):
    import torch

    offset = torch.zeros(seq_len, device=device, dtype=dtype)
    if row.get("gold_injected"):
        return offset, False, 0, False

    step_coef = float(os.environ.get("GSPO_STEP_ADV_COEF", "0.30"))
    prefix_coef = float(os.environ.get("GSPO_PREFIX_ADV_COEF", "0.35"))
    error_coef = float(os.environ.get("GSPO_ERROR_ADV_COEF", "0.50"))

    first_error = row.get("first_error_char")
    eligible_steps = []
    good_prefix_steps = []
    for step in row.get("reasoning_steps") or []:
        start_char = int(step.get("char_start", 0))
        if first_error is not None and start_char > int(first_error):
            continue
        eligible_steps.append(step)
        if str(step.get("status") or "") == "correct":
            if first_error is None or int(step.get("char_end", start_char)) <= int(first_error):
                good_prefix_steps.append(step)

    # SRaR-style step-relative offset. It is decoupled from the answer baseline
    # and only touches the tokens belonging to that verified arithmetic step.
    for step in eligible_steps:
        relative = float(step.get("relative_offset", 0.0))
        if abs(relative) <= 1e-12:
            continue
        start, end = _token_span_for_chars(
            self,
            sample,
            int(step.get("char_start", 0)),
            int(step.get("char_end", 0)),
        )
        offset[start:end] += step_coef * relative

    # VPPO-style good-prefix preservation. When the final answer is wrong,
    # verified correct steps before the first error receive an absolute positive
    # bonus even if every rollout shares the same prefix and group variance is 0.
    prefix_applied = False
    if not bool(row.get("answer_correct")) and good_prefix_steps and prefix_coef > 0:
        per_step = prefix_coef / len(good_prefix_steps)
        for step in good_prefix_steps:
            start, end = _token_span_for_chars(
                self,
                sample,
                int(step.get("char_start", 0)),
                int(step.get("char_end", 0)),
            )
            offset[start:end] += per_step
        prefix_applied = True

    # Hard first-error penalty. This is what fixes the "answer is correct but
    # process is wrong" case: the answer keeps its positive outcome advantage,
    # while the localized bad process span is pushed down independently.
    error_applied = False
    if first_error is not None and error_coef > 0:
        start, end = _token_span_for_chars(
            self,
            sample,
            int(first_error),
            row.get("first_error_end_char"),
        )
        offset[start:end] -= error_coef
        error_applied = True

    active_tokens = int((offset.abs() > 1e-12).sum().item())
    return offset, bool(active_tokens), active_tokens, prefix_applied, error_applied


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
        seq_len = int(grpo_batch.advantages.shape[-1])
        batch_rows = rows[cursor : cursor + len(batch)]
        cursor += len(batch)

        parent_advantages = grpo_batch.advantages.clone()
        answer_values = []
        for row_index, row in enumerate(batch_rows):
            # Preserve the existing calibrated Pass@0 partial-answer channel,
            # but route it only to the terminal answer span. Mixed groups use
            # strict binary answer correctness; mastered k=8 groups stay zero.
            if int(row.get("group_k", -1)) == 0:
                value = float(parent_advantages[row_index, 0].detach().item())
            else:
                value = (
                    float(row["outcome_advantage"])
                    * float(row["answer_rl_weight"])
                )
            answer_values.append(value)
        answer_adv = torch.tensor(
            answer_values,
            dtype=dtype,
            device=device,
        )
        perception_adv = torch.tensor(
            [float(row["perception_advantage"]) for row in batch_rows],
            dtype=dtype,
            device=device,
        )
        answer_mask = torch.zeros(
            (len(batch), seq_len),
            dtype=dtype,
            device=device,
        )
        outcome_mask = torch.zeros_like(answer_mask)
        process_offsets = torch.zeros_like(answer_mask)
        process_active = torch.zeros(len(batch), dtype=torch.bool, device=device)
        prefix_rows = 0
        error_rows = 0

        for row_index, (sample, row) in enumerate(zip(batch, batch_rows)):
            if row.get("gold_injected"):
                continue
            a_start, a_end = _token_span_for_chars(
                self,
                sample,
                row.get("answer_start_char"),
                row.get("answer_end_char"),
            )
            answer_mask[row_index, a_start:a_end] = 1.0
            outcome_mask[row_index, a_start:a_end] = 1.0

            # Positive outcome credit is routed only to reasoning spans that
            # the deterministic verifier can prove correct. Negative outcome
            # credit stays on the final answer span, so an incorrect answer
            # cannot erase a verified-good reasoning prefix.
            if float(row["outcome_advantage"]) > 0:
                first_error = row.get("first_error_char")
                for step in row.get("reasoning_steps") or []:
                    if str(step.get("status") or "") != "correct":
                        continue
                    if first_error is not None and int(step.get("char_start", 0)) >= int(first_error):
                        continue
                    s_start, s_end = _token_span_for_chars(
                        self,
                        sample,
                        int(step.get("char_start", 0)),
                        int(step.get("char_end", 0)),
                    )
                    outcome_mask[row_index, s_start:s_end] = 1.0

            local_offset, active, _active_tokens, prefix_applied, error_applied = _process_offset_tensor(
                self,
                sample,
                row,
                seq_len,
                device=device,
                dtype=dtype,
            )
            process_offsets[row_index] = local_offset
            process_active[row_index] = active
            if prefix_applied:
                prefix_rows += 1
            if error_applied:
                error_rows += 1

        grpo_batch.gspo_answer_advantages = answer_adv
        grpo_batch.gspo_answer_mask = answer_mask
        grpo_batch.gspo_outcome_mask = outcome_mask
        grpo_batch.gspo_process_offsets = process_offsets
        grpo_batch.gspo_perception_advantages = perception_adv

        # The curriculum may mark k=0 / k=8 rows as RL-skipped. Re-enable only
        # rows that now carry independently verified process/perception credit.
        base_row_weights = getattr(grpo_batch, "gspo_rl_row_weights", None)
        if base_row_weights is None:
            base_row_weights = torch.ones(len(batch), dtype=torch.float32, device=device)
        else:
            base_row_weights = base_row_weights.to(device=device, dtype=torch.float32)

        perception_active = perception_adv.abs() > 1e-12
        gold_rows = torch.tensor(
            [bool(row.get("gold_injected")) for row in batch_rows],
            dtype=torch.bool,
            device=device,
        )
        auxiliary_active = (process_active | perception_active) & (~gold_rows)
        grpo_batch.gspo_rl_row_weights = torch.where(
            auxiliary_active,
            torch.ones_like(base_row_weights),
            base_row_weights,
        )

        # Parent advantages are no longer the Reasoning objective. Set a neutral
        # placeholder; the per-token tensor is assembled after log-probs are
        # available, immediately before the parent loss consumes it.
        grpo_batch.advantages = torch.zeros_like(grpo_batch.advantages)

        grpo_batch.gspo_credit_meta = {
            "prefix_rows": prefix_rows,
            "error_rows": error_rows,
            "process_active_rows": int(process_active.sum().item()),
        }


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
    return weights.to(dtype=per_token_logps.dtype)


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

    answer_adv = getattr(grpo_batch, "gspo_answer_advantages", None)
    answer_mask = getattr(grpo_batch, "gspo_answer_mask", None)
    outcome_mask = getattr(grpo_batch, "gspo_outcome_mask", None)
    process_offsets = getattr(grpo_batch, "gspo_process_offsets", None)
    perception_adv = getattr(grpo_batch, "gspo_perception_advantages", None)
    if any(value is None for value in (answer_adv, answer_mask, outcome_mask, process_offsets, perception_adv)):
        return per_token_logps, entropies

    completion_mask = grpo_batch.completion_mask.to(dtype=per_token_logps.dtype)
    visual_weights = _counterfactual_visual_weights(
        self,
        model,
        model_inputs,
        grpo_batch,
        per_token_logps,
    )
    perception_coef = float(os.environ.get("GSPO_PERCEPTION_ADV_COEF", "0.25"))

    combined = (
        answer_adv.view(-1, 1) * outcome_mask
        + process_offsets
        + perception_coef * perception_adv.view(-1, 1) * visual_weights
    )
    grpo_batch.advantages = combined * completion_mask

    active = completion_mask.sum().clamp(min=1.0)
    credit_meta = getattr(grpo_batch, "gspo_credit_meta", {}) or {}
    self._gspo_multi_adv_metrics = {
        "visual_dependency_mean": float(
            (visual_weights * completion_mask).sum().detach().item()
            / active.detach().item()
        ),
        "answer_adv_abs_mean": float(answer_adv.abs().mean().detach().item()),
        "process_offset_abs_mean": float(
            (process_offsets.abs() * completion_mask).sum().detach().item()
            / active.detach().item()
        ),
        "perception_adv_abs_mean": float(perception_adv.abs().mean().detach().item()),
        "prefix_rows": float(credit_meta.get("prefix_rows", 0)),
        "error_rows": float(credit_meta.get("error_rows", 0)),
        "process_active_rows": float(credit_meta.get("process_active_rows", 0)),
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
