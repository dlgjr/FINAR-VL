"""Final W&B history-axis and reasoning-length fixes for GSPO.

Imported after gspo_wandb_plugin. It does not change reward/loss/Gold behavior.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import scripts.dlc.gspo_wandb_plugin as wandb_plugin
from scripts.dlc.gspo_trainer_plugin import GSPOEvalCallback, GSPOGRPOTrainer


def _tokenizer(trainer):
    template = getattr(trainer, "template", None)
    tokenizer = getattr(template, "tokenizer", None)
    if tokenizer is not None:
        return tokenizer

    processor = (
        getattr(trainer, "processing_class", None)
        or getattr(trainer, "processor", None)
    )
    tokenizer = getattr(processor, "tokenizer", None)
    return tokenizer or processor


def _completion_text(trainer, sample) -> str:
    """Decode the actual online response, preferring response_token_ids."""
    token_ids = getattr(sample, "response_token_ids", None)
    if token_ids is not None:
        try:
            ids = token_ids.tolist() if hasattr(token_ids, "tolist") else list(token_ids)
        except Exception:
            ids = []
        if ids:
            tokenizer = _tokenizer(trainer)
            if tokenizer is not None and hasattr(tokenizer, "decode"):
                try:
                    return str(tokenizer.decode(ids, skip_special_tokens=True))
                except Exception:
                    pass

    for attr in ("response", "completion"):
        value = getattr(sample, attr, None)
        if isinstance(value, str) and value:
            return value

    messages = getattr(sample, "messages", None) or []
    if messages and isinstance(messages[-1], dict) and messages[-1].get("role") == "assistant":
        content = messages[-1].get("content", "")
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts = []
            for item in content:
                if isinstance(item, str):
                    parts.append(item)
                elif isinstance(item, dict) and isinstance(item.get("text"), str):
                    parts.append(item["text"])
            return "".join(parts)
    return ""


def _reasoning_token_count(trainer, sample) -> int:
    text = wandb_plugin._reasoning_prefix(_completion_text(trainer, sample))
    if not text:
        return 0

    tokenizer = _tokenizer(trainer)
    if tokenizer is not None and hasattr(tokenizer, "encode"):
        try:
            return len(tokenizer.encode(text, add_special_tokens=False))
        except Exception:
            pass

    compact = "".join(text.split())
    return max(1, (len(compact) + 1) // 2)


# Existing too-short-ratio code resolves this module global dynamically.
wandb_plugin._reasoning_token_count = _reasoning_token_count


# Also attach the ratio directly to raw rollout metrics. The existing concise
# recorder may set the same key later; dict overwrite is harmless and identical.
if not getattr(GSPOGRPOTrainer._initial_rollout_metrics, "_gspo_short_ratio_v3", False):
    _original_initial_rollout_metrics = GSPOGRPOTrainer._initial_rollout_metrics

    def _initial_rollout_metrics_v3(self, rewards_per_func):
        metrics = _original_initial_rollout_metrics(self, rewards_per_func)
        too_short = self.__dict__.get("_gspo_reasoning_too_short_ratio")
        if too_short is not None:
            metrics["reasoning/too_short_ratio"] = float(too_short)
        return metrics

    _initial_rollout_metrics_v3._gspo_short_ratio_v3 = True
    GSPOGRPOTrainer._initial_rollout_metrics = _initial_rollout_metrics_v3


try:
    from transformers.integrations.integration_utils import WandbCallback
except ImportError:  # pragma: no cover
    from transformers.integrations import WandbCallback


def _configure_axis(wandb_module) -> Any:
    run = getattr(wandb_module, "run", None)
    if run is None:
        return None
    if getattr(run, "_gspo_axis_configured_v3", False):
        return run

    # Use an explicit hidden metric as x-axis. overwrite=True replaces the
    # Transformers train/global_step binding established during callback setup.
    run.define_metric("_gspo_step", hidden=True, summary="none", overwrite=True)
    for raw_key in wandb_plugin.TRAIN_WANDB_KEYS:
        run.define_metric(
            f"train/{raw_key}",
            step_metric="_gspo_step",
            step_sync=True,
            overwrite=True,
        )
    for key in ("eval/pass_at_1", "eval/pass_at_8"):
        run.define_metric(
            key,
            step_metric="_gspo_step",
            step_sync=True,
            overwrite=True,
        )

    run._gspo_axis_configured_v3 = True
    return run


def _concise_wandb_on_log_v3(self, args, state, control, model=None, logs=None, **kwargs):
    if self._wandb is None:
        return control
    if not self._initialized:
        self.setup(args, state, model, **kwargs)
    if not state.is_world_process_zero:
        return control

    run = _configure_axis(self._wandb)
    if run is None:
        return control

    payload: dict[str, Any] = {"_gspo_step": int(state.global_step)}
    for key, value in (logs or {}).items():
        raw_key = key.removeprefix("train/")
        if raw_key in wandb_plugin.TRAIN_WANDB_KEYS:
            payload[f"train/{raw_key}"] = value

    if len(payload) > 1:
        run.log(payload)
    return control


_concise_wandb_on_log_v3._gspo_concise_wandb_v3 = True
WandbCallback.on_log = _concise_wandb_on_log_v3


# Replace the previous eval wrapper so Pass@k is logged exactly once and uses
# the same hidden training-step axis.
_original_eval_run = wandb_plugin._original_eval_run


def _eval_run_v3(self, state, control=None, *, force: bool = False):
    step = int(state.global_step)
    previous_step = self.last_eval_step
    result = _original_eval_run(self, state, control, force=force)

    actually_ran = self.last_eval_step == step and previous_step != step
    if not actually_ran or not getattr(state, "is_world_process_zero", True):
        return result

    summary_path = (
        Path(self.args.output_dir)
        / "eval"
        / f"step-{step:06d}"
        / "summary.json"
    )
    if not summary_path.is_file():
        return result
    summary = json.loads(summary_path.read_text(encoding="utf-8"))

    try:
        import wandb
    except ImportError:
        return result

    run = _configure_axis(wandb)
    if run is not None:
        run.log(
            {
                "_gspo_step": step,
                "eval/pass_at_1": float(summary.get("pass_at_1", 0.0)),
                "eval/pass_at_8": float(summary.get("pass_at_8", 0.0)),
            }
        )
    return result


_eval_run_v3._gspo_eval_passk_wandb_v3 = True
GSPOEvalCallback._run = _eval_run_v3
