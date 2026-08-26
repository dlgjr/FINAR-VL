from collections import Counter
import json
from pathlib import Path
from types import SimpleNamespace

from scripts.sft.checkpoint_eval_wandb import (
    build_wandb_metrics,
    collect_metrics,
    load_benchmark_counts,
    log_to_wandb,
    summary_path,
    validate_summary,
)


TASKS = [f"task_{index:02d}" for index in range(24)]


def _summary() -> dict:
    return {
        "total": 240,
        "completed": 240,
        "error_count": 0,
        "coverage": 1.0,
        "pass_at_1": 0.25,
        "pass_at_8": 0.75,
        "tasks": {
            task: {"completed": 10, "pass_at_1": index / 100, "pass_at_8": index / 50}
            for index, task in enumerate(TASKS)
        },
    }


def test_metric_payload_contains_only_total_and_24_task_pass_metrics() -> None:
    metrics = build_wandb_metrics(_summary(), TASKS)

    assert len(metrics) == 2 + 24 * 2
    assert set(metrics) == {
        "pass_at_1",
        "pass_at_8",
        *(f"task/{task}/pass_at_{k}" for task in TASKS for k in (1, 8)),
    }


def test_summary_validation_requires_complete_24_task_evaluation() -> None:
    counts = Counter({task: 10 for task in TASKS})
    validate_summary(_summary(), counts)

    incomplete = _summary()
    incomplete["error_count"] = 1
    incomplete["coverage"] = 239 / 240
    try:
        validate_summary(incomplete, counts)
    except ValueError as error:
        assert "errors" in str(error)
    else:
        raise AssertionError("incomplete summary must be rejected")


def test_collect_and_wandb_log_use_numeric_checkpoint_order_and_step(tmp_path: Path) -> None:
    benchmark = tmp_path / "all.jsonl"
    benchmark.write_text(
        "".join(
            json.dumps({"task": task}) + "\n"
            for task in TASKS
            for _ in range(10)
        ),
        encoding="utf-8",
    )
    counts = load_benchmark_counts(benchmark, 24)
    checkpoint_root = tmp_path / "checkpoints"
    eval_root = tmp_path / "eval"
    for name in ("checkpoint-100", "checkpoint-20"):
        (checkpoint_root / name).mkdir(parents=True)
        path = summary_path(eval_root, name)
        path.parent.mkdir(parents=True)
        path.write_text(json.dumps(_summary()), encoding="utf-8")

    collected = collect_metrics(checkpoint_root, eval_root, counts)
    assert [step for step, _, _ in collected] == [20, 100]

    logged = []

    class Run:
        def log(self, metrics, step):
            logged.append((step, metrics))

        def finish(self):
            logged.append(("finish", None))

    wandb = SimpleNamespace(init=lambda **kwargs: Run())
    log_to_wandb(
        collected,
        wandb_module=wandb,
        project="p",
        name="n",
        mode="offline",
        wandb_dir=tmp_path / "wandb",
        config={},
    )

    assert [entry[0] for entry in logged] == [20, 100, "finish"]
    assert all(len(metrics) == 50 for _, metrics in logged[:-1])


def test_launcher_uses_sft_benchmark_seven_eval_gpus_and_qwen30_judge() -> None:
    root = Path(__file__).resolve().parents[1]
    text = (root / "scripts/sft/run_gspo_checkpoint_eval_all.sh").read_text(encoding="utf-8")

    for expected in (
        "/mnt/nas/bihaoran/qwen3vl/data/benchmark/my_benchmark/all.jsonl",
        "/mnt/nas/bihaoran/model/qwen30",
        "0,1,2,3,4,5,6",
        'JUDGE_GPU="${SFT_CHECKPOINT_EVAL_JUDGE_GPU:-7}"',
        "export SFT_EVAL_MAX_SAMPLES=0",
        "--served-model-name qwen30-judge",
        "--max-model-len 8192",
        "--max-num-seqs 8",
        "--gpu-memory-utilization 0.70",
        "export WANDB_MODE=offline",
        'EVAL_ROOT="${SFT_CHECKPOINT_EVAL_ROOT:-$CHECKPOINT_ROOT/eval_sft_all}"',
        '[[ "$(basename "$checkpoint")" =~ ^checkpoint-[0-9]+$ ]]',
        "unset RANK WORLD_SIZE LOCAL_RANK MASTER_ADDR MASTER_PORT",
        "wave_start += 7",
    ):
        assert expected in text
