"""OpenAI-compatible client for FINAR-VL GSPO judging."""

from __future__ import annotations

import json
import os
import re
import urllib.request
from pathlib import Path
from typing import Any, Mapping


_IMAGE_TAG_RE = re.compile(r"(<image>)")


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
        "你是严格的金融 Generation RL 裁判。下面 10 个评分点已在看到候选答案之前根据 required facts 固定。"
        "你只能逐点判定，不能新增、删除、合并、改写评分点，也不能引入外部事实。\n"
        "每个 point 只能给 0 或 1：完整满足该 point 才给1；遗漏、事实错误、关系错误、结论不成立或与支撑事实冲突均给0。"
        "不允许0.5或其他中间分。措辞不同但语义等价可以给1。不要因为文风、长度或格式额外加减分。\n"
        "必须恰好返回 P1-P10 各一次。严格只返回 JSON："
        '{"point_scores":[{"id":"P1","score":1},{"id":"P2","score":0}]}\n'
        "固定10点 rubric：\n" + json.dumps(rubric, ensure_ascii=False, indent=2)
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


def _score_generation_rubric(result: str, rubric: Mapping[str, Any]) -> str:
    points = rubric.get("points")
    if not isinstance(points, list) or len(points) != 10:
        raise ValueError("generation rubric must contain exactly 10 points")
    expected_ids = [str(item.get("id") or "") for item in points]
    if expected_ids != [f"P{index}" for index in range(1, 11)]:
        raise ValueError("generation rubric point ids must be P1-P10")

    payload = json.loads(result)
    if not isinstance(payload, Mapping) or not isinstance(payload.get("point_scores"), list):
        raise ValueError("invalid binary10 judge schema")

    scores: dict[str, int] = {}
    for item in payload["point_scores"]:
        if not isinstance(item, Mapping):
            raise ValueError("invalid point score item")
        point_id = str(item.get("id") or "")
        score = item.get("score")
        if point_id in scores or point_id not in expected_ids:
            raise ValueError("unknown or duplicate point id")
        if isinstance(score, bool) or not isinstance(score, (int, float)) or float(score) not in {0.0, 1.0}:
            raise ValueError("each Generation reward point must be binary 0/1")
        scores[point_id] = int(score)

    if set(scores) != set(expected_ids):
        raise ValueError("judge must score all P1-P10 exactly once")

    total = sum(scores[point_id] for point_id in expected_ids)
    reward = total / 10.0
    return json.dumps(
        {
            "score": reward,
            "points_earned": total,
            "points_total": 10,
            "point_scores": [{"id": point_id, "score": scores[point_id]} for point_id in expected_ids],
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
) -> str:
    """Ask the local judge to score a rollout with an optional fixed generation rubric."""

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
    return _score_generation_rubric(result, generation_rubric) if generation_rubric else result


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
    )
