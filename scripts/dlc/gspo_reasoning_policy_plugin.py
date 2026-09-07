"""Reasoning-policy controls for the 4-GPU Pass@8 GSPO run.

Side effects applied after ``gspo_wandb_plugin``:
- strengthen rollout prompting: read image -> analyze/calculate -> final answer;
- assign total reward -0.1 to online responses shorter than 20 response tokens;
- run each in-training evaluation with three fixed seeds and return their mean;
- keep evaluation Pass@k out of W&B (evaluation remains on disk/stdout).
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import scripts.dlc.gspo_trainer_plugin as trainer_plugin
import scripts.dlc.gspo_wandb_plugin as wandb_plugin
import scripts.sft.pass_at_8_eval as eval_module
from scripts.dlc.gspo_trainer_plugin import GSPOEvalCallback, GSPOGRPOTrainer


_OLD_PROMPT = (
    "\n请先独立分析问题，结合相关文本、表格和图像信息，完成必要的推理、计算和结果核对后再作答。不要直接猜测答案。"
    "\n请在回复最后一行按“答案：具体答案”的格式给出最终答案。"
)
_NEW_PROMPT = (
    "\n请严格按以下顺序作答："
    "\n1. 先仔细读取并理解图像、表格和文本中的相关信息，明确需要使用的数据；"
    "\n2. 再基于读取到的信息进行分析、推理和必要的计算，并核对结果；"
    "\n3. 最后给出答案。"
    "\n不要跳过读图直接猜答案，也不要只输出最终答案。"
    "\n请在回复最后一行按“答案：具体答案”的格式给出最终答案。"
)


def _replace_prompt_text(text: str) -> str:
    if _NEW_PROMPT in text:
        return text
    if _OLD_PROMPT in text:
        return text.replace(_OLD_PROMPT, _NEW_PROMPT, 1)
    return text + _NEW_PROMPT


def _patch_sample_prompt(sample: Any) -> None:
    messages = getattr(sample, "messages", None) or []
    for message in reversed(messages):
        if not isinstance(message, dict) or message.get("role") != "user":
            continue
        content = message.get("content", "")
        if isinstance(content, str):
            message["content"] = _replace_prompt_text(content)
        elif isinstance(content, list):
            for item in reversed(content):
                if isinstance(item, dict) and item.get("type") == "text" and isinstance(item.get("text"), str):
                    item["text"] = _replace_prompt_text(item["text"])
                    break
            else:
                content.append({"type": "text", "text": _NEW_PROMPT.lstrip("\n")})
        break


# Apply the strengthened prompt to every online rollout, including dynamic resamples.
if not getattr(GSPOGRPOTrainer._generate_completions, "_gspo_read_analyze_calculate_prompt", False):
    _original_generate_completions = GSPOGRPOTrainer._generate_completions

    def _generate_completions_with_reasoning_prompt(self, samples):
        for sample in samples:
            _patch_sample_prompt(sample)
        return _original_generate_completions(self, samples)

    _generate_completions_with_reasoning_prompt._gspo_read_analyze_calculate_prompt = True
    GSPOGRPOTrainer._generate_completions = _generate_completions_with_reasoning_prompt


# Treat an online response shorter than the threshold as a failed reasoning sample.
# This overrides its total reward to -0.1 even when the final answer happens to be correct.
if not getattr(GSPOGRPOTrainer._compute_rewards_per_func, "_gspo_short_response_penalty", False):
    _original_compute_rewards_per_func = GSPOGRPOTrainer._compute_rewards_per_func

    def _compute_rewards_with_short_response_penalty(self, samples):
        import torch

        rewards = _original_compute_rewards_per_func(self, samples)
        threshold = int(os.environ.get("GSPO_REASONING_SHORT_TOKENS", "20"))
        penalty = float(os.environ.get("GSPO_REASONING_SHORT_REWARD", "-0.1"))

        local_lengths = torch.tensor(
            [len(getattr(sample, "response_token_ids", None) or []) for sample in samples],
            dtype=torch.long,
            device=self.accelerator.device,
        )
        global_lengths = self.accelerator.gather_for_metrics(local_lengths)
        global_lengths = global_lengths.reshape(-1)
        if rewards.shape[0] != global_lengths.numel():
            raise RuntimeError(
                "short-response reward alignment mismatch: "
                f"rewards={rewards.shape[0]} response_lengths={global_lengths.numel()}"
            )

        short_mask = global_lengths < threshold
        if bool(short_mask.any()):
            rewards = rewards.clone()
            rewards[short_mask, :] = penalty
        return rewards

    _compute_rewards_with_short_response_penalty._gspo_short_response_penalty = True
    GSPOGRPOTrainer._compute_rewards_per_func = _compute_rewards_with_short_response_penalty


# _evaluate_row currently derives row seeds from the historical base 42.
# Shift that seed deterministically so the same evaluator can be run three times.
if not getattr(eval_module._generate_candidates, "_gspo_eval_seed_override", False):
    _original_generate_candidates = eval_module._generate_candidates

    def _generate_candidates_with_seed_override(*args, **kwargs):
        active_seed = os.environ.get("GSPO_EVAL_ACTIVE_SEED")
        if active_seed is not None and "seed" in kwargs:
            kwargs["seed"] = int(active_seed) + (int(kwargs["seed"]) - 42)
        return _original_generate_candidates(*args, **kwargs)

    _generate_candidates_with_seed_override._gspo_eval_seed_override = True
    eval_module._generate_candidates = _generate_candidates_with_seed_override


def _eval_seeds() -> list[int]:
    values = [part.strip() for part in os.environ.get("GSPO_EVAL_SEEDS", "17,42,73").split(",") if part.strip()]
    seeds = [int(value) for value in values]
    if len(seeds) != 3 or len(set(seeds)) != 3:
        raise ValueError(f"GSPO_EVAL_SEEDS must contain exactly 3 distinct integers, got {seeds}")
    return seeds


def _rank() -> int:
    try:
        import torch.distributed as dist
        if dist.is_available() and dist.is_initialized():
            return dist.get_rank()
    except ImportError:
        pass
    return 0


# Replace the W&B plugin's old fixed-20 eval wrapper with a fixed-dataset,
# three-seed wrapper. Each seed writes its own artifacts; step summary stores the mean.
def _three_seed_run_distributed_evaluation(*args, **kwargs):
    eval_data = Path(
        os.environ.get(
            "GSPO_EVAL_DATA",
            "/mnt/nas/duolg/qwen3vl/data/benchmark/reasoning_calc_seen_50_clean.jsonl",
        )
    )
    if not eval_data.is_file():
        raise FileNotFoundError(eval_data)

    base_output = Path(kwargs["output_dir"])
    step = int(kwargs["step"])
    max_samples = int(os.environ.get("GSPO_EVAL_MAX_SAMPLES", "50")) or None
    seeds = _eval_seeds()

    # Evaluate every task in the fixed file; do not inherit the old finmmr allowlist.
    old_allowlist = os.environ.get("GSPO_BENCHMARK_ALLOWLIST")
    old_active_seed = os.environ.get("GSPO_EVAL_ACTIVE_SEED")
    os.environ["GSPO_BENCHMARK_ALLOWLIST"] = ""

    per_seed: list[dict[str, Any]] = []
    try:
        for seed in seeds:
            os.environ["GSPO_EVAL_ACTIVE_SEED"] = str(seed)
            seed_kwargs = dict(kwargs)
            seed_kwargs["benchmark_path"] = eval_data
            seed_kwargs["project_root"] = eval_data.parent
            seed_kwargs["output_dir"] = base_output / f"seed-{seed}"
            seed_kwargs["max_samples"] = max_samples
            metrics = eval_module.run_distributed_evaluation(*args, **seed_kwargs)
            per_seed.append({"seed": seed, **metrics})
    finally:
        if old_allowlist is None:
            os.environ.pop("GSPO_BENCHMARK_ALLOWLIST", None)
        else:
            os.environ["GSPO_BENCHMARK_ALLOWLIST"] = old_allowlist
        if old_active_seed is None:
            os.environ.pop("GSPO_EVAL_ACTIVE_SEED", None)
        else:
            os.environ["GSPO_EVAL_ACTIVE_SEED"] = old_active_seed

    mean_metrics: dict[str, Any] = {}
    numeric_keys = set.intersection(
        *[
            {key for key, value in row.items() if key != "seed" and isinstance(value, (int, float))}
            for row in per_seed
        ]
    ) if per_seed else set()
    for key in sorted(numeric_keys):
        mean_metrics[key] = sum(float(row[key]) for row in per_seed) / len(per_seed)

    mean_metrics["eval_seed_count"] = len(seeds)
    mean_metrics["eval_seeds"] = seeds

    if _rank() == 0:
        aggregate_dir = base_output / f"step-{step:06d}"
        aggregate_dir.mkdir(parents=True, exist_ok=True)
        summary = {
            "dataset": str(eval_data),
            "seeds": seeds,
            "seed_count": len(seeds),
            "pass_at_1": float(mean_metrics.get("pass_at_1", 0.0)),
            "pass_at_8": float(mean_metrics.get("pass_at_8", 0.0)),
            "coverage": float(mean_metrics.get("coverage", 0.0)),
            "per_seed": per_seed,
        }
        (aggregate_dir / "summary.json").write_text(
            json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(
            "[GSPO_EVAL_3SEED] "
            + json.dumps(
                {
                    "step": step,
                    "seeds": seeds,
                    "pass_at_1_mean": summary["pass_at_1"],
                    "pass_at_8_mean": summary["pass_at_8"],
                },
                ensure_ascii=False,
            ),
            flush=True,
        )

    return mean_metrics


trainer_plugin.run_distributed_evaluation = _three_seed_run_distributed_evaluation


# Keep evaluation observational: artifacts/stdout only, no eval/pass@k W&B series.
if hasattr(wandb_plugin, "_original_eval_run"):
    GSPOEvalCallback._run = wandb_plugin._original_eval_run
