"""Validate and log batch checkpoint evaluation summaries to W&B."""

from __future__ import annotations

import argparse
import json
import re
import shlex
from collections import Counter
from pathlib import Path
from typing import Any


CHECKPOINT_RE = re.compile(r"^checkpoint-(\d+)$")


def load_benchmark_counts(path: Path, expected_task_count: int) -> Counter[str]:
    counts: Counter[str] = Counter()
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                counts[str(json.loads(line)["task"])] += 1
    if len(counts) != expected_task_count:
        raise ValueError(
            f"benchmark task count mismatch: expected={expected_task_count} actual={len(counts)} "
            f"tasks={sorted(counts)}"
        )
    return counts


def validate_summary(summary: dict[str, Any], benchmark_counts: Counter[str]) -> None:
    total = sum(benchmark_counts.values())
    if int(summary.get("total", -1)) != total:
        raise ValueError(f"summary total mismatch: expected={total} actual={summary.get('total')}")
    if int(summary.get("completed", -1)) != total:
        raise ValueError(f"summary incomplete: expected={total} completed={summary.get('completed')}")
    if int(summary.get("error_count", -1)) != 0:
        raise ValueError(f"summary has errors: error_count={summary.get('error_count')}")
    if float(summary.get("coverage", -1.0)) != 1.0:
        raise ValueError(f"summary coverage is not complete: coverage={summary.get('coverage')}")

    tasks = summary.get("tasks") or {}
    if set(tasks) != set(benchmark_counts):
        raise ValueError(
            "summary task set mismatch: "
            f"missing={sorted(set(benchmark_counts) - set(tasks))} "
            f"extra={sorted(set(tasks) - set(benchmark_counts))}"
        )
    for task, expected in benchmark_counts.items():
        actual = int(tasks[task].get("completed", -1))
        if actual != expected:
            raise ValueError(f"task {task} incomplete: expected={expected} completed={actual}")


def build_wandb_metrics(summary: dict[str, Any], task_names: list[str]) -> dict[str, float]:
    metrics = {
        "pass_at_1": float(summary["pass_at_1"]),
        "pass_at_8": float(summary["pass_at_8"]),
    }
    for task in task_names:
        task_summary = summary["tasks"][task]
        metrics[f"task/{task}/pass_at_1"] = float(task_summary["pass_at_1"])
        metrics[f"task/{task}/pass_at_8"] = float(task_summary["pass_at_8"])
    return metrics


def checkpoint_directories(root: Path) -> list[tuple[int, Path]]:
    checkpoints = []
    for path in root.iterdir():
        match = CHECKPOINT_RE.fullmatch(path.name)
        if path.is_dir() and match:
            checkpoints.append((int(match.group(1)), path))
    return sorted(checkpoints)


def summary_path(eval_root: Path, checkpoint_name: str) -> Path:
    return eval_root / "checkpoints" / checkpoint_name / "eval" / "step-000000" / "summary.json"


def collect_metrics(
    checkpoint_root: Path,
    eval_root: Path,
    benchmark_counts: Counter[str],
) -> list[tuple[int, str, dict[str, float]]]:
    task_names = sorted(benchmark_counts)
    collected = []
    checkpoints = checkpoint_directories(checkpoint_root)
    if not checkpoints:
        raise ValueError(f"no checkpoint-<step> directories found in {checkpoint_root}")
    for step, checkpoint in checkpoints:
        path = summary_path(eval_root, checkpoint.name)
        if not path.is_file():
            raise ValueError(f"missing summary for {checkpoint.name}: {path}")
        summary = json.loads(path.read_text(encoding="utf-8"))
        validate_summary(summary, benchmark_counts)
        collected.append((step, checkpoint.name, build_wandb_metrics(summary, task_names)))
    return collected


def print_metrics(
    collected: list[tuple[int, str, dict[str, float]]],
    task_names: list[str],
    focus_tasks: list[str],
) -> None:
    for step, name, metrics in collected:
        print(
            f"CHECKPOINT_RESULT checkpoint={name} step={step} "
            f"pass_at_1={metrics['pass_at_1']:.4f} pass_at_8={metrics['pass_at_8']:.4f}",
            flush=True,
        )
        for task in task_names:
            print(
                f"  task={task} "
                f"pass_at_1={metrics[f'task/{task}/pass_at_1']:.4f} "
                f"pass_at_8={metrics[f'task/{task}/pass_at_8']:.4f}",
                flush=True,
            )
        for task in focus_tasks:
            print(
                f"  CALCULATION_FOCUS task={task} "
                f"pass_at_1={metrics[f'task/{task}/pass_at_1']:.4f} "
                f"pass_at_8={metrics[f'task/{task}/pass_at_8']:.4f}",
                flush=True,
            )


def write_metrics_jsonl(path: Path, collected: list[tuple[int, str, dict[str, float]]]) -> None:
    records = [
        json.dumps({"checkpoint": name, "step": step, **metrics}, ensure_ascii=False) + "\n"
        for step, name, metrics in collected
    ]
    path.write_text("".join(records), encoding="utf-8")


def log_to_wandb(
    collected: list[tuple[int, str, dict[str, float]]],
    *,
    wandb_module: Any,
    project: str,
    name: str,
    mode: str,
    wandb_dir: Path,
    config: dict[str, Any],
) -> Path | None:
    run = wandb_module.init(
        project=project,
        name=name,
        mode=mode,
        dir=str(wandb_dir),
        config=config,
    )
    for step, _, metrics in collected:
        run.log(metrics, step=step)
    run.finish()
    offline_runs = sorted((wandb_dir / "wandb").glob("offline-run-*"))
    return offline_runs[-1] if offline_runs else None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate = subparsers.add_parser("validate-benchmark")
    validate.add_argument("--benchmark", type=Path, required=True)
    validate.add_argument("--expected-task-count", type=int, default=24)
    validate.add_argument("--focus-task", action="append", default=[])

    check = subparsers.add_parser("check-summary")
    check.add_argument("--benchmark", type=Path, required=True)
    check.add_argument("--expected-task-count", type=int, default=24)
    check.add_argument("--summary", type=Path, required=True)

    log = subparsers.add_parser("log")
    log.add_argument("--checkpoint-root", type=Path, required=True)
    log.add_argument("--eval-root", type=Path, required=True)
    log.add_argument("--benchmark", type=Path, required=True)
    log.add_argument("--expected-task-count", type=int, default=24)
    log.add_argument("--focus-task", action="append", default=[])
    log.add_argument("--wandb-dir", type=Path, required=True)
    log.add_argument("--wandb-project", required=True)
    log.add_argument("--wandb-name", required=True)
    log.add_argument("--wandb-mode", default="offline")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    counts = load_benchmark_counts(args.benchmark, args.expected_task_count)

    if args.command == "validate-benchmark":
        missing_focus = sorted(set(args.focus_task) - set(counts))
        if missing_focus:
            raise ValueError(f"focus tasks missing from benchmark: {missing_focus}")
        print(f"BENCHMARK_OK rows={sum(counts.values())} tasks={len(counts)}")
        for task in sorted(counts):
            print(f"  task={task} rows={counts[task]}")
        return

    if args.command == "check-summary":
        if not args.summary.is_file():
            raise SystemExit(1)
        try:
            validate_summary(json.loads(args.summary.read_text(encoding="utf-8")), counts)
        except (KeyError, TypeError, ValueError, json.JSONDecodeError):
            raise SystemExit(1)
        return

    task_names = sorted(counts)
    missing_focus = sorted(set(args.focus_task) - set(counts))
    if missing_focus:
        raise ValueError(f"focus tasks missing from benchmark: {missing_focus}")
    collected = collect_metrics(args.checkpoint_root, args.eval_root, counts)
    print_metrics(collected, task_names, args.focus_task)
    write_metrics_jsonl(args.eval_root / "all_checkpoint_metrics.jsonl", collected)

    import wandb

    args.wandb_dir.mkdir(parents=True, exist_ok=True)
    offline_run = log_to_wandb(
        collected,
        wandb_module=wandb,
        project=args.wandb_project,
        name=args.wandb_name,
        mode=args.wandb_mode,
        wandb_dir=args.wandb_dir,
        config={
            "checkpoint_root": str(args.checkpoint_root),
            "benchmark": str(args.benchmark),
            "tasks": task_names,
            "focus_tasks": args.focus_task,
        },
    )
    print(f"WANDB_OK mode={args.wandb_mode} dir={args.wandb_dir}", flush=True)
    if offline_run is not None:
        print(f"WANDB_SYNC_COMMAND=wandb sync {shlex.quote(str(offline_run))}", flush=True)


if __name__ == "__main__":
    main()
