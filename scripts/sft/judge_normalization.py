"""Deterministic normalization for format-sensitive SFT benchmark judges."""

from __future__ import annotations

import ast
import json
import re
import unicodedata
from decimal import Decimal, InvalidOperation
from typing import Any


_NUMBER_TOKEN_RE = re.compile(
    r"(?<![\d.])[-+]?(?:\d{1,3}(?:[,，]\d{3})+|\d+)(?:\.\d+)?(?![\d.])"
)
_FENCE_RE = re.compile(r"^\s*```(?:json|python)?\s*(.*?)\s*```\s*$", re.IGNORECASE | re.DOTALL)
_ANSWER_PREFIX_RE = re.compile(
    r"^\s*(?:答案|答|结果|数值|answer|result)\s*(?:是|为|=|[:：])?\s*",
    re.IGNORECASE,
)


def _surface(value: Any) -> str:
    text = unicodedata.normalize("NFKC", str(value)).strip()
    fence = _FENCE_RE.fullmatch(text)
    if fence is not None:
        text = fence.group(1).strip()
    return _ANSWER_PREFIX_RE.sub("", text).strip()


def _decimal_token(token: str) -> Decimal | None:
    try:
        return Decimal(token.replace(",", "").replace("，", ""))
    except InvalidOperation:
        return None


def _unit_signature(value: str) -> str:
    """Canonicalize the non-numeric OCR context without inventing missing units."""
    text = unicodedata.normalize("NFKC", value).casefold()
    text = _ANSWER_PREFIX_RE.sub("", text)

    # Longest/specific financial-unit aliases first.
    replacements = (
        (r"人民币|\brmb\b|\bcny\b", "cny"),
        (r"美元|\busd\b|us\$", "usd"),
        (r"欧元|\beur\b", "eur"),
        (r"英镑|\bgbp\b", "gbp"),
        (r"日元|\bjpy\b", "jpy"),
        (r"亿元", "亿cny"),
        (r"万元", "万cny"),
        (r"千元", "千cny"),
        (r"￥|¥", "cny"),
        (r"€", "eur"),
        (r"£", "gbp"),
        (r"\$", "usd"),
        (r"元", "cny"),
        (r"每桶", "/桶"),
        (r"百分之|百分比", "%"),
        (r"百分点", "pctpoint"),
    )
    for pattern, replacement in replacements:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

    # Only formatting punctuation is discarded; slash, percent and Chinese/Latin
    # unit text remain part of the signature.
    text = re.sub(r"[\s,，。.;；:：()（）\[\]{}<>《》]+", "", text)
    text = text.strip("=+-")
    return text


def _single_numeric_ocr(value: str) -> tuple[Decimal, str] | None:
    text = _surface(value)
    matches = list(_NUMBER_TOKEN_RE.finditer(text))
    if len(matches) != 1:
        return None
    match = matches[0]
    number = _decimal_token(match.group(0))
    if number is None:
        return None
    context = text[: match.start()] + text[match.end() :]
    return number, _unit_signature(context)


def _normalize_ocr_text(value: str) -> str:
    text = _surface(value).casefold()
    text = re.sub(r"\s+", "", text)
    return text.strip(" \t\r\n.,;:!?，。；：！？()[]{}<>")


def judge_ocr_answer(reference: Any, candidate: Any) -> bool:
    """Judge OCR deterministically while treating omitted implicit units as format noise.

    Numeric OCR is exact after thousands-separator/decimal normalization. If both
    answers explicitly state a unit/currency, those normalized unit signatures
    must also agree. A candidate may omit a unit that is already implicit in the
    question/reference, but an explicitly conflicting unit is never accepted.
    """
    expected_text = _surface(reference)
    actual_text = _surface(candidate)
    expected_numeric = _single_numeric_ocr(expected_text)
    actual_numeric = _single_numeric_ocr(actual_text)

    if expected_numeric is not None:
        if actual_numeric is None:
            return False
        expected_number, expected_unit = expected_numeric
        actual_number, actual_unit = actual_numeric
        if actual_number != expected_number:
            return False
        if expected_unit and actual_unit and expected_unit != actual_unit:
            return False
        return True

    return _normalize_ocr_text(expected_text) == _normalize_ocr_text(actual_text)


def _parse_structure(value: Any) -> Any | None:
    if isinstance(value, (dict, list, tuple)):
        return value
    text = _surface(value)
    if not text.startswith(("{", "[", "(")):
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    try:
        parsed = ast.literal_eval(text)
    except (SyntaxError, ValueError):
        return None
    return parsed if isinstance(parsed, (dict, list, tuple)) else None


def _canonical_scalar(value: Any) -> tuple[str, str]:
    if value is None:
        return ("none", "")
    if isinstance(value, bool):
        return ("bool", "1" if value else "0")
    if isinstance(value, (int, float, Decimal)) and not isinstance(value, bool):
        try:
            number = Decimal(str(value)).normalize()
            return ("number", format(number, "f"))
        except InvalidOperation:
            pass
    text = unicodedata.normalize("NFKC", str(value)).casefold()
    text = re.sub(r"\s+", " ", text).strip()
    return ("text", text)


def _canonical_structure(value: Any) -> Any:
    if isinstance(value, dict):
        return (
            "dict",
            tuple(
                sorted(
                    (
                        _canonical_scalar(key),
                        _canonical_structure(item),
                    )
                    for key, item in value.items()
                )
            ),
        )
    if isinstance(value, (list, tuple)):
        items = [_canonical_structure(item) for item in value]
        # Entity/relation extraction answers are sets/multisets. Sorting keeps
        # duplicate counts but removes irrelevant generation order.
        return ("list", tuple(sorted(items, key=repr)))
    return _canonical_scalar(value)


def judge_structured_extraction(reference: Any, candidate: Any) -> bool | None:
    """Order-insensitive exact-set judge for entity/relation structured output.

    Returns None when the reference is not structured so the caller can use its
    existing fallback. Missing items, extra items, wrong types or wrong relation
    directions still fail because canonical structures must be exactly equal.
    """
    expected = _parse_structure(reference)
    if expected is None:
        return None
    actual = _parse_structure(candidate)
    if actual is None:
        return False
    return _canonical_structure(actual) == _canonical_structure(expected)
