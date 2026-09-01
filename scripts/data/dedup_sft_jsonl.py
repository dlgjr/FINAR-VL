#!/usr/bin/env python3
"""Deduplicate SFT JSONL files with MinHash over message text."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Iterable


DEFAULT_THRESHOLD = 0.90
DEFAULT_NUM_PERM = 128
DEFAULT_NGRAM = 5
DEFAULT_MESSAGE_SCOPE = "all"
DEFAULT_BANDS = 16
MASK64 = (1 << 64) - 1


def _content_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict):
                parts.append(str(item.get("text") or item.get("content") or ""))
            else:
                parts.append(str(item))
        return "\n".join(parts)
    return str(content or "")


def message_text(record: dict[str, Any], *, message_scope: str = DEFAULT_MESSAGE_SCOPE) -> str:
    parts = []
    for message in record.get("messages") or []:
        if not isinstance(message, dict):
            continue
        role = str(message.get("role") or "")
        if message_scope != "all" and role != message_scope:
            continue
        parts.append(f"{role}: {_content_text(message.get('content'))}")
    return "\n".join(parts)


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


def _rolling_shingles(text: str, ngram: int) -> set[int]:
    if not text:
        return {0}
    if len(text) <= ngram:
        return {_mix64(sum((index + 1) * ord(char) for index, char in enumerate(text)))}

    base = 257
    base_power = pow(base, ngram - 1, 1 << 64)
    value = 0
    shingles: set[int] = set()
    for index, char in enumerate(text):
        value = ((value * base) + ord(char)) & MASK64
        if index >= ngram:
            value = (value - (ord(text[index - ngram]) * base_power * base)) & MASK64
        if index >= ngram - 1:
            shingles.add(_mix64(value))
    return shingles or {0}


def _mix64(value: int) -> int:
    value &= MASK64
    value ^= value >> 30
    value = (value * 0xBF58476D1CE4E5B9) & MASK64
    value ^= value >> 27
    value = (value * 0x94D049BB133111EB) & MASK64
    value ^= value >> 31
    return value & MASK64


def _perm_seeds(num_perm: int) -> list[int]:
    return [_mix64(0x9E3779B97F4A7C15 * (index + 1)) for index in range(num_perm)]


def minhash_signature(text: str, *, num_perm: int, ngram: int) -> tuple[int, ...]:
    shingles = _rolling_shingles(text, ngram)
    seeds = _perm_seeds(num_perm)
    signature = [MASK64] * num_perm
    for shingle in shingles:
        for index, seed in enumerate(seeds):
            value = _mix64(shingle ^ seed)
            if value < signature[index]:
                signature[index] = value
    return tuple(signature)


def signature_similarity(left: tuple[int, ...], right: tuple[int, ...]) -> float:
    if len(left) != len(right):
        raise ValueError("signature lengths differ")
    return sum(1 for a, b in zip(left, right) if a == b) / len(left)


def _band_keys(signature: tuple[int, ...], *, bands: int) -> Iterable[tuple[int, tuple[int, ...]]]:
    band_size = len(signature) // bands
    for band_index in range(bands):
        start = band_index * band_size
        yield band_index, signature[start : start + band_size]


def dedup_jsonl(
    input_path: Path,
    output_path: Path,
    *,
    threshold: float = DEFAULT_THRESHOLD,
    num_perm: int = DEFAULT_NUM_PERM,
    ngram: int = DEFAULT_NGRAM,
    message_scope: str = DEFAULT_MESSAGE_SCOPE,
    bands: int = DEFAULT_BANDS,
) -> dict[str, Any]:
    if not input_path.is_file():
        raise FileNotFoundError(f"missing input file: {input_path}")
    if not 0 < threshold <= 1:
        raise ValueError("threshold must be in (0, 1]")
    if num_perm <= 0 or num_perm % bands != 0:
        raise ValueError("num_perm must be positive and divisible by bands")
    if ngram <= 0:
        raise ValueError("ngram must be positive")
    if message_scope not in {"all", "user", "assistant"}:
        raise ValueError("message_scope must be one of: all, user, assistant")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    exact_seen: set[str] = set()
    signatures: list[tuple[int, ...]] = []
    buckets: dict[tuple[int, tuple[int, ...]], list[int]] = {}
    report: dict[str, Any] = {
        "input": str(input_path),
        "output": str(output_path),
        "read": 0,
        "written": 0,
        "duplicates_removed": 0,
        "threshold": threshold,
        "num_perm": num_perm,
        "ngram": ngram,
        "message_scope": message_scope,
        "ignored_images": True,
    }

    with input_path.open("r", encoding="utf-8-sig") as source, output_path.open(
        "w", encoding="utf-8", newline="\n"
    ) as output:
        for line_number, line in enumerate(source, start=1):
            raw = line.strip()
            if not raw:
                continue
            try:
                record = json.loads(raw)
            except json.JSONDecodeError as exc:
                raise ValueError(f"invalid JSON in {input_path}:{line_number}: {exc}") from exc
            report["read"] += 1
            text = normalize_text(message_text(record, message_scope=message_scope))
            if text in exact_seen:
                report["duplicates_removed"] += 1
                continue
            signature = minhash_signature(text, num_perm=num_perm, ngram=ngram)
            candidate_indexes: set[int] = set()
            for band_key in _band_keys(signature, bands=bands):
                candidate_indexes.update(buckets.get(band_key, []))
            duplicate = any(
                signature_similarity(signature, signatures[index]) >= threshold
                for index in candidate_indexes
            )
            if duplicate:
                report["duplicates_removed"] += 1
                continue
            exact_seen.add(text)
            signatures.append(signature)
            signature_index = len(signatures) - 1
            for band_key in _band_keys(signature, bands=bands):
                buckets.setdefault(band_key, []).append(signature_index)
            output.write(raw + "\n")
            report["written"] += 1
    return report


def dedup_default_outputs(
    project_root: Path,
    *,
    threshold: float = DEFAULT_THRESHOLD,
    num_perm: int = DEFAULT_NUM_PERM,
    ngram: int = DEFAULT_NGRAM,
    message_scope: str = DEFAULT_MESSAGE_SCOPE,
) -> dict[str, Any]:
    data_root = project_root / "data"
    return {
        "train_text_sft": dedup_jsonl(
            data_root / "train_text" / "train_text_sft.jsonl",
            data_root / "train_text" / "train_text_sft_minhash_dedup.jsonl",
            threshold=threshold,
            num_perm=num_perm,
            ngram=ngram,
            message_scope=message_scope,
        ),
        "train_multi_sft": dedup_jsonl(
            data_root / "train_multi" / "train_multi_sft.jsonl",
            data_root / "train_multi" / "train_multi_sft_minhash_dedup.jsonl",
            threshold=threshold,
            num_perm=num_perm,
            ngram=ngram,
            message_scope=message_scope,
        ),
    }


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--input", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD)
    parser.add_argument("--num-perm", type=int, default=DEFAULT_NUM_PERM)
    parser.add_argument("--ngram", type=int, default=DEFAULT_NGRAM)
    parser.add_argument(
        "--message-scope",
        choices=("all", "user", "assistant"),
        default=DEFAULT_MESSAGE_SCOPE,
    )
    args = parser.parse_args(argv)
    if bool(args.input) != bool(args.output):
        parser.error("--input and --output must be provided together")
    if args.input and args.output:
        reports = {
            "single": dedup_jsonl(
                args.input.resolve(),
                args.output.resolve(),
                threshold=args.threshold,
                num_perm=args.num_perm,
                ngram=args.ngram,
                message_scope=args.message_scope,
            )
        }
    else:
        reports = dedup_default_outputs(
            args.project_root.resolve(),
            threshold=args.threshold,
            num_perm=args.num_perm,
            ngram=args.ngram,
            message_scope=args.message_scope,
        )
    print(json.dumps(reports, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
