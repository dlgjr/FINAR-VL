"""Reward-pool sampling and completion anomaly metrics."""

from __future__ import annotations

import random
import re
from collections import Counter, defaultdict
from typing import Any, Iterable, Mapping

from .gspo_reward import extract_prefixed_answer


DEFAULT_AUDIT_COUNT = 32
_LEXEME_RE = re.compile(r"[A-Za-z0-9]+(?:[._%+\-][A-Za-z0-9]+)*|[\u3400-\u9fff]")


def _completion_text(completion: Any) -> tuple[str, str | None, int | None]:
    if isinstance(completion, Mapping):
        text = str(completion.get("content", completion.get("text", "")) or "")
        finish_reason = completion.get("finish_reason")
        token_count = completion.get("completion_tokens")
        if token_count is None and isinstance(completion.get("usage"), Mapping):
            token_count = completion["usage"].get("completion_tokens")
        try:
            token_count = int(token_count) if token_count is not None else None
        except (TypeError, ValueError):
            token_count = None
        return text, str(finish_reason) if finish_reason is not None else None, token_count
    return str(completion or ""), None, None


def _lexemes(text: str) -> list[str]:
    return _LEXEME_RE.findall(text.casefold())


def _abnormal_repetition(tokens: list[str]) -> bool:
    if len(tokens) < 8:
        return False
    if max(Counter(tokens).values()) / len(tokens) > 0.6:
        return True
    for width in (2, 3, 4):
        if len(tokens) < width * 3:
            continue
        grams = [tuple(tokens[index : index + width]) for index in range(len(tokens) - width + 1)]
        most_common = max(Counter(grams).values())
        if most_common >= 3 and (most_common * width) / len(tokens) > 0.6:
            return True
    return False


def _estimated_tokens(text: str) -> int:
    cjk = len(re.findall(r"[\u3400-\u9fff]", text))
    ascii_chunks = re.findall(r"[^\u3400-\u9fff\s]+", text)
    ascii_estimate = sum(max(1, (len(chunk) + 3) // 4) for chunk in ascii_chunks)
    return cjk + ascii_estimate


def analyze_completion(completion: Any, *, max_completion_length: int = 2048) -> dict[str, Any]:
    text, finish_reason, token_count = _completion_text(completion)
    answer = extract_prefixed_answer(text)
    tokens = _lexemes(text)
    estimated = token_count if token_count is not None else _estimated_tokens(text)
    truncated = finish_reason == "length" or (max_completion_length > 0 and estimated >= max_completion_length)
    return {
        "answer_prefix_missing": answer is None,
        "answer_prefix_empty": answer == "",
        "parse_failed": answer is None or not answer.strip(),
        "control_char_count": sum(ord(char) < 32 and char not in "\n\t\r" for char in text),
        "replacement_char_count": text.count("\ufffd"),
        "abnormal_repetition": _abnormal_repetition(tokens),
        "truncated": truncated,
        "finish_reason": finish_reason,
        "completion_length": len(text),
        "estimated_token_count": estimated,
        "answer_length": len(answer or ""),
        "token_diversity": len(set(tokens)) / len(tokens) if tokens else 0.0,
    }


def _stratum(record: Mapping[str, Any]) -> tuple[str, str]:
    return str(record.get("verifier_type") or "unknown"), str(record.get("source") or "unknown")


def select_high_reward_samples(records: Iterable[Mapping[str, Any]], *, seed: int, count: int = DEFAULT_AUDIT_COUNT) -> list[dict[str, Any]]:
    """Select distinct high-reward samples stratified by verifier type and source."""

    by_id: dict[str, dict[str, Any]] = {}
    for record in records:
        sample_id = str(record.get("sample_id", ""))
        if not sample_id:
            continue
        candidate = dict(record)
        if sample_id not in by_id or float(candidate.get("reward", 0.0)) > float(by_id[sample_id].get("reward", 0.0)):
            by_id[sample_id] = candidate
    if not by_id:
        return []
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for item in by_id.values():
        grouped[_stratum(item)].append(item)
    rng = random.Random(seed)
    queues: list[tuple[tuple[str, str], list[dict[str, Any]]]] = []
    for key in sorted(grouped):
        rows = grouped[key]
        rng.shuffle(rows)
        rows.sort(key=lambda item: -float(item.get("reward", 0.0)))
        queues.append((key, rows))
    chosen: list[dict[str, Any]] = []
    while len(chosen) < count:
        progressed = False
        for key, rows in queues:
            if len(chosen) >= count:
                break
            if not rows:
                continue
            item = rows.pop(0)
            item["_audit_stratum"] = {"verifier_type": key[0], "source": key[1]}
            chosen.append(item)
            progressed = True
        if not progressed:
            break
    return chosen


def build_audit_records(
    records: Iterable[Mapping[str, Any]],
    *,
    seed: int,
    count: int = DEFAULT_AUDIT_COUNT,
    max_completion_length: int = 2048,
) -> list[dict[str, Any]]:
    output = []
    for record in select_high_reward_samples(records, seed=seed, count=count):
        item = dict(record)
        item["answer"] = extract_prefixed_answer(item.get("completion", ""))
        item["anomalies"] = analyze_completion(item.get("completion", ""), max_completion_length=max_completion_length)
        output.append(item)
    return output
