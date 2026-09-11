"""Direct-answer policy controls for the 4-GPU Pass@8 GRPO run.

The filename is kept for compatibility with existing launch/import paths.
Online rollouts and fixed-set evaluation both use the same minimal direct-answer
prompt. No response-length or forced-reasoning reward shaping is applied here.
"""

from __future__ import annotations

import json
import os
import shutil
from pathlib import Path
from typing import Any

import scripts.dlc.gspo_trainer_plugin as trainer_plugin
import scripts.sft.pass_at_8_eval as eval_module
from scripts.dlc.gspo_trainer_plugin import GSPOGRPOTrainer


# Historical prompts are stripped before applying the direct-answer suffix so
# dynamic resampling cannot accumulate conflicting instructions.
_OLD_PROMPT = (
    "\n请先独立分析问题，结合相关文本、表格和图像信息，完成必要的推理、计算和结果核对后再作答。不要直接猜测答案。"
    "\n请在回复最后一行按“答案：具体答案”的格式给出最终答案。"
)
_PREVIOUS_PROMPT = (
    "\n请严格按以下顺序作答："
    "\n1. 先仔细读取并理解图像、表格和文本中的相关信息，明确需要使用的数据；"
    "\n2. 再基于读取到的信息进行分析、推理和必要的计算，并核对结果；"
    "\n3. 最后给出答案。"
    "\n不要跳过读图直接猜答案，也不要只输出最终答案。"
    "\n请在回复最后一行按“答案：具体答案”的格式给出最终答案。"
)
_LEGACY_SYSTEM_PROMPT = """请仔细完成用户给出的计算题，并给出每一步的详细计算步骤，严禁直接输出答案。

1. 先理解题意，明确题目要求计算的目标是什么。

2. 如果题目已经明确描述了计算关系，必须首先严格按照题目原意写出计算公式。
不得自行改变题目给出的运算关系，不得自行增加、删除或替换计算指标。

3. 写出完成这个计算实际需要的数据。
如果题目包含图片、表格或图表，请从中读取与当前计算直接相关的数据；
如果没有图片，则从题干或文本中提取所需数据。

只允许使用前面计算公式中出现的指标。
不要读取、列举或计算题目没有要求的其他指标。
不要用名称相似的指标替代题目明确指定的指标。
如果题目已经直接给出了某个计算所需指标的数值，请直接使用该数值，不要根据其他相关指标重新推导或替代它。

4. 将提取的数据代入前面确定的公式，并展示必要的计算过程。
计算过程中必须保持与题目原始计算关系一致。

5. 在完成前面的数据提取和计算步骤之前，不要直接输出最终答案。

最后一行严格按照以下格式输出：

最终答案：具体答案"""
_LEGACY_USER_SUFFIX_SENTENCES = (
    "严禁直接给出答案，必须给出计算的相关步骤。",
    "只使用完成用户所问计算直接需要的数据；即使图片中存在其他指标，也不要把它们加入计算过程。",
)
_DIRECT_SUFFIX = "请只输出最终答案本身，不要输出分析过程或额外解释。"


def _clean_user_text(text: str) -> str:
    cleaned = text
    for legacy in (_OLD_PROMPT, _PREVIOUS_PROMPT):
        cleaned = cleaned.replace(legacy, "")
    for sentence in _LEGACY_USER_SUFFIX_SENTENCES:
        cleaned = cleaned.replace("\n" + sentence, "")
        cleaned = cleaned.replace(sentence, "")
    cleaned = cleaned.replace("\n" + _DIRECT_SUFFIX, "")
    cleaned = cleaned.replace(_DIRECT_SUFFIX, "")
    return cleaned.rstrip()


def _patch_user_text(text: str) -> str:
    return _clean_user_text(text) + "\n" + _DIRECT_SUFFIX


def _strip_legacy_system_prompt(messages: list[Any]) -> None:
    """Remove only the legacy forced-reasoning system prompt we used to inject."""
    remove_indices: list[int] = []
    for index, message in enumerate(messages):
        if not isinstance(message, dict) or message.get("role") != "system":
            continue
        content = message.get("content", "")
        if isinstance(content, str):
            cleaned = content.replace(_LEGACY_SYSTEM_PROMPT, "").strip()
            if cleaned:
                message["content"] = cleaned
            else:
                remove_indices.append(index)
        elif isinstance(content, list):
            new_content = []
            for item in content:
                if isinstance(item, dict) and item.get("type") == "text" and isinstance(item.get("text"), str):
                    cleaned = item["text"].replace(_LEGACY_SYSTEM_PROMPT, "").strip()
                    if cleaned:
                        copied = dict(item)
                        copied["text"] = cleaned
                        new_content.append(copied)
                else:
                    new_content.append(item)
            if new_content:
                message["content"] = new_content
            else:
                remove_indices.append(index)
    for index in reversed(remove_indices):
        messages.pop(index)


def _patch_messages(messages: list[Any], *, source: str) -> None:
    if not isinstance(messages, list):
        raise TypeError(f"{source} messages must be a list, got {type(messages)!r}")

    _strip_legacy_system_prompt(messages)

    for message in reversed(messages):
        if not isinstance(message, dict) or message.get("role") != "user":
            continue
        content = message.get("content", "")
        if isinstance(content, str):
            message["content"] = _patch_user_text(content)
        elif isinstance(content, list):
            for item in reversed(content):
                if isinstance(item, dict) and item.get("type") == "text" and isinstance(item.get("text"), str):
                    item["text"] = _patch_user_text(item["text"])
                    break
            else:
                content.append({"type": "text", "text": _DIRECT_SUFFIX})
        else:
            raise TypeError(f"{source} user message content must be str/list, got {type(content)!r}")
        break
    else:
        raise RuntimeError(f"{source} sample has no user message to patch")


def _patch_sample_prompt(sample: Any) -> None:
    messages = getattr(sample, "messages", None) or []
    _patch_messages(messages, source="GSPO rollout")


# Apply the direct-answer suffix to every online rollout, including dynamic resamples.
if not getattr(GSPOGRPOTrainer._generate_completions, "_gspo_direct_answer_prompt", False):
    _original_generate_completions = GSPOGRPOTrainer._generate_completions

    def _generate_completions_with_direct_prompt(self, samples):
        for sample in samples:
            _patch_sample_prompt(sample)
        return _original_generate_completions(self, samples)

    _generate_completions_with_direct_prompt._gspo_direct_answer_prompt = True
    GSPOGRPOTrainer._generate_completions = _generate_completions_with_direct_prompt


# Make eval message construction use exactly the same direct-answer transformation as online rollouts. The only eval-specific work here is
# converting benchmark image paths into the multimodal user content format.
def _make_direct_eval_messages(row: dict[str, Any]) -> list[dict[str, Any]]:
    question = str(row["messages"][0]["content"]).replace("<image>", "")
    content: list[dict[str, Any]] = [
        {"type": "image", "image": str(path)}
        for path in row["image_paths"]
    ]
    content.append({"type": "text", "text": question})
    messages: list[dict[str, Any]] = [{"role": "user", "content": content}]
    _patch_messages(messages, source="GSPO eval")
    return messages


eval_module._make_messages = _make_direct_eval_messages


# _evaluate_row derives row seeds from the historical base 42. Shift that seed
# deterministically so the same evaluator can be run with three fixed seeds.
if not getattr(eval_module._generate_candidates, "_gspo_eval_seed_override", False):
    _original_generate_candidates = eval_module._generate_candidates

    def _generate_candidates_with_seed_override(*args, **kwargs):
        active_seed = os.environ.get("GSPO_EVAL_ACTIVE_SEED")
        if active_seed is not None and "seed" in kwargs:
            kwargs["seed"] = int(active_seed) + (int(kwargs["seed"]) - 42)
        return _original_generate_candidates(*args, **kwargs)

    _generate_candidates_with_seed_override._gspo_eval_seed_override = True
    eval_module._generate_candidates = _generate_candidates_with_seed_override


def _reasoning_eval_temperature() -> float:
    temperature = float(os.environ.get("GSPO_TEMPERATURE", "1.2"))
    if temperature <= 0:
        raise ValueError(f"GSPO_TEMPERATURE must be positive, got {temperature}")
    return temperature


def _judge_reasoning_generation(row: dict[str, Any], reference: str, candidate: str) -> dict[str, Any]:
    # Use the same terminal-answer verifier as GSPO training reward. This avoids
    # false positives from non-terminal numbers in malformed outputs.
    correct = eval_module._benchmark_programmatic_judge(row, reference, candidate)
    return {
        "text": candidate,
        "extracted_answer": eval_module.extract_answer(candidate),
        "correct": bool(correct),
        "judge": "programmatic_reward",
    }


# Pass@1 and Pass@8 must describe the same policy distribution. Generate exactly
# eight candidates once, at the same temperature as training rollouts. Pass@1 is
# candidate 0; Pass@8 is whether any of those same eight candidates is correct.
def _evaluate_reasoning_row(model: Any, processor: Any, judge_url: str, row: dict[str, Any], step: int) -> dict[str, Any]:
    del judge_url, step
    index = int(row["sample_id"].rsplit(":", 1)[1])
    base_seed = 42 + index * 101
    candidates = eval_module._generate_candidates(
        model,
        processor,
        row,
        seed=base_seed,
        do_sample=True,
        temperature=_reasoning_eval_temperature(),
        num_return_sequences=8,
    )
    if len(candidates) != 8:
        raise RuntimeError(f"reasoning eval expected exactly 8 candidates, got {len(candidates)}")

    reference = str(row["messages"][-1]["content"])
    generations = [
        _judge_reasoning_generation(row, reference, candidate)
        for candidate in candidates
    ]
    pass_at_1_generation = generations[0]
    correct_count = sum(item["correct"] for item in generations)
    return {
        "sample_id": row["sample_id"],
        "task": row["task"],
        "reference_answer": eval_module.extract_answer(reference),
        "correct_count": correct_count,
        "first_correct": bool(pass_at_1_generation["correct"]),
        "pass_at_1_generation": pass_at_1_generation,
        "programmatic_count": len(generations),
        "model_judged_count": 0,
        "generations": generations,
    }


eval_module._evaluate_row = _evaluate_reasoning_row


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


def _eval_barrier() -> None:
    try:
        import torch.distributed as dist
        if dist.is_available() and dist.is_initialized():
            dist.barrier()
    except ImportError:
        pass


def _reset_eval_step_dir(path: Path) -> None:
    # Base evaluator appends rank prediction JSONL files. Remove an existing
    # seed/step directory before re-running the same checkpoint so retries and
    # resumes are idempotent instead of doubling coverage and Pass@k.
    if _rank() == 0 and path.exists():
        shutil.rmtree(path)
    _eval_barrier()


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
            _reset_eval_step_dir(seed_kwargs["output_dir"] / f"step-{step:06d}")
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
            "temperature": _reasoning_eval_temperature(),
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
                    "temperature": summary["temperature"],
                    "pass_at_1_mean": summary["pass_at_1"],
                    "pass_at_8_mean": summary["pass_at_8"],
                },
                ensure_ascii=False,
            ),
            flush=True,
        )

    return mean_metrics


trainer_plugin.run_distributed_evaluation = _three_seed_run_distributed_evaluation
