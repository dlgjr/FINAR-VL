"""Deterministic process-grounding verifier for FINAR-VL Reasoning RL.

The verifier is deliberately conservative. It labels and localizes only
process facts that can be proved from hard construction-time constraints:

1. an explicit arithmetic equation is numerically inconsistent;
2. an explicitly assigned evidence value contradicts a hidden verifier-only
   Finance World fact;
3. an explicitly cited page for that fact contradicts the gold evidence page.

Anything unsupported or ambiguous is UNKNOWN rather than a failure. Terminal
answer correctness is kept separate from these process labels so the trainer
can assign answer and step credit independently. The module can be used both
from the GSPO reward path and as a standalone JSONL auditor.
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import unicodedata
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Mapping, Sequence


NUMERIC_VERIFIERS = {"numeric", "numeric_final", "composite_numeric"}
_OPERATOR_RE = re.compile(r"[+\-*/×÷]")
_NUMBER_RE = re.compile(
    r"[-+]?(?:(?:\d{1,3}(?:[,，]\d{3})+|\d+)(?:\.\d+)?|\.\d+)(?:[eE][-+]?\d+)?"
)
_ASSIGN_RE = re.compile(
    r"(?:=|＝|为|是|[:：])\s*"
    r"(?P<number>[-+]?(?:(?:\d{1,3}(?:[,，]\d{3})+|\d+)(?:\.\d+)?|\.\d+)(?:[eE][-+]?\d+)?)"
    r"\s*(?P<unit>%|％|百分点|亿元|万元|元|亿美元|万美元|美元|倍|点)?"
)
_PAGE_RE = re.compile(r"第\s*(\d+)\s*页")
_TRAILING_PAGE_RE = re.compile(r"(?:page|p\.?)[\s:#-]*(\d+)", re.IGNORECASE)
_PERCEPTION_RE = re.compile(
    r"<perception(?:\s+page\s*=\s*[\"']?(?P<page>\d+)[\"']?)?\s*>(?P<body>.*?)</perception>",
    re.IGNORECASE | re.DOTALL,
)
_THINK_RE = re.compile(r"<think>(.*?)</think>", re.IGNORECASE | re.DOTALL)
_ANSWER_TAG_RE = re.compile(r"<answer>(.*?)</answer>", re.IGNORECASE | re.DOTALL)
_ANSWER_PREFIX_RE = re.compile(
    r"(?:最终答案|答案|最终结果|结论|Final\\s+Answer|Answer)\\s*[:：]\\s*([^\\r\\n]*)",
    re.IGNORECASE,
)


def _completion_text(completion: Any) -> str:
    if isinstance(completion, Mapping):
        return str(completion.get("content", completion.get("text", "")))
    return str(completion)


def _decimal(value: Any) -> Decimal | None:
    if value in (None, ""):
        return None
    try:
        return Decimal(str(value).replace(",", "").replace("，", ""))
    except (InvalidOperation, ValueError):
        return None


def _eval_arithmetic(expression: str) -> Decimal | None:
    text = unicodedata.normalize("NFKC", expression)
    text = text.replace("×", "*").replace("÷", "/").replace("−", "-").replace("–", "-")
    text = text.replace(",", "").replace("，", "")
    text = text.strip().strip("$")
    text = re.sub(r"^\s*(?:[-*]|\d+[.)])\s*", "", text)
    if ":" in text:
        text = text.rsplit(":", 1)[-1].strip()
    if "：" in text:
        text = text.rsplit("：", 1)[-1].strip()
    text = re.sub(
        r"(?<![\w.])(\d+(?:\.\d+)?|\.\d+)\s*[%％]",
        r"(\1/100)",
        text,
    )
    if not text or len(text) > 256 or not _OPERATOR_RE.search(text):
        return None
    if re.search(r"[A-Za-z_\u4e00-\u9fff￥¥€£]", text):
        return None

    try:
        root = ast.parse(text, mode="eval")
    except SyntaxError:
        return None

    def visit(node: ast.AST) -> Decimal:
        if isinstance(node, ast.Expression):
            return visit(node.body)
        if (
            isinstance(node, ast.Constant)
            and not isinstance(node.value, bool)
            and isinstance(node.value, (int, float))
        ):
            return Decimal(str(node.value))
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
            value = visit(node.operand)
            return value if isinstance(node.op, ast.UAdd) else -value
        if isinstance(node, ast.BinOp) and isinstance(
            node.op, (ast.Add, ast.Sub, ast.Mult, ast.Div)
        ):
            left, right = visit(node.left), visit(node.right)
            if isinstance(node.op, ast.Add):
                return left + right
            if isinstance(node.op, ast.Sub):
                return left - right
            if isinstance(node.op, ast.Mult):
                return left * right
            if right == 0:
                raise ZeroDivisionError
            return left / right
        raise ValueError("unsupported arithmetic syntax")

    try:
        return visit(root)
    except (InvalidOperation, ValueError, ZeroDivisionError):
        return None


def _rhs_numeric(rhs: str) -> list[tuple[Decimal, Decimal]] | None:
    text = unicodedata.normalize("NFKC", rhs).strip()
    if _OPERATOR_RE.search(text.lstrip("+-")):
        return None
    match = _NUMBER_RE.search(text)
    if not match:
        return None

    value = _decimal(match.group(0))
    if value is None:
        return None
    tail = text[match.end() :].lstrip()
    percent = tail.startswith("%") or tail.startswith("％")

    raw = match.group(0).replace(",", "").replace("，", "")
    mantissa = re.split(r"[eE]", raw, maxsplit=1)[0]
    decimals = len(mantissa.split(".", 1)[1]) if "." in mantissa else 0
    quantum = Decimal(1).scaleb(-decimals)
    display = (value, quantum / Decimal(2) + Decimal("1e-12"))
    if not percent:
        return [display]

    # Financial CoTs use both conventions:
    #   (120-100)/100 = 20%        -> ratio 0.2
    #   (120-100)/100*100 = 20%    -> display value 20
    # Accept either representation to avoid false vetoes.
    base = (
        value / Decimal(100),
        quantum / Decimal(200) + Decimal("1e-12"),
    )
    return [display, base]


def _arithmetic_checks(text: str) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    char_offset = 0
    for line_number, raw_line in enumerate(text.splitlines(keepends=True), 1):
        visible_line = raw_line.rstrip("\r\n")
        line = visible_line.replace("＝", "=")
        line_start = char_offset
        line_end = char_offset + len(visible_line)
        char_offset += len(raw_line)
        if "=" not in line:
            continue
        parts = line.split("=")
        for index in range(len(parts) - 1):
            lhs = parts[index].strip()
            rhs = parts[index + 1].strip()
            computed = _eval_arithmetic(lhs)
            targets = _rhs_numeric(rhs)
            if computed is None or targets is None:
                continue
            ok = any(abs(computed - expected) <= tolerance for expected, tolerance in targets)
            checks.append(
                {
                    "kind": "arithmetic",
                    "line": line_number,
                    "char_start": line_start,
                    "char_end": line_end,
                    "lhs": lhs,
                    "rhs": rhs,
                    "computed": str(computed),
                    "expected_candidates": [str(expected) for expected, _ in targets],
                    "tolerances": [str(tolerance) for _, tolerance in targets],
                    "ok": bool(ok),
                }
            )
    return checks


def _construction(record: Mapping[str, Any]) -> Mapping[str, Any]:
    metadata = record.get("metadata")
    if not isinstance(metadata, Mapping):
        return {}
    construction = metadata.get("construction")
    return construction if isinstance(construction, Mapping) else {}


def process_constraints(record: Mapping[str, Any]) -> dict[str, Any]:
    """Expose the hard constraints carried by Reasoning RL construction metadata."""

    metadata = record.get("metadata")
    metadata = metadata if isinstance(metadata, Mapping) else {}
    construction = _construction(record)

    raw_facts = construction.get("evidence_facts")
    facts = [
        dict(item)
        for item in raw_facts
        if isinstance(raw_facts, Sequence)
        and not isinstance(raw_facts, (str, bytes))
        and isinstance(item, Mapping)
    ] if isinstance(raw_facts, Sequence) and not isinstance(raw_facts, (str, bytes)) else []

    evidence_ids = construction.get("required_evidence_ids") or metadata.get("evidence_ids") or []
    visual_ids = construction.get("visual_fact_ids") or []
    if not isinstance(evidence_ids, Sequence) or isinstance(evidence_ids, (str, bytes)):
        evidence_ids = []
    if not isinstance(visual_ids, Sequence) or isinstance(visual_ids, (str, bytes)):
        visual_ids = []

    required_ids = {str(value) for value in evidence_ids}
    visual_set = {str(value) for value in visual_ids}
    if required_ids:
        facts = [fact for fact in facts if str(fact.get("id", "")) in required_ids]

    return {
        "program": str(metadata.get("program") or ""),
        "operation_count": metadata.get("operation_count"),
        "required_evidence_ids": sorted(required_ids),
        "visual_fact_ids": sorted(visual_set),
        "vision_required": bool(required_ids & visual_set),
        "evidence_facts": facts,
        "images_present": bool(record.get("images")),
        "builder": str(construction.get("builder") or ""),
    }


def _fact_identity_ambiguous(fact: Mapping[str, Any], facts: Sequence[Mapping[str, Any]]) -> bool:
    metric = str(fact.get("metric") or "").strip()
    period = str(fact.get("period") or "").strip()
    if not metric or not period:
        return True
    peers = [
        item
        for item in facts
        if str(item.get("metric") or "").strip() == metric
        and str(item.get("period") or "").strip() == period
    ]
    entities = {str(item.get("entity") or "").strip() for item in peers}
    return len(peers) > 1 and len(entities) > 1


def _line_matches_fact(
    line: str,
    fact: Mapping[str, Any],
    facts: Sequence[Mapping[str, Any]],
) -> bool:
    metric = str(fact.get("metric") or "").strip()
    period = str(fact.get("period") or "").strip()
    entity = str(fact.get("entity") or "").strip()

    if not metric or metric not in line:
        return False
    if period and period not in line:
        return False
    if _fact_identity_ambiguous(fact, facts) and entity and entity not in line:
        return False
    return True


def _assignment_after_fact(line: str, fact: Mapping[str, Any]) -> re.Match[str] | None:
    anchors = []
    for key in ("entity", "period", "metric"):
        token = str(fact.get(key) or "").strip()
        if token:
            pos = line.find(token)
            if pos >= 0:
                anchors.append(pos + len(token))
    if not anchors:
        return None
    tail = line[max(anchors) : max(anchors) + 100]
    return _ASSIGN_RE.search(tail)


def _unit_compatible(candidate_unit: str, fact_unit: str) -> bool:
    candidate_unit = candidate_unit.replace("％", "%").strip()
    fact_unit = fact_unit.replace("％", "%").strip()
    if not candidate_unit or not fact_unit:
        return True
    aliases = {
        "%": {"%"},
        "百分点": {"百分点"},
    }
    return candidate_unit in aliases.get(fact_unit, {fact_unit})


def _display_tolerance(raw_number: str, gold: Decimal) -> Decimal:
    raw = raw_number.replace(",", "").replace("，", "")
    mantissa = re.split(r"[eE]", raw, maxsplit=1)[0]
    decimals = len(mantissa.split(".", 1)[1]) if "." in mantissa else 0
    rounding = Decimal(1).scaleb(-decimals) / Decimal(2)
    relative = abs(gold) * Decimal("1e-10")
    return max(rounding, relative, Decimal("1e-12"))



def _structured_format(text: str) -> dict[str, Any]:
    think_matches = list(_THINK_RE.finditer(text))
    answer_matches = list(_ANSWER_TAG_RE.finditer(text))
    perception_matches = list(_PERCEPTION_RE.finditer(text))
    open_count = len(re.findall(r"<perception(?:\s|>)", text, flags=re.IGNORECASE))
    close_count = len(re.findall(r"</perception>", text, flags=re.IGNORECASE))
    valid = (
        len(think_matches) == 1
        and len(answer_matches) == 1
        and open_count == close_count == len(perception_matches)
        and think_matches[0].start() < think_matches[0].end() <= answer_matches[0].start()
        and all(
            think_matches[0].start() <= match.start()
            and match.end() <= think_matches[0].end()
            for match in perception_matches
        )
    )
    return {
        "valid": bool(valid),
        "think_count": len(think_matches),
        "answer_count": len(answer_matches),
        "perception_count": len(perception_matches),
        "perception_open_count": open_count,
        "perception_close_count": close_count,
    }


def _perception_metrics(text: str, constraints: Mapping[str, Any]) -> dict[str, Any]:
    """Score PG-CoT perception actions against construction-time visual facts.

    This follows the spirit of Learning-When-to-Look / Vision-SR1 without
    pretending XML spans are themselves token-level visual dependencies:
    tags define observable perception actions, while hard Finance World facts
    decide whether each action is grounded, sufficient, and non-redundant.
    """

    facts = [
        item
        for item in constraints.get("evidence_facts", [])
        if isinstance(item, Mapping) and bool(item.get("is_visual"))
    ]
    required_ids = {
        str(value) for value in constraints.get("required_evidence_ids", [])
    }
    facts = [
        fact for fact in facts
        if not required_ids or str(fact.get("id") or "") in required_ids
    ]
    required = {str(fact.get("id") or ""): fact for fact in facts if str(fact.get("id") or "")}

    segments = []
    covered: set[str] = set()
    productive = 0
    redundant = 0
    explicit_errors: list[dict[str, Any]] = []

    for index, match in enumerate(_PERCEPTION_RE.finditer(text)):
        body = unicodedata.normalize("NFKC", match.group("body")).strip()
        flat = re.sub(r"\s+", " ", body)
        tag_page = str(match.group("page") or "").strip()
        introduced: list[str] = []
        mentioned: list[str] = []

        for fact_id, fact in required.items():
            if not _line_matches_fact(flat, fact, facts):
                continue
            mentioned.append(fact_id)
            assignment = _assignment_after_fact(flat, fact)
            gold = _decimal(fact.get("value"))
            value_ok: bool | None = None
            claimed_value = ""
            if assignment is not None and gold is not None:
                candidate = _decimal(assignment.group("number"))
                if candidate is not None:
                    claimed_value = str(candidate)
                    candidate_unit = str(assignment.group("unit") or "")
                    fact_unit = str(fact.get("unit") or "")
                    if _unit_compatible(candidate_unit, fact_unit):
                        tolerance = _display_tolerance(assignment.group("number"), gold)
                        value_ok = abs(candidate - gold) <= tolerance
                        if not value_ok:
                            explicit_errors.append(
                                {
                                    "kind": "perception_value",
                                    "segment": index,
                                    "fact_id": fact_id,
                                    "expected": str(gold),
                                    "claimed": claimed_value,
                                    "unit": fact_unit,
                                }
                            )

            page_ok: bool | None = None
            gold_page = str(fact.get("page") or "").strip()
            if tag_page and gold_page:
                page_ok = (tag_page.lstrip("0") or "0") == (gold_page.lstrip("0") or "0")
                if not page_ok:
                    explicit_errors.append(
                        {
                            "kind": "perception_page",
                            "segment": index,
                            "fact_id": fact_id,
                            "expected_page": gold_page,
                            "claimed_page": tag_page,
                        }
                    )

            # A visual fact counts as covered only when the model explicitly
            # emits its value and any explicit page claim is correct. Missing
            # page stays an omission, while a wrong page is a hard contradiction.
            if value_ok is True and page_ok is not False:
                introduced.append(fact_id)

        new_ids = [fact_id for fact_id in introduced if fact_id not in covered]
        if new_ids:
            productive += 1
            covered.update(new_ids)
        else:
            redundant += 1
        segments.append(
            {
                "index": index,
                "char_start": match.start(),
                "char_end": match.end(),
                "page": tag_page,
                "body": body,
                "mentioned_fact_ids": mentioned,
                "matched_fact_ids": introduced,
                "new_fact_ids": new_ids,
                "productive": bool(new_ids),
            }
        )

    total = len(segments)
    required_count = len(required)
    coverage = len(covered) / required_count if required_count else 1.0
    productive_ratio = productive / total if total else (1.0 if required_count == 0 else 0.0)
    nonredundant_ratio = 1.0 - (redundant / total) if total else (1.0 if required_count == 0 else 0.0)
    sufficient = 1.0 if not required or len(covered) == required_count else 0.0

    return {
        "segments": segments,
        "required_visual_fact_ids": sorted(required),
        "covered_visual_fact_ids": sorted(covered),
        "coverage": float(coverage),
        "productive_ratio": float(productive_ratio),
        "nonredundant_ratio": float(nonredundant_ratio),
        "sufficient": float(sufficient),
        "explicit_errors": explicit_errors,
    }


def _criterion_scores(
    *,
    format_result: Mapping[str, Any],
    perception: Mapping[str, Any],
    arithmetic_checks: Sequence[Mapping[str, Any]],
    fact_checks: Sequence[Mapping[str, Any]],
    constraints: Mapping[str, Any],
    terminal_support: float,
) -> dict[str, float]:
    """Expose independent visual/reasoning criteria for group normalization."""

    criteria: dict[str, float] = {
        "format": float(bool(format_result.get("valid"))),
        "perception_sufficiency": float(perception.get("sufficient", 0.0)),
        "perception_productive": float(perception.get("productive_ratio", 0.0)),
        "perception_nonredundant": float(perception.get("nonredundant_ratio", 0.0)),
    }

    covered = set(perception.get("covered_visual_fact_ids") or [])
    for fact_id in perception.get("required_visual_fact_ids") or []:
        criteria[f"visual_fact:{fact_id}"] = float(fact_id in covered)

    passed_arithmetic = sum(bool(item.get("ok")) for item in arithmetic_checks)
    criteria["reasoning_arithmetic_valid"] = float(
        bool(arithmetic_checks) and passed_arithmetic == len(arithmetic_checks)
    )
    # Keep this deliberately simple: the terminal answer must already appear,
    # numerically normalized, somewhere before the final-answer span.
    criteria["reasoning_terminal_support"] = float(terminal_support)

    grounded_checks = [
        item for item in fact_checks
        if item.get("kind") in {"evidence_value", "evidence_page"}
    ]
    criteria["grounding_consistency"] = float(
        bool(grounded_checks) and all(bool(item.get("ok")) for item in grounded_checks)
    ) if constraints.get("vision_required") else 1.0
    return criteria

def _fact_checks(text: str, constraints: Mapping[str, Any]) -> list[dict[str, Any]]:
    facts = [
        item
        for item in constraints.get("evidence_facts", [])
        if isinstance(item, Mapping)
    ]
    if not facts:
        return []

    checks: list[dict[str, Any]] = []
    char_offset = 0
    for line_number, raw_line in enumerate(text.splitlines(keepends=True), 1):
        visible_line = raw_line.rstrip("\r\n")
        line = unicodedata.normalize("NFKC", visible_line)
        line_start = char_offset
        line_end = char_offset + len(visible_line)
        char_offset += len(raw_line)
        for fact in facts:
            if not _line_matches_fact(line, fact, facts):
                continue

            fact_id = str(fact.get("id") or "")
            page = str(fact.get("page") or "").strip()
            page_matches = [
                *[match.group(1) for match in _PAGE_RE.finditer(line)],
                *[match.group(1) for match in _TRAILING_PAGE_RE.finditer(line)],
            ]
            if page and page_matches:
                normalized_gold_page = page.lstrip("0") or "0"
                normalized_pages = {(value.lstrip("0") or "0") for value in page_matches}
                checks.append(
                    {
                        "kind": "evidence_page",
                        "line": line_number,
                        "char_start": line_start,
                        "char_end": line_end,
                        "fact_id": fact_id,
                        "expected_page": page,
                        "claimed_pages": page_matches,
                        "visual": bool(fact.get("is_visual")),
                        "ok": normalized_gold_page in normalized_pages,
                    }
                )

            assignment = _assignment_after_fact(line, fact)
            gold = _decimal(fact.get("value"))
            if assignment is None or gold is None:
                continue

            candidate = _decimal(assignment.group("number"))
            if candidate is None:
                continue
            candidate_unit = str(assignment.group("unit") or "")
            fact_unit = str(fact.get("unit") or "")
            if not _unit_compatible(candidate_unit, fact_unit):
                # Explicit unit conversions require semantic interpretation.
                # Leave them UNKNOWN instead of risking a false veto.
                continue

            tolerance = _display_tolerance(assignment.group("number"), gold)
            checks.append(
                {
                    "kind": "evidence_value",
                    "line": line_number,
                    "char_start": line_start,
                    "char_end": line_end,
                    "fact_id": fact_id,
                    "entity": str(fact.get("entity") or ""),
                    "period": str(fact.get("period") or ""),
                    "metric": str(fact.get("metric") or ""),
                    "expected": str(gold),
                    "claimed": str(candidate),
                    "unit": fact_unit,
                    "visual": bool(fact.get("is_visual")),
                    "text_value_hidden": bool(fact.get("text_value_hidden")),
                    "tolerance": str(tolerance),
                    "ok": bool(abs(candidate - gold) <= tolerance),
                }
            )
    return checks


def _answer_body_and_span(text: str) -> tuple[str, int | None, int | None]:
    tagged = list(_ANSWER_TAG_RE.finditer(text))
    if tagged:
        match = tagged[-1]
        return match.group(1).strip(), match.start(), match.end()

    prefixed = list(_ANSWER_PREFIX_RE.finditer(text))
    if prefixed:
        match = prefixed[-1]
        return match.group(1).strip(), match.start(), match.end()

    return "", None, None


def _answer_span(text: str) -> tuple[int | None, int | None]:
    _body, start, end = _answer_body_and_span(text)
    return start, end


def _numeric_mentions(text: str) -> list[set[Decimal]]:
    normalized = unicodedata.normalize("NFKC", text)
    mentions: list[set[Decimal]] = []
    for match in _NUMBER_RE.finditer(normalized):
        value = _decimal(match.group(0))
        if value is None:
            continue
        aliases = {value}
        tail = normalized[match.end() :].lstrip()
        if tail.startswith("%") or tail.startswith("％"):
            aliases.add(value / Decimal(100))
        mentions.append(aliases)
    return mentions


def _decimal_equivalent(left: Decimal, right: Decimal) -> bool:
    tolerance = max(
        Decimal("1e-10"),
        abs(left) * Decimal("1e-10"),
        abs(right) * Decimal("1e-10"),
    )
    return abs(left - right) <= tolerance


def _reasoning_terminal_support(text: str) -> float:
    """Whether every numeric atom in the final answer already appears before it."""

    answer_body, answer_start, _answer_end = _answer_body_and_span(text)
    if answer_start is None:
        return 0.0

    answer_values = _numeric_mentions(answer_body)
    reasoning_values = _numeric_mentions(text[:answer_start])
    if not answer_values or not reasoning_values:
        return 0.0

    for answer_aliases in answer_values:
        matched = any(
            _decimal_equivalent(answer_value, reasoning_value)
            for answer_value in answer_aliases
            for reasoning_aliases in reasoning_values
            for reasoning_value in reasoning_aliases
        )
        if not matched:
            return 0.0
    return 1.0


def verify_reasoning_process(
    completion: Any,
    record: Mapping[str, Any],
) -> dict[str, Any]:
    """Return pass/fail/unknown for hard-verifiable reasoning properties."""

    verifier_type = str(record.get("verifier_type") or "")
    if verifier_type not in NUMERIC_VERIFIERS:
        return {
            "status": "not_applicable",
            "checked": 0,
            "errors": [],
            "constraints": {},
        }

    text = _completion_text(completion)
    constraints = process_constraints(record)
    format_result = _structured_format(text)
    arithmetic_checks = _arithmetic_checks(text)
    fact_checks = _fact_checks(text, constraints)
    perception = _perception_metrics(text, constraints)
    terminal_support = _reasoning_terminal_support(text)
    checks = [*arithmetic_checks, *fact_checks]
    errors = [
        *[item for item in checks if not item.get("ok", False)],
        *list(perception.get("explicit_errors") or []),
    ]

    answer_start_char, answer_end_char = _answer_span(text)

    integrity_errors: list[str] = []
    if constraints.get("vision_required") and not constraints.get("images_present"):
        integrity_errors.append("required_visual_evidence_without_images")

    criteria = _criterion_scores(
        format_result=format_result,
        perception=perception,
        arithmetic_checks=arithmetic_checks,
        fact_checks=fact_checks,
        constraints=constraints,
        terminal_support=terminal_support,
    )

    if errors:
        status = "fail"
    elif checks or perception.get("segments"):
        status = "pass"
    else:
        status = "unknown"

    return {
        "status": status,
        "checked": len(checks),
        "errors": errors,
        "checks": checks,
        "format": format_result,
        "perception": perception,
        "criteria": criteria,
        "answer_start_char": answer_start_char,
        "answer_end_char": answer_end_char,
        "constraints": {
            "builder": constraints.get("builder"),
            "vision_required": constraints.get("vision_required"),
            "required_evidence_ids": constraints.get("required_evidence_ids"),
            "visual_fact_ids": constraints.get("visual_fact_ids"),
            "evidence_fact_count": len(constraints.get("evidence_facts") or []),
            "has_program": bool(constraints.get("program")),
        },
        "integrity_errors": integrity_errors,
    }


def _self_test() -> None:
    record = {
        "verifier_type": "numeric",
        "images": ["page.png"],
        "metadata": {
            "program": "subtract(120,100),divide(#0,100),multiply(#1,100)",
            "evidence_ids": ["f2023", "f2024"],
            "construction": {
                "builder": "period_percentage_change",
                "visual_fact_ids": ["f2023", "f2024"],
                "evidence_facts": [
                    {
                        "id": "f2023",
                        "entity": "公司A",
                        "period": "2023",
                        "metric": "营业收入",
                        "value": "100",
                        "unit": "亿元",
                        "page": "3",
                        "is_visual": True,
                        "text_value_hidden": True,
                    },
                    {
                        "id": "f2024",
                        "entity": "公司A",
                        "period": "2024",
                        "metric": "营业收入",
                        "value": "120",
                        "unit": "亿元",
                        "page": "4",
                        "is_visual": True,
                        "text_value_hidden": True,
                    },
                ],
            },
        },
    }

    good = verify_reasoning_process(
        "2023营业收入=100亿元\n2024营业收入=120亿元\n(120-100)/100=20%\n答案：20%",
        record,
    )
    good_scaled = verify_reasoning_process(
        "2023营业收入=100亿元\n2024营业收入=120亿元\n(120-100)/100*100=20%\n答案：20%",
        record,
    )
    bad_math = verify_reasoning_process(
        "2023营业收入=100亿元\n2024营业收入=120亿元\n(120-100)/100=25%\n答案：20%",
        record,
    )
    bad_visual = verify_reasoning_process(
        "2023营业收入=50亿元\n2024营业收入=60亿元\n(60-50)/50=20%\n答案：20%",
        record,
    )
    unknown = verify_reasoning_process("经过计算可得答案。\n答案：20%", record)

    assert good["status"] == "pass", good
    assert good_scaled["status"] == "pass", good_scaled
    assert bad_math["status"] == "fail", bad_math
    assert bad_visual["status"] == "fail", bad_visual
    unsupported_terminal = verify_reasoning_process(
        "2023营业收入=100亿元\n2024营业收入=120亿元\n(120-100)/120=16.67%\n答案：20%",
        record,
    )

    assert unknown["status"] == "unknown", unknown
    assert good["criteria"]["reasoning_terminal_support"] == 1.0, good
    assert good_scaled["criteria"]["reasoning_terminal_support"] == 1.0, good_scaled
    assert unsupported_terminal["criteria"]["reasoning_terminal_support"] == 0.0, unsupported_terminal
    print(json.dumps({
        "good": good,
        "good_scaled": good_scaled,
        "bad_math": bad_math,
        "bad_visual": bad_visual,
        "unknown": unknown,
        "unsupported_terminal": unsupported_terminal,
    }, ensure_ascii=False))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--record-json", type=Path)
    parser.add_argument("--completion")
    args = parser.parse_args()

    if args.self_test:
        _self_test()
        return
    if args.record_json is None or args.completion is None:
        parser.error("use --self-test or provide --record-json and --completion")

    record = json.loads(args.record_json.read_text(encoding="utf-8"))
    result = verify_reasoning_process(args.completion, record)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
