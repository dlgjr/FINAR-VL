"""Deterministic process-grounding verifier for FINAR-VL Reasoning RL.

The verifier is deliberately conservative. It only vetoes an outcome-correct
numeric rollout when it can prove a contradiction from hard construction-time
constraints:

1. an explicit arithmetic equation is numerically inconsistent;
2. an explicitly assigned evidence value contradicts a hidden verifier-only
   Finance World fact;
3. an explicitly cited page for that fact contradicts the gold evidence page.

Anything unsupported or ambiguous is UNKNOWN rather than a failure. The module
can be used both from the GSPO reward path and as a standalone JSONL auditor.
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
    for line_number, raw_line in enumerate(text.splitlines(), 1):
        line = raw_line.replace("＝", "=")
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


def _fact_checks(text: str, constraints: Mapping[str, Any]) -> list[dict[str, Any]]:
    facts = [
        item
        for item in constraints.get("evidence_facts", [])
        if isinstance(item, Mapping)
    ]
    if not facts:
        return []

    checks: list[dict[str, Any]] = []
    for line_number, raw_line in enumerate(text.splitlines(), 1):
        line = unicodedata.normalize("NFKC", raw_line)
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
    checks = _arithmetic_checks(text)
    checks.extend(_fact_checks(text, constraints))
    errors = [item for item in checks if not item.get("ok", False)]

    integrity_errors: list[str] = []
    if constraints.get("vision_required") and not constraints.get("images_present"):
        integrity_errors.append("required_visual_evidence_without_images")

    if errors:
        status = "fail"
    elif checks:
        status = "pass"
    else:
        status = "unknown"

    return {
        "status": status,
        "checked": len(checks),
        "errors": errors,
        "checks": checks,
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
    assert unknown["status"] == "unknown", unknown
    print(json.dumps({"good": good, "good_scaled": good_scaled, "bad_math": bad_math, "bad_visual": bad_visual, "unknown": unknown}, ensure_ascii=False))


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
