"""Pure reward functions shared by DSW tests and the DLC reward plugin.

The module deliberately has no dependency on Swift, vLLM, or a GPU service so
that parsing and scoring can be tested before a DLC submission.
"""

from __future__ import annotations

import json
import re
import unicodedata
from decimal import Decimal, InvalidOperation
from typing import Any, Callable, Iterable, Mapping, Sequence


_ANSWER_RE = re.compile(r"<answer>\s*(.*?)\s*</answer>", re.IGNORECASE | re.DOTALL)
_ANSWER_PREFIX_RE = re.compile(r"答案\s*[:：][ \t]*([^\r\n]*)")
_NUMBER_RE = re.compile(r"[-+]?(?:\d{1,3}(?:[,，]\d{3})+|\d+)(?:\.\d+)?(?:\s*(?:%|％|元|人民币|美元|\$|¥|￥|亿元|万元|万|亿))?", re.IGNORECASE)


def extract_last_answer(completion: Any) -> str | None:
    """Return the final non-empty complete answer block, or ``None``."""

    if completion is None:
        return None
    if isinstance(completion, Mapping):
        completion = completion.get("content", completion.get("text", ""))
    matches = _ANSWER_RE.findall(str(completion))
    if not matches:
        return None
    value = matches[-1].strip()
    return value or None


def extract_prefixed_answer(completion: Any) -> str | None:
    """Return text after the last ``答案：``/``答案:`` prefix.

    ``None`` means that no prefix exists; an empty string means the prefix is
    present but has no answer on the same line.
    """

    if completion is None:
        return None
    if isinstance(completion, Mapping):
        completion = completion.get("content", completion.get("text", ""))
    matches = _ANSWER_PREFIX_RE.findall(str(completion))
    return matches[-1].strip() if matches else None


def _fold_text(value: str) -> str:
    value = unicodedata.normalize("NFKC", str(value)).strip()
    value = value.replace("，", ",").replace("、", ",").replace("；", ";")
    return re.sub(r"\s+", " ", value)


def _unit(value: str) -> str:
    value = _fold_text(value).lower()
    if "%" in value or "％" in value:
        return "%"
    if any(token in value for token in ("美元", "$")):
        return "美元"
    if any(token in value for token in ("元", "人民币", "¥", "￥")):
        return "元"
    if "亿元" in value:
        return "亿元"
    if "万元" in value:
        return "万元"
    if "亿" in value:
        return "亿"
    if "万" in value:
        return "万"
    return ""


def normalize_numeric(value: str) -> tuple[float, str]:
    """Parse a number and its explicit unit, normalizing common formatting."""

    text = _fold_text(value).replace("$", "美元").replace("¥", "元").replace("￥", "元")
    match = re.search(r"[-+]?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?", text)
    if not match:
        raise ValueError(f"no numeric value: {value!r}")
    try:
        number = float(Decimal(match.group(0).replace(",", "")))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"invalid numeric value: {value!r}") from exc
    return number, _unit(text)


def _question_unit(question: str) -> str:
    return _unit(question or "")


def _split_atoms(answer: str, verifier_type: str) -> list[str]:
    text = _fold_text(answer)
    if verifier_type == "page_numbers":
        return list(dict.fromkeys(re.findall(r"\d+", text)))
    if verifier_type == "true_false":
        lowered = text.lower()
        if any(x in lowered for x in ("true", "yes", "是", "正确", "对")):
            return ["true"]
        if any(x in lowered for x in ("false", "no", "否", "错误", "错")):
            return ["false"]
        return []
    if verifier_type in {"single_choice", "multiple_choice", "choice"}:
        # Keep option labels and numeric labels, while ignoring prose around them.
        tokens = re.findall(r"(?<![A-Za-z])[A-H](?![A-Za-z])|(?<!\d)\d+(?!\d)", text.upper())
        return list(dict.fromkeys(tokens))
    pieces = re.split(r"[,;\n|/]+", text)
    return list(dict.fromkeys(piece.strip() for piece in pieces if piece.strip()))


def _numeric_atoms(value: str) -> list[str]:
    return list(dict.fromkeys(match.group(0) for match in _NUMBER_RE.finditer(_fold_text(value))))


def _numeric_match(pred: str, gold: str, question: str) -> bool:
    try:
        pred_number, pred_unit = normalize_numeric(pred)
        gold_number, gold_unit = normalize_numeric(gold)
    except ValueError:
        return False
    inherited = _question_unit(question)
    effective_pred_unit = pred_unit or inherited
    effective_gold_unit = gold_unit or inherited
    if gold_unit and not pred_unit and not inherited:
        return False
    if effective_pred_unit and effective_gold_unit and effective_pred_unit != effective_gold_unit:
        return False
    return abs(pred_number - gold_number) <= 0.01 + 1e-12


def score_programmatic_answer(
    completion: Any,
    gold_atoms: Sequence[str],
    verifier_type: str,
    question: str = "",
) -> float:
    """Score the last prefixed answer using set-Jaccard semantics."""

    answer = extract_prefixed_answer(completion)
    if answer is None:
        return -0.1
    if not answer or not gold_atoms:
        return 0.0
    if verifier_type in {"numeric", "number_or_free_text", "numeric_or_short_text"}:
        pred_atoms = _numeric_atoms(answer)
        gold = list(dict.fromkeys(str(x) for x in gold_atoms))
        if not pred_atoms:
            return 0.0
        matched = sum(any(_numeric_match(pred, expected, question) for expected in gold) for pred in pred_atoms)
        matched = min(matched, len(gold))
        union = len(set(pred_atoms)) + len(gold) - matched
        return matched / union if union else 0.0
    pred = set(_split_atoms(answer, verifier_type))
    gold = set(_split_atoms(";".join(map(str, gold_atoms)), verifier_type))
    if not pred or not gold:
        return 0.0
    return len(pred & gold) / len(pred | gold)


def parse_judge_result(result: Any, gold_claim_ids: Sequence[str]) -> tuple[float, dict[str, Any] | None, str | None]:
    try:
        payload = json.loads(result) if isinstance(result, str) else result
    except (TypeError, json.JSONDecodeError):
        return 0.0, None, "invalid_json"
    if not isinstance(payload, dict) or not isinstance(payload.get("matched_claim_ids"), list):
        return 0.0, None, "invalid_schema"
    wrong = payload.get("wrong_claim_count")
    if isinstance(wrong, bool) or not isinstance(wrong, int) or wrong < 0:
        return 0.0, None, "invalid_wrong_claim_count"
    known = set(map(str, gold_claim_ids))
    matched = list(dict.fromkeys(map(str, payload["matched_claim_ids"])))
    if any(claim_id not in known for claim_id in matched):
        return 0.0, None, "unknown_claim_id"
    count = len(matched)
    denominator = count + (len(known) - count) + wrong
    return (count / denominator if denominator else 0.0), {"matched_claim_ids": matched, "wrong_claim_count": wrong}, None


def score_judge_result(result: Any, gold_claim_ids: Sequence[str]) -> float:
    return parse_judge_result(result, gold_claim_ids)[0]


class MixedReward:
    """Single reward-plugin interface for structured and model-judged samples."""

    def __init__(self, judge: Callable[[str, Mapping[str, Any]], Any] | None = None):
        self.judge = judge
        self.errors: list[dict[str, Any]] = []

    def __call__(self, completions: Sequence[Any], records: Sequence[Mapping[str, Any]] | None = None, **kwargs: Any) -> list[float]:
        records = list(records or kwargs.get("data", kwargs.get("prompts_metadata", [])))
        rewards: list[float] = []
        for index, completion in enumerate(completions):
            record = records[index] if index < len(records) else {}
            if record.get("verifier_type") == "model_judge":
                answer = extract_prefixed_answer(completion)
                if answer is None:
                    rewards.append(-0.1)
                elif not answer or self.judge is None:
                    rewards.append(0.0)
                else:
                    try:
                        raw = self.judge(answer, record)
                        score, _, error = parse_judge_result(raw, record.get("gold_claims", []))
                        if isinstance(record, dict):
                            record["_judge_json"] = raw
                        if error:
                            self.errors.append({"sample_id": record.get("sample_id"), "error": error})
                        rewards.append(score)
                    except Exception as error:
                        self.errors.append({"sample_id": record.get("sample_id"), "error": str(error)})
                        rewards.append(0.0)
            else:
                answer = extract_prefixed_answer(completion)
                if isinstance(record, dict):
                    record["_parser_result"] = {"answer": answer, "verifier_type": record.get("verifier_type", "")}
                rewards.append(score_programmatic_answer(completion, record.get("gold_atoms", []), record.get("verifier_type", ""), record.get("question", "")))
        return rewards
