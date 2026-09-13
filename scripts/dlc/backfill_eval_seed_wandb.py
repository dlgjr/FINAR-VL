#!/usr/bin/env python3
"""Clone available W&B history, then backfill fixed-eval metrics from local summaries."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import wandb

ROOT = Path("/mnt/nas/duolg/qwen3vl")
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.dlc.clone_wandb_history import clone_history  # noqa: E402

STEP_RE = re.compile(r"step-(\d+)$")


def _logical_step(row: dict) -> int | None:
    for key in ("_gspo_step", "train/global_step", "global_step", "trainer/global_step"):
        value = row.get(key)
        if value is None:
            continue
        try:
            return int(value)
        except (TypeError, ValueError):
            continue
    return None


def _source_max_step(entity: str, project: str, run_id: str) -> int:
    source = wandb.Api().run(f"{entity}/{project}/{run_id}")
    max_step = -1
    for raw_row in source.scan_history(page_size=1000):
        step = _logical_step(dict(raw_row))
        if step is not None:
            max_step = max(max_step, step)
    return max_step


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--entity", required=True)
    parser.add_argument("--project", required=True)
    parser.add_argument("--source-run-id", required=True)
    parser.add_argument("--target-run-id", required=True)
    parser.add_argument("--target-name", required=True)
    parser.add_argument("--until-step", required=True, type=int)
    args = parser.parse_args()

    checkpoint = Path(args.checkpoint)
    eval_root = checkpoint.parent / "eval"
    if not eval_root.is_dir():
        raise FileNotFoundError(eval_root)

    source_max_step = _source_max_step(args.entity, args.project, args.source_run_id)
    if source_max_step < 0:
        raise RuntimeError("source W&B run has no logical GSPO step")
    clone_until = min(args.until_step, source_max_step)
    if clone_until < args.until_step:
        print(
            f"[BACKFILL] source W&B history ends at {source_max_step}; "
            f"clone scalar history through {clone_until}, then use local eval summaries through {args.until_step}",
            flush=True,
        )

    clone_history(
        entity=args.entity,
        project=args.project,
        source_run_id=args.source_run_id,
        target_run_id=args.target_run_id,
        until_step=clone_until,
        target_name=args.target_name,
    )

    rows: list[tuple[int, dict]] = []
    for summary_path in sorted(eval_root.glob("step-*/summary.json")):
        match = STEP_RE.fullmatch(summary_path.parent.name)
        if match is None:
            continue
        step = int(match.group(1))
        if step > args.until_step:
            continue
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        per_seed = summary.get("per_seed")
        if isinstance(per_seed, list) and per_seed:
            rows.append((step, summary))

    if not rows:
        raise RuntimeError(
            f"no per-seed eval summaries found under {eval_root} through step {args.until_step}"
        )

    run = wandb.init(
        entity=args.entity,
        project=args.project,
        id=args.target_run_id,
        name=args.target_name,
        resume="must",
    )
    if run is None:
        raise RuntimeError("wandb.init returned no run")

    run.define_metric("_gspo_step", hidden=True, summary="none", overwrite=True)
    run.define_metric("eval/pass_at_1", step_metric="_gspo_step", step_sync=True, overwrite=True)
    run.define_metric("eval/pass_at_8", step_metric="_gspo_step", step_sync=True, overwrite=True)
    logged = 0
    seeds_seen: set[int] = set()
    try:
        for step, summary in sorted(rows):
            payload = {
                "_gspo_step": step,
                "eval/pass_at_1": float(summary.get("pass_at_1", 0.0)),
                "eval/pass_at_8": float(summary.get("pass_at_8", 0.0)),
            }
            for row in summary["per_seed"]:
                seed = int(row["seed"])
                seeds_seen.add(seed)
                pass1_key = f"eval/seed_{seed}/pass_at_1"
                pass8_key = f"eval/seed_{seed}/pass_at_8"
                run.define_metric(pass1_key, step_metric="_gspo_step", step_sync=True, overwrite=True)
                run.define_metric(pass8_key, step_metric="_gspo_step", step_sync=True, overwrite=True)
                payload[pass1_key] = float(row["pass_at_1"])
                payload[pass8_key] = float(row["pass_at_8"])
            run.log(payload)
            logged += 1
    finally:
        run.finish()

    print(
        f"[BACKFILL_DONE] target_run={args.target_run_id} source_max_step={source_max_step} "
        f"eval_points={logged} seeds={sorted(seeds_seen)} "
        f"max_eval_step={max(step for step, _ in rows)}"
    )


if __name__ == "__main__":
    main()
