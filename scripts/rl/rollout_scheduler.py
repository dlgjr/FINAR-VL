"""Cost-aware fine-grained rollout scheduling helpers."""

from __future__ import annotations

import heapq
from typing import Any, Iterable, Mapping


def estimate_cost(record: Mapping[str, Any]) -> float:
    if record.get("estimated_cost") is not None:
        return float(record["estimated_cost"])
    question = str(record.get("question", ""))
    images = record.get("images") or []
    return float(max(1, len(question) // 4) + len(images) * 256 + (2048 if record.get("verifier_type") == "model_judge" else 512))


def cost_balanced_batches(records: Iterable[Mapping[str, Any]], workers: int, batch_size: int = 7) -> list[list[dict[str, Any]]]:
    """Create many small batches and greedily balance their estimated cost."""

    if workers < 1 or batch_size < 1:
        raise ValueError("workers and batch_size must be positive")
    rows = sorted((dict(row) for row in records), key=lambda row: (-estimate_cost(row), str(row.get("sample_id", ""))))
    batches = [rows[index : index + batch_size] for index in range(0, len(rows), batch_size)]
    loads: list[tuple[float, int]] = [(0.0, index) for index in range(workers)]
    heapq.heapify(loads)
    assigned: list[list[dict[str, Any]]] = [[] for _ in range(workers)]
    for batch in batches:
        load, worker = heapq.heappop(loads)
        assigned[worker].extend(batch)
        heapq.heappush(loads, (load + sum(estimate_cost(row) for row in batch), worker))
    return assigned

