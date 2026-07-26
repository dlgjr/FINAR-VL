"""Glob pattern normalization and analysis utilities."""

from __future__ import annotations

from collections.abc import Iterable

# Characters that introduce a glob wildcard segment.
_WILDCARD_CHARS: frozenset[str] = frozenset("*?[")
# Separator used to expand inline pattern lists.
_PATTERN_SEPARATOR: str = ","
# Path separator used for prefix segmentation.
_PATH_SEPARATOR: str = "/"


def _split_inline(value: str) -> list[str]:
    """Split a single string by separator and strip whitespace, dropping empties."""
    return [part.strip() for part in value.split(_PATTERN_SEPARATOR) if part.strip()]


def _flatten(items: Iterable[str]) -> list[str]:
    """Expand each item via inline split and collect non-empty patterns."""
    result: list[str] = []
    for item in items:
        if not isinstance(item, str):
            continue
        result.extend(_split_inline(item))
    return result


def normalize_patterns(
    raw_input: str | Iterable[str] | None,
) -> list[str] | None:
    """Normalize glob pattern input into a clean list or None.

    Accepts None, a single string (optionally comma-separated), or any iterable
    of strings (list, tuple, etc.) whose elements may also be comma-separated.
    Returns None when the input yields no usable patterns.
    """
    if raw_input is None:
        return None
    if isinstance(raw_input, str):
        patterns = _split_inline(raw_input)
    elif isinstance(raw_input, Iterable):
        patterns = _flatten(raw_input)
    else:
        return None
    return patterns or None


def _pattern_dir_prefix(pattern: str) -> str | None:
    """Return the directory portion preceding the first wildcard, or None."""
    wildcard_index = next(
        (i for i, ch in enumerate(pattern) if ch in _WILDCARD_CHARS),
        -1,
    )
    literal = pattern if wildcard_index == -1 else pattern[:wildcard_index]
    sep_index = literal.rfind(_PATH_SEPARATOR)
    if sep_index < 0:
        return None
    prefix = literal[:sep_index]
    return prefix or None


def _common_segments(prefixes: list[str]) -> str | None:
    """Compute the longest common path-segment prefix across all inputs."""
    segment_lists = [p.split(_PATH_SEPARATOR) for p in prefixes]
    common: list[str] = []
    for segments in zip(*segment_lists):
        first = segments[0]
        if any(seg != first for seg in segments[1:]):
            break
        common.append(first)
    if not common:
        return None
    joined = _PATH_SEPARATOR.join(common)
    return joined or None


def extract_common_prefix(patterns: list[str] | None) -> str | None:
    """Extract the longest common directory prefix shared by all patterns.

    Returns None if the input is empty, any pattern lacks a directory prefix,
    or the prefixes do not share a common leading segment.
    """
    if not patterns:
        return None
    prefixes: list[str] = []
    for pattern in patterns:
        prefix = _pattern_dir_prefix(pattern)
        if prefix is None:
            return None
        prefixes.append(prefix)
    return _common_segments(prefixes)


__all__ = ["normalize_patterns", "extract_common_prefix"]
