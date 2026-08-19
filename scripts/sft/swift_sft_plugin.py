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

_COMPLETENESS_INSTRUCTIONS = {
    "financial_relation_extraction": "请完整输出所有符合要求的关系，不要只输出部分关系或首条关系。",
    "financial_entity_extraction": "请完整输出所有符合要求的实体及其类型，不要遗漏已出现的实体。",
    "entity_extraction_classification": "请完整输出所有符合要求的实体及其分类，不要只输出部分结果。",
    "image_caption": "请完整描述图中的主要标题、文字、图表、关键数值与趋势，不要只输出标题或单个短语。",
    "financial_visual_description": "请完整描述图中的主要标题、文字、图表、关键数值与趋势，不要只输出标题或单个短语。",
}

# (probability, lambda) for CE + lambda * KL(base || student).
# These are retention-only tasks: normal SFT CE is always kept. The existing
# task=generation route remains KL-only in kl_retention_plugin.py.
_DEFAULT_MIXED_KL_POLICY = {
    "financial_summarization": (0.30, 0.15),
    "document_summarization": (0.20, 0.10),
    "summary_announcement": (0.15, 0.05),
    "image_caption": (0.30, 0.15),
    "financial_data_description": (0.20, 0.10),
    "financial_ocr": (0.10, 0.05),
}


def _mixed_kl_policy(task: str) -> tuple[float, float] | None:
    default = _DEFAULT_MIXED_KL_POLICY.get(task)
    if default is None:
        return None
    env_key = task.upper().replace("-", "_")
    probability = float(os.environ.get(f"SFT_MIXED_KL_PROB_{env_key}", str(default[0])))
    weight = float(os.environ.get(f"SFT_MIXED_KL_WEIGHT_{env_key}", str(default[1])))
    if not 0.0 <= probability <= 1.0:
        raise ValueError(f"mixed KL probability for {task} must be in [0,1], got {probability}")
    if weight < 0.0:
        raise ValueError(f"mixed KL weight for {task} must be non-negative, got {weight}")
    return probability, weight


def _should_apply_mixed_kl(trainer, task: str, route: dict, probability: float) -> bool:
    if probability <= 0.0:
        return False
    if probability >= 1.0:
        return True
    state = getattr(trainer, "state", None)
    step = int(getattr(state, "global_step", 0) or 0) + 1
    seed = int(os.environ.get("SFT_PLAN_SEED", "42"))
    payload = ":".join(
        [
            str(seed),
            str(step),
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
        instruction = _COMPLETENESS_INSTRUCTIONS.get(str(row.get("task") or ""))
        if instruction is None:
            return row
        row = copy.deepcopy(row)
        for message in row.get("messages") or []:
            if message.get("role") == "user" and isinstance(message.get("content"), str):
                message["content"] = message["content"].rstrip() + "\n" + instruction
                break
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
    for task in ("financial_ocr", "financial_summarization", "financial_visual_description", "image_caption", "accounting_audit_reasoning"):
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
    """Keep normal CE and add a small, sampled retention KL on selected tasks."""

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
            route = dict(getattr(trainer, "_finar_runtime_route", {}) or getattr(trainer, "_finar_kl_route", {}) or {})
            route.setdefault("task", task)
            route.setdefault("raw_index", route.get("index", -1))
            probability, weight = policy
            applied = weight > 0.0 and _should_apply_mixed_kl(trainer, task, route, probability)
            if not applied:
                trainer._finar_last_mixed_kl = {
                    "task": task,
                    "applied": False,
                    "probability": probability,
                    "weight": weight,
                }
                return result

            # Import lazily so the original KL plugin remains the single owner of
            # teacher rollout, multimodal re-encoding, SP alignment, and KL math.
            from scripts.sft import kl_retention_plugin as _kl

            kl_loss = _kl._generation_distill_loss(model, trainer, route, return_outputs=False)
            if isinstance(result, tuple):
                ce_loss, outputs = result
            else:
                ce_loss, outputs = result, None
            total_loss = ce_loss + weight * kl_loss
            metrics = {
                "task": task,
                "applied": True,
                "probability": probability,
                "weight": weight,
                "ce_loss": float(ce_loss.detach().item()),
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
                    f"task={metrics['task']} p={metrics['probability']:.2f} lambda={metrics['weight']:.3f} "
                    f"ce={metrics['ce_loss']:.4f} kl={metrics['kl_loss']:.4f} total={metrics['total_loss']:.4f}",
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
