"""Human-friendly formatting utilities."""

from __future__ import annotations

import time
from typing import Iterable, Sequence

# ---------------------------------------------------------------------------
# Size formatting
# ---------------------------------------------------------------------------
# unit_system -> (base, ordered units from smallest to largest)
_UNIT_SYSTEMS: dict[str, tuple[int, tuple[str, ...]]] = {
    "iec": (1024, ("B", "KiB", "MiB", "GiB", "TiB", "PiB")),
    "si": (1000, ("B", "KB", "MB", "GB", "TB", "PB")),
}


def format_size(size_bytes: int | float, *, unit_system: str = "iec") -> str:
    """Format a byte count as a human-readable string.

    ``unit_system`` selects between IEC (1024-based) and SI (1000-based) units.
    Returns ``"0 B"`` for zero, otherwise one decimal place is kept unless the
    value is integral (e.g. ``"2 MiB"``).
    """
    if unit_system not in _UNIT_SYSTEMS:
        raise ValueError(f"Unknown unit_system: {unit_system!r}")
    if size_bytes == 0:
        return "0 B"

    base, units = _UNIT_SYSTEMS[unit_system]
    value = float(size_bytes)
    unit = units[0]
    for unit in units:
        if abs(value) < base or unit is units[-1]:
            break
        value /= base

    # Drop trailing ``.0`` for integral results.
    rendered = f"{value:.0f}" if value == int(value) else f"{value:.1f}"
    return f"{rendered} {unit}"


# ---------------------------------------------------------------------------
# Relative time formatting
# ---------------------------------------------------------------------------
# Each chunk: (singular_label, seconds_per_unit, upper_bound_in_units).
# ``upper_bound`` is exclusive — once the count reaches it we promote to the
# next unit. The final entry uses ``None`` to mean "no upper bound".
_TIME_CHUNKS: tuple[tuple[str, int, int | None], ...] = (
    ("second", 1, 60),
    ("minute", 60, 60),
    ("hour", 3600, 24),
    ("day", 86400, 7),
    ("week", 604800, 4),
    ("month", 2629800, 12),  # 30.4375 days ~ average month
    ("year", 31557600, None),  # 365.25 days
)


def format_timesince(ts: float) -> str:
    """Format a UNIX timestamp as a relative ``"... ago"`` phrase."""
    delta = max(0, int(time.time() - ts))
    if delta < 20:
        return "a few seconds ago"

    for label, divisor, upper in _TIME_CHUNKS:
        count = delta // divisor
        if upper is None or count < upper:
            suffix = "" if count == 1 else "s"
            return f"{count} {label}{suffix} ago"
    # Unreachable: the final chunk has upper=None.
    return "a long time ago"  # pragma: no cover


# ---------------------------------------------------------------------------
# Table rendering
# ---------------------------------------------------------------------------
def _cell(value: object, max_width: int) -> str:
    """Stringify a cell, replacing ``None`` with ``-`` and truncating overlong text."""
    text = "-" if value is None else str(value)
    if len(text) > max_width:
        return text[: max_width - 1] + "…"
    return text


def tabulate(
    rows: Iterable[Sequence[object]],
    headers: Sequence[str],
    *,
    sep: str = "  ",
    max_width: int = 80,
) -> str:
    """Render ``rows`` as a left-aligned ASCII table.

    Columns auto-size to their widest cell; cells longer than ``max_width`` are
    truncated with an ellipsis. ``None`` values render as ``-``.

    Raises :class:`ValueError` if ``max_width`` is less than 1.
    """
    if max_width < 1:
        raise ValueError(f"max_width must be >= 1, got {max_width}")
    ncols = len(headers)
    str_rows: list[list[str]] = [
        [_cell(row[i] if i < len(row) else "", max_width) for i in range(ncols)]
        for row in rows
    ]

    widths = [len(h) for h in headers]
    for row in str_rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(cell))

    def _join(cells: Sequence[str]) -> str:
        return sep.join(cells[i].ljust(widths[i]) for i in range(ncols))

    lines = [
        _join(list(headers)),
        sep.join("-" * w for w in widths),
    ]
    lines.extend(_join(row) for row in str_rows)
    return "\n".join(lines)


__all__ = ["format_size", "format_timesince", "tabulate"]
