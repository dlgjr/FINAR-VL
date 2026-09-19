"""Keep GSPO W&B focused and make fixed-set evaluation metrics reproducible.

This module is imported for side effects by ``gspo_plugins.py``. It leaves
Trainer/stdout/checkpoint behavior alone and only changes what is emitted to
W&B, plus the fixed 20-row RL evaluation routing and two concise diagnostics:
raw pre-Gold reward and too-short reasoning ratio.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

from scripts.dlc.gspo_reward_plugin import GSPOReward
import scripts.dlc.gspo_trainer_plugin as trainer_plugin
from scripts.dlc.gspo_trainer_plugin import GSPOEvalCallback, GSPOGRPOTrainer


# Keep only training diagnostics that are useful for optimization/quality.
# Intentionally excluded: learning_rate, step_time, epoch/global_step panels,
# rollout/all8, duplicate rewards/<func>/{mean,std}, and entropy/coef.
TRAIN_WANDB_KEYS = {
    "loss",
    "grad_norm",
    "reward",
    "reward_std",
    "frac_reward_zero_std",
    "rollout/raw_reward_mean",
    "rollout/pass8",
    "rollout/positive_per_8",
    "reasoning/too_short_ratio",
    "intervention/gold_group_ratio",
    "kl",
    "ess/ratio",
    "clip_ratio/region_mean",
    "clip_ratio/low_mean",
    "clip_ratio/low_min",
    "clip_ratio/high_mean",
    "clip_ratio/high_max",
    "entropy/mean",
    "entropy/min",
    "entropy/max",
    "entropy/regularized_mean",
    "entropy/regularization_loss",
    "completions/min_length",
    "completions/mean_length",
    "completions/max_length",
    "completions/clipped_ratio",
}


def _configure_fixed_eval() -> None:
    """Route the in-training callback to the fixed rl_test.jsonl set."""
    eval_data = os.environ.get("GSPO_EVAL_DATA")
    if not eval_data:
        return
    eval_path = Path(eval_data)
    os.environ["GSPO_BENCHMARK"] = str(eval_path)
    os.environ["GSPO_BENCHMARK_ALLOWLIST"] = "finmmr"
    os.environ["GSPO_EVAL_MAX_SAMPLES"] = "20"
    # rl_test.jsonl contains paths such as assets/finmmr/xxx.png, so its parent
    # data/benchmark is the correct root (not data/benchmark/assets).
    os.environ["SFT_BENCHMARK_ROOT"] = str(eval_path.parent)


_configure_fixed_eval()


# The callback used QWEN3VL_ROOT as the image root. Override only the evaluation
# call so assets/finmmr/... resolves under data/benchmark.
_original_run_distributed_evaluation = trainer_plugin.run_distributed_evaluation


def _fixed_run_distributed_evaluation(*args, **kwargs):
    eval_data = os.environ.get("GSPO_EVAL_DATA")
    if eval_data:
        kwargs["benchmark_path"] = Path(eval_data)
        kwargs["project_root"] = Path(
            os.environ.get("SFT_BENCHMARK_ROOT", str(Path(eval_data).parent))
        )
        kwargs["max_samples"] = 20
    return _original_run_distributed_evaluation(*args, **kwargs)


trainer_plugin.run_distributed_evaluation = _fixed_run_distributed_evaluation


# The reward ORM used to call wandb.log() independently from Trainer. Suppress
# that second stream while preserving its stdout/reward-pool diagnostics.
if not getattr(GSPOReward.__call__, "_gspo_wandb_suppressed", False):
    _original_reward_call = GSPOReward.__call__

    def _reward_call_without_wandb(self, *args, **kwargs):
        old_mode = os.environ.get("WANDB_MODE")
        os.environ["WANDB_MODE"] = "offline-disabled"
        try:
            return _original_reward_call(self, *args, **kwargs)
        finally:
            if old_mode is None:
                os.environ.pop("WANDB_MODE", None)
            else:
                os.environ["WANDB_MODE"] = old_mode

    _reward_call_without_wandb._gspo_wandb_suppressed = True
    GSPOReward.__call__ = _reward_call_without_wandb


# The active V11 methods override an earlier entropy implementation. Populate
# regularized entropy metrics from the entropy term actually added to the loss.
# entropy/coef is deliberately not recorded because it is constant.
if not getattr(GSPOGRPOTrainer._compute_loss_and_metrics, "_gspo_entropy_wandb", False):
    _original_compute_loss_and_metrics = GSPOGRPOTrainer._compute_loss_and_metrics

    def _compute_loss_and_metrics_with_entropy_metrics(self, model, model_inputs, grpo_batch):
        loss, metrics_data = _original_compute_loss_and_metrics(
            self, model, model_inputs, grpo_batch
        )
        entropy_mean = metrics_data.get("concise_entropy_mean")
        if entropy_mean is not None:
            coef = float(os.environ.get("GSPO_ENTROPY_COEF", "0.02"))
            metrics_data["gspo_entropy_regularization"] = {
                "mean": float(entropy_mean),
                "loss": -coef * float(entropy_mean),
            }
        return loss, metrics_data

    _compute_loss_and_metrics_with_entropy_metrics._gspo_entropy_wandb = True
    GSPOGRPOTrainer._compute_loss_and_metrics = _compute_loss_and_metrics_with_entropy_metrics


if not getattr(GSPOGRPOTrainer._update_metrics, "_gspo_entropy_wandb", False):
    _original_update_metrics = GSPOGRPOTrainer._update_metrics

    def _update_metrics_with_entropy_metrics(self, metrics_data):
        _original_update_metrics(self, metrics_data)
        regularization = metrics_data.get("gspo_entropy_regularization")
        if regularization is None:
            return
        mode = metrics_data["mode"]
        # Keep the useful raw entropy mean/min/max and the actual regularization
        # contribution. Do not emit the constant coefficient series.
        self._metrics[mode]["entropy/regularized_mean"].append(regularization["mean"])
        self._metrics[mode]["entropy/regularization_loss"].append(regularization["loss"])

    _update_metrics_with_entropy_metrics._gspo_entropy_wandb = True
    GSPOGRPOTrainer._update_metrics = _update_metrics_with_entropy_metrics


# Raw reward is the policy reward before any Gold trajectory is inserted.
if not getattr(GSPOGRPOTrainer._initial_rollout_metrics, "_gspo_raw_reward_mean", False):
    _original_initial_rollout_metrics = GSPOGRPOTrainer._initial_rollout_metrics

    def _initial_rollout_metrics_with_raw_reward(self, rewards_per_func):
        import torch

        metrics = _original_initial_rollout_metrics(self, rewards_per_func)
        rewards = self._weighted_rewards(rewards_per_func).float()
        finite = rewards[torch.isfinite(rewards)]
        metrics["rollout/raw_reward_mean"] = (
            float(finite.mean().item()) if finite.numel() else 0.0
        )
        return metrics

    _initial_rollout_metrics_with_raw_reward._gspo_raw_reward_mean = True
    GSPOGRPOTrainer._initial_rollout_metrics = _initial_rollout_metrics_with_raw_reward


_FINAL_ANSWER_LINE_RE = re.compile(
    r"(?im)^\s*(?:最终答案|答案|answer)\s*[:：]"
)
_OTHER_FINAL_MARK_RE = re.compile(r"(?is)<answer>|\\boxed\s*\{")


def _completion_text(sample) -> str:
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


def _reasoning_prefix(text: str) -> str:
    starts = [match.start() for match in _FINAL_ANSWER_LINE_RE.finditer(text)]
    starts.extend(match.start() for match in _OTHER_FINAL_MARK_RE.finditer(text))
    if starts:
        text = text[:max(starts)]
    return text.strip()


def _reasoning_token_count(trainer, sample) -> int:
    text = _reasoning_prefix(_completion_text(sample))
    if not text:
        return 0

    tokenizer = getattr(getattr(trainer, "template", None), "tokenizer", None)
    if tokenizer is None:
        processor = getattr(trainer, "processing_class", None)
        tokenizer = getattr(processor, "tokenizer", None) or processor
    if tokenizer is not None and hasattr(tokenizer, "encode"):
        try:
            return len(tokenizer.encode(text, add_special_tokens=False))
        except Exception:
            pass

    # Fallback only if the tokenizer interface is unavailable. This keeps the
    # metric observational and never changes reward/training behavior.
    compact = re.sub(r"\s+", "", text)
    return max(1, (len(compact) + 1) // 2)


def _reasoning_too_short_ratio(trainer, samples) -> float:
    import torch

    threshold = int(os.environ.get("GSPO_REASONING_SHORT_TOKENS", "12"))
    flags = [
        float(_reasoning_token_count(trainer, sample) < threshold)
        for sample in samples
    ]
    if not flags:
        return 0.0
    local = torch.tensor(
        flags,
        dtype=torch.float32,
        device=trainer.accelerator.device,
    )
    gathered = trainer.accelerator.gather_for_metrics(local)
    return float(gathered.float().mean().item())


# Compute too-short reasoning on the raw online completions before Gold injection.
if not getattr(GSPOGRPOTrainer._dynamic_sampling, "_gspo_reasoning_metric", False):
    _original_dynamic_sampling = GSPOGRPOTrainer._dynamic_sampling

    def _dynamic_sampling_with_reasoning_metric(self, samples, rewards_per_func):
        self._gspo_reasoning_too_short_ratio = _reasoning_too_short_ratio(self, samples)
        try:
            return _original_dynamic_sampling(self, samples, rewards_per_func)
        finally:
            self.__dict__.pop("_gspo_reasoning_too_short_ratio", None)

    _dynamic_sampling_with_reasoning_metric._gspo_reasoning_metric = True
    GSPOGRPOTrainer._dynamic_sampling = _dynamic_sampling_with_reasoning_metric


# rollout/all8 is redundant. Add only the reasoning-short diagnostic to the
# same concise raw rollout metric bundle.
if not getattr(GSPOGRPOTrainer._record_concise_train_metrics, "_gspo_concise_metrics_v2", False):
    _original_record_concise_train_metrics = GSPOGRPOTrainer._record_concise_train_metrics

    def _record_concise_train_metrics_v2(self, metrics):
        concise = dict(metrics)
        concise.pop("rollout/all8", None)
        too_short = self.__dict__.get("_gspo_reasoning_too_short_ratio")
        if too_short is not None:
            concise["reasoning/too_short_ratio"] = float(too_short)
        return _original_record_concise_train_metrics(self, concise)

    _record_concise_train_metrics_v2._gspo_concise_metrics_v2 = True
    GSPOGRPOTrainer._record_concise_train_metrics = _record_concise_train_metrics_v2


# Replace only Transformers' W&B on_log sink. Trainer still computes/logs its
# full diagnostics to stdout/state, while W&B receives the whitelist above.
# This prevents automatic learning-rate/step-time/epoch/global-step panels.
try:
    from transformers.integrations.integration_utils import WandbCallback
except ImportError:  # pragma: no cover
    from transformers.integrations import WandbCallback


if not getattr(WandbCallback.on_log, "_gspo_concise_wandb", False):
    def _concise_wandb_on_log(self, args, state, control, model=None, logs=None, **kwargs):
        if self._wandb is None:
            return control
        if not self._initialized:
            self.setup(args, state, model, **kwargs)
        if not state.is_world_process_zero:
            return control

        payload: dict[str, Any] = {}
        for key, value in (logs or {}).items():
            raw_key = key.removeprefix("train/")
            if raw_key in TRAIN_WANDB_KEYS:
                payload[f"train/{raw_key}"] = value
        if payload:
            self._wandb.log(payload)
        return control

    _concise_wandb_on_log._gspo_concise_wandb = True
    WandbCallback.on_log = _concise_wandb_on_log


# After each completed fixed-set evaluation, publish only Pass@1 and Pass@8.
# Coverage/errors/timing remain in summary.json/stdout rather than cluttering W&B.
if not getattr(GSPOEvalCallback._run, "_gspo_eval_passk_wandb", False):
    _original_eval_run = GSPOEvalCallback._run

    def _run_with_passk_wandb(self, state, control=None, *, force: bool = False):
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
        if wandb.run is not None:
            wandb.log(
                {
                    "eval/pass_at_1": float(summary.get("pass_at_1", 0.0)),
                    "eval/pass_at_8": float(summary.get("pass_at_8", 0.0)),
                }
            )
        return result

    _run_with_passk_wandb._gspo_eval_passk_wandb = True
    GSPOEvalCallback._run = _run_with_passk_wandb
