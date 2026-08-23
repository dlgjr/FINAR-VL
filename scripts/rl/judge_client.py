"""OpenAI-compatible client for the fixed GSPO claim judge."""

from __future__ import annotations

import json
import os
import urllib.request
from typing import Any, Mapping


def judge_completion(
    judge_url: str,
    *,
    question: str,
    gold_claims: list[Any],
    reference: str,
    reference_mode: str,
    candidate: str,
    model: str = "qwen3-judge",
    timeout: float = 180.0,
) -> str:
    """Ask the local judge to return the strict claim-match JSON string."""

    if gold_claims:
        prompt = (
            "依据问题、标准主张和候选答案进行核对。只返回一个 JSON 对象，不要 Markdown、解释或思考过程。"
            'JSON 格式必须为 {"matched_claim_ids":["G1"],"wrong_claim_count":0}。'
            "matched_claim_ids 只能使用标准主张中的编号；遗漏标准主张不计入 wrong_claim_count；"
            "候选答案中错误、矛盾或回答错误对象的主张计入 wrong_claim_count。\n"
            f"问题：{question}\n标准主张：{json.dumps(gold_claims, ensure_ascii=False)}\n候选答案：{candidate}"
        )
    else:
        reference_block = f"\n参考答案：{reference}" if reference_mode == "reference" else ""
        prompt = (
            "你是严格的金融问答裁判。依据问题中给出的上下文和金融知识评估候选答案；"
            "若提供参考答案，还必须核对候选答案是否覆盖其关键结论。"
            "只返回一个 JSON 对象，不要 Markdown、解释或思考过程。"
            'JSON 格式必须为 {"score":0.0}，score 只能是 0 到 1 之间的数字：'
            "完全正确且完整为 1，部分正确按覆盖程度给分，错误、无关或无法由上下文支持为 0。\n"
            f"问题：{question}{reference_block}\n候选答案：{candidate}"
        )
    payload = json.dumps(
        {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.0,
            "top_p": 1.0,
            "max_tokens": 256,
            "response_format": {"type": "json_object"},
            "chat_template_kwargs": {"enable_thinking": False},
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
        gold_claims=list(record.get("gold_claim_details") or record.get("gold_claims", [])),
        reference=str(record.get("judge_reference", "")),
        reference_mode=str(record.get("judge_reference_mode", "question_only")),
        candidate=candidate,
        model=os.environ.get("GSPO_JUDGE_SERVE_NAME", "qwen3-judge"),
        timeout=float(os.environ.get("GSPO_JUDGE_TIMEOUT", "180")),
    )
