"""Timestamp parsing and timezone conversion utilities."""

from __future__ import annotations

import re
import zoneinfo
from datetime import datetime, timezone
from typing import Union

# Accepted ISO-like formats for naive (local) timestamps.
_NAIVE_FORMATS: tuple[str, ...] = (
    "%Y-%m-%dT%H:%M:%S.%f",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%d %H:%M:%S.%f",
    "%Y-%m-%d %H:%M:%S",
)

# Pattern to truncate sub-second precision beyond microseconds (e.g. nanoseconds).
_SUBSECOND_RE = re.compile(r"(\.\d{6})\d+")


def _truncate_subseconds(value: str) -> str:
    """Truncate fractional seconds to microsecond precision."""
    return _SUBSECOND_RE.sub(r"\1", value)


def _parse_utc_string(value: str, target_tz: zoneinfo.ZoneInfo) -> datetime:
    """Parse a trailing-Z UTC string and convert to the target timezone."""
    # Replace trailing Z with +00:00 so fromisoformat can handle it.
    iso = value[:-1] + "+00:00"
    iso = _truncate_subseconds(iso)
    try:
        dt = datetime.fromisoformat(iso)
    except ValueError as exc:
        raise ValueError(f"Invalid UTC timestamp string: {value!r}") from exc
    return dt.astimezone(target_tz)


def _parse_naive_string(value: str, target_tz: zoneinfo.ZoneInfo) -> datetime:
    """Parse a naive timestamp string and attach the target timezone."""
    candidate = _truncate_subseconds(value)
    for fmt in _NAIVE_FORMATS:
        try:
            dt = datetime.strptime(candidate, fmt)
        except ValueError:
            continue
        return dt.replace(tzinfo=target_tz)
    # Fallback to fromisoformat for other ISO 8601 variants (e.g. with offset).
    try:
        dt = datetime.fromisoformat(candidate)
    except ValueError as exc:
        raise ValueError(f"Unrecognized timestamp string: {value!r}") from exc
    if dt.tzinfo is None:
        return dt.replace(tzinfo=target_tz)
    return dt.astimezone(target_tz)


def parse_timestamp(
    value: Union[int, str, datetime, None],
    *,
    tz: str = "Asia/Shanghai",
) -> datetime | None:
    """Normalize heterogeneous timestamp inputs to a timezone-aware datetime.

    Args:
        value: A UNIX timestamp (int), an ISO-like string, a datetime, or None.
        tz: IANA timezone name used as the conversion target and the default
            timezone for naive inputs.

    Returns:
        A timezone-aware datetime, or None when value is None.
    """
    if value is None:
        return None

    target_tz = zoneinfo.ZoneInfo(tz)

    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=target_tz)
        return value.astimezone(target_tz)

    # bool is a subclass of int; reject it explicitly to avoid silent coercion.
    if isinstance(value, bool):
        raise TypeError(f"Unsupported timestamp type: {type(value).__name__}")

    if isinstance(value, (int, float)):
        ts = value / 1000 if value > 9_999_999_999 else value
        try:
            dt = datetime.fromtimestamp(ts, tz=timezone.utc)
        except (OverflowError, OSError, ValueError) as exc:
            raise ValueError(f"Invalid UNIX timestamp: {value!r}") from exc
        return dt.astimezone(target_tz)

    if isinstance(value, str):
        text = value.strip()
        if not text:
            raise ValueError("Empty timestamp string")
        if text.endswith("Z"):
            return _parse_utc_string(text, target_tz)
        return _parse_naive_string(text, target_tz)

    raise TypeError(f"Unsupported timestamp type: {type(value).__name__}")


__all__ = ["parse_timestamp"]
