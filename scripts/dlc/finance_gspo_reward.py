"""Deterministic and Qwen-235B reward functions for finance GSPO."""

import json
import os
import re
import urllib.request
from concurrent.futures import ThreadPoolExecutor

from swift.rewards import ORM, orms


def _at(value, index, default=""):
    if isinstance(value, (list, tuple)):
        return value[index] if index < len(value) else default
    return default if value is None else value


def _completion_text(value):
    if isinstance(value, str):
        return value
    if isinstance(value, list) and value and isinstance(value[-1], dict):
        return str(value[-1].get("content", ""))
    return str(value)


def _letters(text):
    text = str(text).strip()
    matches = []
    for pattern in (
        re.compile(r"(?i)(?:最终答案|答案|answer)\s*[:：]?\s*([A-F](?:\s*[,，、/]\s*[A-F])*)\b"),
        re.compile(r"(?i)(?:最终答案|答案|answer)\s*[:：]?\s*([A-F]{1,6})\b"),
        re.compile(r"(?i)^\s*([A-F](?:\s*[,，、/]\s*[A-F])*)\s*[。.]?\s*$"),
        re.compile(r"(?i)^\s*([A-F]{1,6})\s*[。.]?\s*$"),
    ):
        for match in pattern.finditer(text):
            matches.append((match.start(), match.group(1)))
    if not matches:
        return None
    raw = max(matches, key=lambda item: item[0])[1]
    return "".join(sorted(set(re.findall(r"[A-F]", raw.upper()))))


def _true_false(text):
    text = str(text).strip()
    matches = list(
        re.finditer(
            r"(?i)(?:最终答案|答案|answer)\s*[:：]?\s*(正确|错误|对|错|true|false)",
            text,
        )
    )
    value = matches[-1].group(1).lower() if matches else text.splitlines()[-1].strip().lower()
    if value in {"正确", "对", "true", "a"}:
        return "正确"
    if value in {"错误", "错", "false", "b"}:
        return "错误"
    return None


def _normalize(text):
    return re.sub(r"\s+", " ", str(text).strip().lower())


class FinanceRuleReward(ORM):
    def __call__(self, completions, **kwargs):
        rewards = []
        for index, completion in enumerate(completions):
            candidate = _completion_text(completion)
            subtype = str(_at(kwargs.get("reward_subtype"), index))
            gold = str(_at(kwargs.get("solution"), index))
            gold_text = str(_at(kwargs.get("gold_option_text"), index))

            if subtype in {"single_choice", "multiple_choice"}:
                predicted = _letters(candidate)
                correct = predicted == "".join(sorted(set(gold.upper())))
                if not correct and subtype == "single_choice" and gold_text:
                    correct = _normalize(gold_text) in _normalize(candidate)
            elif subtype == "true_false":
                predicted = _true_false(candidate)
                if predicted is None:
                    label = _letters(candidate)
                    predicted = "正确" if label == "A" else "错误" if label == "B" else None
                correct = predicted == gold
            else:
                correct = _normalize(candidate) == _normalize(gold)

            rewards.append(1.0 if correct else 0.0)

        print("[FINANCE_RULE_REWARD]", rewards, flush=True)
        return rewards


def _judge_one(item):
    index, question, reference, candidate = item
    urls = [url.strip() for url in os.environ["REWARD_URLS"].split(",") if url.strip()]
    url = urls[index % len(urls)]

    prompt = f"""你是金融领域强化学习奖励模型。根据问题和参考答案评价候选答案的金融知识正确性。

评分标准：
1.0：核心结论正确，关键事实、计算、机制或规则完整。
0.75：核心结论正确，存在轻微遗漏或少量无关内容。
0.5：部分正确，但存在重要遗漏、含混或局部错误。
0.25：只有少量相关内容，核心回答基本错误。
0.0：错误、答非所问，或与参考答案的关键结论冲突。

允许与参考答案采用不同表述。重点判断金融概念、因果关系、计算结论、监管要求和专业边界是否正确。
只返回 JSON：{{"score": 0.0}}

问题：
{question}

参考答案：
{reference}

候选答案：
{candidate}
"""

    payload = json.dumps(
        {
            "model": os.environ.get("REWARD_SERVE_NAME", "qwen235-reward"),
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.0,
            "max_tokens": 64,
            "response_format": {"type": "json_object"},
            "chat_template_kwargs": {"enable_thinking": False},
        },
        ensure_ascii=False,
    ).encode("utf-8")

    request = urllib.request.Request(
        url.rstrip("/") + "/v1/chat/completions",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(
            request, timeout=float(os.environ.get("REWARD_TIMEOUT", "300"))
        ) as response:
            content = json.loads(response.read().decode("utf-8"))["choices"][0]["message"]["content"]
        try:
            score = float(json.loads(content)["score"])
        except Exception:
            score = float(re.search(r'"?score"?\s*:\s*([0-9.]+)', content).group(1))
        return max(0.0, min(1.0, score))
    except Exception as error:
        print("[FINANCE_JUDGE_ERROR]", url, repr(error), flush=True)
        return 0.0


class FinanceJudgeReward(ORM):
    def __call__(self, completions, **kwargs):
        items = [
            (
                index,
                str(_at(kwargs.get("question"), index)),
                str(_at(kwargs.get("solution"), index)),
                _completion_text(completion),
            )
            for index, completion in enumerate(completions)
        ]
        with ThreadPoolExecutor(
            max_workers=int(os.environ.get("REWARD_CONCURRENCY", "4"))
        ) as pool:
            rewards = list(pool.map(_judge_one, items))
        print("[FINANCE_JUDGE_REWARD]", rewards, flush=True)
        return rewards


orms["finance_rule"] = FinanceRuleReward
orms["finance_judge"] = FinanceJudgeReward
