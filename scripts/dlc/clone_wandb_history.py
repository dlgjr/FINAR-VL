"""Clone scalar W&B history through a logical GSPO step into a new run.

This is used when training branches from an older checkpoint with changed reward
logic. The new W&B run receives the source run's history up to the branch step,
then normal Trainer logging resumes that target run for subsequent steps.
"""

from __future__ import annotations

import argparse
import math
from typing import Any

import wandb


_CLONE_SOURCE_KEY = "gspo/history_clone_source_run_id"
_CLONE_UNTIL_KEY = "gspo/history_clone_until_step"
_CLONE_COMPLETE_KEY = "gspo/history_clone_complete"


def _logical_step(row: dict[str, Any]) -> int | None:
    for key in ("_gspo_step", "train/global_step", "global_step", "trainer/global_step"):
        value = row.get(key)
        if value is None:
            continue
        try:
            return int(value)
        except (TypeError, ValueError):
            continue
    return None


def _scalar_payload(row: dict[str, Any], logical_step: int) -> dict[str, Any]:
    payload: dict[str, Any] = {"_gspo_step": logical_step}
    for key, value in row.items():
        if key == "_gspo_step" or key.startswith("_"):
            continue
        if value is None:
            continue
        if isinstance(value, bool):
            payload[key] = value
        elif isinstance(value, (int, float)):
            if isinstance(value, float) and not math.isfinite(value):
                continue
            payload[key] = value
    return payload


def _get_existing_run(api: wandb.Api, path: str):
    try:
        return api.run(path)
    except wandb.errors.CommError:
        return None


def clone_history(
    *,
    entity: str,
    project: str,
    source_run_id: str,
    target_run_id: str,
    until_step: int,
    target_name: str,
) -> None:
    if source_run_id == target_run_id:
        raise ValueError("source and target W&B run IDs must differ")
    if until_step < 0:
        raise ValueError(f"until_step must be non-negative, got {until_step}")

    api = wandb.Api()
    source_path = f"{entity}/{project}/{source_run_id}"
    target_path = f"{entity}/{project}/{target_run_id}"

    source = api.run(source_path)
    existing = _get_existing_run(api, target_path)
    if existing is not None:
        configured_source = existing.config.get(_CLONE_SOURCE_KEY)
        configured_until = existing.config.get(_CLONE_UNTIL_KEY)
        clone_complete = bool(existing.config.get(_CLONE_COMPLETE_KEY, False))
        same_source = configured_source == source_run_id
        same_until = str(configured_until) == str(until_step)
        if same_source and same_until and clone_complete:
            print(
                f"[WANDB_HISTORY_CLONE] target={target_run_id} already_seeded=true "
                f"source={source_run_id} until_step={until_step}",
                flush=True,
            )
            return
        if same_source and same_until and not clone_complete:
            raise RuntimeError(
                f"target W&B run {target_path} contains an incomplete history clone; "
                "delete that target run or use a fresh WANDB_RUN_ID"
            )
        raise RuntimeError(
            f"target W&B run {target_path} already exists without the expected clone marker; "
            "use a fresh WANDB_RUN_ID"
        )

    run = wandb.init(
        entity=entity,
        project=project,
        id=target_run_id,
        name=target_name,
        resume="never",
        config={
            _CLONE_SOURCE_KEY: source_run_id,
            _CLONE_UNTIL_KEY: until_step,
            _CLONE_COMPLETE_KEY: False,
            "gspo/history_clone_source_name": source.name,
            "gspo/history_clone_mode": "prefix_then_branch",
        },
    )
    if run is None:
        raise RuntimeError("wandb.init returned no run")

    run.define_metric("_gspo_step", hidden=True, summary="none", overwrite=True)
    run.define_metric("train/*", step_metric="_gspo_step", step_sync=True, overwrite=True)
    run.define_metric("eval/*", step_metric="_gspo_step", step_sync=True, overwrite=True)

    copied_rows = 0
    skipped_without_step = 0
    max_copied_step = -1
    try:
        for raw_row in source.scan_history(page_size=1000):
            row = dict(raw_row)
            step = _logical_step(row)
            if step is None:
                skipped_without_step += 1
                continue
            if step > until_step:
                continue

            payload = _scalar_payload(row, step)
            if len(payload) == 1:
                continue
            run.log(payload)
            copied_rows += 1
            max_copied_step = max(max_copied_step, step)

        if copied_rows == 0:
            raise RuntimeError(
                f"no scalar history rows with a logical GSPO step <= {until_step} were found in {source_path}"
            )
        if max_copied_step < until_step:
            raise RuntimeError(
                f"source history only reached logical step {max_copied_step}, below requested branch step {until_step}"
            )

        run.summary["gspo/history_clone_rows"] = copied_rows
        run.summary["gspo/history_clone_max_step"] = max_copied_step
        run.summary["gspo/history_clone_skipped_without_step"] = skipped_without_step
        run.config.update({_CLONE_COMPLETE_KEY: True}, allow_val_change=True)
    finally:
        run.finish()

    print(
        f"[WANDB_HISTORY_CLONE] target={target_run_id} source={source_run_id} "
        f"until_step={until_step} copied_rows={copied_rows} max_copied_step={max_copied_step} "
        f"skipped_without_step={skipped_without_step}",
        flush=True,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--entity", required=True)
    parser.add_argument("--project", required=True)
    parser.add_argument("--source-run-id", required=True)
    parser.add_argument("--target-run-id", required=True)
    parser.add_argument("--until-step", required=True, type=int)
    parser.add_argument("--target-name", required=True)
    args = parser.parse_args()

    clone_history(
        entity=args.entity,
        project=args.project,
        source_run_id=args.source_run_id,
        target_run_id=args.target_run_id,
        until_step=args.until_step,
        target_name=args.target_name,
    )


if __name__ == "__main__":
    main()
