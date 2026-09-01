"""Compatibility entry point for the FINAR SFT plugin.

The implementation is kept in ``swift_sft_plugin_impl.py``. Runtime sample
replacement must be installed only after ``Seq2SeqTrainer.__init__`` has
assigned ``train_dataset``/``data_collator``. ms-swift constructs callbacks
before those attributes exist, so this shim defers only that installation until
the first ``get_train_dataloader()`` call.
"""

from __future__ import annotations

import copy
import hashlib
import json
import os
import types
from pathlib import Path

from scripts.sft import pass_at_8_eval as _pass_at_8_eval
from scripts.sft import swift_sft_plugin_impl as _impl


# Preserve the historical import surface, including private helpers used by the
# SFT tests and the KL plugin. Function/class globals still point at _impl,
# which is intentional: patching the installer globals below changes the
# behavior of the already-registered FinarPlanCallback without copying it.
globals().update({
    name: value
    for name, value in vars(_impl).items()
    if not name.startswith("__")
})

# External plugins can be loaded by file path under a non-package module name,
# while later code imports scripts.sft.swift_sft_plugin normally. Preserve the
# true implementation functions on _impl so a second execution of this shim
# never mistakes an already-patched function for the original.
if not hasattr(_impl, "_finar_original_install_runtime_replacement"):
    _impl._finar_original_install_runtime_replacement = _impl._install_runtime_replacement
if not hasattr(_impl, "_finar_original_install_plan_dataloader"):
    _impl._finar_original_install_plan_dataloader = _impl._install_plan_dataloader
if not hasattr(_impl, "_finar_original_runtime_replacement_dataset"):
    _impl._finar_original_runtime_replacement_dataset = _impl.RuntimeReplacementDataset
if not hasattr(_pass_at_8_eval, "_finar_original_summarize_results"):
    _pass_at_8_eval._finar_original_summarize_results = _pass_at_8_eval.summarize_results
if not hasattr(_impl, "_finar_original_merge_plan_block"):
    _impl._finar_original_merge_plan_block = _impl._PlanRuntimeTracker.merge_block
if not hasattr(_impl, "_finar_original_plan_callback"):
    _impl._finar_original_plan_callback = _impl.FinarPlanCallback

_ORIGINAL_INSTALL_RUNTIME_REPLACEMENT = _impl._finar_original_install_runtime_replacement
_ORIGINAL_INSTALL_PLAN_DATALOADER = _impl._finar_original_install_plan_dataloader
_ORIGINAL_RUNTIME_REPLACEMENT_DATASET = _impl._finar_original_runtime_replacement_dataset
_ORIGINAL_SUMMARIZE_RESULTS = _pass_at_8_eval._finar_original_summarize_results
_ORIGINAL_MERGE_PLAN_BLOCK = _impl._finar_original_merge_plan_block
_ORIGINAL_PLAN_CALLBACK = _impl._finar_original_plan_callback

# These instructions are applied to both the supervised CE prompt and, for
# mixed-retention samples, the frozen-teacher prompt. Keeping the two prompt
# conditions identical is essential: otherwise the CE objective can ask for a
# complete answer while the KL objective anchors the student on a shorter raw
# prompt distribution.
_COMPLETENESS_INSTRUCTIONS = {
    "financial_relation_extraction": "请完整输出所有符合要求的关系，不要只输出部分关系或首条关系。",
    "financial_entity_extraction": "请完整输出所有符合要求的实体及其类型，不要遗漏已出现的实体。",
    "entity_extraction_classification": "请完整输出所有符合要求的实体及其分类，不要只输出部分结果。",
    "financial_summarization": (
        "请输出完整的金融摘要：概括核心经营和财务趋势，区分一次性或非经营性因素，"
        "评价利润与现金流质量及其可持续性，并结合管理层指引指出主要前瞻风险；"
        "不要只罗列数字或单一事实。"
    ),
    "document_summarization": (
        "请完整概括材料中的核心经营和财务变化、一次性因素、现金流或盈利质量、"
        "管理层指引及主要前瞻风险，不要只摘录个别数字。"
    ),
    "summary_announcement": (
        "请完整总结公告的核心变化、主要驱动、一次性因素、可持续性和后续风险，"
        "不要只复述标题或单一指标。"
    ),
    "financial_visual_description": (
        "请完整描述图中的主要标题、文字、图表类型、关键数值、趋势或结构及其含义；"
        "不要只输出标题、图表类别或单个短语。"
    ),
    "financial_data_description": (
        "请完整描述图表或数据中的关键字段、数值、趋势和相互关系，不要只给出图表名称或单个数字。"
    ),
    "insufficient_information_detection": (
        "请先判断现有材料是否足以唯一回答问题。若信息足够，必须给出可确定的结果和必要计算；"
        "只有信息确实不足时才回答无法确定，并明确指出缺失的具体变量、时点或假设以及其必要性。"
        "不要默认选择信息不足。"
    ),
    "financial_ocr": (
        "请按图中原文精确读取目标内容，保留正负号、小数位、千分位、百分号、货币符号和单位等关键信息，"
        "不要只给出近似数值。"
    ),
    "financial_ocr_transcription": (
        "请按图中原文精确转写，保留正负号、小数位、千分位、百分号、货币符号和单位等格式信息。"
    ),
}


def _append_retention_instruction(messages, task: str):
    """Append the task instruction to the last user turn, once."""
    instruction = _COMPLETENESS_INSTRUCTIONS.get(str(task or ""))
    if instruction is None:
        return messages

    for message in reversed(messages or []):
        if str(message.get("role") or "") != "user":
            continue
        content = message.get("content")
        if isinstance(content, str):
            if instruction not in content:
                message["content"] = content.rstrip() + "\n" + instruction
            return messages
        if isinstance(content, list):
            already_present = any(
                isinstance(item, dict)
                and str(item.get("type") or "") == "text"
                and instruction in str(item.get("text") or "")
                for item in content
            )
            if not already_present:
                content.append({"type": "text", "text": "\n" + instruction})
            return messages
    return messages


def _patch_kl_teacher_prompt(kl_module) -> None:
    """Make mixed-KL teacher prompts use the same task instruction as CE."""
    if not hasattr(kl_module, "_finar_original_teacher_messages"):
        kl_module._finar_original_teacher_messages = kl_module._teacher_messages
    original_teacher_messages = kl_module._finar_original_teacher_messages

    def teacher_messages_with_retention(record, *, data_file):
        messages = original_teacher_messages(record, data_file=data_file)
        return _append_retention_instruction(messages, str(record.get("task") or ""))

    kl_module._teacher_messages = teacher_messages_with_retention


# Keep teacher trajectories stable by default. An explicit environment override
# still wins, but repeated encounters otherwise use the same greedy base answer.
os.environ.setdefault("SFT_TEACHER_TEMPERATURE", "0")

# `task == generation` is a pure online-distillation objective (CE=0). Keep its
# anchor strong but below the historical beta=1.0, and decouple it from mixed
# retention so summary/visual/insufficient KL can use their own scale.
os.environ.setdefault("SFT_GENERATION_KL_BETA", "0.7")
os.environ.setdefault("SFT_MIXED_KL_BETA", "1.0")
os.environ["SFT_KL_BETA"] = os.environ["SFT_GENERATION_KL_BETA"]

# Group retention by benchmark-relevant semantic capability rather than exact
# task name. Values are (probability, KL lambda, CE scale).
# Summary and full visual description are retention-first because step-0 is
# already strong but later SFT collapses completeness/stability. Insufficient
# information keeps the previous strength after recovering close to base, while
# OCR receives a moderate retention increase without suppressing adaptation.
_RETENTION_FAMILIES = {
    "summary": {
        "financial_summarization": (1.00, 1.00, 0.25),
        "document_summarization": (0.90, 0.90, 0.35),
        "summary_announcement": (0.90, 0.80, 0.40),
    },
    "visual_description": {
        "financial_visual_description": (1.00, 1.00, 0.20),
        # Keep short-caption adaptation active. Do not attach the long-form
        # completeness instruction to image_caption because its CE targets are
        # intentionally short and would otherwise contradict the prompt.
        "image_caption": (0.10, 0.10, 1.00),
        "financial_data_description": (0.90, 0.80, 0.35),
    },
    "insufficient_information": {
        "insufficient_information_detection": (0.60, 0.70, 0.50),
        # Adjacent truthfulness QA is only a weak proxy, so do not suppress CE.
        "financial_truthfulness_qa": (0.04, 0.08, 1.00),
    },
    "ocr": {
        "financial_ocr": (0.30, 0.35, 0.85),
        "financial_ocr_transcription": (0.30, 0.30, 0.90),
    },
    "chart": {
        "candlestick_time_series": (0.03, 0.10, 1.00),
        "chart_arithmetic_reasoning": (0.03, 0.10, 1.00),
        "chart_counting": (0.03, 0.10, 1.00),
        "chart_data_extraction": (0.03, 0.10, 1.00),
        "chart_legend_identification": (0.03, 0.10, 1.00),
        "chart_statement_verification": (0.03, 0.10, 1.00),
        "chart_trend_inference": (0.03, 0.10, 1.00),
        "chart_visual_property_reasoning": (0.03, 0.10, 1.00),
        "multimodal_financial_chart_reasoning_v5": (0.03, 0.10, 1.00),
    },
}
_RETENTION_TASK_TO_FAMILY = {
    task: family
    for family, tasks in _RETENTION_FAMILIES.items()
    for task in tasks
}
_DEFAULT_MIXED_KL_POLICY = {
    task: policy
    for tasks in _RETENTION_FAMILIES.values()
    for task, policy in tasks.items()
}


def _mixed_kl_policy(task: str) -> tuple[float, float, float] | None:
    default = _DEFAULT_MIXED_KL_POLICY.get(task)
    if default is None:
        return None

    family = _RETENTION_TASK_TO_FAMILY[task]
    task_key = task.upper().replace("-", "_")
    family_key = family.upper().replace("-", "_")

    family_probability = os.environ.get(f"SFT_MIXED_KL_PROB_FAMILY_{family_key}")
    family_weight = os.environ.get(f"SFT_MIXED_KL_WEIGHT_FAMILY_{family_key}")
    family_ce_scale = os.environ.get(f"SFT_MIXED_CE_SCALE_FAMILY_{family_key}")
    probability_default = default[0] if family_probability is None else float(family_probability)
    weight_default = default[1] if family_weight is None else float(family_weight)
    ce_scale_default = default[2] if family_ce_scale is None else float(family_ce_scale)

    probability = float(os.environ.get(f"SFT_MIXED_KL_PROB_{task_key}", str(probability_default)))
    weight = float(os.environ.get(f"SFT_MIXED_KL_WEIGHT_{task_key}", str(weight_default)))
    ce_scale = float(os.environ.get(f"SFT_MIXED_CE_SCALE_{task_key}", str(ce_scale_default)))
    if not 0.0 <= probability <= 1.0:
        raise ValueError(f"mixed KL probability for {task} must be in [0,1], got {probability}")
    if weight < 0.0:
        raise ValueError(f"mixed KL weight for {task} must be non-negative, got {weight}")
    if ce_scale < 0.0:
        raise ValueError(f"mixed CE scale for {task} must be non-negative, got {ce_scale}")
    return probability, weight, ce_scale


def _should_apply_mixed_kl(trainer, task: str, route: dict, probability: float) -> bool:
    if probability <= 0.0:
        return False
    if probability >= 1.0:
        return True

    # Intentionally omit global_step: the same raw sample belongs to the same
    # retention cohort every time it is drawn. Changing p gives nested cohorts.
    seed = int(os.environ.get("SFT_PLAN_SEED", "42"))
    payload = ":".join(
        [
            str(seed),
            task,
            str(route.get("modality") or ""),
            str(route.get("raw_index", route.get("index", -1))),
        ]
    ).encode("utf-8")
    value = int.from_bytes(hashlib.sha256(payload).digest()[:8], "big") / float(1 << 64)
    return value < probability


class _CompletenessDataset:
    def __init__(self, dataset):
        self.dataset = dataset

    def __len__(self):
        return len(self.dataset)

    def __getitem__(self, index):
        row = self.dataset[index]
        if isinstance(index, str) or not isinstance(row, dict):
            return row
        task = str(row.get("task") or "")
        if task not in _COMPLETENESS_INSTRUCTIONS:
            return row
        row = copy.deepcopy(row)
        _append_retention_instruction(row.get("messages") or [], task)
        return row


class _CompletenessRuntimeReplacementDataset(_ORIGINAL_RUNTIME_REPLACEMENT_DATASET):
    def __init__(self, dataset, *args, **kwargs):
        super().__init__(_CompletenessDataset(dataset), *args, **kwargs)


def _summarize_results_with_correct_rate(results, *, total, errors):
    summary = _ORIGINAL_SUMMARIZE_RESULTS(results, total=total, errors=errors)
    completed = len(results)
    summary["mean_correct_at_8"] = (
        sum(int(result["correct_count"]) for result in results) / (8 * completed)
        if completed else 0.0
    )
    grouped = {}
    for result in results:
        task = str(result["task"])
        values = grouped.setdefault(task, [0, 0])
        values[0] += int(result["correct_count"])
        values[1] += 1
    for task, (correct_count, count) in grouped.items():
        summary["tasks"][task]["mean_correct_at_8"] = correct_count / (8 * count)
    return summary


def _merge_plan_block_with_actual_log(self, block_id: int) -> None:
    _ORIGINAL_MERGE_PLAN_BLOCK(self, block_id)
    payload = json.loads((self.output_dir / f"block_{block_id:04d}.json").read_text(encoding="utf-8"))
    actual = payload["actual"]
    parts = [f"block={block_id}"]
    for task in (
        "financial_ocr",
        "financial_ocr_transcription",
        "financial_summarization",
        "financial_visual_description",
        "image_caption",
        "insufficient_information_detection",
        "accounting_audit_reasoning",
    ):
        values = actual["tasks"].get(task)
        if values is not None:
            parts.append(f"{task}={values['samples']}")
    family = actual["families"].get("document_perception")
    if family is not None:
        parts.append(f"document_perception={family['samples']}({family['sample_ratio']:.3f})")
    print("INFO     | >> actual_sample_distribution " + " ".join(parts), flush=True)


def _defer_runtime_replacement(trainer, plan_dir: Path, tracker) -> None:
    """Record replacement state without touching trainer.train_dataset yet."""
    trainer._finar_runtime_replacement_pending = (Path(plan_dir), tracker)
    trainer._finar_runtime_replacement_installed = False


def _install_plan_dataloader_deferred(trainer) -> bool:
    """Install the plan dataloader and resolve replacement on first use."""
    installed = _ORIGINAL_INSTALL_PLAN_DATALOADER(trainer)
    if not installed:
        return False

    planned_get_train_dataloader = trainer.get_train_dataloader

    def deferred_get_train_dataloader(self, *args, **kwargs):
        if not bool(getattr(self, "_finar_runtime_replacement_installed", False)):
            pending = getattr(self, "_finar_runtime_replacement_pending", None)
            if pending is None:
                raise RuntimeError("runtime replacement state missing before train dataloader creation")
            plan_dir, tracker = pending
            # At this point Trainer.__init__ is complete: train_dataset,
            # template and data_collator are all available. Wrap them exactly
            # once, before PlanSampler/DataLoaderShard capture them.
            _ORIGINAL_INSTALL_RUNTIME_REPLACEMENT(self, Path(plan_dir), tracker)
            self._finar_runtime_replacement_installed = True
            self._finar_runtime_replacement_pending = None
        return planned_get_train_dataloader(*args, **kwargs)

    trainer.get_train_dataloader = types.MethodType(deferred_get_train_dataloader, trainer)
    return True


class FinarMixedKLPlanCallback(_ORIGINAL_PLAN_CALLBACK):
    """Apply task-level CE scaling plus sampled semantic retention KL."""

    def __init__(self, args, trainer):
        super().__init__(args, trainer)
        original_compute_loss = trainer.compute_loss

        def mixed_kl_compute_loss(model, inputs, *compute_args, **compute_kwargs):
            result = original_compute_loss(model, inputs, *compute_args, **compute_kwargs)
            task = str(getattr(trainer, "_finar_current_task", "") or "")
            policy = _mixed_kl_policy(task)
            if policy is None:
                trainer._finar_last_mixed_kl = None
                return result

            if isinstance(result, tuple):
                ce_loss, outputs = result
            else:
                ce_loss, outputs = result, None

            route = dict(getattr(trainer, "_finar_runtime_route", {}) or getattr(trainer, "_finar_kl_route", {}) or {})
            route.setdefault("task", task)
            route.setdefault("raw_index", route.get("index", -1))
            probability, weight, ce_scale = policy
            family = _RETENTION_TASK_TO_FAMILY[task]
            scaled_ce_loss = ce_scale * ce_loss
            applied = weight > 0.0 and _should_apply_mixed_kl(trainer, task, route, probability)

            if not applied:
                trainer._finar_last_mixed_kl = {
                    "task": task,
                    "family": family,
                    "applied": False,
                    "probability": probability,
                    "weight": weight,
                    "ce_scale": ce_scale,
                    "raw_ce_loss": float(ce_loss.detach().item()),
                    "scaled_ce_loss": float(scaled_ce_loss.detach().item()),
                }
                return (scaled_ce_loss, outputs) if isinstance(result, tuple) else scaled_ce_loss

            # Import lazily so the original KL plugin remains the single owner of
            # teacher rollout, multimodal re-encoding, SP alignment, and KL math.
            from scripts.sft import kl_retention_plugin as _kl

            # Mixed-retention teacher and CE must see the same task-level
            # instruction. Generation has no entry in the instruction table, so
            # its standalone pure-KL behavior remains unchanged.
            _patch_kl_teacher_prompt(_kl)

            # `_generation_distill_loss` reads SFT_KL_BETA internally. Temporarily
            # switch to a dedicated mixed-retention beta so task=generation can
            # stay at beta=0.7 without shrinking the semantic retention KL.
            generation_beta = os.environ.get("SFT_KL_BETA")
            os.environ["SFT_KL_BETA"] = os.environ.get("SFT_MIXED_KL_BETA", "1.0")
            try:
                kl_loss = _kl._generation_distill_loss(model, trainer, route, return_outputs=False)
            finally:
                if generation_beta is None:
                    os.environ.pop("SFT_KL_BETA", None)
                else:
                    os.environ["SFT_KL_BETA"] = generation_beta

            total_loss = scaled_ce_loss + weight * kl_loss
            metrics = {
                "task": task,
                "family": family,
                "applied": True,
                "probability": probability,
                "weight": weight,
                "ce_scale": ce_scale,
                "raw_ce_loss": float(ce_loss.detach().item()),
                "scaled_ce_loss": float(scaled_ce_loss.detach().item()),
                "kl_loss": float(kl_loss.detach().item()),
                "total_loss": float(total_loss.detach().item()),
            }
            trainer._finar_last_mixed_kl = metrics
            if isinstance(getattr(trainer, "_finar_last_kl", None), dict):
                trainer._finar_last_kl.update(metrics)
                trainer._finar_last_kl["mixed_ce_kl"] = True
            return (total_loss, outputs) if isinstance(result, tuple) else total_loss

        trainer.compute_loss = mixed_kl_compute_loss

    def on_step_end(self, args, state, control, **kwargs):
        control = super().on_step_end(args, state, control, **kwargs)
        if state.is_world_process_zero:
            metrics = getattr(self.trainer, "_finar_last_mixed_kl", None)
            if isinstance(metrics, dict) and metrics.get("applied"):
                print(
                    "INFO     | >> mixed_kl "
                    f"task={metrics['task']} family={metrics['family']} "
                    f"p={metrics['probability']:.2f} lambda={metrics['weight']:.3f} "
                    f"ce_scale={metrics['ce_scale']:.2f} "
                    f"ce_raw={metrics['raw_ce_loss']:.4f} "
                    f"ce_scaled={metrics['scaled_ce_loss']:.4f} "
                    f"kl={metrics['kl_loss']:.4f} total={metrics['total_loss']:.4f}",
                    flush=True,
                )
            self.trainer._finar_last_mixed_kl = None
        return control


# FinarPlanCallback was defined in _impl, so its global lookups resolve through
# the _impl module. Replace only these helpers; all sampling/accounting
# behavior remains the existing implementation.
_impl.RuntimeReplacementDataset = _CompletenessRuntimeReplacementDataset
_impl._PlanRuntimeTracker.merge_block = _merge_plan_block_with_actual_log
_impl._install_runtime_replacement = _defer_runtime_replacement
_impl._install_plan_dataloader = _install_plan_dataloader_deferred
_pass_at_8_eval.summarize_results = _summarize_results_with_correct_rate
_impl.FinarPlanCallback = FinarMixedKLPlanCallback
_impl.callbacks_map["finar_plan"] = FinarMixedKLPlanCallback

# Keep direct imports from this compatibility module consistent with the
# patched behavior too.
RuntimeReplacementDataset = _CompletenessRuntimeReplacementDataset
_install_runtime_replacement = _defer_runtime_replacement
_install_plan_dataloader = _install_plan_dataloader_deferred
callbacks_map["finar_plan"] = FinarMixedKLPlanCallback
