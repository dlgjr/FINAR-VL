"""Reward-pool sampling and completion anomaly metrics."""

from __future__ import annotations

import random
from collections import Counter, defaultdict
from typing import Any, Iterable, Mapping

from .gspo_reward import extract_prefixed_answer


DEFAULT_AUDIT_COUNT = 32


def analyze_completion(completion: Any, *, max_completion_length: int = 2048) -> dict[str, Any]:
    text = str(completion or "")
    answer = extract_prefixed_answer(text)
    tokens = text.split()
    repeated = bool(tokens) and (max(Counter(tokens).values()) / len(tokens) > 0.5)
    return {
        "answer_prefix_missing": answer is None,
        "answer_prefix_empty": answer == "",
        "parse_failed": answer is None or not answer.strip(),
        "control_char_count": sum(ord(char) < 32 and char not in "\n\t\r" for char in text),
        "replacement_char_count": text.count("\ufffd"),
        "abnormal_repetition": repeated,
        "truncated": len(text) >= max_completion_length,
        "completion_length": len(text),
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
