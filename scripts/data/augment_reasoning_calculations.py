"""Build reasoning RL data with fewer retrieval rows and more calculation rows."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


NUMERIC_ANSWER_RE = re.compile(
    r"\s*[-+]?\d[\d,]*(?:\.\d+)?(?:[eE][-+]?\d+)?\s*(?:%|[a-zA-Z/]+)?\s*"
)
CALCULATION_RE = re.compile(
    r"calculate|compute|calculation|"
    r"what (?:is|was|would be) (?:the )?(?:average|total|sum|difference|change|percentage|percent|ratio|margin|rate|yield|return|index|earnings per share)|"
    r"how much (?:did|does|would)|how many times|compound annual growth|cagr|standard deviation|variance|weighted average|"
    r"percent(?:age)? (?:change|difference|increase|decrease)|increase by|decrease by|"
    r"if .* (?:increase|decrease|goes up|goes down)|"
    r"计算|求出|算出|平均|合计|总和|差额|相差|占比|比例|增幅|增速|同比|环比|复合增长|标准差|方差|周转率|利润率|收益率",
    re.IGNORECASE,
)
STRONG_CALCULATION_RE = re.compile(
    r"calculate|compute|calculation|cagr|standard deviation|variance|weighted average|"
    r"percent(?:age)? (?:change|difference|increase|decrease)|"
    r"计算|求出|算出|复合增长|标准差|方差|同比|环比",
    re.IGNORECASE,
)
SOURCE_PRIORITY = {
    "finmmr": 4,
    "famma": 3,
    "finchart_bench": 2,
    "finmme": 1,
    "visfineval": 1,
}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def message_text(row: dict[str, Any], role: str) -> str:
    return "\n".join(
        str(message.get("content", ""))
        for message in row.get("messages", [])
        if message.get("role") == role
    ).strip()


def normalized_question(row: dict[str, Any]) -> str:
    return re.sub(r"\s+", "", message_text(row, "user")).replace("<image>", "")


def stable_key(row: dict[str, Any], seed: int) -> str:
    value = f"{seed}\0{row.get('source', '')}\0{normalized_question(row)}"
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def is_calculation_candidate(row: dict[str, Any]) -> bool:
    question = message_text(row, "user")
    answer = message_text(row, "assistant")
    return bool(CALCULATION_RE.search(question) and NUMERIC_ANSWER_RE.fullmatch(answer))


def candidate_score(row: dict[str, Any]) -> int:
    question = message_text(row, "user")
    return (
        4 * int(bool(STRONG_CALCULATION_RE.search(question)))
        + SOURCE_PRIORITY.get(str(row.get("source", "")), 0)
        + int(len(re.findall(r"[-+]?\d+(?:\.\d+)?", question)) >= 2)
    )


def stratified_retrieval_sample(
    rows: list[dict[str, Any]], count: int, seed: int
) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[str(row.get("source", ""))].append(row)
    total = len(rows)
    quotas = {source: count * len(group) // total for source, group in groups.items()}
    remaining = count - sum(quotas.values())
    remainders = sorted(
        groups,
        key=lambda source: (-(count * len(groups[source]) % total), source),
    )
    for source in remainders[:remaining]:
        quotas[source] += 1
    selected_ids: set[int] = set()
    for source, group in groups.items():
        chosen = sorted(group, key=lambda row: stable_key(row, seed))[: quotas[source]]
        selected_ids.update(id(row) for row in chosen)
    return [row for row in rows if id(row) in selected_ids]


def proportional_quotas(sizes: dict[str, int], count: int) -> dict[str, int]:
    quotas = {key: 0 for key in sizes}
    remaining = count
    if count >= len(sizes):
        for key in sizes:
            quotas[key] = 1
            remaining -= 1
    capacities = {key: sizes[key] - quotas[key] for key in sizes}
    total_capacity = sum(capacities.values())
    if remaining:
        for key, capacity in capacities.items():
            quotas[key] += remaining * capacity // total_capacity
        left = count - sum(quotas.values())
        remainders = sorted(
            sizes,
            key=lambda key: (-(remaining * capacities[key] % total_capacity), key),
        )
        for key in remainders[:left]:
            quotas[key] += 1
    return quotas


def select_calculations(
    rows: list[dict[str, Any]], existing_questions: set[str], count: int, seed: int
) -> list[dict[str, Any]]:
    candidates = []
    seen = set(existing_questions)
    for source_line, row in enumerate(rows, 1):
        question = normalized_question(row)
        if not question or question in seen or not is_calculation_candidate(row):
            continue
        seen.add(question)
        candidates.append((source_line, row))
    if len(candidates) < count:
        raise ValueError(f"only {len(candidates)} calculation candidates found, need {count}")
    groups: dict[str, list[tuple[int, dict[str, Any]]]] = defaultdict(list)
    for item in candidates:
        groups[str(item[1].get("task", ""))].append(item)
    quotas = proportional_quotas({task: len(group) for task, group in groups.items()}, count)
    chosen = []
    for task, group in groups.items():
        group.sort(key=lambda item: (-candidate_score(item[1]), stable_key(item[1], seed)))
        chosen.extend(group[: quotas[task]])
    chosen.sort(key=lambda item: (str(item[1].get("task", "")), stable_key(item[1], seed)))
    selected = []
    image_paths: dict[str, str] = {}
    for source_line, row in chosen:
        augmented = dict(row)
        original_images = list(row.get("images") or [])
        rewritten_images = []
        for original_image in original_images:
            original_image = str(original_image)
            if original_image not in image_paths:
                suffix = Path(original_image).suffix.lower() or ".png"
                image_paths[original_image] = f"assets_rl/ewai/{len(image_paths) + 1}{suffix}"
            rewritten_images.append(image_paths[original_image])
        augmented.update(
            {
                "images": rewritten_images,
                "task": "multi_step_numerical_reasoning",
                "task_original": row.get("task", ""),
                "task_group": "visual_numerical_reasoning",
                "output_format": "number_or_free_text",
                "verifier_type": "numeric",
                "reward_type": "rule",
                "reward_subtype": "numeric",
                "_reward_routing": {
                    "version": "reasoning_calculation_augmentation_v1",
                    "reason": "numeric_answer_with_explicit_calculation_request",
                    "source_dataset": "test.jsonl",
                    "source_line": source_line,
                    "original_images": original_images,
                },
            }
        )
        selected.append(augmented)
    return selected


def build_dataset(
    reasoning_rows: list[dict[str, Any]],
    test_rows: list[dict[str, Any]],
    *,
    retrieval_count: int,
    calculation_count: int,
    seed: int,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    retrieval = [row for row in reasoning_rows if row.get("task") == "evidence_retrieval"]
    non_retrieval = [row for row in reasoning_rows if row.get("task") != "evidence_retrieval"]
    if len(retrieval) < retrieval_count:
        raise ValueError(f"only {len(retrieval)} retrieval rows found, need {retrieval_count}")
    kept_retrieval = stratified_retrieval_sample(retrieval, retrieval_count, seed)
    retained_ids = {id(row) for row in non_retrieval + kept_retrieval}
    retained = [row for row in reasoning_rows if id(row) in retained_ids]
    existing_questions = {normalized_question(row) for row in retained}
    calculations = select_calculations(test_rows, existing_questions, calculation_count, seed)
    output = retained + calculations
    audit = {
        "input_reasoning_rows": len(reasoning_rows),
        "input_test_rows": len(test_rows),
        "retrieval_before": len(retrieval),
        "retrieval_after": len(kept_retrieval),
        "retained_original_rows": len(retained),
        "added_calculation_rows": len(calculations),
        "output_rows": len(output),
        "seed": seed,
        "task_counts": dict(sorted(Counter(str(row.get("task", "")) for row in output).items())),
        "added_source_counts": dict(
            sorted(Counter(str(row.get("source", "")) for row in calculations).items())
        ),
        "added_original_task_counts": dict(
            sorted(Counter(str(row.get("task_original", "")) for row in calculations).items())
        ),
        "added_image_references": sum(len(row.get("images") or []) for row in calculations),
        "added_unique_images": len(
            {image for row in calculations for image in row.get("images", [])}
        ),
        "kept_retrieval_source_counts": dict(
            sorted(Counter(str(row.get("source", "")) for row in kept_retrieval).items())
        ),
    }
    return output, audit


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reasoning", type=Path, required=True)
    parser.add_argument("--test", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--audit", type=Path, required=True)
    parser.add_argument("--retrieval-count", type=int, default=1300)
    parser.add_argument("--calculation-count", type=int, default=5000)
    parser.add_argument("--seed", type=int, default=20260826)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output, audit = build_dataset(
        read_jsonl(args.reasoning),
        read_jsonl(args.test),
        retrieval_count=args.retrieval_count,
        calculation_count=args.calculation_count,
        seed=args.seed,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as handle:
        for row in output:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    args.audit.parent.mkdir(parents=True, exist_ok=True)
    args.audit.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(audit, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
