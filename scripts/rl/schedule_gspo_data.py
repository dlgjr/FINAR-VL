"""Build a stable, cost-balanced fine-grained order for distributed rollout."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .rollout_scheduler import cost_balanced_batches, estimate_cost


def schedule(input_path: str | Path, output_path: str | Path, *, workers: int = 28, batch_size: int = 7) -> dict:
    rows = [json.loads(line) for line in Path(input_path).read_text(encoding="utf-8").splitlines() if line.strip()]
    assigned = cost_balanced_batches(rows, workers=workers, batch_size=batch_size)
    loads = [sum(estimate_cost(row) for row in group) for group in assigned]
    ordered: list[dict] = []
    cursor = [0] * len(assigned)
    while True:
        progressed = False
        for worker, group in enumerate(assigned):
            start = cursor[worker]
            if start >= len(group):
                continue
            ordered.extend(group[start : start + batch_size])
            cursor[worker] += batch_size
            progressed = True
        if not progressed:
            break
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_path).write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in ordered), encoding="utf-8")
    report = {
        "records": len(rows),
        "workers": workers,
        "batch_size": batch_size,
        "planned_cost_by_worker": loads,
        "estimated_time_ratio": max(loads) / min(loads) if loads and min(loads) > 0 else 0.0,
        "stable_sample_ids": len({str(row.get("sample_id")) for row in rows}) == len(rows),
    }
    Path(str(output_path) + ".schedule.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input")
    parser.add_argument("output")
    parser.add_argument("--workers", type=int, default=28)
    parser.add_argument("--batch-size", type=int, default=7)
    args = parser.parse_args()
    report = schedule(args.input, args.output, workers=args.workers, batch_size=args.batch_size)
    print(json.dumps(report, ensure_ascii=False))
    if report["estimated_time_ratio"] > 1.2:
        raise SystemExit("estimated rollout cost ratio exceeds 1.2")


if __name__ == "__main__":
    main()

