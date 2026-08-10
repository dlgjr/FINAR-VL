"""Select training rows whose content matches benchmark capability definitions."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import orjson


@dataclass(frozen=True)
class Decision:
    accepted: bool
    score: float
    subtype: str
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class Candidate:
    input_name: str
    line_number: int
    content_hash: str
    score: float
    subtype: str
    reasons: tuple[str, ...]
    original_task: str
    source: str
    image_count: int
    review_reasons: tuple[str, ...] = ()


def select_top(
    candidates: list[Candidate],
    count: int,
    benchmark_hashes: set[str],
) -> list[Candidate]:
    """Select highest-scoring unique rows and exclude exact benchmark rows."""
    selected: list[Candidate] = []
    seen: set[str] = set()
    ordered = sorted(
        candidates,
        key=lambda item: (-item.score, -int(item.image_count > 0), item.input_name, item.line_number),
    )
    for candidate in ordered:
        if candidate.content_hash in benchmark_hashes or candidate.content_hash in seen:
            continue
        selected.append(candidate)
        seen.add(candidate.content_hash)
        if len(selected) == count:
            break
    return selected


def select_modality_quota(
    candidates: list[Candidate],
    count: int,
    multimodal_target: int,
    benchmark_hashes: set[str],
) -> list[Candidate]:
    """Select a multimodal/text quota, then fill any shortage with aligned rows."""
    multimodal_target = max(0, min(count, multimodal_target))
    multimodal = [item for item in candidates if item.image_count > 0]
    text = [item for item in candidates if item.image_count == 0]
    selected = select_top(multimodal, multimodal_target, benchmark_hashes)
    excluded = benchmark_hashes | {item.content_hash for item in selected}
    text_target = count - multimodal_target
    selected.extend(select_top(text, text_target, excluded))
    excluded = benchmark_hashes | {item.content_hash for item in selected}
    if len(selected) < count:
        selected.extend(select_top(candidates, count - len(selected), excluded))
    return selected


FINANCE_TERMS = (
    "公司", "企业", "收入", "营收", "利润", "成本", "股价", "股票", "证券", "市场",
    "资金", "投资", "金融", "财务", "经济", "货币", "债券", "基金", "组合", "审计",
    "合规", "监管", "披露", "交易", "company", "revenue", "profit", "stock", "market",
    "financial", "finance", "economic", "investment", "portfolio", "audit", "trading", "bond", "credit", "bank",
)

CAPABILITIES = (
    "explanation_anomaly_causality",
    "risk_sentiment_policy",
    "multimodal_financial_knowledge",
    "investment_advice_strategy",
    "candlestick_time_series",
    "basic_arithmetic_metrics",
    "compliance_safety_suitability",
    "image_caption",
    "entity_extraction_classification",
    "financial_event_extraction",
    "portfolio_allocation_risk_return",
    "summary_announcement",
    "financial_audit_fundamentals",
)

RULE_VERSION = "benchmark_alignment_v19"

FINANCIAL_KNOWLEDGE_TERMS = (
    "主营业务", "主要业务", "收入", "营收", "利润", "净利", "股票", "股价", "证券", "金融市场",
    "金融机构", "金融报表", "财务报表", "财务报告", "金融披露", "投资", "债券", "基金", "交易", "融资", "负债", "资本", "现金流",
    "流动性", "偿还比", "两融", "沪股通", "深股通", "陆股通", "港股通", "险资举牌", "退市",
    "内盘", "外盘", "通货膨胀", "国内生产总值", "货币政策", "经济负担", "boll", "kdj", "rsi", "macd",
    "revenue", "profit", "income", "stock", "share price", "securities", "financial statement",
    "financial report", "financial disclosure", "financial institution", "inflation", "gdp", "monetary policy",
    "economic burden", "investment", "portfolio",
    "audit", "trading", "bond", "credit", "bank", "capital", "debt", "cash flow", "liquidity",
    "regulatory ratio", "primary business", "main business", "dependency ratio",
)


def _contains(text: str, terms: tuple[str, ...]) -> bool:
    return any(term in text for term in terms)


def _text(row: dict[str, Any], role: str) -> str:
    parts = [
        str(message.get("content", ""))
        for message in row.get("messages", [])
        if message.get("role") == role
    ]
    return " ".join(parts).casefold()


def _has_image(row: dict[str, Any], question: str) -> bool:
    return bool(row.get("images")) or "<image>" in question


def _focus_question(question: str) -> str:
    """Extract the requested operation without treating supplied context as intent."""
    focused = question
    localized_question = False
    for marker in ("问题:", "问题："):
        if marker in focused:
            focused = focused.split(marker, 1)[1]
            localized_question = True
            break
    if not localized_question and "### question" in focused:
        focused = focused.rsplit("### question", 1)[1].lstrip(" :：\n")
        localized_question = True
    if not localized_question and "question:" in focused:
        focused = focused.rsplit("question:", 1)[1]
    context_is_query = _contains(
        focused,
        ("professional technical analysis trading question", "your task is to select the correct answer option", "task on the topic", "chart construction"),
    ) and "context:" in focused
    if context_is_query:
        return focused.rsplit("context:", 1)[1].strip()
    cut_positions = [
        focused.find(marker)
        for marker in (
            "证据材料:", "证据材料：", "监管材料:", "监管材料：",
            "上下文:", "上下文：", "context:", "contract:", "财务披露:", "财务披露：",
            "财务报告材料:", "财务报告材料：", "[company introduction]:", "## 对话", "## dialogue",
            "documents:", "earnings-call excerpt:", "编号:", "编号：", "|内容id|",
        )
        if focused.find(marker) > 0
    ]
    if cut_positions:
        focused = focused[:min(cut_positions)]
    return focused.strip()


def _accept(score: float, subtype: str, *reasons: str) -> Decision:
    return Decision(True, score, subtype, tuple(reasons))


def _reject(*reasons: str) -> Decision:
    return Decision(False, 0.0, "", tuple(reasons))


def review_alignment(
    row: dict[str, Any],
    capability: str,
    decision: Decision,
) -> tuple[bool, tuple[str, ...]]:
    """Apply a second per-row content review after candidate recall."""
    question = _text(row, "user")
    answer = _text(row, "assistant")
    focus = _focus_question(question)
    combined = f"{focus} {answer}"
    if not decision.accepted or not question.strip() or not answer.strip():
        return False, ("missing accepted question-answer pair",)
    extraction = _contains(
        focus,
        ("抽取事件", "提取事件", "extract event", "extract the event", "extract the contract", "return the relevant clause"),
    ) or answer.lstrip().startswith(("[[", "[{"))
    if extraction and capability != "financial_event_extraction":
        return False, ("structured event extraction excluded",)
    if "image_grounded" in decision.reasons and not _has_image(row, question):
        return False, ("declared image grounding required",)

    checks = {
        "explanation_anomaly_causality": _has_image(row, question) and _contains(
            combined,
            ("原因", "导致", "由于", "cause", "because", "due to", "result"),
        ),
        "risk_sentiment_policy": _has_image(row, question) and _contains(focus, ("风险", "risk")) and _contains(answer, ("风险", "risk")),
        "multimodal_financial_knowledge": _has_image(row, question) and _contains(combined, FINANCE_TERMS),
        "investment_advice_strategy": _has_image(row, question) and _contains(combined, ("投资", "股票", "组合", "买入", "卖出", "预测", "investment", "stock", "portfolio", "buy", "sell", "prediction", "forecast")),
        "candlestick_time_series": _has_image(row, question) and _contains(
            combined,
            (
                "走势", "趋势", "k线", "成交量", "boll", "kdj", "rsi", "macd", "trend", "candlestick",
                "technical analysis", "tick volume", "oscillator", "moving average", "price", "volatility",
                "intraday", "futures", "chart", "breakout", "time series",
            ),
        ),
        "basic_arithmetic_metrics": len(re.findall(r"\d+(?:\.\d+)?", focus)) >= 2
        and (bool(re.search(r"\d", answer)) or bool(re.fullmatch(r"[a-d]", answer.strip())))
        and _contains(focus, ("公式", "formula", "=", "/", "×", "*", "^", "%")),
        "compliance_safety_suitability": _contains(combined, FINANCE_TERMS) or _contains(combined, ("gips", "合规", "监管")),
        "image_caption": _has_image(row, question) and len(answer) >= 24,
        "entity_extraction_classification": _contains(
            focus,
            ("是不是股票", "是不是公司", "是不是行业概念", "是否为股票", "是否为公司", "entity disambiguation"),
        ) and bool(re.fullmatch(r"[a-c]", answer.strip())),
        "financial_event_extraction": _contains(
            focus,
            ("抽取下列实体", "抽取以下实体", "抽取金融事件及其字段", "金融资讯", "financial event", "extract the following fields"),
        ) and _contains(
            answer,
            ("argument", "role", "披露", "公司", "金额", "equitypledge", "equityoverweight", "equityunderweight", "event_type"),
        ),
        "portfolio_allocation_risk_return": _contains(
            focus,
            ("比较两只基金", "对比两只基金", "比较两者", "对比两者", "比较其绩效", "compare the two funds", "compare both funds", "compare two funds"),
        ) and _contains(
            answer,
            ("更高", "更低", "更强", "更弱", "较差", "绩效", "风险", "收益", "优于", "higher", "lower", "risk", "return"),
        ),
        "summary_announcement": (
            _contains(focus, ("公告", "announcement"))
            and _contains(combined, ("经营", "股价", "影响", "business", "share price", "impact"))
        ) or (
            _contains(focus, ("个股研究员", "行业研究员"))
            and _contains(focus, ("分析", "评价"))
            and _contains(
                answer,
                (
                    "影响", "经营", "股价", "收入", "利润", "风险", "发展", "目的", "协同", "现金流", "人才", "信心",
                    "资本结构", "研发", "市场拓展", "安全", "产品质量", "竞争力",
                ),
            )
        ),
        "financial_audit_fundamentals": _contains(
            combined,
            (
                "审计意见", "保留意见", "无保留意见", "经营情况", "经营盈利情况", "毛利率", "权益报酬率",
                "投资收益", "偿债能力", "财务成本", "周转率", "负债率", "杜邦分析", "主要会计数据",
                "财务指标", "经营现金流", "现金流量", "盈利能力", "成长能力", "收益质量",
                "主营产品", "产品业务数据", "知识产权", "股东户数", "机构持仓", "限售股", "流通股东",
                "研发投入", "经营模式", "财务状况", "管理费用", "估值", "分红", "营业周期", "财务结构",
                "投入资本", "资本固化",
                "audit opinion", "operating condition", "gross margin",
            ),
        ) and _contains(
            answer,
            (
                "风险", "利润", "盈利", "收入", "成本", "能力", "上升", "下降", "现金流", "质量", "效率", "趋势",
                "营收", "持仓", "股价", "创新", "研发", "估值", "分红", "结构", "周期", "影响", "利好", "利空",
                "risk", "profit", "revenue", "cost",
            ),
        ),
    }
    if not checks[capability]:
        return False, ("second-stage capability evidence missing",)
    return True, (
        "question reviewed",
        "answer reviewed",
        "benchmark capability evidence confirmed",
        "split ignored",
        "image existence not checked",
    )


def assess_row(
    row: dict[str, Any],
    capability: str,
    _prepared: tuple[str, str, str, str, bool, bool] | None = None,
) -> Decision:
    """Judge capability alignment from content; task and split fields are ignored."""
    if _prepared is None:
        question = _text(row, "user")
        answer = _text(row, "assistant")
        combined = f"{question} {answer}"
        focus = _focus_question(question)
        has_image = _has_image(row, question)
        financial = _contains(combined, FINANCE_TERMS)
    else:
        question, answer, combined, focus, has_image, financial = _prepared

    if capability == "risk_sentiment_policy":
        intent = _contains(
            focus,
            ("哪些风险", "什么风险", "风险信息", "风险因素", "潜在风险", "主要风险", "风险等级", "risks", "risk factors", "risk information", "risk analysis"),
        ) or bool(re.search(r"(?:哪些|什么|可能存在).{0,12}风险", focus))
        answer_has_risk = _contains(answer, ("风险", "risk", "波动", "流动性", "通胀", "下行"))
        if has_image and intent and answer_has_risk and financial:
            return _accept(10.0, "risk_identification", "image_grounded", "explicit_risk_request", "risk_answer")
        return _reject("requires image-grounded financial risk identification")

    if capability == "investment_advice_strategy":
        intent = _contains(
            focus,
            (
                "投资建议", "交易建议", "建议投资", "如何操作", "该如何操作", "操作策略", "投资者应当",
                "是否买入", "是否卖出", "值得投资", "如何配置", "investment advice", "trading advice",
                "recommend investing", "should i invest", "should i buy", "should i sell", "what do i do",
                "what should i do", "is it prudent", "is it smart", "how should i invest", "where should i invest",
                "how can i find", "how can i invest", "what should investors", "what should an investor",
                "where to invest", "good investment",
            ),
        )
        advice = _contains(
            answer,
            ("建议", "买入", "卖出", "持有", "止损", "观望", "配置", "recommend", "buy", "sell", "hold", "consider", "diversif", "stop loss", "avoid"),
        )
        personal_decision = _contains(focus, ("should i", "can i", "would it", "should an investor", "should investors")) and _contains(
            focus,
            ("invest", "stock", "portfolio", "fund", "etf", "dividend", "option", "bond"),
        )
        intent = intent or personal_decision
        if has_image and intent and advice and financial:
            return _accept(10.0, "evidence_based_advice", "image_grounded", "explicit_advice_request", "actionable_answer")
        forecast_intent = _contains(
            focus,
            ("分析和预测", "走势预测", "未来趋势", "analysis and prediction", "stock price movement", "price movement", "price prediction"),
        )
        forecast_answer = _contains(
            answer,
            ("prediction", "analysis", "bullish", "bearish", "上涨", "下跌", "趋势", "预计", "可能"),
        )
        if has_image and forecast_intent and forecast_answer and financial:
            return _accept(9.5, "evidence_based_market_forecast", "image_grounded", "explicit_forecast_request", "evidence_based_prediction")
        return _reject("requires image-grounded evidence-based investment advice")

    if capability == "basic_arithmetic_metrics":
        calculate = _contains(focus[:700], ("计算", "求出", "calculate", "compute"))
        numeric_inputs = len(re.findall(r"\d+(?:\.\d+)?", focus)) >= 2
        numeric_answer = bool(re.search(r"\d", answer)) or bool(re.fullmatch(r"[a-d]", answer.strip()))
        metric = _contains(f"{focus} {answer}", ("公式", "增长率", "收益率", "比例", "比率", "利润", "收入", "成本", "formula", "rate", "ratio", "return"))
        formula_evidence = _contains(focus, ("公式", "formula", "=", "/", "×", "*", "^", "%"))
        arithmetic_answer = _contains(answer, ("步骤1:arithmetic", "step 1: arithmetic")) or bool(
            re.search(r"\d(?:[\d,.]*)\s*(?:[+\-*/×÷^]|加上|减去|乘以|除以)\s*\d", answer)
        ) or _contains(focus[:500], ("指标计算助手", "计算公式", "公式为", "calculation formula"))
        meta_task = _contains(focus, ("编号之和", "内容编号", "description id", "dialogue id"))
        foreign_task = _contains(
            focus[:500],
            (
                "实体消岐助手", "是不是公司", "是不是股票", "抽取金融事件", "情感倾向", "预测股票", "预测该股票", "stock price prediction",
                "summary of the key performance indicators", "extract this data", "总结5家", "总结评估", "提取2022年",
            ),
        )
        if not has_image and calculate and numeric_inputs and numeric_answer and metric and formula_evidence and arithmetic_answer and financial and not meta_task and not foreign_task:
            return _accept(10.0, "financial_metric_calculation", "text_only", "explicit_formula_calculation", "numeric_or_option_answer")
        return _reject("requires text financial metric calculation with numeric answer")

    if capability == "candlestick_time_series":
        if not has_image:
            return _reject("requires an image-grounded market chart task")
        if _contains(answer, ("无法回答", "不能回答", "无法判断", "cannot answer", "not answerable")):
            return _reject("unanswerable or image-question mismatch")
        chart_specific = _contains(
            f"{focus} {answer}",
            (
                "k线", "蜡烛图", "candlestick", "v型底", "三只乌鸦", "开盘价", "收盘价", "最高价", "最低价", "最高点", "最低点",
                "均线", "成交量", "量价", "boll", "kdj", "rsi", "macd", "ohlc", "moving average",
            ),
        )
        if not chart_specific:
            return _reject("requires K-line or chart-specific technical evidence")
        technical_exam_framing = _contains(
            question,
            ("professional technical analysis trading question", "point and figure charting", "japanese candlesticks", "chart construction", "oscillators and contrary opinion"),
        )
        direct_technical_concept = _contains(
            focus,
            (
                "technical analysis", "tick volume", "candlestick", "k线", "蜡烛图", "v型底", "三只乌鸦",
                "oscillator", "moving average", "均线", "量价", "support and resistance", "chart pattern",
                "commodity channel index", "a/d oscillator", "point and figure", "real body", "box size", "pivot point",
                "relative strength", "technical indicator", "technical pattern", "gamma exposure", "detrend",
                "backtest", "mean reversion", "trend-following", "trend following", "stop loss", "pine script",
                "momentum analysis", "trend analysis", "market reversal", "market scenario",
            ),
        )
        indicator_token = bool(
            re.search(r"(?<![a-z0-9])(?:boll|kdj|rsi|macd|cci|ema|sma|vwap|ohlc)(?![a-z0-9])", focus)
        )
        direct_technical_concept = direct_technical_concept or indicator_token
        framed_technical_concept = technical_exam_framing and _contains(
            focus,
            (
                "price change", "volatility", "price shock", "price series",
                "intraday", "breakout", "price target", "entry filter", "futures", "fourier analysis", "data frequency",
                "cross-market correlation", "price levels",
            ),
        )
        technical_concept = direct_technical_concept or framed_technical_concept
        concept_request = _contains(
            focus,
            (
                "定义", "解释", "是什么", "公式", "如何", "计算", "define", "explain", "what", "which",
                "formula", "how", "calculate", "compute", "analysis type", "market scenario", "strategy from book",
                "risk concept", "concept:",
            ),
        )
        technical_framing = technical_exam_framing or len(focus) < 600
        meta_task = _contains(
            focus,
            ("identify which dialogue", "description comes from", "数据错误", "对话梳理", "证据段落", "extract the relevant"),
        )
        if technical_concept and concept_request and technical_framing and not meta_task and len(answer) >= 20 and (financial or technical_exam_framing):
            return _accept(9.5, "technical_analysis_knowledge", "image_grounded", "technical_concept_request", "technical_explanation")
        if technical_exam_framing and concept_request and not meta_task and len(answer) >= 20:
            return _accept(9.0, "technical_analysis_knowledge", "image_grounded", "explicit_technical_analysis_frame", "technical_answer")
        if technical_exam_framing and concept_request and re.fullmatch(r"[a-d]", answer.strip()):
            return _accept(9.0, "technical_analysis_exam", "image_grounded", "technical_exam_question", "answer_option")

        price_change_request = _contains(
            focus,
            ("最高点到当前", "最低点到当前", "下跌幅度", "上涨幅度", "from the high to the current", "from the low to the current"),
        )
        price_change_answer = bool(re.search(r"\d", answer)) and _contains(
            f"{focus} {answer}",
            ("股价", "价格", "stock price", "price", "%", "百分比"),
        )
        if price_change_request and price_change_answer and financial and len(focus) < 500:
            return _accept(10.0, "market_price_change_calculation", "image_grounded", "high_low_price_change_request", "numeric_price_change_answer")

        series_forecast_request = _contains(
            focus,
            ("时间序列", "周度序列", "日度序列", "time series", "weekly series", "daily series", "weekly financial series"),
        ) and _contains(focus, ("预测", "走势", "predict", "forecast", "stock price movement", "price movement"))
        series_forecast_answer = _contains(
            answer,
            ("预测", "上涨", "下跌", "看涨", "看跌", "prediction", "bullish", "bearish", "rise", "fall"),
        )
        if series_forecast_request and series_forecast_answer and financial:
            return _accept(9.0, "market_time_series_forecast", "image_grounded", "explicit_time_series_request", "directional_forecast_answer")

        stock_direction_request = _contains(
            focus,
            ("stock price movement", "share price movement", "股票的下个月的涨跌", "股票下月涨跌", "预测股价走势"),
        ) and _contains(focus, ("predict", "prediction", "upcoming week", "next week", "下个月", "下月", "预测"))
        stock_direction_answer = _contains(
            answer,
            ("prediction", "bullish", "bearish", "rise", "fall", "上涨", "下跌", "涨", "跌"),
        )
        if stock_direction_request and stock_direction_answer and financial:
            return _accept(8.5, "evidence_based_stock_direction_forecast", "image_grounded", "explicit_stock_direction_request", "directional_forecast_answer")

        technical = _contains(
            f"{focus} {answer}",
            ("k线", "蜡烛图", "v型底", "三只乌鸦", "均线", "量价", "成交量", "开盘价", "收盘价", "candlestick"),
        ) or bool(re.search(r"(?<![a-z0-9])(?:boll|kdj|rsi|macd)(?![a-z0-9])", f"{focus} {answer}"))
        temporal = _contains(f"{focus} {answer}", ("走势", "趋势", "突破", "反转", "上涨", "下跌", "波动", "高点", "低点", "trend", "breakout"))
        technical_question = _contains(
            focus,
            ("k线", "蜡烛图", "v型底", "三只乌鸦", "均线", "量价", "开盘价", "收盘价", "candlestick"),
        ) or bool(re.search(r"(?<![a-z0-9])(?:boll|kdj|rsi|macd)(?![a-z0-9])", focus))
        time_series_request = _contains(
            focus,
            ("分析走势", "价格走势", "股价走势", "走势如何", "趋势如何", "下跌幅度", "上涨幅度", "技术分析", "price trend", "technical analysis"),
        )
        generic_visual = has_image and _contains(focus, ("概述", "描述", "展示了什么", "describe", "overview"))
        classification = _contains(
            focus,
            ("情感", "分类", "标签", "sentiment", "classify", "核对", "错误的描述", "data verification", "verify each description", "description ids", "dialogue analysis"),
        ) or len(answer.strip()) < 8
        if technical and temporal and (technical_question or time_series_request or generic_visual) and financial and not classification:
            return _accept(10.0, "technical_time_series", "image_grounded", "technical_indicator", "temporal_reasoning")
        return _reject("requires market technical time-series reasoning")

    if capability == "image_caption":
        intent = _contains(
            focus,
            ("概述图片", "概述一下这张图", "描述图片", "描述了什么", "展示了什么", "图中讲了啥", "图中描述了什么", "describe the image", "summarize the image", "what is shown", "what does the image show", "provide an overview", "give an overview"),
        )
        holistic = len(answer) >= 24 and _contains(answer, ("图片", "图中", "图表", "界面", "显示", "展示", "image", "figure", "chart", "shows"))
        if has_image and intent and holistic:
            return _accept(10.0, "holistic_image_description", "image_grounded", "generic_description_request", "holistic_answer")
        return _reject("requires holistic image-description intent")

    if capability == "explanation_anomaly_causality":
        if not has_image:
            return _reject("requires image-grounded anomaly explanation")
        contract_yes_no = bool(re.fullmatch(r"\s*(?:yes|no|是|否)\s*", answer)) and _contains(
            question,
            ("merger-agreement", "merger agreement", "contract excerpt", "clause type", "material adverse effect"),
        )
        if contract_yes_no:
            return _reject("contract yes-no judgment is not causal explanation")
        chain_request = _contains(
            focus,
            ("因果事件流", "因果顺序", "因果关系", "逻辑排序", "causal order", "causally linked", "cause-and-effect", "root cause analysis"),
        )
        ordered_answer = len(re.findall(r"\d", answer)) >= 2 and bool(
            re.fullmatch(r"[\[\]{}\"':,\d\s]+", answer.strip())
        )
        if chain_request and ordered_answer and financial:
            return _reject("causal ordering is not benchmark anomaly explanation")

        impact_request = _contains(
            focus,
            ("影响路径", "对什么影响", "如何影响", "有何影响", "impact of", "impact on", "effect of", "effect on", "drive revenue", "drive profit"),
        )
        impact_answer = _contains(
            answer,
            ("影响", "导致", "增加", "降低", "提升", "压缩", "impact", "lead", "increase", "reduce", "compress", "slow", "drive"),
        )
        if impact_request and impact_answer and financial:
            return _reject("generic impact analysis is not benchmark anomaly explanation")

        causal_question = _contains(focus, ("为什么", "为何", "原因", "何种因素")) or bool(
            re.search(r"\b(?:why|reason|what caused)\b", focus)
        )
        causal_answer = _contains(answer, ("因为", "由于", "原因", "导致", "影响", "cause", "because", "due to", "result"))
        causal_selection = _contains(focus, ("识别", "找出", "identify", "which")) and (
            _contains(focus, ("导致", "造成", "引起")) or bool(re.search(r"\b(?:caused|cause)\b", focus))
        )
        anomaly = _contains(focus, ("异常", "大幅", "剧烈", "下降", "上涨", "大涨", "下跌", "波动", "破产", "激增", "surge", "decline", "drop", "anomal"))
        identifier_answer = bool(re.fullmatch(r"[\[\](){}\d,，、\s]+", answer.strip()))
        if causal_question and causal_answer and anomaly and financial and not causal_selection and not identifier_answer:
            return _accept(11.0, "financial_anomaly_causality", "image_grounded", "causal_question", "causal_evidence", "financial_anomaly")
        return _reject("requires financial anomaly and causal explanation")

    if capability == "multimodal_financial_knowledge":
        concept = _contains(
            focus,
            (
                "是什么", "什么是", "什么意思", "含义", "如何使用", "使用方法", "主营业务", "主要业务",
                "介绍一下", "解释", "what is", "what does", "meaning", "how to use", "how does", "explain",
                "is used", "main business",
            ),
        )
        knowledge = _contains(focus, FINANCIAL_KNOWLEDGE_TERMS)
        lookup_or_ranking = _contains(
            focus,
            (
                "largest", "smallest", "highest", "lowest", "ranked", "which bank", "which company", "which quarter",
                "第几大", "排名第", "最高的是", "最低的是", "哪家银行", "哪家公司", "哪个季度",
            ),
        ) or bool(re.search(r"\b\d+(?:st|nd|rd|th)\b", focus))
        foreign_analysis = _contains(focus, ("你是一个金融分析师", "杜邦分析", "进行分析", "分析公司的", "analyze the company"))
        letter_answer = bool(re.fullmatch(r"[a-d\s,]+", answer.strip()))
        quantitative = _contains(
            focus,
            (
                "how much", "how many", "average", "difference", "change in", "percentage", "estimated amount",
                "estimated value", "projected number", "market value", "计算", "多少", "平均", "差额", "变化率", "增长率",
                "预计金额", "预计数值", "数值是多少", "range of", "mode of", "median of", "sum of", "total of",
                "as of", "for the year", "in trillion", "in billion", "in million", "most profitable",
                "total decrease", "gross income", "total retail sales", "how many times", "how many years",
            ),
        ) or bool(re.search(r"\d\s*[-+*/]\s*\d", answer))
        numeric_lookup = bool(re.search(r"\d", answer)) and _contains(
            focus,
            (
                "estimated", "projected", "predicted", "expected", "forecast", "outlook", "increase", "amount", "value", "volume", "market size",
                "market cap", "growth rate", "market share", "revenue", "gdp", "预计", "预测", "数额", "市值",
                "市场规模", "增长率", "市场份额", "收入是多少",
            ),
        )
        quantitative = quantitative or numeric_lookup
        document_lookup = _contains(
            focus,
            ("primary message", "title of", "tag line", "tagline", "data point", "content usage", "what is credit union offers"),
        )
        if has_image and concept and knowledge and not quantitative and not document_lookup and not lookup_or_ranking and not foreign_analysis and not letter_answer and len(answer) >= 20:
            return _accept(10.0, "image_grounded_financial_concept", "image_grounded", "concept_request", "financial_explanation")
        interpretation = _contains(
            focus,
            ("说明了什么", "表明什么", "反映什么", "意味着什么", "有何影响", "what does", "indicate", "suggest", "imply", "interpret"),
        )
        explanatory_answer = _contains(
            answer,
            ("说明", "表明", "反映", "意味着", "影响", "indicate", "suggest", "imply", "reflect", "because"),
        )
        if has_image and interpretation and explanatory_answer and knowledge and not quantitative and not lookup_or_ranking and not foreign_analysis and not letter_answer and len(answer) >= 40:
            return _accept(8.5, "image_grounded_financial_interpretation", "image_grounded", "financial_interpretation_request", "explanatory_answer")
        return _reject("requires image-grounded financial concept explanation")

    if capability == "compliance_safety_suitability":
        rule_terms = (
            "gips", "合规", "监管", "适当性", "受托", "披露义务", "退市规则", "融资融券",
            "compliance", "regulation", "suitability", "fiduciary", "mandatory standard",
        )
        intent_head = focus[:1200]
        application = _contains(intent_head, ("判断", "是否符合", "依据", "要求", "正确答案", "choose", "which", "comply", "require"))
        extraction = _contains(focus, ("抽取", "提取", "extract", "return the relevant clause")) or answer.lstrip().startswith(("[[", "[{"))
        causal_template = _contains(focus, ("causal order", "causally linked", "因果事件流", "因果顺序", "逻辑排序"))
        foreign_task = _contains(
            focus[:500],
            (
                "实体消岐助手", "是不是公司", "是不是股票", "专业的财务分析师", "财务状况最好的公司",
                "classify the contract clause", "legal clause category", "identify content unrelated", "unrelated to the surge",
                "抽取金融事件", "金融情绪分析助手", "情感倾向", "sentiment", "stock price movement",
                "merger-agreement", "merger agreement", "material adverse effect", "mae forward looking",
            ),
        )
        option_format = bool(re.search(r"a\s*[.、:：].*b\s*[.、:：]", intent_head, re.DOTALL))
        regulatory_basis = _contains(
            intent_head,
            (
                "依据《", "根据《", "法规", "办法", "监管要求", "监管规定", "监管标准", "披露义务",
                "gips", "regulatory authority", "regulatory requirements", "compliance requirements", "adgm",
            ),
        )
        direct_compliance = _contains(
            intent_head,
            ("合规审核", "是否合规", "是否符合", "符合合规要求", "compliance and regulatory", "stay current with evolving compliance"),
        )
        rule_application = (option_format and regulatory_basis) or direct_compliance or _contains(intent_head, ("gips",))
        if _contains(intent_head, rule_terms) and application and rule_application and not extraction and not causal_template and not foreign_task:
            grounding = "image_grounded" if has_image else "core_capability"
            return _accept(10.0 if has_image else 8.5, "compliance_rule_application", grounding, "financial_rule", "rule_application")
        mechanism_terms = (
            "沪股通", "深股通", "陆股通", "港股通", "险资举牌", "退市", "融资融券", "两融",
            "信息披露", "证券交易", "持股比例", "margin trading", "stock connect", "delisting",
        )
        mechanism_intent = _contains(focus, ("是什么", "什么是", "什么意思", "如何计算", "占比", "介绍一下", "what is", "what does", "how is"))
        if has_image and mechanism_intent and _contains(combined, mechanism_terms) and not extraction:
            return _accept(9.0, "benchmark_financial_mechanism", "image_grounded", "benchmark_mixed_subtype", "financial_market_mechanism")
        return _reject("requires financial compliance or suitability rule application")

    if capability == "entity_extraction_classification":
        entity_type_question = _contains(
            focus,
            (
                "是不是股票", "是不是公司", "是不是行业概念", "是否为股票", "是否为公司", "是否属于股票",
                "whether the mentioned entity is a stock", "whether the entity is a company", "entity disambiguation",
            ),
        )
        option_format = bool(re.search(r"a\s*[.、:：].*b\s*[.、:：]", focus, re.DOTALL))
        answer_option = bool(re.fullmatch(r"[a-c]", answer.strip()))
        if entity_type_question and option_format and answer_option:
            grounding = "image_grounded" if has_image else "core_capability"
            return _accept(
                10.0 if has_image else 8.5,
                "financial_entity_disambiguation",
                grounding,
                "explicit_entity_type_judgment",
                "classification_option_answer",
            )
        return _reject("requires financial entity type disambiguation with classification answer")

    if capability == "financial_event_extraction":
        extraction_intent = _contains(
            focus,
            (
                "从下面资讯中", "从金融资讯中", "抽取下列实体", "抽取以下实体", "金融行业的信息抽取",
                "抽取金融事件及其字段", "extract the following fields", "extract financial event arguments", "financial event extraction",
            ),
        )
        event_roles = _contains(
            focus,
            (
                "披露日期", "披露时间", "中标公司", "招标方", "中标金额", "减持方", "质押方", "质权方",
                "收购方", "被收购方", "融资金额", "被投资方", "回购方", "交易金额", "上市公司",
                "event date", "bidder", "issuer", "acquirer", "target company", "financing amount", "share amount",
            ),
        ) or _contains(answer, ("equitypledge", "equityoverweight", "equityunderweight", "repurchase", "acquisition", "financing", "event_type"))
        structured_answer = (
            _contains(answer, ('"argument"', '"role"'))
            or bool(re.search(r"(?:披露|公司|金额|日期|时间|收购方|回购方)\s*[:：]", answer))
            or answer.lstrip().startswith(("[[", "[{"))
        )
        if extraction_intent and event_roles and structured_answer and financial:
            grounding = "image_grounded" if has_image else "core_capability"
            return _accept(
                10.0 if has_image else 8.5,
                "financial_event_argument_extraction",
                grounding,
                "explicit_financial_event_fields",
                "structured_argument_role_answer",
            )
        return _reject("requires structured argument extraction from a financial event")

    if capability == "portfolio_allocation_risk_return":
        comparison_intent = _contains(
            focus,
            (
                "比较两只基金", "对比两只基金", "比较两者", "对比两者", "比较其绩效",
                "compare the two funds", "compare both funds", "compare two funds",
            ),
        )
        portfolio_subject = _contains(
            combined,
            ("基金", "投资组合", "资产配置", "portfolio", "fund", "etf", "tracking error", "information ratio"),
        )
        metric_evidence = _contains(
            focus,
            (
                "回报", "收益", "损失", "风险", "盈利概率", "跟踪误差", "信息比率", "择时能力", "选股能力",
                "return", "loss", "risk", "profitability", "tracking error", "information ratio", "performance",
            ),
        )
        comparative_answer = _contains(
            answer,
            ("更高", "更低", "更强", "更弱", "更优", "优于", "风险", "收益", "higher", "lower", "better", "worse", "risk", "return"),
        )
        if comparison_intent and portfolio_subject and metric_evidence and comparative_answer:
            grounding = "image_grounded" if has_image else "core_capability"
            return _accept(
                10.0 if has_image else 8.5,
                "fund_risk_return_comparison",
                grounding,
                "explicit_fund_comparison",
                "risk_return_metric_evidence",
                "comparative_conclusion",
            )
        return _reject("requires fund or portfolio risk-return comparison")

    if capability == "summary_announcement":
        announcement = _contains(focus, ("公告", "通知书", "三季报", "中标", "回购", "并购", "股权激励", "announcement"))
        impact_request = _contains(
            focus,
            ("对公司经营及股价的影响", "对其股价的影响", "对公司股价的影响", "分析", "impact on operations", "impact on share price"),
        )
        impact_answer = _contains(
            answer,
            ("经营", "股价", "收入", "利润", "风险", "积极", "负面", "影响", "operations", "share price", "revenue", "profit", "risk", "impact"),
        )
        generic_summary = _contains(focus, ("体育", "sports article", "小说", "novel"))
        researcher_analysis = _contains(focus, ("个股研究员", "行业研究员")) and _contains(
            focus,
            ("分析", "评价"),
        )
        supported_interpretation = len(answer) >= 20 and _contains(
            answer,
            (
                "影响", "经营", "股价", "收入", "利润", "风险", "发展", "目的", "协同", "现金流", "人才", "信心",
                "利好", "利空", "资本结构", "研发", "市场拓展", "安全", "产品质量", "竞争力",
            ),
        )
        if (
            (announcement and impact_request and impact_answer)
            or (researcher_analysis and supported_interpretation)
        ) and financial and not generic_summary:
            grounding = "image_grounded" if has_image else "core_capability"
            return _accept(
                10.0 if has_image else 8.5,
                "announcement_business_market_impact",
                grounding,
                "financial_announcement",
                "business_or_market_impact_request",
                "impact_analysis_answer",
            )
        return _reject("requires financial announcement impact analysis")

    if capability == "financial_audit_fundamentals":
        multiple_choice_task = _contains(focus, ("选项:", "选项：")) or bool(
            re.search(r"a\s*[.、:：].*b\s*[.、:：]", focus, re.DOTALL)
        )
        if multiple_choice_task:
            return _reject("concept multiple-choice is not fundamentals analysis")
        audit_opinion = _contains(
            focus,
            ("审计意见", "保留意见", "无保留意见", "审计证据", "审计报告", "audit opinion", "qualified opinion", "audit evidence"),
        )
        audit_analysis = _contains(
            focus,
            ("分析原因", "为何", "为什么", "需要关注", "财务风险", "是否代表", "analyze", "why", "financial risk"),
        )
        audit_answer = _contains(
            answer,
            ("审计证据", "风险", "坏账", "减值", "应收", "真实", "完整", "audit evidence", "risk", "impairment", "receivable"),
        )
        if audit_opinion and audit_analysis and audit_answer and financial:
            grounding = "image_grounded" if has_image else "core_capability"
            return _accept(
                10.0 if has_image else 8.5,
                "audit_opinion_risk_analysis",
                grounding,
                "audit_opinion_evidence",
                "financial_risk_analysis",
            )

        operating_request = _contains(
            focus,
            (
                "分析公司的经营情况", "分析经营情况", "分析该数据变化", "经营情况", "经营盈利情况",
                "盈利情况", "偿债能力", "营运能力", "发展能力", "财务成本", "权益报酬率", "投资收益情况",
                "operating condition", "analyze operations",
            ),
        )
        operating_metrics = _contains(
            focus,
            ("营业收入", "营业成本", "营业利润", "毛利率", "收入构成", "利润构成", "净资产收益率", "职工总数", "revenue", "cost", "profit", "gross margin", "roe"),
        )
        operating_answer = _contains(
            answer,
            ("主营业务", "收入", "利润", "毛利率", "盈利能力", "成本", "员工", "main business", "revenue", "profit", "margin", "cost"),
        )
        retrieval_only = _contains(focus, ("原文", "原句", "exact sentence", "return the sentence", "extract the clause"))
        if operating_request and operating_metrics and operating_answer and financial and not retrieval_only:
            grounding = "image_grounded" if has_image else "core_capability"
            return _accept(
                10.0 if has_image else 8.5,
                "operating_fundamentals_analysis",
                grounding,
                "financial_operating_metrics",
                "evidence_based_operating_analysis",
            )

        fundamental_frame = _contains(focus, ("金融分析师", "财务咨询专员"))
        fundamental_request = _contains(
            focus,
            ("分析", "评价", "评估", "结论", "看出什么", "得到什么", "怎么样", "如何", "高吗", "稳定"),
        )
        table_evidence = bool(re.search(r"\d", focus)) and ("|" in focus or len(focus) >= 100)
        fundamental_metrics = _contains(
            focus,
            (
                "会计数据", "财务指标", "营业收入", "营业利润", "净利润", "毛利率", "现金流", "总资产",
                "净资产", "总负债", "收益率", "周转率", "负债率", "偿债", "营运资本", "财务费用",
                "研发投入", "股权质押", "机构持仓", "投资收益", "盈利", "营收", "成本", "利润",
                "主营产品", "产品业务数据", "知识产权", "股东户数", "限售股", "流通股东", "经营模式",
                "管理费用", "估值", "pe", "pb", "分红", "营业周期", "财务结构", "投入资本", "资本固化",
            ),
        )
        analytical_answer = len(answer) >= 20 and _contains(
            answer,
            (
                "收入", "营收", "利润", "盈利", "成本", "风险", "能力", "现金流", "资产", "负债", "上升", "下降",
                "增长", "降低", "稳定", "效率", "持仓", "股价", "创新", "研发", "估值", "分红", "结构", "周期",
                "影响", "利好", "利空",
            ),
        )
        if fundamental_frame and fundamental_request and table_evidence and fundamental_metrics and analytical_answer:
            grounding = "image_grounded" if has_image else "core_capability"
            return _accept(
                8.5 if has_image else 7.5,
                "structured_financial_fundamentals_analysis",
                grounding,
                "explicit_financial_analysis_request",
                "tabular_fundamental_metrics",
                "analytical_financial_answer",
            )
        rendered_fundamentals = has_image and _contains(
            focus,
            ("经营", "财务", "盈利", "营收", "偿债", "现金流", "收益", "成本", "能力", "风险"),
        )
        if fundamental_frame and fundamental_request and rendered_fundamentals and analytical_answer:
            return _accept(
                9.0,
                "image_grounded_financial_fundamentals_analysis",
                "image_grounded",
                "explicit_financial_analysis_request",
                "image_grounded_fundamental_evidence",
                "analytical_financial_answer",
            )
        return _reject("requires audit-opinion or operating-fundamentals analysis")

    raise ValueError(f"unknown capability: {capability}")


def assess_all(row: dict[str, Any]) -> dict[str, Decision]:
    """Assess all target capabilities while extracting row text only once."""
    question = _text(row, "user")
    answer = _text(row, "assistant")
    combined = f"{question} {answer}"
    prepared = (
        question,
        answer,
        combined,
        _focus_question(question),
        _has_image(row, question),
        _contains(combined, FINANCE_TERMS),
    )
    return {capability: assess_row(row, capability, prepared) for capability in CAPABILITIES}


def _content_hash(row: dict[str, Any]) -> str:
    messages = [
        {
            "role": str(message.get("role", "")),
            "content": " ".join(str(message.get("content", "")).split()),
        }
        for message in row.get("messages", [])
    ]
    payload = json.dumps(
        {
            "messages": messages,
            "images": [str(path).replace("\\", "/") for path in row.get("images", [])],
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _image_paths(row: dict[str, Any]) -> list[str]:
    images = row.get("images", [])
    if isinstance(images, str):
        return [images]
    if isinstance(images, list):
        return [str(image) for image in images]
    return []


def _benchmark_hashes(path: Path) -> set[str]:
    hashes: set[str] = set()
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                hashes.add(_content_hash(orjson.loads(line)))
    return hashes


def _cache_sources(paths: dict[str, Path]) -> dict[str, str]:
    return {name: str(path.resolve()) for name, path in paths.items()}


def _candidate_cache_record(capability: str, candidate: Candidate) -> dict[str, Any]:
    return {
        "capability": capability,
        "candidate": {
            "input_name": candidate.input_name,
            "line_number": candidate.line_number,
            "content_hash": candidate.content_hash,
            "score": candidate.score,
            "subtype": candidate.subtype,
            "reasons": list(candidate.reasons),
            "original_task": candidate.original_task,
            "source": candidate.source,
            "image_count": candidate.image_count,
            "review_reasons": list(candidate.review_reasons),
        },
    }


def _load_candidate_cache(
    cache_path: Path,
    paths: dict[str, Path],
) -> dict[str, list[Candidate]]:
    candidates: dict[str, list[Candidate]] = defaultdict(list)
    complete = False
    with cache_path.open("r", encoding="utf-8") as handle:
        first_line = handle.readline()
        if not first_line:
            raise ValueError(f"candidate cache is empty: {cache_path}")
        meta = json.loads(first_line).get("_meta", {})
        if meta.get("rule_version") != RULE_VERSION:
            raise ValueError(f"candidate cache rule version does not match: {cache_path}")
        if meta.get("sources") != _cache_sources(paths):
            raise ValueError(f"candidate cache source paths do not match: {cache_path}")
        for line in handle:
            if not line.strip():
                continue
            record = json.loads(line)
            if record.get("_complete") is True:
                complete = True
                continue
            capability = record["capability"]
            payload = record["candidate"]
            payload["reasons"] = tuple(payload.get("reasons", ()))
            payload["review_reasons"] = tuple(payload.get("review_reasons", ()))
            candidates[capability].append(Candidate(**payload))
    if not complete:
        raise ValueError(f"candidate cache is incomplete and cannot be reused: {cache_path}")
    for capability in CAPABILITIES:
        candidates[capability]
    return candidates


def _scan_inputs(
    paths: dict[str, Path],
    cache_path: Path | None = None,
) -> dict[str, list[Candidate]]:
    candidates: dict[str, list[Candidate]] = defaultdict(list)
    cache_handle = None
    if cache_path is not None:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_handle = cache_path.open("w", encoding="utf-8", buffering=1)
        cache_handle.write(
            json.dumps(
                {"_meta": {"rule_version": RULE_VERSION, "sources": _cache_sources(paths)}},
                ensure_ascii=False,
            )
            + "\n"
        )
    try:
        for input_name, path in paths.items():
            with path.open("r", encoding="utf-8") as handle:
                for line_number, line in enumerate(handle, 1):
                    if not line.strip():
                        continue
                    row = orjson.loads(line)
                    content_hash = _content_hash(row)
                    image_count = len(_image_paths(row)) + int(
                        "<image>" in _text(row, "user") and not row.get("images")
                    )
                    for capability, decision in assess_all(row).items():
                        if not decision.accepted:
                            continue
                        reviewed, review_reasons = review_alignment(row, capability, decision)
                        if not reviewed:
                            continue
                        candidate = Candidate(
                            input_name=input_name,
                            line_number=line_number,
                            content_hash=content_hash,
                            score=decision.score,
                            subtype=decision.subtype,
                            reasons=decision.reasons,
                            original_task=str(row.get("task", "")),
                            source=str(row.get("source", "")),
                            image_count=image_count,
                            review_reasons=review_reasons,
                        )
                        candidates[capability].append(candidate)
                        if cache_handle is not None:
                            cache_handle.write(
                                json.dumps(
                                    _candidate_cache_record(capability, candidate),
                                    ensure_ascii=False,
                                )
                                + "\n"
                            )
                    if line_number % 50000 == 0:
                        print(f"scanned {input_name}: {line_number:,}", flush=True)
        if cache_handle is not None:
            cache_handle.write(json.dumps({"_complete": True}) + "\n")
    finally:
        if cache_handle is not None:
            cache_handle.close()
    for capability in CAPABILITIES:
        candidates[capability]
    return candidates


def _select_capability(
    capability: str,
    candidates: list[Candidate],
    count: int,
    multimodal_target: int,
    benchmark_hashes: set[str],
) -> list[Candidate]:
    if capability != "compliance_safety_suitability":
        return select_modality_quota(candidates, count, multimodal_target, benchmark_hashes)

    strict_target = round(count / 7)
    strict_multimodal_target = round(multimodal_target * strict_target / count) if count else 0
    strict = [item for item in candidates if item.subtype == "compliance_rule_application"]
    mechanism = [item for item in candidates if item.subtype == "benchmark_financial_mechanism"]
    selected = select_modality_quota(
        strict,
        strict_target,
        strict_multimodal_target,
        benchmark_hashes,
    )
    excluded = benchmark_hashes | {item.content_hash for item in selected}
    selected.extend(
        select_modality_quota(
            mechanism,
            count - len(selected),
            max(0, multimodal_target - sum(item.image_count > 0 for item in selected)),
            excluded,
        )
    )
    excluded = benchmark_hashes | {item.content_hash for item in selected}
    if len(selected) < count:
        selected.extend(select_top(candidates, count - len(selected), excluded))
    return selected


def _selected_lookup(selected: dict[str, list[Candidate]]) -> dict[tuple[str, int], list[tuple[str, Candidate]]]:
    lookup: dict[tuple[str, int], list[tuple[str, Candidate]]] = defaultdict(list)
    for capability, items in selected.items():
        for item in items:
            lookup[(item.input_name, item.line_number)].append((capability, item))
    return lookup


def _write_outputs(
    paths: dict[str, Path],
    output_dir: Path,
    selected: dict[str, list[Candidate]],
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    audit_dir = output_dir / "audit"
    audit_dir.mkdir(parents=True, exist_ok=True)
    data_handles = {
        capability: (output_dir / f"{capability}.jsonl").open("w", encoding="utf-8")
        for capability in CAPABILITIES
    }
    audit_handles = {
        capability: (audit_dir / f"{capability}.jsonl").open("w", encoding="utf-8")
        for capability in CAPABILITIES
    }
    lookup = _selected_lookup(selected)
    try:
        for input_name, path in paths.items():
            with path.open("r", encoding="utf-8") as handle:
                for line_number, line in enumerate(handle, 1):
                    matches = lookup.get((input_name, line_number))
                    if not matches:
                        continue
                    row = orjson.loads(line)
                    for capability, candidate in matches:
                        data_handles[capability].write(line.rstrip("\r\n") + "\n")
                        audit = {
                            "capability": capability,
                            "input_name": input_name,
                            "source_file": str(path.resolve()),
                            "line_number": line_number,
                            "content_hash": candidate.content_hash,
                            "score": candidate.score,
                            "subtype": candidate.subtype,
                            "reasons": list(candidate.reasons),
                            "review_status": "approved",
                            "review_method": "second_stage_question_answer_content_review",
                            "review_reasons": list(candidate.review_reasons),
                            "original_task": candidate.original_task,
                            "source": candidate.source,
                            "split_ignored": True,
                            "original_split": row.get("split"),
                            "image_existence_checked": False,
                            "declared_images": _image_paths(row),
                            "image_count": candidate.image_count,
                        }
                        audit_handles[capability].write(
                            json.dumps(audit, ensure_ascii=False) + "\n"
                        )
    finally:
        for handle in data_handles.values():
            handle.close()
        for handle in audit_handles.values():
            handle.close()


def _write_summary(
    output_dir: Path,
    selected: dict[str, list[Candidate]],
    candidate_counts: dict[str, int],
    benchmark_count: int,
    requested_count: int,
) -> None:
    summary: dict[str, Any] = {
        "benchmark_rows": benchmark_count,
        "requested_per_capability": requested_count,
        "selection_policy": {
            "split_ignored": True,
            "image_existence_checked": False,
            "labels_used_for_acceptance": False,
            "exact_benchmark_rows_excluded": True,
        },
        "capabilities": {},
    }
    for capability in CAPABILITIES:
        items = selected[capability]
        summary["capabilities"][capability] = {
            "candidate_count": candidate_counts[capability],
            "selected_count": len(items),
            "shortfall": max(0, requested_count - len(items)),
            "subtypes": dict(Counter(item.subtype for item in items)),
            "input_files": dict(Counter(item.input_name for item in items)),
            "original_tasks": dict(Counter(item.original_task for item in items)),
            "sources": dict(Counter(item.source for item in items)),
            "declared_image_rows": sum(item.image_count > 0 for item in items),
        }
    with (output_dir / "selection_summary.json").open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def _parse_named_input(value: str) -> tuple[str, Path]:
    name, separator, path = value.partition("=")
    if not separator or not name.strip() or not path.strip():
        raise argparse.ArgumentTypeError("--input must use name=path")
    return name.strip(), Path(path.strip())


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--train-text", type=Path, default=Path("data/train_text_sft.jsonl"))
    parser.add_argument("--train-multi", type=Path, default=Path("data/train_multi.jsonl"))
    parser.add_argument("--input", action="append", type=_parse_named_input, default=[])
    parser.add_argument("--benchmark", type=Path, default=Path("data/benchmark/my_benchmark/all.jsonl"))
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/benchmark_aligned_declining_tasks"),
    )
    parser.add_argument("--per-capability", type=int, default=2000)
    parser.add_argument("--multimodal-per-capability", type=int, default=1500)
    parser.add_argument("--count-only", action="store_true")
    parser.add_argument("--candidate-cache", type=Path)
    parser.add_argument("--reuse-candidate-cache", action="store_true")
    parser.add_argument("--allow-shortfall", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    paths = {"train_text": args.train_text, "train_multi": args.train_multi}
    paths.update(dict(args.input))
    benchmark_hashes = _benchmark_hashes(args.benchmark)
    cache_path = args.candidate_cache or args.output_dir / "reviewed_candidate_cache.jsonl"
    if args.reuse_candidate_cache:
        candidates = _load_candidate_cache(cache_path, paths)
    else:
        candidates = _scan_inputs(paths, cache_path)
    candidate_counts = {capability: len(candidates[capability]) for capability in CAPABILITIES}
    print(json.dumps(candidate_counts, ensure_ascii=False, indent=2), flush=True)
    if args.count_only:
        return

    selected = {
        capability: _select_capability(
            capability,
            candidates[capability],
            args.per_capability,
            args.multimodal_per_capability,
            benchmark_hashes,
        )
        for capability in CAPABILITIES
    }
    insufficient = {
        capability: len(items)
        for capability, items in selected.items()
        if len(items) != args.per_capability
    }
    if insufficient:
        if not args.allow_shortfall:
            raise RuntimeError(
                f"insufficient benchmark-aligned rows (wanted {args.per_capability}): {insufficient}"
            )
        print(
            f"warning: writing verified shortfalls instead of filling with misaligned rows: {insufficient}",
            flush=True,
        )
    _write_outputs(paths, args.output_dir, selected)
    _write_summary(
        args.output_dir,
        selected,
        candidate_counts,
        len(benchmark_hashes),
        args.per_capability,
    )
    print(f"wrote {sum(len(items) for items in selected.values()):,} rows to {args.output_dir}", flush=True)


if __name__ == "__main__":
    main()
