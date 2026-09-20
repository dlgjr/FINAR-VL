#!/usr/bin/env python3
"""Generate fixed 10-point fact-grounded rubrics for FINAR-VL Generation RL."""

from __future__ import annotations

import argparse
import json
import os
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Mapping, Sequence


RUBRIC_SYSTEM = """你是 FINAR-VL Generation RL 的 rubric 构造器。

上游数据构造已经通过金融证据图固定 required_fact_ids；这些 required facts 是不可修改的硬约束。
你的任务是根据问题、参考答案、任务要求和 required facts，为当前样本生成恰好 10 个二值评分点。

要求：
1. 必须输出恰好 10 个 points。
2. 每个 point 只能依赖给定 required facts，可关联 1 条或多条 fact_id，但不能使用外部知识。
3. 10 个 points 合起来必须覆盖所有 required_fact_ids；任何 required fact 都不能遗漏。
4. point 要原子化、可判定。尽量把事实正确性、关键比较、跨事实关系、必要结论拆成独立点。
5. 不得改写 required fact 的主体、期间、指标、scope、数值、单位、币种或原始结论。
6. 可以把多个 required facts 的关系作为一个 point，但必须列出所有支撑该 point 的 fact_ids。
7. 不为文风、篇幅、措辞漂亮程度单独设点；只评价事实、基于事实的分析、完整性和 grounding。
8. 每点在训练 judge 阶段只能判 0 或 1，因此 criterion 必须能做明确二值判断。
9. 不要输出 weight、总分、critical error 或其他评分机制；10 点等权，每点 1 分。

严格输出一个 JSON 对象：
{
  "points": [
    {
      "fact_ids": ["给定 fact_id"],
      "criterion": "候选答案满足该事实或事实关系时得1分，否则0分"
    }
  ]
}
只输出 JSON。"""


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
    payload: Mapping[str, Any],
    timeout: float,
    max_tokens: int,
) -> dict[str, Any]:
    body = json.dumps(
        {
            "model": model,
            "messages": [
                {"role": "system", "content": RUBRIC_SYSTEM},
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
    facts_by_id: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    points = raw.get("points")
    if not isinstance(points, list) or len(points) != 10:
        raise ValueError("rubric must contain exactly 10 points")

    required = list(dict.fromkeys(map(str, required_ids)))
    required_set = set(required)
    covered: set[str] = set()
    normalized_points: list[dict[str, Any]] = []
    seen_criteria: set[str] = set()

    for index, item in enumerate(points, 1):
        if not isinstance(item, Mapping):
            raise ValueError(f"invalid point at index {index}")
        criterion = str(item.get("criterion") or "").strip()
        fact_ids = item.get("fact_ids")
        if not criterion or not isinstance(fact_ids, list) or not fact_ids:
            raise ValueError(f"point {index} requires criterion and fact_ids")

        normalized_ids = list(dict.fromkeys(map(str, fact_ids)))
        if any(fact_id not in required_set for fact_id in normalized_ids):
            raise ValueError(f"point {index} references fact outside required_fact_ids")
        criterion_key = "".join(criterion.split()).lower()
        if criterion_key in seen_criteria:
            raise ValueError(f"duplicate criterion at point {index}")
        seen_criteria.add(criterion_key)
        covered.update(normalized_ids)

        normalized_points.append(
            {
                "id": f"P{index}",
                "fact_ids": normalized_ids,
                "criterion": criterion,
                "facts": [fact_payload(facts_by_id[fact_id]) for fact_id in normalized_ids],
            }
        )

    if covered != required_set:
        missing = sorted(required_set - covered)
        raise ValueError(f"10 points do not cover all required facts: {missing}")

    return {
        "version": "generation_rubric_v2_binary10",
        "scoring": {"num_points": 10, "point_values": [0, 1], "reward": "sum(points)/10"},
        "required_fact_ids": required,
        "points": normalized_points,
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
    if not required_ids:
        raise ValueError(f"{sample_id(row, index)} missing metadata.required_evidence_ids")
    missing = [fact_id for fact_id in required_ids if fact_id not in facts_by_id]
    if missing:
        raise ValueError(f"{sample_id(row, index)} missing evidence facts: {missing}")

    payload = {
        "sample_id": sample_id(row, index),
        "task": row.get("task"),
        "question": row.get("question"),
        "reference_answer": row.get("reference_answer") or row.get("solution"),
        "generation_spec": metadata.get("generation_spec") or {},
        "required_fact_ids": required_ids,
        "required_facts": [fact_payload(facts_by_id[fact_id]) for fact_id in required_ids],
    }
    last_error: Exception | None = None
    for _ in range(args.retries + 1):
        try:
            raw = teacher_completion(args.judge_url, args.model, payload, args.timeout, args.max_tokens)
            result = dict(row)
            result["generation_rubric"] = normalize_rubric(raw, required_ids, facts_by_id)
            return result
        except Exception as exc:
            last_error = exc
    raise RuntimeError(f"rubric generation failed for {sample_id(row, index)}: {last_error}")


def main() -> None:
    args = parse_args()
    evidence_path = args.evidence_facts or (args.input.parent / "generation_evidence_facts.jsonl")
    rows = read_jsonl(args.input)
    facts = read_jsonl(evidence_path)
    facts_by_id = {str(row["fact_id"]): row for row in facts}

    completed: set[str] = set()
    if args.output.exists() and not args.overwrite:
        for index, row in enumerate(read_jsonl(args.output), 1):
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
                    print(json.dumps({"rubrics_written": len(completed) + done, "total": len(rows)}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
