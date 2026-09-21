"""OpenAI-compatible client for FINAR-VL GSPO judging."""

from __future__ import annotations

import json
import os
import re
import urllib.request
from pathlib import Path
from typing import Any, Mapping


_IMAGE_TAG_RE = re.compile(r"(<image>)")
_DEFAULT_IMPORTANCE_WEIGHTS = {"core": 3.0, "important": 2.0, "optional": 1.0}
_DEFAULT_DIMENSION_WEIGHTS = {"fact": 0.50, "relation": 0.25, "synthesis": 0.15, "completeness": 0.10}


def _local_image_url(value: Any) -> str:
    raw = str(value)
    if raw.startswith(("http://", "https://", "data:", "file://")):
        return raw
    path = Path(raw).expanduser()
    if not path.is_absolute():
        path = Path(os.environ.get("ROOT_IMAGE_DIR", ".")).expanduser() / path
    path = path.resolve()
    if not path.is_file():
        raise FileNotFoundError(f"judge image not found: {raw}")
    return path.as_uri()


def _multimodal_content(rubric: str, question: str, candidate: str, images: list[Any]) -> list[dict[str, Any]]:
    image_urls = [_local_image_url(image) for image in images]
    content: list[dict[str, Any]] = [{"type": "text", "text": rubric + "\n问题："}]
    image_index = 0
    if "<image>" in question:
        for piece in _IMAGE_TAG_RE.split(question):
            if not piece:
                continue
            if piece == "<image>":
                if image_index >= len(image_urls):
                    raise ValueError("question contains more <image> placeholders than images")
                content.append({"type": "image_url", "image_url": {"url": image_urls[image_index]}})
                image_index += 1
            else:
                content.append({"type": "text", "text": piece})
    else:
        for image_url in image_urls:
            content.append({"type": "image_url", "image_url": {"url": image_url}})
            image_index += 1
        content.append({"type": "text", "text": question})
    if image_index != len(image_urls):
        raise ValueError("question contains fewer <image> placeholders than images")
    content.append({"type": "text", "text": f"\n候选答案：{candidate}"})
    return content


def _generation_rubric_instruction(rubric: Mapping[str, Any]) -> str:
    return (
        "你是严格的金融 Generation RL 裁判。下面的 sample-specific rubric 已在看到候选答案之前冻结。"
        "required facts 来自上游金融证据图；reference answer 不参与本次 runtime judging。\n"
        "\n"
        "任务一：逐项 rubric 判定。\n"
        "- 对每个 point 只能给 0 或 1，不允许0.5或其他中间分。\n"
        "- 只有候选答案明确满足 criterion 时才能给1。遗漏、关系错误、事实错误或结论不成立给0。\n"
        "- score=1 时 candidate_evidence 必须逐字摘录候选答案中的最短支持片段；仅仅主题相关、隐含猜测或语义沾边不能给1。\n"
        "- 措辞不同但语义等价可以给1；不要按文风、长度、格式加减分。\n"
        "\n"
        "任务二：独立 factual audit。这里只检查不可接受的事实完整性问题，不把普通遗漏当 hard fail。\n"
        "1. contradicted_fact_ids：候选明确陈述了与 required fact 冲突的主体、期间、指标、scope、数值、方向、单位、币种或结论。"
        "没有提到某个 required fact 不算 contradiction。\n"
        "2. used_distractor_ids：候选把已标记 distractor 的事实当成当前问题有效依据并据此形成重要事实/结论。"
        "明确排除或否定 distractor 不算 misuse。\n"
        "3. unsupported_material_claims：候选引入 required facts 与 rubric-defined inference 都无法支持的重要断言。"
        "只有新的关键数字、关键实体/事件、主要因果解释、核心比较依据或会改变最终结论的 unsupported claim 才记录；"
        "普通措辞、弱背景描述、合理概括不记录。\n"
        "4. 合理的跨事实归纳允许判 SUPPORTED_INFERENCE；不要因为某句话没有逐字出现在单一 fact 中就当 hallucination。\n"
        "\n"
        "必须恰好返回每个 rubric point 一次。严格只返回 JSON：\n"
        "{"
        "\"point_scores\":[{\"id\":\"P1\",\"score\":1,\"candidate_evidence\":\"候选答案中的原文片段\"}],"
        "\"contradicted_fact_ids\":[],"
        "\"used_distractor_ids\":[],"
        "\"unsupported_material_claims\":[{\"claim\":\"...\",\"reason\":\"...\"}]"
        "}\n"
        "冻结 rubric：\n" + json.dumps(rubric, ensure_ascii=False, indent=2)
    )


def _default_instruction() -> str:
    return (
        "你是严格的金融问答裁判。只能依据问题提供的上下文、明确条件和可靠的金融知识，"
        "评估训练模型的候选答案，不得使用问题和候选答案之外的样本字段。按以下量表计算总分：\n"
        "1. 正确性50%：事实、数字、概念、因果关系和最终结论正确；\n"
        "2. 完整性20%：覆盖问题要求的全部子问题、条件和必要结论；\n"
        "3. 依据可靠性20%：结论能由题目上下文或可靠金融知识支持，不虚构数据、实体或依据；\n"
        "4. 相关性与表达10%：直接回答问题，含义明确且无自相矛盾。\n"
        "若核心结论错误，总分不得高于0.2；影响结论的虚构内容，总分不得高于0.3；"
        "空答、拒答或无关回答为0。问题只要求简短事实或结论时，答案简洁不应扣分；"
        "措辞不同但语义等价不应扣分。只返回一个JSON对象，不要Markdown、解释、分项分数或思考过程。"
        '格式必须为 {"score":0.0}，score为0到1之间的数字，最多保留两位小数。'
    )


def _compact_ws(value: str) -> str:
    return re.sub(r"\s+", "", str(value))


def _score_generation_rubric(
    result: str,
    rubric: Mapping[str, Any],
    *,
    candidate: str,
    accept_threshold: float,
) -> str:
    points = rubric.get("points")
    if not isinstance(points, list) or not points:
        raise ValueError("generation rubric must contain points")
    if rubric.get("version") != "generation_rubric_v3_dynamic":
        raise ValueError("unsupported generation rubric version")

    expected_ids = [str(item.get("id") or "") for item in points if isinstance(item, Mapping)]
    if expected_ids != [f"P{index}" for index in range(1, len(points) + 1)]:
        raise ValueError("generation rubric point ids must be sequential P1..PK")

    scoring = rubric.get("scoring") or {}
    importance_weights = scoring.get("importance_weights") or _DEFAULT_IMPORTANCE_WEIGHTS
    dimension_weights = scoring.get("dimension_weights") or _DEFAULT_DIMENSION_WEIGHTS
    if not isinstance(importance_weights, Mapping) or not isinstance(dimension_weights, Mapping):
        raise ValueError("invalid rubric aggregation weights")

    point_weights: dict[str, float] = {}
    point_dimensions: dict[str, str] = {}
    for point in points:
        if not isinstance(point, Mapping):
            raise ValueError("invalid generation rubric point")
        point_id = str(point["id"])
        importance = str(point.get("importance") or "")
        dimension = str(point.get("dimension") or "")
        if importance not in importance_weights:
            raise ValueError(f"unknown rubric importance: {importance}")
        if dimension not in dimension_weights:
            raise ValueError(f"unknown rubric dimension: {dimension}")
        weight = float(importance_weights[importance])
        if weight <= 0 or float(dimension_weights[dimension]) <= 0:
            raise ValueError("rubric aggregation weights must be positive")
        point_weights[point_id] = weight
        point_dimensions[point_id] = dimension

    payload = json.loads(result)
    if not isinstance(payload, Mapping) or not isinstance(payload.get("point_scores"), list):
        raise ValueError("invalid generation rubric judge schema")

    candidate_compact = _compact_ws(candidate)
    scores: dict[str, int] = {}
    evidence_by_id: dict[str, str] = {}
    for item in payload["point_scores"]:
        if not isinstance(item, Mapping):
            raise ValueError("invalid point score item")
        point_id = str(item.get("id") or "")
        score = item.get("score")
        evidence = str(item.get("candidate_evidence") or "").strip()
        if point_id in scores or point_id not in point_weights:
            raise ValueError("unknown or duplicate point id")
        if isinstance(score, bool) or not isinstance(score, (int, float)) or float(score) not in {0.0, 1.0}:
            raise ValueError("each Generation rubric point must be binary 0/1")
        binary_score = int(score)
        if binary_score == 1:
            if not evidence or _compact_ws(evidence) not in candidate_compact:
                raise ValueError(f"score=1 for {point_id} requires an exact candidate evidence span")
        scores[point_id] = binary_score
        evidence_by_id[point_id] = evidence

    if set(scores) != set(expected_ids):
        raise ValueError("judge must score every rubric point exactly once")

    required_ids = set(map(str, rubric.get("required_fact_ids") or []))
    distractor_ids = set(map(str, rubric.get("distractor_fact_ids") or []))

    contradicted = payload.get("contradicted_fact_ids") or []
    used_distractors = payload.get("used_distractor_ids") or []
    unsupported = payload.get("unsupported_material_claims") or []
    if not isinstance(contradicted, list) or not isinstance(used_distractors, list) or not isinstance(unsupported, list):
        raise ValueError("invalid factual audit schema")

    contradicted_ids = list(dict.fromkeys(map(str, contradicted)))
    used_distractor_ids = list(dict.fromkeys(map(str, used_distractors)))
    if any(fact_id not in required_ids for fact_id in contradicted_ids):
        raise ValueError("contradicted_fact_ids contains unknown required fact")
    if any(fact_id not in distractor_ids for fact_id in used_distractor_ids):
        raise ValueError("used_distractor_ids contains unknown distractor fact")

    unsupported_claims: list[dict[str, str]] = []
    for item in unsupported:
        if not isinstance(item, Mapping):
            raise ValueError("invalid unsupported material claim")
        claim = str(item.get("claim") or "").strip()
        reason = str(item.get("reason") or "").strip()
        if not claim or not reason:
            raise ValueError("unsupported material claim requires claim and reason")
        unsupported_claims.append({"claim": claim, "reason": reason})

    dimension_scores: dict[str, float] = {}
    for dimension in dict.fromkeys(point_dimensions[point_id] for point_id in expected_ids):
        ids = [point_id for point_id in expected_ids if point_dimensions[point_id] == dimension]
        denominator = sum(point_weights[point_id] for point_id in ids)
        dimension_scores[dimension] = (
            sum(point_weights[point_id] * scores[point_id] for point_id in ids) / denominator
        )
    dimension_denominator = sum(float(dimension_weights[dimension]) for dimension in dimension_scores)
    quality_score = sum(
        float(dimension_weights[dimension]) * value
        for dimension, value in dimension_scores.items()
    ) / dimension_denominator
    hard_fail = bool(contradicted_ids or used_distractor_ids or unsupported_claims)
    accepted = (not hard_fail) and quality_score >= accept_threshold

    return json.dumps(
        {
            "score": round(quality_score, 6),
            "quality_score": round(quality_score, 6),
            "accepted": accepted,
            "hard_fail": hard_fail,
            "accept_threshold": accept_threshold,
            "dimension_scores": {key: round(value, 6) for key, value in dimension_scores.items()},
            "point_scores": [
                {
                    "id": point_id,
                    "score": scores[point_id],
                    "candidate_evidence": evidence_by_id[point_id],
                }
                for point_id in expected_ids
            ],
            "contradicted_fact_ids": contradicted_ids,
            "used_distractor_ids": used_distractor_ids,
            "unsupported_material_claims": unsupported_claims,
        },
        ensure_ascii=False,
    )


def judge_completion(
    judge_url: str,
    *,
    question: str,
    candidate: str,
    images: list[Any] | None = None,
    model: str = "qwen235-judge",
    timeout: float = 180.0,
    max_tokens: int = 64,
    generation_rubric: Mapping[str, Any] | None = None,
    generation_accept_threshold: float = 0.75,
) -> str:
    """Ask the local judge to score a rollout with an optional fixed generation rubric."""

    if not 0.0 <= generation_accept_threshold <= 1.0:
        raise ValueError("generation accept threshold must be in [0, 1]")
    instruction = _generation_rubric_instruction(generation_rubric) if generation_rubric else _default_instruction()
    payload = json.dumps(
        {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": _multimodal_content(instruction, question, candidate, list(images or [])),
                }
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
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        body = json.loads(response.read().decode("utf-8"))
    result = str(body["choices"][0]["message"]["content"])
    return (
        _score_generation_rubric(
            result,
            generation_rubric,
            candidate=candidate,
            accept_threshold=generation_accept_threshold,
        )
        if generation_rubric
        else result
    )


def judge_from_record(candidate: str, record: Mapping[str, Any]) -> str:
    url = os.environ["GSPO_JUDGE_URL"]
    generation_rubric = record.get("generation_rubric")
    if isinstance(generation_rubric, str):
        generation_rubric = json.loads(generation_rubric)
    return judge_completion(
        url,
        question=str(record.get("question", "")),
        candidate=candidate,
        images=list(record.get("images") or []),
        model=os.environ.get("GSPO_JUDGE_SERVE_NAME", "qwen235-judge"),
        timeout=float(os.environ.get("GSPO_JUDGE_TIMEOUT", "180")),
        max_tokens=int(os.environ.get("GSPO_JUDGE_MAX_TOKENS", "64")),
        generation_rubric=generation_rubric if isinstance(generation_rubric, Mapping) else None,
        generation_accept_threshold=float(os.environ.get("GSPO_GENERATION_ACCEPT_THRESHOLD", "0.75")),
    )
