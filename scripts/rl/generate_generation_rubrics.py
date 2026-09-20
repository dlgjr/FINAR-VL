#!/usr/bin/env python3
"""Generate fixed sample-specific rubrics for FINAR-VL Generation RL."""

from __future__ import annotations

import argparse
import json
import os
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Mapping, Sequence


RUBRIC_SYSTEM = """你是 FINAR-VL Generation RL 的 rubric 构造器。

上游数据构造已经通过金融证据图固定 required_fact_ids；这些 required facts 是不可修改的硬约束。你的任务是基于问题、参考答案、任务要求和这些事实，为当前样本生成固定评分 rubric。

要求：
1. fact_criteria 必须与 required_fact_ids 一一对应，不能新增、删除、合并或替换 fact_id。
2. 每个 fact criterion 只描述候选答案应如何正确使用该事实，不得改写事实值、主体、期间、指标、口径、单位或币种。
3. analysis_criteria 评价跨事实归纳、比较、因果/风险分析、结论完整性等当前问题真正需要的能力，不要加入泛化的文风偏好。
4. factual criteria 的总权重至少占全部 criterion 权重的 50%。
5. critical_errors 只写会实质破坏答案正确性的任务特定错误；不要把措辞、篇幅或风格问题设为 critical error。
6. rubric 只根据给定材料生成，不引入外部知识。
7. criterion 要简洁、可判定。权重必须为正数。

严格输出一个 JSON 对象：
{
  "fact_criteria": [
    {"fact_id":"给定 fact_id", "criterion":"候选答案满足该事实约束的判定标准", "weight":0.2}
  ],
  "analysis_criteria": [
    {"id":"A1", "criterion":"当前问题需要的分析/综合要求", "weight":0.2}
  ],
  "critical_errors": [
    {"id":"E1", "description":"任务特定重大错误", "score_cap":0.3}
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
    fact_criteria = raw.get("fact_criteria")
    analysis_criteria = raw.get("analysis_criteria")
    critical_errors = raw.get("critical_errors") or []
    if not isinstance(fact_criteria, list) or not isinstance(analysis_criteria, list) or not isinstance(critical_errors, list):
        raise ValueError("invalid rubric schema")

    expected = list(required_ids)
    actual = [str(item.get("fact_id") or "") for item in fact_criteria if isinstance(item, Mapping)]
    if len(actual) != len(fact_criteria) or len(set(actual)) != len(actual) or set(actual) != set(expected):
        raise ValueError("fact_criteria must match required_fact_ids exactly")

    normalized_facts: list[dict[str, Any]] = []
    normalized_analysis: list[dict[str, Any]] = []
    total_weight = 0.0
    fact_weight = 0.0
    for index, fact_id in enumerate(expected, 1):
        item = next(item for item in fact_criteria if str(item.get("fact_id") or "") == fact_id)
        criterion = str(item.get("criterion") or "").strip()
        weight = float(item.get("weight") or 0)
        if not criterion or weight <= 0:
            raise ValueError(f"invalid fact criterion for {fact_id}")
        normalized_facts.append(
            {
                "id": f"F{index}",
                "fact_id": fact_id,
                "criterion": criterion,
                "weight": weight,
                "fact": fact_payload(facts_by_id[fact_id]),
            }
        )
        fact_weight += weight
        total_weight += weight

    seen_analysis: set[str] = set()
    for index, item in enumerate(analysis_criteria, 1):
        if not isinstance(item, Mapping):
            raise ValueError("invalid analysis criterion")
        criterion = str(item.get("criterion") or "").strip()
        criterion_id = f"A{index}"
        weight = float(item.get("weight") or 0)
        if not criterion or weight <= 0:
            raise ValueError("invalid analysis criterion")
        seen_analysis.add(criterion_id)
        normalized_analysis.append({"id": criterion_id, "criterion": criterion, "weight": weight})
        total_weight += weight

    if total_weight <= 0 or fact_weight / total_weight < 0.5:
        raise ValueError("factual criterion weight must be at least 50%")

    for item in [*normalized_facts, *normalized_analysis]:
        item["weight"] = round(float(item["weight"]) / total_weight, 6)

    normalized_errors: list[dict[str, Any]] = [
        {
            "id": "E_REQUIRED_FACT_CONTRADICTION",
            "description": "候选答案明确否定、篡改或混淆任一 required fact 的主体、期间、指标、口径、数值、单位、币种或结论。",
            "score_cap": 0.2,
        },
        {
            "id": "E_UNSUPPORTED_MATERIAL_CLAIM",
            "description": "候选答案引入材料无法支持且会实质改变分析结论的重要事实、因果关系或数据。",
            "score_cap": 0.3,
        },
    ]
    seen_errors = {item["id"] for item in normalized_errors}
    for index, item in enumerate(critical_errors, 1):
        if not isinstance(item, Mapping):
            raise ValueError("invalid critical error")
        error_id = str(item.get("id") or f"E{index}")
        description = str(item.get("description") or "").strip()
        cap = float(item.get("score_cap") if item.get("score_cap") is not None else 0.3)
        if not description or error_id in seen_errors or not 0 <= cap <= 0.5:
            raise ValueError("invalid critical error")
        seen_errors.add(error_id)
        normalized_errors.append({"id": error_id, "description": description, "score_cap": cap})

    return {
        "version": "generation_rubric_v1",
        "required_fact_ids": expected,
        "fact_criteria": normalized_facts,
        "analysis_criteria": normalized_analysis,
        "critical_errors": normalized_errors,
    }


def build_row(
    indexed_row: tuple[int, dict[str, Any]],
    facts_by_id: Mapping[str, Mapping[str, Any]],
    args: argparse.Namespace,
) -> dict[str, Any]:
    index, row = indexed_row
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
