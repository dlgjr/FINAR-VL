"""Pure reward functions shared by DSW tests and the DLC reward plugin."""

from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any, Callable, Mapping, Sequence


_ANSWER_RE = re.compile(r"<answer>\s*(.*?)\s*</answer>", re.IGNORECASE | re.DOTALL)
_ANSWER_PREFIX_RE = re.compile(r"答案\s*[:：][ \t]*([^\r\n]*)")
_NUMBER_TOKEN_RE = re.compile(
    r"(?P<prefix>[\$￥¥€£])?\s*"
    r"(?P<number>[-+]?(?:(?:\d{1,3}(?:[,，]\d{3})+|\d+)(?:\.\d+)?|\.\d+)(?:[eE][-+]?\d+)?)\s*"
    r"(?P<suffix>人民币千亿元|人民币百亿元|人民币十亿元|人民币亿元|人民币千万元|人民币百万元|人民币十万元|人民币万元|人民币千元|"
    r"billion美元|million美元|thousand美元|billion元|million元|thousand元|"
    r"千亿美元|百亿美元|十亿美元|亿美元|千万美元|百万美元|十万美元|万美元|"
    r"万亿元|千亿元|百亿元|十亿元|亿元|千万元|百万元|十万元|万元|千元|"
    r"千亿|百亿|十亿|亿|千万|百万|十万|万|千|港元|人民币|美元|元|HKD|USD|CNY|RMB|"
    r"percentage\s+points?|个百分点|百分点|billion|million|thousand|[%％]|倍|家|项|个|点|万|亿)?",
    re.IGNORECASE,
)
_EDGE_PUNCTUATION = " \t\r\n.,;:!?，。；：！？、\"'“”‘’`()[]{}<>《》"


@dataclass(frozen=True)
class NumericValue:
    value: Decimal
    unit: str
    dimension: str
    factor: Decimal

    @property
    def base_value(self) -> Decimal:
        return self.value * self.factor


def extract_last_answer(completion: Any) -> str | None:
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


def _unit_descriptor(prefix: str, suffix: str) -> tuple[str, str, Decimal]:
    prefix = _fold_text(prefix or "")
    suffix = _fold_text(suffix or "").lower()
    currency = {
        "$": ("美元", "USD"),
        "usd": ("美元", "USD"),
        "美元": ("美元", "USD"),
        "￥": ("元", "CNY"),
        "¥": ("元", "CNY"),
        "cny": ("元", "CNY"),
        "rmb": ("元", "CNY"),
        "人民币": ("元", "CNY"),
        "元": ("元", "CNY"),
        "港元": ("港元", "HKD"),
        "hkd": ("港元", "HKD"),
    }
    direct = {
        "万亿元": ("万亿元", "CNY", Decimal("1e12")),
        "人民币千亿元": ("千亿元", "CNY", Decimal("1e11")),
        "人民币百亿元": ("百亿元", "CNY", Decimal("1e10")),
        "人民币十亿元": ("十亿元", "CNY", Decimal("1e9")),
        "人民币亿元": ("亿元", "CNY", Decimal("1e8")),
        "人民币千万元": ("千万元", "CNY", Decimal("1e7")),
        "人民币百万元": ("百万元", "CNY", Decimal("1e6")),
        "人民币十万元": ("十万元", "CNY", Decimal("1e5")),
        "人民币万元": ("万元", "CNY", Decimal("1e4")),
        "人民币千元": ("千元", "CNY", Decimal("1e3")),
        "千亿元": ("千亿元", "CNY", Decimal("1e11")),
        "百亿元": ("百亿元", "CNY", Decimal("1e10")),
        "十亿元": ("十亿元", "CNY", Decimal("1e9")),
        "亿元": ("亿元", "CNY", Decimal("1e8")),
        "千万元": ("千万元", "CNY", Decimal("1e7")),
        "百万元": ("百万元", "CNY", Decimal("1e6")),
        "十万元": ("十万元", "CNY", Decimal("1e5")),
        "万元": ("万元", "CNY", Decimal("1e4")),
        "千元": ("千元", "CNY", Decimal("1e3")),
        "千亿美元": ("千亿美元", "USD", Decimal("1e11")),
        "百亿美元": ("百亿美元", "USD", Decimal("1e10")),
        "十亿美元": ("十亿美元", "USD", Decimal("1e9")),
        "亿美元": ("亿美元", "USD", Decimal("1e8")),
        "千万美元": ("千万美元", "USD", Decimal("1e7")),
        "百万美元": ("百万美元", "USD", Decimal("1e6")),
        "十万美元": ("十万美元", "USD", Decimal("1e5")),
        "万美元": ("万美元", "USD", Decimal("1e4")),
        "thousand美元": ("thousand美元", "USD", Decimal("1e3")),
        "million美元": ("million美元", "USD", Decimal("1e6")),
        "billion美元": ("billion美元", "USD", Decimal("1e9")),
        "thousand元": ("thousand元", "CNY", Decimal("1e3")),
        "million元": ("million元", "CNY", Decimal("1e6")),
        "billion元": ("billion元", "CNY", Decimal("1e9")),
        "%": ("%", "percent", Decimal("0.01")),
        "个百分点": ("百分点", "percentage_point", Decimal(1)),
        "百分点": ("百分点", "percentage_point", Decimal(1)),
        "percentage point": ("百分点", "percentage_point", Decimal(1)),
        "percentage points": ("百分点", "percentage_point", Decimal(1)),
        "倍": ("倍", "multiple", Decimal(1)),
        "count": ("count", "count", Decimal(1)),
        "家": ("count", "count", Decimal(1)),
        "项": ("count", "count", Decimal(1)),
        "个": ("count", "count", Decimal(1)),
        "点": ("点", "point", Decimal(1)),
        "万": ("万", "scalar", Decimal("1e4")),
        "千": ("千", "scalar", Decimal("1e3")),
        "十万": ("十万", "scalar", Decimal("1e5")),
        "百万": ("百万", "scalar", Decimal("1e6")),
        "千万": ("千万", "scalar", Decimal("1e7")),
        "十亿": ("十亿", "scalar", Decimal("1e9")),
        "百亿": ("百亿", "scalar", Decimal("1e10")),
        "千亿": ("千亿", "scalar", Decimal("1e11")),
        "亿": ("亿", "scalar", Decimal("1e8")),
        "thousand": ("thousand", "scalar", Decimal("1e3")),
        "million": ("million", "scalar", Decimal("1e6")),
        "billion": ("billion", "scalar", Decimal("1e9")),
    }
    if suffix in direct:
        label, dimension, factor = direct[suffix]
        if prefix in currency and dimension == "scalar":
            base_label, base_dimension = currency[prefix]
            return f"{suffix}{base_label}", base_dimension, factor
        return label, dimension, factor
    if suffix in currency:
        label, dimension = currency[suffix]
        return label, dimension, Decimal(1)
    if prefix in currency:
        label, dimension = currency[prefix]
        return label, dimension, Decimal(1)
    return "", "scalar", Decimal(1)


def _parse_numeric(value: str) -> NumericValue:
    text = _fold_text(value)
    match = _NUMBER_TOKEN_RE.search(text)
    if not match:
        raise ValueError(f"no numeric value: {value!r}")
    raw = match.group("number").replace(",", "")
    try:
        number = Decimal(raw)
    except InvalidOperation as exc:
        raise ValueError(f"invalid numeric value: {value!r}") from exc
    unit, dimension, factor = _unit_descriptor(match.group("prefix") or "", match.group("suffix") or "")
    return NumericValue(number, unit, dimension, factor)


def normalize_numeric(value: str) -> tuple[float, str]:
    parsed = _parse_numeric(value)
    return float(parsed.value), parsed.unit


def _split_atoms(answer: str, verifier_type: str) -> list[str]:
    text = _fold_text(answer)
    if verifier_type == "page_numbers":
        return list(dict.fromkeys(re.findall(r"\d+", text)))
    if verifier_type == "true_false":
        normalized = text.casefold().strip(_EDGE_PUNCTUATION)
        truthy = {"true", "yes", "是", "正确", "对", "a"}
        falsy = {"false", "no", "否", "错误", "错", "不正确", "不是", "不对", "b"}
        if normalized in truthy:
            return ["true"]
        if normalized in falsy:
            return ["false"]
        return []
    if verifier_type in {"single_choice", "multiple_choice", "choice"}:
        compact = re.sub(r"[\s,;，；、/|]+", "", text.upper())
        if re.fullmatch(r"[A-H]+", compact):
            return list(dict.fromkeys(compact))
        tokens = re.findall(r"(?<![A-Za-z])[A-H](?![A-Za-z])|(?<!\d)\d+(?!\d)", text.upper())
        return list(dict.fromkeys(tokens))
    pieces = re.split(r"[,;\n|/]+", text)
    return list(dict.fromkeys(piece.strip() for piece in pieces if piece.strip()))


def _numeric_atoms(value: str) -> list[str]:
    # Preserve Chinese list punctuation as a separator before NFKC turns it into
    # an ASCII comma, which would otherwise be mistaken for a thousands separator.
    text = str(value).replace("，", "\n").replace("、", "\n")
    text = unicodedata.normalize("NFKC", text)
    return list(dict.fromkeys(match.group(0).strip() for match in _NUMBER_TOKEN_RE.finditer(text)))


def numeric_gold_from_text(value: str) -> list[dict[str, str]]:
    atoms = _numeric_atoms(value)
    if not atoms:
        raise ValueError(f"no numeric gold in {value!r}")
    parsed = _parse_numeric(atoms[-1])
    return [{"value": str(parsed.value), "unit": parsed.unit}]


def _structured_numeric(value: Mapping[str, Any]) -> NumericValue:
    if "value" not in value:
        raise ValueError("numeric gold missing value")
    try:
        number = Decimal(str(value["value"]))
    except InvalidOperation as exc:
        raise ValueError("invalid numeric gold value") from exc
    unit = str(value.get("unit") or "")
    canonical = {
        "": ("scalar", Decimal(1)),
        "%": ("percent", Decimal("0.01")),
        "百分点": ("percentage_point", Decimal(1)),
        "元": ("CNY", Decimal(1)),
        "万元": ("CNY", Decimal("1e4")),
        "千元": ("CNY", Decimal("1e3")),
        "十万元": ("CNY", Decimal("1e5")),
        "百万元": ("CNY", Decimal("1e6")),
        "千万元": ("CNY", Decimal("1e7")),
        "亿元": ("CNY", Decimal("1e8")),
        "十亿元": ("CNY", Decimal("1e9")),
        "百亿元": ("CNY", Decimal("1e10")),
        "千亿元": ("CNY", Decimal("1e11")),
        "万亿元": ("CNY", Decimal("1e12")),
        "美元": ("USD", Decimal(1)),
        "万美元": ("USD", Decimal("1e4")),
        "十万美元": ("USD", Decimal("1e5")),
        "百万美元": ("USD", Decimal("1e6")),
        "千万美元": ("USD", Decimal("1e7")),
        "亿美元": ("USD", Decimal("1e8")),
        "十亿美元": ("USD", Decimal("1e9")),
        "百亿美元": ("USD", Decimal("1e10")),
        "千亿美元": ("USD", Decimal("1e11")),
        "港元": ("HKD", Decimal(1)),
        "count": ("count", Decimal(1)),
        "倍": ("multiple", Decimal(1)),
        "点": ("point", Decimal(1)),
        "万": ("scalar", Decimal("1e4")),
        "千": ("scalar", Decimal("1e3")),
        "十万": ("scalar", Decimal("1e5")),
        "百万": ("scalar", Decimal("1e6")),
        "千万": ("scalar", Decimal("1e7")),
        "亿": ("scalar", Decimal("1e8")),
        "十亿": ("scalar", Decimal("1e9")),
        "百亿": ("scalar", Decimal("1e10")),
        "千亿": ("scalar", Decimal("1e11")),
        "thousand": ("scalar", Decimal("1e3")),
        "million": ("scalar", Decimal("1e6")),
        "billion": ("scalar", Decimal("1e9")),
        "thousand美元": ("USD", Decimal("1e3")),
        "million美元": ("USD", Decimal("1e6")),
        "billion美元": ("USD", Decimal("1e9")),
        "thousand元": ("CNY", Decimal("1e3")),
        "million元": ("CNY", Decimal("1e6")),
        "billion元": ("CNY", Decimal("1e9")),
    }
    if unit not in canonical:
        raise ValueError(f"invalid numeric gold unit: {unit!r}")
    dimension, factor = canonical[unit]
    return NumericValue(number, unit, dimension, factor)


def _decimal_setting(spec: Mapping[str, Any] | None, key: str) -> Decimal | None:
    if not spec or spec.get(key) in (None, ""):
        return None
    try:
        value = Decimal(str(spec[key]))
    except InvalidOperation as exc:
        raise ValueError(f"invalid {key}: {spec[key]!r}") from exc
    if value < 0:
        raise ValueError(f"negative {key}: {value}")
    return value


def _numeric_tolerance(gold: NumericValue, spec: Mapping[str, Any] | None = None) -> tuple[Decimal, Decimal]:
    abs_override = _decimal_setting(spec, "abs_tol")
    rel_override = _decimal_setting(spec, "rel_tol")
    if gold.dimension == "count":
        default_abs, default_rel = Decimal(0), Decimal(0)
    elif gold.dimension == "percent":
        default_abs, default_rel = Decimal("1e-5"), Decimal("1e-6")
    elif gold.dimension in {"percentage_point", "multiple", "point"}:
        default_abs, default_rel = Decimal("1e-6"), Decimal("1e-6")
    elif gold.dimension in {"CNY", "USD", "HKD"}:
        default_abs, default_rel = Decimal("0.01"), Decimal("1e-8")
    elif abs(gold.base_value) < 1:
        default_abs, default_rel = Decimal("1e-4"), Decimal("1e-5")
    else:
        default_abs, default_rel = Decimal("1e-4"), Decimal("1e-8")
    return abs_override if abs_override is not None else default_abs, rel_override if rel_override is not None else default_rel


def _numeric_match(pred: NumericValue, gold: NumericValue, spec: Mapping[str, Any] | None = None) -> bool:
    abs_tol, rel_tol = _numeric_tolerance(gold, spec)
    if pred.dimension == "scalar" and pred.unit == "":
        targets = {gold.base_value, gold.value}
        for target in targets:
            target_abs_tol = abs_tol if target == gold.base_value else abs_tol / gold.factor
            delta = abs(pred.value - target)
            if delta <= target_abs_tol or delta <= abs(target) * rel_tol:
                return True
        return False
    same_dimension = pred.dimension == gold.dimension
    if not same_dimension:
        return False
    pred_value = pred.base_value
    delta = abs(pred_value - gold.base_value)
    if delta <= abs_tol:
        return True
    return delta <= abs(gold.base_value) * rel_tol


def score_programmatic_answer(
    completion: Any,
    gold_atoms: Sequence[str],
    verifier_type: str,
    question: str = "",
    gold_numeric: Sequence[Mapping[str, Any]] | None = None,
) -> float:
    """Score the last prefixed answer using deterministic verifier semantics."""

    del question
    answer = extract_prefixed_answer(completion)
    if answer is None:
        return -0.1
    if not answer:
        return 0.0
    if verifier_type in {
        "numeric",
        "numeric_final",
        "composite_numeric",
    }:
        pred_atoms = _numeric_atoms(answer)
        if not pred_atoms:
            return 0.0
        try:
            pred_values = [_parse_numeric(atom) for atom in pred_atoms]
            if gold_numeric:
                gold_specs = []
                for item in gold_numeric:
                    primary = _structured_numeric(item)
                    aliases = []
                    for alias in item.get("aliases", []) or []:
                        if not isinstance(alias, Mapping):
                            raise ValueError("numeric alias is not an object")
                        aliases.append((alias, _structured_numeric(alias)))
                    gold_specs.append((item, primary, aliases))
            else:
                gold_specs = [({}, _parse_numeric(str(atom)), []) for atom in gold_atoms]
        except (TypeError, ValueError):
            return 0.0
        if not gold_specs:
            return 0.0
        matched_gold: set[int] = set()
        matched_pred = 0
        for pred in pred_values:
            for index, (spec, gold, aliases) in enumerate(gold_specs):
                if index in matched_gold:
                    continue
                candidates = [(spec, gold), *aliases]
                if any(_numeric_match(pred, candidate, candidate_spec) for candidate_spec, candidate in candidates):
                    matched_gold.add(index)
                    matched_pred += 1
                    break
        union = len(pred_values) + len(gold_specs) - matched_pred
        return matched_pred / union if union else 0.0
    if verifier_type not in {"page_numbers", "true_false", "single_choice", "multiple_choice", "choice"}:
        return 0.0
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
    if not isinstance(payload, dict):
        return 0.0, None, "invalid_schema"
    if not gold_claim_ids and "score" in payload:
        score = payload.get("score")
        if isinstance(score, bool) or not isinstance(score, (int, float)) or not 0 <= float(score) <= 1:
            return 0.0, None, "invalid_score"
        return float(score), {"score": float(score)}, None
    if not isinstance(payload.get("matched_claim_ids"), list):
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
    def __init__(self, judge: Callable[[str, Mapping[str, Any]], Any] | None = None):
        self.judge = judge
        self.errors: list[dict[str, Any]] = []

    def __call__(self, completions: Sequence[Any], records: Sequence[Mapping[str, Any]] | None = None, **kwargs: Any) -> list[float]:
        records = list(records or kwargs.get("data", kwargs.get("prompts_metadata", [])))
        rewards: list[float] = []
        for index, completion in enumerate(completions):
            record = records[index] if index < len(records) else {}
            if record.get("reward_type") == "judge" or record.get("verifier_type") == "model_judge":
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
                rewards.append(
                    score_programmatic_answer(
                        completion,
                        record.get("gold_atoms", []),
                        record.get("verifier_type", ""),
                        record.get("question", ""),
                        record.get("gold_numeric", []),
                    )
                )
        return rewards
