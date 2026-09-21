#!/usr/bin/env python3
"""Generate fixed dynamic-K fact-grounded rubrics for FINAR-VL Generation RL."""

from __future__ import annotations

import argparse
import json
import os
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Mapping, Sequence


RUBRIC_SYSTEM = """你是 FINAR-VL Generation RL 的 sample-specific rubric 构造器。

上游 Generation 数据已经用金融证据图固定了 required_fact_ids、distractor_ids、reasoning_graph 和 analysis_dimensions。
required facts 是允许回答使用的主要证据空间；它们不是要求候选答案逐字逐条复述的 checklist。
reference_answer 只是一条合理参考路径，不是唯一正确表达。

请为当前样本生成数量由任务复杂度决定的原子评分点。不要为了固定数量硬拆或重复事实。

要求：
1. points 数量必须在输入 min_points 和 max_points 之间，由任务复杂度决定。
2. 每个 point 必须原子、可二值判定；不要把多个可独立失败的要求塞进一个 criterion。
3. 每个 point 的 fact_ids 只能来自 required_fact_ids；可以依赖一个或多个 facts。
4. 所有 required_fact_ids 在整组 points 中至少被引用一次，以保证 rubric 覆盖证据空间；但候选答案不需要满足所有 points 才能成为高质量回答。
5. dimension 只能是 fact / relation / synthesis / completeness：
   - fact：某个直接事实使用是否正确；
   - relation：多个事实之间的比较、驱动、对照、因果或约束关系；
   - synthesis：跨事实形成的任务核心结论；
   - completeness：问题明确要求的必要覆盖维度。
6. importance 只能是 core / important / optional。core 只给直接影响任务核心正确性的 criterion；不要把所有 points 都标 core。
7. 不生成 style、篇幅、格式、措辞漂亮程度等 criterion。
8. 不得引入 required facts 之外的新事实，不得改写主体、期间、指标、scope、数值、单位、币种或原始结论。
9. reasoning_graph 和 analysis_dimensions 应优先用于构造 relation / synthesis criteria，而不是只从 reference_answer 反推。
10. criterion 不得重复或近义重复。若两个点高度相关，应合并或保留更直接、可判定的一个。
11. 训练时每个 point 只会判 0/1，因此 criterion 必须允许明确二值判断。

严格输出一个 JSON 对象：
{
  "points": [
    {
      "dimension": "fact|relation|synthesis|completeness",
      "importance": "core|important|optional",
      "fact_ids": ["给定 required fact_id"],
      "criterion": "候选答案满足该要求时得1，否则0"
    }
  ]
}
只输出 JSON。"""


RUBRIC_REVIEW_SYSTEM = """你是 FINAR-VL Generation RL rubric reviewer。你会看到任务证据、任务规格和一份 draft rubric。
请只修订 rubric，不回答问题。

检查并修复：
1. points 数量必须位于 min_points..max_points，不为凑数量重复拆分。
2. criterion 必须原子化；compound criterion 要拆开，但不能产生近义重复。
3. 删除 style / verbosity / formatting 偏好。
4. fact_ids 只能引用 required_fact_ids；整组 points 必须覆盖全部 required_fact_ids。
5. relation / synthesis 必须能由 required facts 和 reasoning_graph 支撑，不能引入外部事实。
6. importance 要克制：core 只用于任务核心正确性，important 用于关键分析，optional 用于有价值但非必要的覆盖。
7. reference_answer 不是唯一答案；不要把其措辞或组织方式写成 criterion。
8. 如果多个 criteria 实际测量同一内容，合并或删除冗余项。

严格输出：
{"points":[{"dimension":"fact|relation|synthesis|completeness","importance":"core|important|optional","fact_ids":["..."],"criterion":"..."}]}
只输出 JSON。"""


DIMENSIONS = {"fact", "relation", "synthesis", "completeness"}
IMPORTANCE_WEIGHTS = {"core": 3, "important": 2, "optional": 1}
DIMENSION_WEIGHTS = {"fact": 0.50, "relation": 0.25, "synthesis": 0.15, "completeness": 0.10}
HARD_CHECKS = [
    {
        "id": "H_REQUIRED_FACT_CONTRADICTION",
        "description": "候选答案明确陈述与 required fact 冲突的主体、期间、指标、scope、数值、方向、单位、币种或结论；遗漏 required fact 不属于 contradiction。",
    },
    {
        "id": "H_DISTRACTOR_MISUSE",
        "description": "候选答案把 distractor fact 当成当前问题的有效依据并据此形成重要事实或结论；明确排除/否定 distractor 不算 misuse。",
    },
    {
        "id": "H_UNSUPPORTED_MATERIAL_CLAIM",
        "description": "候选答案引入 required facts 与 rubric-defined inference 都无法支持、且会影响核心结论/主要因果解释/关键数字/关键实体事件的重要断言。",
    },
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--evidence-facts", type=Path)
    parser.add_argument("--judge-url", default=os.environ.get("GSPO_JUDGE_URL", "http://127.0.0.1:8001"))
    parser.add_argument("--model", default=os.environ.get("GSPO_JUDGE_SERVE_NAME", "qwen235-judge"))
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--timeout", type=float, default=180.0)
    parser.add_argument("--max-tokens", type=int, default=2048)
    parser.add_argument("--retries", type=int, default=2)
    parser.add_argument("--min-points", type=int, default=2)
    parser.add_argument("--max-points", type=int, default=15)
    parser.add_argument("--skip-review", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def sample_id(row: Mapping[str, Any], index: int) -> str:
    return str(row.get("sample_id") or row.get("id") or f"line:{index}")


def fact_payload(fact: Mapping[str, Any]) -> dict[str, Any]:
    return {
        key: fact.get(key)
        for key in (
            "fact_id",
            "entity",
            "period",
            "fact_type",
            "metric",
            "scope",
            "value_text",
            "numeric_value",
            "unit",
            "currency",
            "claim",
            "topic",
            "source_mode",
            "page",
            "evidence_quote",
        )
        if fact.get(key) not in (None, "")
    }


def teacher_completion(
    judge_url: str,
    model: str,
    system: str,
    payload: Mapping[str, Any],
    timeout: float,
    max_tokens: int,
) -> dict[str, Any]:
    body = json.dumps(
        {
            "model": model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": json.dumps(payload, ensure_ascii=False, indent=2)},
            ],
            "temperature": 0.0,
            "top_p": 1.0,
            "max_tokens": max_tokens,
            "response_format": {"type": "json_object"},
            "chat_template_kwargs": {"enable_thinking": False, "thinking": False},
        },
        ensure_ascii=False,
    ).encode("utf-8")
    request = urllib.request.Request(
        judge_url.rstrip("/") + "/v1/chat/completions",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        result = json.loads(response.read().decode("utf-8"))
    return json.loads(result["choices"][0]["message"]["content"])


def normalize_rubric(
    raw: Mapping[str, Any],
    required_ids: Sequence[str],
    distractor_ids: Sequence[str],
    facts_by_id: Mapping[str, Mapping[str, Any]],
    *,
    min_points: int,
    max_points: int,
) -> dict[str, Any]:
    points = raw.get("points")
    if not isinstance(points, list) or not min_points <= len(points) <= max_points:
        raise ValueError(f"rubric must contain {min_points}..{max_points} points")

    required = list(dict.fromkeys(map(str, required_ids)))
    distractors = list(dict.fromkeys(map(str, distractor_ids)))
    required_set = set(required)
    distractor_set = set(distractors)
    if required_set & distractor_set:
        raise ValueError("required and distractor fact ids must be disjoint")

    covered: set[str] = set()
    normalized_points: list[dict[str, Any]] = []
    seen_criteria: set[str] = set()
    core_count = 0

    for index, item in enumerate(points, 1):
        if not isinstance(item, Mapping):
            raise ValueError(f"invalid point at index {index}")
        criterion = str(item.get("criterion") or "").strip()
        dimension = str(item.get("dimension") or "").strip().lower()
        importance = str(item.get("importance") or "").strip().lower()
        fact_ids = item.get("fact_ids")
        if not criterion or dimension not in DIMENSIONS or importance not in IMPORTANCE_WEIGHTS:
            raise ValueError(f"invalid rubric point at index {index}")
        if not isinstance(fact_ids, list) or not fact_ids:
            raise ValueError(f"point {index} requires non-empty fact_ids")

        normalized_ids = list(dict.fromkeys(map(str, fact_ids)))
        if any(fact_id not in required_set for fact_id in normalized_ids):
            raise ValueError(f"point {index} references fact outside required_fact_ids")

        criterion_key = "".join(criterion.split()).casefold()
        if criterion_key in seen_criteria:
            raise ValueError(f"duplicate criterion at point {index}")
        seen_criteria.add(criterion_key)
        covered.update(normalized_ids)
        core_count += int(importance == "core")

        normalized_points.append(
            {
                "id": f"P{index}",
                "dimension": dimension,
                "importance": importance,
                "fact_ids": normalized_ids,
                "criterion": criterion,
                "facts": [fact_payload(facts_by_id[fact_id]) for fact_id in normalized_ids],
            }
        )

    if covered != required_set:
        raise ValueError(f"rubric does not cover required facts: {sorted(required_set - covered)}")
    if core_count == 0:
        raise ValueError("rubric must contain at least one core criterion")
    if core_count == len(normalized_points) and len(normalized_points) > min_points:
        raise ValueError("rubric must not mark every criterion as core")

    return {
        "version": "generation_rubric_v3_dynamic",
        "required_fact_ids": required,
        "distractor_fact_ids": distractors,
        "points": normalized_points,
        "distractor_facts": [fact_payload(facts_by_id[fact_id]) for fact_id in distractors],
        "hard_checks": HARD_CHECKS,
        "point_bounds": {"min": min_points, "max": max_points},
        "scoring": {
            "point_values": [0, 1],
            "importance_weights": IMPORTANCE_WEIGHTS,
            "dimension_weights": DIMENSION_WEIGHTS,
            "quality_score": "dimension_weighted_mean",
            "acceptance": "quality_score>=runtime_threshold and no_hard_fail",
        },
    }


def build_row(
    indexed_row: tuple[int, dict[str, Any]],
    facts_by_id: Mapping[str, Mapping[str, Any]],
    args: argparse.Namespace,
) -> dict[str, Any]:
    index, row = indexed_row
    verifier_type = str(row.get("verifier_type") or row.get("reward_subtype") or "")
    if str(row.get("reward_type") or "") != "judge" and verifier_type != "model_judge":
        return dict(row)

    metadata = row.get("metadata") or {}
    required_ids = [str(value) for value in metadata.get("required_evidence_ids") or []]
    distractor_ids = [str(value) for value in metadata.get("distractor_ids") or []]
    if not required_ids:
        raise ValueError(f"{sample_id(row, index)} missing metadata.required_evidence_ids")

    missing = [fact_id for fact_id in [*required_ids, *distractor_ids] if fact_id not in facts_by_id]
    if missing:
        raise ValueError(f"{sample_id(row, index)} missing evidence facts: {missing}")

    payload = {
        "sample_id": sample_id(row, index),
        "task": row.get("task"),
        "question": row.get("question"),
        "reference_answer": row.get("reference_answer") or row.get("solution"),
        "generation_spec": metadata.get("generation_spec") or {},
        "reasoning_graph": metadata.get("reasoning_graph") or {},
        "required_fact_ids": required_ids,
        "required_facts": [fact_payload(facts_by_id[fact_id]) for fact_id in required_ids],
        "distractor_ids": distractor_ids,
        "distractor_facts": [fact_payload(facts_by_id[fact_id]) for fact_id in distractor_ids],
        "min_points": args.min_points,
        "max_points": args.max_points,
    }

    last_error: Exception | None = None
    for _ in range(args.retries + 1):
        try:
            raw = teacher_completion(
                args.judge_url,
                args.model,
                RUBRIC_SYSTEM,
                payload,
                args.timeout,
                args.max_tokens,
            )
            if not args.skip_review:
                raw = teacher_completion(
                    args.judge_url,
                    args.model,
                    RUBRIC_REVIEW_SYSTEM,
                    {**payload, "draft_rubric": raw},
                    args.timeout,
                    args.max_tokens,
                )
            result = dict(row)
            result["generation_rubric"] = normalize_rubric(
                raw,
                required_ids,
                distractor_ids,
                facts_by_id,
                min_points=args.min_points,
                max_points=args.max_points,
            )
            return result
        except Exception as exc:
            last_error = exc
    raise RuntimeError(f"rubric generation failed for {sample_id(row, index)}: {last_error}")


def main() -> None:
    args = parse_args()
    if args.min_points < 1 or args.max_points < args.min_points:
        raise ValueError("invalid rubric point bounds")

    evidence_path = args.evidence_facts or (args.input.parent / "generation_evidence_facts.jsonl")
    rows = read_jsonl(args.input)
    facts = read_jsonl(evidence_path)
    facts_by_id = {str(row["fact_id"]): row for row in facts}

    completed: set[str] = set()
    if args.output.exists() and not args.overwrite:
        for index, row in enumerate(read_jsonl(args.output), 1):
            rubric = row.get("generation_rubric")
            if isinstance(rubric, Mapping) and rubric.get("version") == "generation_rubric_v3_dynamic":
                completed.add(sample_id(row, index))
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text("", encoding="utf-8")

    pending = [(index, row) for index, row in enumerate(rows, 1) if sample_id(row, index) not in completed]
    with args.output.open("a", encoding="utf-8") as handle:
        with ThreadPoolExecutor(max_workers=args.workers) as executor:
            for done, result in enumerate(executor.map(lambda item: build_row(item, facts_by_id, args), pending), 1):
                handle.write(json.dumps(result, ensure_ascii=False) + "\n")
                handle.flush()
                if done % 20 == 0 or done == len(pending):
                    print(
                        json.dumps(
                            {"rubrics_written": len(completed) + done, "total": len(rows)},
                            ensure_ascii=False,
                        ),
                        flush=True,
                    )


if __name__ == "__main__":
    main()
