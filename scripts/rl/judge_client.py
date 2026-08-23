"""OpenAI-compatible client for the reference-free GSPO judge."""

from __future__ import annotations

import json
import os
import urllib.request
from typing import Any, Mapping


def judge_completion(
    judge_url: str,
    *,
    question: str,
    candidate: str,
    model: str = "deepseek-v4",
    timeout: float = 180.0,
    max_tokens: int = 64,
) -> str:
    """Ask the local judge to score only the question and rollout answer."""

    prompt = (
        "你是严格的金融问答裁判。只能依据问题提供的上下文、明确条件和可靠的金融知识，"
        "评估训练模型的候选答案，不得使用问题和候选答案之外的样本字段。按以下量表计算总分：\n"
        "1. 正确性50%：事实、数字、概念、因果关系和最终结论正确；\n"
        "2. 完整性20%：覆盖问题要求的全部子问题、条件和必要结论；\n"
        "3. 依据可靠性20%：结论能由题目上下文或可靠金融知识支持，不虚构数据、实体或依据；\n"
        "4. 相关性与表达10%：直接回答问题，含义明确且无自相矛盾。\n"
        "若核心结论错误，总分不得高于0.2；影响结论的虚构内容，总分不得高于0.3；"
        "空答、拒答或无关回答为0。问题只要求简短事实或结论时，答案简洁不应扣分；"
        "措辞不同但语义等价不应扣分。只返回一个JSON对象，不要Markdown、解释、分项分数或思考过程。"
        '格式必须为 {"score":0.0}，score为0到1之间的数字，最多保留两位小数。\n'
        f"问题：{question}\n候选答案：{candidate}"
    )
    payload = json.dumps(
        {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
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
    return str(body["choices"][0]["message"]["content"])


def judge_from_record(candidate: str, record: Mapping[str, Any]) -> str:
    url = os.environ["GSPO_JUDGE_URL"]
    return judge_completion(
        url,
        question=str(record.get("question", "")),
        candidate=candidate,
        model=os.environ.get("GSPO_JUDGE_SERVE_NAME", "deepseek-v4"),
        timeout=float(os.environ.get("GSPO_JUDGE_TIMEOUT", "180")),
        max_tokens=int(os.environ.get("GSPO_JUDGE_MAX_TOKENS", "64")),
    )
