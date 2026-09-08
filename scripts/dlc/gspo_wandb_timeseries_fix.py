"""Final W&B axis and concise reasoning diagnostics for GSPO.

Imported after gspo_wandb_plugin. It changes observability only.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import scripts.dlc.gspo_wandb_plugin as wandb_plugin
from scripts.dlc.gspo_trainer_plugin import GSPOEvalCallback, GSPOGRPOTrainer


# Keep the selected-batch reward diagnostics, but replace the misleading
# post-selection zero-std panel with raw pre-resample group diagnostics.
wandb_plugin.TRAIN_WANDB_KEYS.discard("frac_reward_zero_std")
wandb_plugin.TRAIN_WANDB_KEYS.update(
    {
        "learning_rate",
        "rollout/raw_zero_std_group_ratio",
        "sampling/resample_rounds",
    }
)

_METRIC_ALIASES = {
    "rollout/pass8": "rollout/raw_pass_at_8",
    "rollout/positive_per_8": "rollout/raw_positive_per_8",
    "intervention/gold_group_ratio": "intervention/gold_fallback_group_ratio",
}


def _wandb_key(raw_key: str) -> str:
    return _METRIC_ALIASES.get(raw_key, raw_key)


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
        ids = token_ids.tolist() if hasattr(token_ids, "tolist") else list(token_ids)
        if ids:
            tokenizer = _tokenizer(trainer)
            if tokenizer is not None and hasattr(tokenizer, "decode"):
                return str(tokenizer.decode(ids, skip_special_tokens=True))

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
        return len(tokenizer.encode(text, add_special_tokens=False))

    compact = "".join(text.split())
    return max(1, (len(compact) + 1) // 2)


def _reasoning_too_short_ratio(trainer, samples) -> float:
    import torch

    # This is observational only. Match the <100-token length-shaping boundary,
    # while GSPO_REASONING_SHORT_TOKENS=0 keeps the separate hard penalty disabled.
    threshold = int(os.environ.get("GSPO_REASONING_DIRECT_TOKENS", "100"))
    flags = [float(_reasoning_token_count(trainer, sample) < threshold) for sample in samples]
    if not flags:
        return 0.0
    local = torch.tensor(flags, dtype=torch.float32, device=trainer.accelerator.device)
    gathered = trainer.accelerator.gather_for_metrics(local)
    return float(gathered.float().mean().item())


# Existing rollout wrappers resolve these module globals dynamically.
wandb_plugin._reasoning_token_count = _reasoning_token_count
wandb_plugin._reasoning_too_short_ratio = _reasoning_too_short_ratio


# Attach raw zero-variance ratio and the reasoning-short ratio to the initial
# policy rollout, before resampling and before Gold fallback.
_original_initial_rollout_metrics = GSPOGRPOTrainer._initial_rollout_metrics


def _initial_rollout_metrics_v4(self, rewards_per_func):
    import torch

    metrics = _original_initial_rollout_metrics(self, rewards_per_func)
    rewards = self._weighted_rewards(rewards_per_func).float().view(-1, 8)
    finite = torch.isfinite(rewards).all(dim=1)
    finite_rewards = rewards[finite]
    metrics["rollout/raw_zero_std_group_ratio"] = (
        float((finite_rewards.max(dim=1).values == finite_rewards.min(dim=1).values).float().mean().item())
        if finite_rewards.numel()
        else 0.0
    )
    too_short = self.__dict__.get("_gspo_reasoning_too_short_ratio")
    if too_short is not None:
        metrics["reasoning/too_short_ratio"] = float(too_short)
    return metrics


_initial_rollout_metrics_v4._gspo_short_ratio_v4 = True
GSPOGRPOTrainer._initial_rollout_metrics = _initial_rollout_metrics_v4


# Count only extra generation rounds triggered from inside dynamic sampling.
_original_generate_completions = GSPOGRPOTrainer._generate_completions


def _generate_completions_with_resample_count(self, samples):
    if self.__dict__.get("_gspo_count_resamples", False):
        self._gspo_resample_rounds = int(self.__dict__.get("_gspo_resample_rounds", 0)) + 1
    return _original_generate_completions(self, samples)


_generate_completions_with_resample_count._gspo_resample_count_v4 = True
GSPOGRPOTrainer._generate_completions = _generate_completions_with_resample_count

_original_dynamic_sampling = GSPOGRPOTrainer._dynamic_sampling


def _dynamic_sampling_with_resample_metric(self, samples, rewards_per_func):
    self._gspo_count_resamples = True
    self._gspo_resample_rounds = 0
    try:
        result = _original_dynamic_sampling(self, samples, rewards_per_func)
        self._record_concise_train_metrics(
            {"sampling/resample_rounds": float(self._gspo_resample_rounds)}
        )
        return result
    finally:
        self.__dict__.pop("_gspo_count_resamples", None)
        self.__dict__.pop("_gspo_resample_rounds", None)


_dynamic_sampling_with_resample_metric._gspo_resample_metric_v4 = True
GSPOGRPOTrainer._dynamic_sampling = _dynamic_sampling_with_resample_metric


try:
    from transformers.integrations.integration_utils import WandbCallback
except ImportError:  # pragma: no cover
    from transformers.integrations import WandbCallback


def _configure_axis(wandb_module) -> Any:
    run = getattr(wandb_module, "run", None)
    if run is None:
        return None
    if getattr(run, "_gspo_axis_configured_v4", False):
        return run

    run.define_metric("_gspo_step", hidden=True, summary="none", overwrite=True)
    for raw_key in wandb_plugin.TRAIN_WANDB_KEYS:
        run.define_metric(
            f"train/{_wandb_key(raw_key)}",
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

    run.config.update(
        {
            "gspo/generation_batch_size": int(os.environ.get("GSPO_GENERATION_BATCH_SIZE", "0")),
            "gspo/steps_per_generation": int(os.environ.get("GSPO_STEPS_PER_GENERATION", "0")),
            "gspo/num_iterations": int(os.environ.get("GSPO_NUM_ITERATIONS", "0")),
            "gspo/max_resample_times": int(os.environ.get("GSPO_MAX_RESAMPLE_TIMES", "0")),
            "gspo/gold_mode": "fallback_after_resample",
            "gspo/reasoning_short_metric_tokens": int(os.environ.get("GSPO_REASONING_DIRECT_TOKENS", "100")),
        },
        allow_val_change=True,
    )
    run._gspo_axis_configured_v4 = True
    return run


def _concise_wandb_on_log_v4(self, args, state, control, model=None, logs=None, **kwargs):
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
            payload[f"train/{_wandb_key(raw_key)}"] = value

    if len(payload) > 1:
        run.log(payload)
    return control


_concise_wandb_on_log_v4._gspo_concise_wandb_v4 = True
WandbCallback.on_log = _concise_wandb_on_log_v4


# Publish Pass@k exactly once on the same hidden training-step axis.
_original_eval_run = wandb_plugin._original_eval_run


def _eval_run_v4(self, state, control=None, *, force: bool = False):
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


_eval_run_v4._gspo_eval_passk_wandb_v4 = True
GSPOEvalCallback._run = _eval_run_v4
