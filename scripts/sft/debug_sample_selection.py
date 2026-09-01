"""DSW 调试用代表样本筛选。"""

from __future__ import annotations

from typing import Any, Callable, Iterable


REPRESENTATIVE_COUNTS = {"short": 4, "medium": 2, "long": 2}


def _bucket_name(length: int) -> str:
    if length <= 8192:
        return "short"
    if length <= 32768:
        return "medium"
    if length <= 81920:
        return "long"
    return "skipped"


def select_representative_rows(
    rows: Iterable[dict[str, Any]],
    *,
    length_fn: Callable[[dict[str, Any]], int],
) -> list[dict[str, Any]]:
    selected: dict[str, list[dict[str, Any]]] = {name: [] for name in REPRESENTATIVE_COUNTS}
    for row in rows:
        bucket = _bucket_name(length_fn(row))
        if bucket in selected and len(selected[bucket]) < REPRESENTATIVE_COUNTS[bucket]:
            selected[bucket].append(row)
        if all(len(selected[name]) == count for name, count in REPRESENTATIVE_COUNTS.items()):
            break
    missing = {
        name: count - len(selected[name])
        for name, count in REPRESENTATIVE_COUNTS.items()
        if len(selected[name]) < count
    }
    if missing:
        raise ValueError(f"missing representative samples: {missing}")
    return [row for name in REPRESENTATIVE_COUNTS for row in selected[name]]
