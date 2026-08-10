"""Reward-pool sampling and completion anomaly metrics."""

from __future__ import annotations

import random
import re
from collections import Counter
from typing import Any, Iterable, Mapping

from .gspo_reward import extract_prefixed_answer


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


def select_high_reward_samples(records: Iterable[Mapping[str, Any]], *, seed: int, count: int = 4) -> list[dict[str, Any]]:
    """Select distinct sample IDs from the max-reward pool, then descending fill."""

    by_id: dict[str, dict[str, Any]] = {}
    for record in records:
        sample_id = str(record.get("sample_id", ""))
        if not sample_id:
            continue
        candidate = dict(record)
        if sample_id not in by_id or float(candidate.get("reward", 0.0)) > float(by_id[sample_id].get("reward", 0.0)):
            by_id[sample_id] = candidate
    ranked = sorted(by_id.values(), key=lambda item: (-float(item.get("reward", 0.0)), str(item["sample_id"])))
    if not ranked:
        return []
    max_reward = float(ranked[0].get("reward", 0.0))
    top = [item for item in ranked if float(item.get("reward", 0.0)) == max_reward]
    rng = random.Random(seed)
    rng.shuffle(top)
    chosen = top[:count]
    if len(chosen) < count:
        chosen.extend(item for item in ranked if item["sample_id"] not in {row["sample_id"] for row in chosen})
    return chosen[:count]


def build_audit_records(records: Iterable[Mapping[str, Any]], *, seed: int, count: int = 4, max_completion_length: int = 2048) -> list[dict[str, Any]]:
    output = []
    for record in select_high_reward_samples(records, seed=seed, count=count):
        item = dict(record)
        item["answer"] = extract_prefixed_answer(item.get("completion", ""))
        item["anomalies"] = analyze_completion(item.get("completion", ""), max_completion_length=max_completion_length)
        output.append(item)
    return output
