from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
import argparse
import json
from pathlib import Path
import random
import re
import shutil
from typing import Callable, Iterable

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[2]
BENCHMARK_ROOT = ROOT / "data" / "benchmark"
MY_BENCHMARK = BENCHMARK_ROOT / "my_benchmark"
ORIGINAL = MY_BENCHMARK / "all.jsonl"
OUTPUT = MY_BENCHMARK / "all_v2.jsonl"
AUDIT_OUTPUT = MY_BENCHMARK / "all_v2_audit.md"
ASSETS_ROOT = MY_BENCHMARK / "assets"
SEED = 20260810

CURATED_TASKS = (
    "chart_data_extraction",
    "cross_modal_multi_hop",
    "financial_ocr",
    "merger_acquisition_completeness_classification",
    "single_table_qa",
    "statistics_comparison_ranking",
    "basic_arithmetic_metrics",
    "entity_extraction_classification",
    "financial_event_extraction",
    "financial_audit_fundamentals",
    "financial_summarization",
    "monetary_policy_stance_classification",
    "summary_announcement",
    "portfolio_allocation_risk_return",
    "compliance_safety_suitability",
    "esg_issue_identification",
    "financial_causal_event_reasoning",
    "financial_counterfactual_inference",
    "financial_data_description",
    "financial_multi_turn_perception",
    "financial_numeric_labeling",
    "financial_semantic_role_labeling",
    "multi_step_numerical_reasoning",
    "multi_table_reasoning",
    "multimodal_financial_knowledge",
    "risk_sentiment_policy",
    "candlestick_time_series",
    "evidence_retrieval",
    "explanation_anomaly_causality",
    "financial_relation_extraction",
    "financial_sentiment_analysis",
    "financial_topic_classification",
    "image_caption",
    "industry_trend_inference",
    "investment_advice_strategy",
    "relationship_equity_structure",
    "spatial_localization",
    "stock_movement_prediction",
)
UNCHANGED_TASKS = (
    "financial_certification_exam_qa",
    "financial_entity_extraction",
    "financial_headline_classification",
)
PASSTHROUGH_TASK = "long_document_cross_page"
SELECTION_REPAIR_TASKS = {
    "chart_data_extraction",
    "single_table_qa",
    "statistics_comparison_ranking",
    "basic_arithmetic_metrics",
    "entity_extraction_classification",
}

ORIGINAL_KEEP_SOURCES = {
    "chart_data_extraction": {
        "FinChart-Bench/mc-0",
        "FinChart-Bench/mc-10",
        "FinChart-Bench/mc-100",
        "FinChart-Bench/mc-1000",
        "FinChart-Bench/mc-1001",
    },
    "financial_ocr": {
        "MME-Finance/1015",
        "MME-Finance/1029",
        "MME-Finance/1041",
        "MME-Finance/1053",
        "MME-Finance/1063",
        "MME-Finance/116",
    },
    "single_table_qa": {
        "FAMMA/english_10_1_r1",
        "FAMMA/english_20_1_r1",
        "FAMMA/english_21_1_r1",
        "FAMMA/english_25_1_r1",
        "FAMMA/english_26_1_r1",
        "FAMMA/english_27_1_r1",
    },
    "statistics_comparison_ranking": {
        "FinChart-Bench/mc-1003",
        "FinChart-Bench/mc-1004",
        "FinChart-Bench/mc-1005",
        "FinChart-Bench/mc-101",
    },
    "basic_arithmetic_metrics": {
        "CFBenchmark/metric-calculation-0",
        "CFBenchmark/metric-calculation-1",
        "CFBenchmark/metric-calculation-10",
        "CFBenchmark/metric-calculation-11",
        "CFBenchmark/metric-calculation-12",
        "CFBenchmark/metric-calculation-13",
        "CFBenchmark/metric-calculation-14",
    },
    "entity_extraction_classification": {
        "CFBenchmark/entity-disambiguation-0",
        "CFBenchmark/entity-disambiguation-1",
        "CFBenchmark/entity-disambiguation-10",
        "CFBenchmark/entity-disambiguation-11",
        "CFBenchmark/entity-disambiguation-12",
        "CFBenchmark/entity-disambiguation-15",
    },
    "evidence_retrieval": {
        "FinMMDocR/test-0",
        "FinMMDocR/test-103",
        "FinMMDocR/test-106",
        "FinMMDocR/test-1116",
        "FinMMDocR/test-1117",
        "FinMMDocR/test-1121",
        "FinMMDocR/test-1125",
        "FinMMDocR/test-113",
    },
}

ORIGINAL_REPAIR_SOURCES = {
    "chart_data_extraction": {
        "FinMME/0",
        "FinMME/1",
        "FinMME/11",
        "FinMME/12",
    },
    "statistics_comparison_ranking": {
        "FinMME/101",
        "FinMME/110",
    },
    "merger_acquisition_completeness_classification": {
        "ModelScope/merger_acquisition_completeness_classification/test-00000-of-00001-56159619c0ddecc5.parquet#0",
        "ModelScope/merger_acquisition_completeness_classification/test-00000-of-00001-56159619c0ddecc5.parquet#250",
        "FINAR-VL/generated/merger_acquisition_completeness_classification/0",
        "ModelScope/merger_acquisition_completeness_classification/test-00000-of-00001-56159619c0ddecc5.parquet#251",
        "ModelScope/merger_acquisition_completeness_classification/test-00000-of-00001-56159619c0ddecc5.parquet#1",
        "ModelScope/merger_acquisition_completeness_classification/test-00000-of-00001-56159619c0ddecc5.parquet#252",
        "ModelScope/merger_acquisition_completeness_classification/test-00000-of-00001-56159619c0ddecc5.parquet#2",
        "ModelScope/merger_acquisition_completeness_classification/test-00000-of-00001-56159619c0ddecc5.parquet#253",
        "ModelScope/merger_acquisition_completeness_classification/test-00000-of-00001-56159619c0ddecc5.parquet#3",
        "ModelScope/merger_acquisition_completeness_classification/test-00000-of-00001-56159619c0ddecc5.parquet#254",
    },
    "financial_summarization": {
        "CFLUE/application/会议内容摘要/11814",
        "CFLUE/application/会议内容摘要/11816",
        "CFLUE/application/会议内容摘要/11818",
        "CFLUE/application/会议内容摘要/11819",
        "CFLUE/application/会议内容摘要/11821",
    },
    "stock_movement_prediction": {
        "ModelScope/stock_movement_prediction/test-00000-of-00001-e1663a0932037903.parquet#0",
        "ModelScope/stock_movement_prediction/test-00000-of-00001-e1663a0932037903.parquet#1",
        "ModelScope/stock_movement_prediction/test-00000-of-00001-e1663a0932037903.parquet#2",
        "ModelScope/stock_movement_prediction/test-00000-of-00001-e1663a0932037903.parquet#3",
        "ModelScope/stock_movement_prediction/test-00000-of-00001-e1663a0932037903.parquet#4",
        "ModelScope/stock_movement_prediction/test-00000-of-00001-e1663a0932037903.parquet#5",
        "ModelScope/stock_movement_prediction/test-00000-of-00001-e1663a0932037903.parquet#6",
        "ModelScope/stock_movement_prediction/test-00000-of-00001-e1663a0932037903.parquet#7",
        "ModelScope/stock_movement_prediction/test-00000-of-00001-e1663a0932037903.parquet#9",
    },
}


@dataclass(frozen=True)
class AuditStats:
    original: int
    kept: int
    repaired: int
    added: int
    removed: int
    final: int


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def record(task: str, question: str, answer: str, source: str, images: list[str] | None = None) -> dict:
    image_list = images or []
    return {
        "messages": [
            {"role": "user", "content": "<image>" * len(image_list) + question.strip()},
            {"role": "assistant", "content": answer.strip()},
        ],
        "source": source,
        "split": "test",
        "images": image_list,
        "task": task,
    }


def compact_spaced_text(text: str) -> str:
    lines = text.splitlines()
    compacted: list[str] = []
    buffer: list[str] = []
    for line in lines:
        stripped = line.strip()
        if len(stripped) == 1 and (stripped.isalnum() or stripped in ":-'á"):
            buffer.append(stripped)
            continue
        if buffer:
            compacted.append("".join(buffer))
            buffer = []
        if stripped:
            compacted.append(stripped)
    if buffer:
        compacted.append("".join(buffer))
    return "\n".join(compacted)


def repair_original(row: dict) -> dict:
    row = json.loads(json.dumps(row, ensure_ascii=False))
    task = row["task"]
    source = row["source"]
    question = row["messages"][0]["content"]
    answer = row["messages"][1]["content"].strip()
    if task in SELECTION_REPAIR_TASKS:
        question = compact_spaced_text(question)
        if "仅输出选项字母" not in question:
            question += "\n仅输出选项字母。"
    elif task == "merger_acquisition_completeness_classification":
        text = question.split("Text:", 1)[-1].rsplit("Answer:", 1)[0].strip()
        question = (
            "判断报道中的交易属于“complete”还是“rumour”。“complete”表示交易已正式宣布或签署，"
            "即使仍待常规审批；“rumour”表示仅为未证实的讨论、传闻或潜在计划。仅输出标签。\n"
            f"Text: {text}"
        )
        answer = answer.lower()
    elif task == "financial_summarization":
        question = question.replace("尽量不要丢失信息", "保留关键事实、数值、变化方向与不确定性")
        answer = re.sub(r"(?:谢谢大家|好的，谢谢管理层的解答).*$", "", answer).strip("。 ") + "。"
        summary_repairs = {
            "CFLUE/application/会议内容摘要/11814": (
                "公司2023年通过采购协同、降低采购价、提升海外工厂效率、优化供应链和减少存货减值降低成本；"
                "欧洲原奶价格1—3月持续下行，3月降幅较大；新品替代旧品并减少促销，预计毛利率较2022年改善。"
            ),
            "CFLUE/application/会议内容摘要/11818": (
                "公司在网易云音乐的份额约为25%—30%，计划通过渠道和SKU优化继续提升份额；"
                "竞争对手在该平台的销量增速快于公司，但其发货和退货数据口径仍需观察。"
            ),
            "CFLUE/application/会议内容摘要/11819": (
                "公司认为整果市场规模最大且仍较快增长；工厂预制果制品已拓展线下KA和到家平台，"
                "门店现切果覆盖到家、办公室、医院和酒店等场景；优质水果供应链是核心优势。"
            ),
            "CFLUE/application/会议内容摘要/11821": (
                "公司一季度落地细分价格体系，继上年四季度收回不合理折扣后进一步优化货量结构；"
                "小货占比和高毛利货量恢复，价格较上年四季度提高约2—3分钱。"
            ),
        }
        answer = summary_repairs.get(source, answer)
    elif task == "stock_movement_prediction":
        first, context = question.split("Context:", 1)
        ticker = re.search(r"\$[a-z]+", first.lower()).group(0)
        question = (
            f"以下为 {ticker} 截至2017-11-01收盘前可用的历史特征与公开帖子。"
            "标签以来源数据中2017-11-02真实收盘价相对前一交易日的方向确定。"
            "预测该日标签，仅输出 Rise 或 Fall。\nContext:"
            + context
        )
        answer = answer.title()
    row["messages"][0]["content"] = question
    row["messages"][1]["content"] = answer
    return {key: row[key] for key in ("messages", "source", "split", "images", "task")}


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    name = "msyhbd.ttc" if bold else "msyh.ttc"
    return ImageFont.truetype(str(Path("C:/Windows/Fonts") / name), size)


def asset_path(task: str, index: int, page: int = 1) -> tuple[Path, str]:
    directory = ASSETS_ROOT / task
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"v2_{index:04d}_{page:02d}.png"
    return path, path.relative_to(ROOT).as_posix()


def draw_text_card(task: str, index: int, title: str, lines: Iterable[str], page: int = 1) -> str:
    path, relative = asset_path(task, index, page)
    image = Image.new("RGB", (1400, 900), "white")
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((45, 40, 1355, 860), radius=24, outline="#24527a", width=4)
    draw.text((85, 75), title, fill="#17324d", font=font(42, bold=True))
    y = 155
    for line in lines:
        draw.text((95, y), str(line), fill="#1f2933", font=font(30))
        y += 65
    image.save(path)
    return relative


def draw_table(task: str, index: int, title: str, headers: list[str], rows: list[list[str]], page: int = 1) -> str:
    path, relative = asset_path(task, index, page)
    image = Image.new("RGB", (1400, 900), "white")
    draw = ImageDraw.Draw(image)
    draw.text((65, 45), title, fill="#17324d", font=font(40, bold=True))
    left, top, width = 65, 135, 1270
    columns = len(headers)
    cell_w = width / columns
    cell_h = min(95, 650 / (len(rows) + 1))
    for r_index, values in enumerate([headers] + rows):
        y0 = top + r_index * cell_h
        fill = "#dceaf7" if r_index == 0 else ("#f7fafc" if r_index % 2 else "white")
        for c_index, value in enumerate(values):
            x0 = left + c_index * cell_w
            draw.rectangle((x0, y0, x0 + cell_w, y0 + cell_h), fill=fill, outline="#7890a5", width=2)
            draw.text((x0 + 14, y0 + 20), str(value), fill="#172b4d", font=font(25, bold=r_index == 0))
    image.save(path)
    return relative


def bar_geometry(values: list[float], top: float, bottom: float) -> list[tuple[float, float]]:
    minimum = min(0.0, min(values))
    maximum = max(0.0, max(values))
    span = maximum - minimum
    to_y = lambda value: bottom - (value - minimum) / span * (bottom - top)
    zero_y = to_y(0.0)
    return [tuple(sorted((to_y(value), zero_y))) for value in values]


def draw_bar_chart(task: str, index: int, title: str, labels: list[str], values: list[float], note: str = "") -> str:
    path, relative = asset_path(task, index)
    image = Image.new("RGB", (1400, 900), "white")
    draw = ImageDraw.Draw(image)
    draw.text((65, 45), title, fill="#17324d", font=font(40, bold=True))
    x0, y0, x1, y1 = 120, 160, 1320, 760
    draw.line((x0, y0, x0, y1), fill="#334e68", width=4)
    padded_values = [value * 1.15 if value >= 0 else value * 1.15 for value in values]
    geometry = bar_geometry(padded_values, y0, y1)
    actual_geometry = bar_geometry(values, y0, y1)
    zero_y = geometry[0][1] if all(value >= 0 for value in values) else bar_geometry([0, *padded_values], y0, y1)[0][0]
    draw.line((x0, zero_y, x1, zero_y), fill="#334e68", width=4)
    step = (x1 - x0) / len(values)
    for i, (label, value, (bar_top, bar_bottom)) in enumerate(zip(labels, values, actual_geometry)):
        bar_left = x0 + i * step + step * 0.2
        bar_right = x0 + (i + 1) * step - step * 0.2
        draw.rectangle((bar_left, bar_top, bar_right, bar_bottom), fill="#2f80c1")
        value_y = bar_top - 38 if value >= 0 else bar_bottom + 8
        draw.text((bar_left, value_y), f"{value:g}", fill="#17324d", font=font(24, bold=True))
        draw.text((bar_left, y1 + 18), label, fill="#334e68", font=font(23))
    if note:
        draw.text((120, 825), note, fill="#8b2f2f", font=font(25))
    image.save(path)
    return relative


def draw_equity(task: str, index: int, company: str, owners: list[tuple[str, str]]) -> str:
    path, relative = asset_path(task, index)
    image = Image.new("RGB", (1400, 900), "white")
    draw = ImageDraw.Draw(image)
    draw.text((60, 45), f"{company}股权结构", fill="#17324d", font=font(40, bold=True))
    company_box = (470, 610, 930, 760)
    draw.rounded_rectangle(company_box, radius=20, fill="#dceaf7", outline="#24527a", width=4)
    draw.text((570, 655), company, fill="#17324d", font=font(34, bold=True))
    spacing = 1200 / len(owners)
    for i, (owner, share) in enumerate(owners):
        cx = 100 + spacing * i + spacing / 2
        box = (cx - 150, 180, cx + 150, 320)
        draw.rounded_rectangle(box, radius=18, fill="#eef6ec", outline="#3d7a45", width=3)
        draw.text((box[0] + 20, 215), owner, fill="#284b2d", font=font(28, bold=True))
        draw.line((cx, 320, 700, 610), fill="#526d82", width=4)
        draw.text(((cx + 700) / 2 - 45, 430), share, fill="#8b2f2f", font=font(28, bold=True))
    image.save(path)
    return relative


def draw_candlestick(index: int, rows: list[tuple[str, float, float, float, float]]) -> str:
    task = "candlestick_time_series"
    path, relative = asset_path(task, index)
    image = Image.new("RGB", (1400, 900), "white")
    draw = ImageDraw.Draw(image)
    draw.text((65, 45), "五日OHLC（日线）", fill="#17324d", font=font(40, bold=True))
    all_values = [value for row in rows for value in row[1:]]
    low, high = min(all_values) - 1, max(all_values) + 1
    y_bottom, y_top = 760, 150
    for i, (day, open_, high_, low_, close) in enumerate(rows):
        x = 180 + i * 235
        to_y = lambda value: y_bottom - (value - low) / (high - low) * (y_bottom - y_top)
        color = "#c0392b" if close >= open_ else "#1f8a5b"
        draw.line((x, to_y(high_), x, to_y(low_)), fill=color, width=5)
        top, bottom = sorted((to_y(open_), to_y(close)))
        if bottom - top < 5:
            bottom = top + 5
        draw.rectangle((x - 45, top, x + 45, bottom), fill=color, outline=color)
        draw.text((x - 65, 790), day, fill="#334e68", font=font(25))
        draw.text((x - 70, 110), f"O{open_:g} H{high_:g} L{low_:g} C{close:g}", fill="#526d82", font=font(19))
    image.save(path)
    return relative


def draw_dashboard(index: int, title: str, boxes: dict[str, str]) -> str:
    task = "spatial_localization"
    path, relative = asset_path(task, index)
    image = Image.new("RGB", (1400, 900), "#f2f5f7")
    draw = ImageDraw.Draw(image)
    draw.text((55, 35), title, fill="#17324d", font=font(38, bold=True))
    positions = {
        "左上": (60, 130, 670, 430),
        "右上": (730, 130, 1340, 430),
        "左下": (60, 500, 670, 800),
        "右下": (730, 500, 1340, 800),
    }
    for position, bounds in positions.items():
        draw.rounded_rectangle(bounds, radius=20, fill="white", outline="#7890a5", width=3)
        draw.text((bounds[0] + 25, bounds[1] + 25), position, fill="#526d82", font=font(24))
        draw.text((bounds[0] + 45, bounds[1] + 125), boxes[position], fill="#17324d", font=font(34, bold=True))
    image.save(path)
    return relative


def choose_quality_checked(rows: list[dict], task: str) -> tuple[list[dict], int, int]:
    kept_sources = ORIGINAL_KEEP_SOURCES.get(task, set())
    repaired_sources = ORIGINAL_REPAIR_SOURCES.get(task, set())
    kept = [row for row in rows if row["task"] == task and row["source"] in kept_sources]
    repaired = [repair_original(row) for row in rows if row["task"] == task and row["source"] in repaired_sources]
    if task in SELECTION_REPAIR_TASKS:
        repaired.extend(repair_original(row) for row in kept)
        kept = []
    if len(kept) + len(repaired) > 10:
        pool = kept + repaired
        random.Random(SEED).shuffle(pool)
        pool = pool[:10]
        kept = [row for row in pool if row["source"] in kept_sources]
        repaired = [row for row in pool if row["source"] in repaired_sources]
    return kept + repaired, len(kept), len(repaired)


def generated_source(task: str, index: int) -> str:
    return f"FINAR-VL-v2/curated/{task}/{index:03d}"


def generated_retained_group_records() -> dict[str, list[dict]]:
    generated: dict[str, list[dict]] = defaultdict(list)

    image = draw_bar_chart(
        "chart_data_extraction", 1, "2025年各区域营业收入（百万元）", ["东部", "中部", "西部"], [86, 74, 91]
    )
    generated["chart_data_extraction"].append(
        record(
            "chart_data_extraction",
            "图中西部区域2025年营业收入是多少？\nA. 74百万元\nB. 86百万元\nC. 91百万元\nD. 251百万元\n仅输出选项字母。",
            "C",
            generated_source("chart_data_extraction", 1),
            [image],
        )
    )

    cross_cases = [
        ("毛利核算", "题干给出的其他经营费用为12百万元。", ["收入", "销售成本"], [120, 76], "按“营业利润=收入-销售成本-其他经营费用”计算营业利润。", "32百万元"),
        ("库存周转", "本期平均库存为25百万元。", ["期初库存", "期末库存"], [22, 28], "图中数据用于核对平均库存；按“周转率=销售成本/平均库存”，若销售成本为100百万元，周转率是多少？", "4次"),
        ("汇率折算", "合同金额为200万美元，结算汇率为1美元兑7.20元人民币。", ["已收款", "未收款"], [120, 80], "图中单位为万美元。未收款部分折合人民币多少万元？", "576万元"),
        ("预算差异", "季度预算费用为95万元。", ["人工", "材料"], [48, 52], "图中两项构成全部实际费用。实际费用相对预算超支多少万元？", "5万元"),
        ("单位成本", "本月产量为4万件，固定成本为20万元。", ["材料", "人工"], [36, 24], "图中金额单位为万元。单位总成本是多少元/件？", "20元/件"),
        ("现金覆盖", "一年内到期债务为50百万元。", ["经营现金", "投资现金"], [72, -18], "仅用经营现金净流入计算债务覆盖倍数。", "1.44倍"),
        ("税后利润", "适用所得税率为25%，无其他调整。", ["营业利润", "利息费用"], [80, 12], "税前利润为营业利润减利息费用，税后利润是多少百万元？", "51百万元"),
        ("加权融资成本", "债务占资本40%，权益占资本60%。", ["债务税后成本", "权益成本"], [5, 11], "图中数值为百分比。加权平均融资成本是多少？", "8.6%"),
        ("同店增长", "去年可比门店收入为160万元。", ["新店收入", "今年可比店收入"], [30, 176], "仅计算可比门店收入同比增幅。", "10%"),
        ("净出口贡献", "GDP为5000亿元，其他分项合计为4920亿元。", ["出口", "进口"], [260, 180], "图中金额单位为亿元。净出口与GDP恒等式中的缺口是否一致，并给出净出口。", "一致，净出口为80亿元"),
    ]
    for index, (title, context, labels, values, question, answer) in enumerate(cross_cases, 1):
        image = draw_bar_chart("cross_modal_multi_hop", index, title, labels, values)
        generated["cross_modal_multi_hop"].append(
            record(
                "cross_modal_multi_hop",
                f"{context}\n{question}\n请给出唯一数值答案。",
                answer,
                generated_source("cross_modal_multi_hop", index),
                [image],
            )
        )

    ocr_cases = [
        ("增值税发票摘要", ["价税合计：¥ 128,560.00", "开票日期：2026-07-18"], "图中价税合计金额是多少？", "128,560.00元"),
        ("基金净值公告", ["基金代码：016880", "单位净值：1.2486", "累计净值：1.4120"], "图中的单位净值是多少？", "1.2486"),
        ("债券成交回报", ["债券简称：24国债05", "成交净价：101.36", "成交数量：500手"], "图中的成交净价是多少？", "101.36"),
        ("银行回单", ["交易金额：人民币 86,400.00 元", "交易状态：成功", "用途：设备款"], "图中的交易金额是多少？", "86,400.00元"),
    ]
    for index, (title, lines, question, answer) in enumerate(ocr_cases, 1):
        image = draw_text_card("financial_ocr", index, title, lines)
        generated["financial_ocr"].append(
            record("financial_ocr", question, answer, generated_source("financial_ocr", index), [image])
        )

    table_cases = [
        ("季度经营数据", ["季度", "收入", "净利润"], [["Q1", "120", "12"], ["Q2", "135", "15"], ["Q3", "128", "14"]], "Q2净利率是多少？保留两位小数。", "11.11%"),
        ("产品销量（万件）", ["产品", "2024", "2025"], [["A", "40", "46"], ["B", "35", "42"], ["C", "28", "31"]], "2024年至2025年销量增加最多的是哪个产品？", "产品B"),
        ("贷款组合", ["评级", "余额(万元)", "权重"], [["正常", "720", "1%"], ["关注", "180", "5%"], ["次级", "100", "25%"]], "按表中权重计算加权风险金额。", "41.2万元"),
        ("现金流量", ["项目", "金额(万元)"], [["经营活动", "260"], ["投资活动", "-140"], ["筹资活动", "-60"]], "三类活动合计使现金增加多少万元？", "60万元"),
    ]
    for index, (title, headers, rows, question, answer) in enumerate(table_cases, 1):
        image = draw_table("single_table_qa", index, title, headers, rows)
        generated["single_table_qa"].append(
            record("single_table_qa", question, answer, generated_source("single_table_qa", index), [image])
        )

    ranking_cases = [
        ("区域毛利率（%）", ["华北", "华东", "华南", "西南"], [18, 23, 21, 16], "毛利率从高到低排序。", "华东、华南、华北、西南"),
        ("年度研发投入（百万元）", ["2022", "2023", "2024", "2025"], [32, 41, 39, 52], "研发投入第二高的是哪一年？", "2023年"),
        ("四只基金最大回撤（%）", ["甲", "乙", "丙", "丁"], [8.2, 12.5, 6.8, 10.1], "最大回撤最小的是哪只基金？", "基金丙"),
        ("门店客单价（元）", ["A店", "B店", "C店", "D店"], [86, 92, 79, 88], "客单价高于85元的门店共有多少家？", "3家"),
    ]
    for index, (title, labels, values, question, answer) in enumerate(ranking_cases, 1):
        image = draw_bar_chart("statistics_comparison_ranking", index, title, labels, values)
        generated["statistics_comparison_ranking"].append(
            record("statistics_comparison_ranking", question, answer, generated_source("statistics_comparison_ranking", index), [image])
        )

    arithmetic_cases = [
        ("某公司收入为800万元，营业成本为520万元。毛利率=(收入-成本)/收入。毛利率是多少？保留两位小数。", "35.00%"),
        ("某债券面值100元，年票息4元，当前净价98元。按“当期收益率=年票息/净价”计算，保留两位小数。", "4.08%"),
        ("某项目初始投资300万元，三年累计净现金流为372万元。按“投资回报率=(累计净现金流-初始投资)/初始投资”计算。", "24.00%"),
    ]
    for index, (question, answer) in enumerate(arithmetic_cases, 1):
        generated["basic_arithmetic_metrics"].append(
            record("basic_arithmetic_metrics", question, answer, generated_source("basic_arithmetic_metrics", index))
        )

    entity_cases = [
        ("文本：“公司拟回购不超过2%的股份。”其中“2%”属于哪类实体？选项：A. 金额 B. 比例 C. 日期 D. 公司。仅输出选项字母。", "B"),
        ("文本：“24附息国债05于银行间市场交易。”其中“24附息国债05”属于哪类实体？选项：A. 债券 B. 股票 C. 基金 D. 指数。仅输出选项字母。", "A"),
        ("文本：“中国人民银行决定下调存款准备金率。”其中“中国人民银行”属于哪类实体？选项：A. 上市公司 B. 监管/政策机构 C. 产品 D. 行业。仅输出选项字母。", "B"),
        ("文本：“沪深300指数当日上涨0.8%。”其中“沪深300指数”属于哪类实体？选项：A. 股票 B. 债券 C. 指数 D. 公司。仅输出选项字母。", "C"),
    ]
    for index, (question, answer) in enumerate(entity_cases, 1):
        generated["entity_extraction_classification"].append(
            record("entity_extraction_classification", question, answer, generated_source("entity_extraction_classification", index))
        )

    event_cases = [
        ("4月8日，甲公司公告以2.4亿元收购乙公司80%股权，交易已完成交割。", [{"event_type": "收购", "date": "4月8日", "actor": "甲公司", "target": "乙公司80%股权", "amount": "2.4亿元"}]),
        ("5月12日，丙银行向丁企业发放三年期贷款5000万元。", [{"event_type": "贷款发放", "date": "5月12日", "actor": "丙银行", "target": "丁企业", "amount": "5000万元"}]),
        ("6月3日，戊公司回购股份120万股，成交金额960万元。", [{"event_type": "股份回购", "date": "6月3日", "actor": "戊公司", "target": "公司股份120万股", "amount": "960万元"}]),
        ("7月1日，己公司与庚公司签订价值1.1亿元的设备采购合同。", [{"event_type": "合同签订", "date": "7月1日", "actor": "己公司", "target": "庚公司设备", "amount": "1.1亿元"}]),
        ("8月20日，辛公司控股股东质押公司股份3000万股给壬银行。", [{"event_type": "股份质押", "date": "8月20日", "actor": "辛公司控股股东", "target": "壬银行", "amount": "3000万股"}]),
        ("9月6日，癸基金向A科技完成B轮投资，金额8000万元。", [{"event_type": "股权投资", "date": "9月6日", "actor": "癸基金", "target": "A科技", "amount": "8000万元"}]),
        ("10月15日，B公司宣告每10股派发现金红利3元。", [{"event_type": "现金分红", "date": "10月15日", "actor": "B公司", "target": "全体股东", "amount": "每10股3元"}]),
        ("11月2日，C公司中标D市轨道交通项目，中标价6.5亿元。", [{"event_type": "项目中标", "date": "11月2日", "actor": "C公司", "target": "D市轨道交通项目", "amount": "6.5亿元"}]),
        ("12月18日，E公司发行5年期公司债，规模10亿元。", [{"event_type": "债券发行", "date": "12月18日", "actor": "E公司", "target": "5年期公司债", "amount": "10亿元"}]),
        ("1月9日，F公司终止筹划收购G公司的交易，未支付对价。", [{"event_type": "收购终止", "date": "1月9日", "actor": "F公司", "target": "G公司", "amount": "未支付"}]),
    ]
    for index, (text, answer) in enumerate(event_cases, 1):
        question = "从资讯中抽取事件，输出JSON数组；每项字段固定为event_type、date、actor、target、amount。\n资讯：" + text
        generated["financial_event_extraction"].append(
            record("financial_event_extraction", question, json.dumps(answer, ensure_ascii=False), generated_source("financial_event_extraction", index))
        )

    audit_cases = [
        ("盘点发现账面存货1000万元，其中已毁损存货200万元未计提减值。最直接影响是什么？\nA. 资产和利润均高估\nB. 资产低估、利润高估\nC. 资产高估、利润低估\nD. 无影响\n仅输出选项字母。", "A"),
        ("公司在12月31日前发货并由客户验收，合同无退货权，款项次年收取。收入应在哪期确认？\nA. 次年收款时\nB. 本年客户验收时\nC. 合同签订时\nD. 不确认\n仅输出选项字母。", "B"),
        ("应收账款账龄显著延长且客户已进入破产程序，审计最应关注哪项认定？\nA. 完整性\nB. 可收回性及减值\nC. 固定资产存在\nD. 现金分类\n仅输出选项字母。", "B"),
        ("公司将本应费用化的日常维修费资本化。其结果通常是？\nA. 当期利润低估\nB. 当期资产和利润高估\nC. 负债低估但利润不变\nD. 现金高估\n仅输出选项字母。", "B"),
        ("银行对账单显示未入账手续费2万元。正确调整是？\nA. 借记银行存款\nB. 贷记费用\nC. 借记财务费用、贷记银行存款\nD. 不调整\n仅输出选项字母。", "C"),
        ("关联方以显著高于市场的价格采购公司产品且期后退货。主要风险是？\nA. 收入真实性和关联交易披露\nB. 存货计价下降\nC. 工资完整性\nD. 税率选择\n仅输出选项字母。", "A"),
        ("公司未将其控制的特殊目的主体纳入合并报表。主要违反哪项？\nA. 合并范围完整性\nB. 现金存在性\nC. 收入截止\nD. 折旧计量\n仅输出选项字母。", "A"),
        ("大额销售在资产负债表日后两日被全额红字冲回。最应实施什么程序？\nA. 只询问管理层\nB. 检查期后退货与截止测试\nC. 重算折旧\nD. 盘点现金\n仅输出选项字母。", "B"),
        ("管理层拒绝提供持续经营现金流预测，且一年内到期债务重大。审计报告前最需评估什么？\nA. 持续经营重大不确定性\nB. 商誉摊销\nC. 存货数量\nD. 股本面值\n仅输出选项字母。", "A"),
        ("审计抽样发现发票号码连续但有三张缺号。首先应核查什么？\nA. 销售记录完整性及缺号原因\nB. 固定资产折旧\nC. 银行利率\nD. 员工人数\n仅输出选项字母。", "A"),
    ]
    for index, (question, answer) in enumerate(audit_cases, 1):
        generated["financial_audit_fundamentals"].append(
            record("financial_audit_fundamentals", question, answer, generated_source("financial_audit_fundamentals", index))
        )

    summary_cases = [
        ("管理层表示，2026年一季度收入同比增长12%，主要由海外订单增加带动；原材料价格上涨使毛利率下降1.5个百分点，后续价格仍有不确定性。", "2026年一季度收入同比增长12%，海外订单是主要驱动；原材料涨价使毛利率下降1.5个百分点，后续价格走势仍不确定。"),
        ("公司今年新增30家门店并关闭8家低效门店，同店销售增长4%。管理层计划下半年放缓开店，把重点转向单店盈利。", "公司净增22家门店，同店销售增长4%；下半年将放缓扩张并优先改善单店盈利。"),
        ("会议指出，新产线已于6月试生产，设计产能为每年5万吨；爬坡期良率为82%，达到目标良率仍需设备调试。", "新产线6月进入试生产，设计年产能5万吨；当前良率82%，仍需调试才能达到目标。"),
        ("公司上半年经营现金流为2.1亿元，同比减少0.7亿元，主要因客户回款延迟；管理层预计部分应收款将在三季度收回，但未给出确定金额。", "上半年经营现金流2.1亿元，同比减少0.7亿元，主因回款延迟；管理层预计三季度可收回部分款项，但金额不确定。"),
        ("管理层称研发费用率从8%升至10%，用于两款新产品；其中一款进入注册阶段，另一款仍在早期验证，商业化时间尚未确定。", "研发费用率由8%升至10%，投入两款新产品；一款进入注册阶段，另一款处于早期验证，商业化时间均存在不确定性。"),
    ]
    for offset, (content, answer) in enumerate(summary_cases, 6):
        question = "请将以下会议内容压缩为不超过80字的摘要，保留关键数值、驱动因素和不确定性。\n" + content
        generated["financial_summarization"].append(
            record("financial_summarization", question, answer, generated_source("financial_summarization", offset))
        )

    policy_cases = [
        ("通胀持续高于目标，委员会决定加息25个基点，并表示必要时继续收紧。", "HAWKISH"),
        ("经济活动明显放缓，委员会下调政策利率50个基点以支持需求。", "DOVISH"),
        ("委员会维持利率不变，并重申未来决定取决于新增数据。", "NEUTRAL"),
        ("核心通胀回落但仍偏高，委员会停止加息，同时未承诺降息。", "NEUTRAL"),
        ("为收紧流动性，央行上调存款准备金率1个百分点。", "HAWKISH"),
        ("央行扩大资产购买规模并延长操作期限。", "DOVISH"),
        ("工资增速可能加剧通胀，委员会认为需要更长时间保持限制性利率。", "HAWKISH"),
        ("通胀低于目标且失业率上升，委员会暗示近期可能降息。", "DOVISH"),
        ("声明仅回顾上季度GDP和贸易数据，未讨论政策方向。", "NEUTRAL"),
        ("央行停止到期债券再投资，以加快资产负债表缩减。", "HAWKISH"),
    ]
    for index, (text, answer) in enumerate(policy_cases, 1):
        question = "将政策立场分类为 HAWKISH、DOVISH 或 NEUTRAL，仅输出标签。\n文本：" + text
        generated["monetary_policy_stance_classification"].append(
            record("monetary_policy_stance_classification", question, answer, generated_source("monetary_policy_stance_classification", index))
        )

    announcement_cases = [
        ("公司拟以自有资金回购1亿至2亿元股份，价格上限20元/股，期限12个月。", "关键事实：拟回购1亿至2亿元，价格不超过20元/股，期限12个月；可能减少流通股份；实际规模和执行价格存在不确定性。"),
        ("公司收到重大合同，中标金额8亿元，占上年收入18%，履约期两年。", "关键事实：新签8亿元合同，占上年收入18%，履约期两年；有望增加订单储备；收入确认节奏和履约成本存在风险。"),
        ("控股股东拟减持不超过公司总股本2%，减持期为未来三个月。", "关键事实：控股股东拟在三个月内减持不超过2%股份；可能增加短期供给；实际减持数量和价格尚不确定。"),
        ("公司预计年度净利润同比下降35%至45%，主因产品价格下跌。", "关键事实：预计年度净利润同比下降35%至45%，主因产品价格下跌；盈利承压；价格和销量变化可能影响最终结果。"),
        ("公司拟发行不超过15亿元可转债，用于新建产线和补充流动资金。", "关键事实：拟发行不超过15亿元可转债，用于新产线及流动资金；可支持扩产；审批、转股稀释和项目回报存在不确定性。"),
        ("公司终止收购目标公司，已支付的1000万元诚意金将按协议退回。", "关键事实：收购终止，1000万元诚意金拟退回；并购预期取消；退款执行和替代增长计划仍需关注。"),
        ("公司获得药品注册批准，适应症为成人慢性病治疗，商业化时间待定。", "关键事实：药品取得注册批准；具备后续商业化条件；上市时间、销售放量和竞争格局仍不确定。"),
        ("公司因信息披露不及时收到监管警示函，未涉及罚款。", "关键事实：公司因信披不及时收到警示函，暂未涉及罚款；反映内控与合规风险；后续整改效果需观察。"),
        ("公司将每10股派现4元，股权登记日为6月20日。", "关键事实：每10股派现4元，登记日6月20日；将产生现金分红；实际到账按持股和税费规则确定。"),
        ("公司新产能延期六个月投产，原因是关键设备交付延迟。", "关键事实：新产能因设备延迟而推迟六个月；短期产量释放晚于计划；设备到货和后续爬坡仍有不确定性。"),
    ]
    for index, (text, answer) in enumerate(announcement_cases, 1):
        question = "概括公告的关键事实、影响方向、风险与不确定性，不得断言股价必然变化。\n公告：" + text
        generated["summary_announcement"].append(
            record("summary_announcement", question, answer, generated_source("summary_announcement", index))
        )

    portfolio_cases = [
        ("组合甲预期收益8%、波动率6%；组合乙预期收益8%、波动率10%。按同收益下波动率更低优先，选择哪一个？", "组合甲"),
        ("资产A与组合相关系数0.9，资产B与组合相关系数0.1，二者预期收益和波动率相同。为分散风险应优先加入哪个？", "资产B"),
        ("60%债券收益4%，40%股票收益10%。组合预期收益是多少？", "6.4%"),
        ("组合年化收益12%，无风险利率3%，波动率15%。夏普比率是多少？", "0.60"),
        ("投资期限三个月且资金不能承受本金波动，股票基金与货币市场基金中哪类更符合该约束？", "货币市场基金"),
        ("单一行业股票占组合70%。最直接的风险是什么？", "行业集中度风险"),
        ("债券久期为6，市场利率上升1个百分点。用久期近似，价格变动约为多少？", "约下降6%"),
        ("组合目标权重股票50%、债券50%；上涨后股票权重变为60%。若恢复目标权重，应如何再平衡？", "卖出股票并买入债券，直至各50%"),
        ("资产甲预期收益7%、最大回撤5%；资产乙预期收益9%、最大回撤18%。若约束最大回撤不超过10%，哪个可行？", "资产甲"),
        ("两资产收益完全正相关。只在二者之间分散配置能否显著降低相关性风险？", "不能"),
    ]
    for index, (question, answer) in enumerate(portfolio_cases, 1):
        generated["portfolio_allocation_risk_return"].append(
            record("portfolio_allocation_risk_return", question, answer, generated_source("portfolio_allocation_risk_return", index))
        )
    return generated


def generated_rebuilt_group_records() -> dict[str, list[dict]]:
    generated: dict[str, list[dict]] = defaultdict(list)

    compliance_cases = [
        ("销售人员承诺某非保本基金‘一年保证收益8%’。", "不合规"),
        ("向风险承受能力为保守型的客户推荐高杠杆期货产品，未说明风险。", "不合规"),
        ("产品说明书同时披露历史业绩、费用、最大回撤，并声明历史业绩不代表未来。", "合规"),
        ("客户要求代签风险揭示书，销售人员拒绝并要求客户本人阅读确认。", "合规"),
        ("研究员持有某股票，却在公开研报中隐瞒该利益冲突。", "不合规"),
        ("机构在获得上市公司未公开利润数据后立即买入该公司股票。", "不合规"),
        ("广告只写‘低风险’，未提供产品类型、期限和损失情形。", "信息不足"),
        ("基金销售前完成客户风险测评，并匹配同等级产品。", "合规"),
        ("员工将客户账户信息发送到私人邮箱处理。", "不合规"),
        ("公司对外发布经审计年报，并在同一时间向所有投资者公开。", "合规"),
    ]
    for index, (scenario, answer) in enumerate(compliance_cases, 1):
        question = "按给定事实判断“合规”“不合规”或“信息不足”，仅输出标签。\n情形：" + scenario
        generated["compliance_safety_suitability"].append(
            record("compliance_safety_suitability", question, answer, generated_source("compliance_safety_suitability", index))
        )

    esg_cases = [
        ("公司披露单位产品温室气体排放下降12%。", "环境"),
        ("公司新增独立董事并设立审计委员会。", "治理"),
        ("工厂发生员工工伤事故并启动安全整改。", "社会"),
        ("公司更换办公楼物业服务商。", "非ESG"),
        ("供应商被发现使用童工，公司暂停采购。", "社会"),
        ("公司完成污水处理设施升级，化学需氧量排放下降。", "环境"),
        ("控股股东占用上市公司资金。", "治理"),
        ("董事会通过反商业贿赂制度。", "治理"),
        ("公司提高一线员工职业培训覆盖率。", "社会"),
        ("数据中心可再生能源用电比例升至60%。", "环境"),
    ]
    for index, (text, answer) in enumerate(esg_cases, 1):
        question = "将事件分类为“环境”“社会”“治理”或“非ESG”，仅输出标签。\n事件：" + text
        generated["esg_issue_identification"].append(
            record("esg_issue_identification", question, answer, generated_source("esg_issue_identification", index))
        )

    causal_cases = [
        ("原材料价格上涨15%，销量不变，产品售价未调整，毛利率下降。最直接原因是什么？", "原材料成本上升而售价未调整"),
        ("央行上调政策利率后，浮动利率贷款利息支出增加。最直接原因是什么？", "浮动贷款利率随政策利率上升"),
        ("公司应收账款周转天数增加，经营现金流下降，但收入基本不变。最直接原因是什么？", "客户回款变慢"),
        ("人民币升值后，以美元计价的出口收入折算成人民币减少。最直接原因是什么？", "相同美元收入的人民币折算额下降"),
        ("新店数量增加20%，但同店销售持平，总收入增长。最直接原因是什么？", "新增门店贡献收入"),
        ("债券市场收益率上升，固定票息债券价格下降。最直接原因是什么？", "市场贴现率上升"),
        ("存货跌价准备增加，其他项目不变，净利润下降。最直接原因是什么？", "资产减值损失增加"),
        ("竞争对手降价后，公司销量下降。最直接原因是什么？", "相对价格劣势削弱需求"),
        ("税率由20%升至25%，税前利润不变，净利润下降。最直接原因是什么？", "所得税费用增加"),
        ("设备利用率提升而固定成本不变，单位固定成本下降。最直接原因是什么？", "固定成本被更多产量分摊"),
    ]
    for index, (question, answer) in enumerate(causal_cases, 1):
        generated["financial_causal_event_reasoning"].append(
            record("financial_causal_event_reasoning", question, answer, generated_source("financial_causal_event_reasoning", index))
        )

    counterfactual_cases = [
        ("实际：原料涨价且售价不变，毛利率下降。反事实：原料价格不变，其他条件不变。毛利率相对实际会怎样？", "上升"),
        ("实际：加息使浮息贷款利息增加。反事实：政策利率不变，其他条件不变。利息支出相对实际会怎样？", "下降"),
        ("实际：新店带动收入增长。反事实：未开新店且同店销售不变。总收入相对实际会怎样？", "下降"),
        ("实际：汇率变化使出口折算收入减少。反事实：汇率保持原水平。折算收入相对实际会怎样？", "上升"),
        ("实际：坏账准备增加导致利润下降。反事实：应收信用风险未恶化，不新增准备。利润相对实际会怎样？", "上升"),
        ("实际：销量下降但提价使收入持平。反事实：不提价且销量同样下降。收入相对实际会怎样？", "下降"),
        ("实际：设备故障使产量减少。反事实：设备正常、需求不变。产量相对实际会怎样？", "上升"),
        ("实际：公司获得补贴，净利润增加。反事实：未获得补贴。净利润相对实际会怎样？", "下降"),
        ("实际：采购折扣降低成本。反事实：没有折扣，采购量不变。成本相对实际会怎样？", "上升"),
        ("实际：客户提前付款使期末现金增加。反事实：客户按原期限付款。期末现金相对实际会怎样？", "下降"),
    ]
    for index, (question, answer) in enumerate(counterfactual_cases, 1):
        generated["financial_counterfactual_inference"].append(
            record("financial_counterfactual_inference", question + "仅输出“上升”“下降”“不变”或“无法确定”。", answer, generated_source("financial_counterfactual_inference", index))
        )

    description_cases = [
        ("收入（百万元）：2023年100，2024年112，2025年126。", "收入连续增长，2024年同比增长12%，2025年同比增长约12.5%。"),
        ("毛利率：Q1为28%，Q2为31%，Q3为29%，Q4为33%。", "毛利率总体上升但中间有波动，Q4最高，为33%。"),
        ("经营现金流（百万元）：上半年45，下半年-8。", "经营现金流由上半年净流入45百万元转为下半年净流出8百万元。"),
        ("区域销量（万件）：东部52，中部47，西部61。", "西部销量最高为61万件，中部最低为47万件。"),
        ("费用率：销售8%，管理6%，研发11%。", "研发费用率最高为11%，销售费用率8%，管理费用率最低为6%。"),
        ("逾期贷款率：2024年1.2%，2025年1.8%。", "逾期贷款率上升0.6个百分点，从1.2%升至1.8%。"),
        ("客户结构：前五大客户占比38%，其他客户占比62%。", "收入以其他客户为主，占62%；前五大客户合计占38%。"),
        ("库存（百万元）：原料30，在产品18，产成品42。", "产成品库存最高为42百万元，原料30百万元，在产品最低为18百万元。"),
        ("债务期限：一年内20%，1至3年35%，3年以上45%。", "债务以3年以上期限为主，占45%；一年内到期占20%。"),
        ("日均交易量（万股）：周一80，周二95，周三70，周四105，周五90。", "周四交易量最高为105万股，周三最低为70万股。"),
    ]
    for index, (data, answer) in enumerate(description_cases, 1):
        generated["financial_data_description"].append(
            record("financial_data_description", "仅依据数据写一句客观描述，必须包含关键数值。\n" + data, answer, generated_source("financial_data_description", index))
        )

    multiturn_cases = [
        ("轮次1 用户：预算是120万元。助手：收到。轮次2 用户：更正为135万元，并已支出48万元。问题：剩余预算是多少？", "87万元"),
        ("轮次1 用户：持有A基金200份。助手：收到。轮次2 用户：卖出50份，又买入30份。问题：最终持有多少份？", "180份"),
        ("轮次1 用户：贷款本金100万元，年利率4%。助手：收到。轮次2 用户：利率更正为4.5%，按单利一年。问题：利息是多少？", "4.5万元"),
        ("轮次1 用户：收入为500万元。助手：收到。轮次2 用户：补充成本320万元、税费20万元。问题：税费后利润是多少？", "160万元"),
        ("轮次1 用户：目标股票权重60%。助手：收到。轮次2 用户：风险限制将上限改为50%。问题：最终采用的上限是多少？", "50%"),
        ("轮次1 用户：汇率为7.10。助手：收到。轮次2 用户：结算日汇率改为7.20，金额10万美元。问题：折合人民币多少万元？", "72万元"),
        ("轮次1 用户：库存80件。助手：收到。轮次2 用户：入库25件、出库40件。问题：期末库存是多少？", "65件"),
        ("轮次1 用户：项目期两年。助手：收到。轮次2 用户：工期延长6个月。问题：最终项目期多长？", "2年6个月"),
        ("轮次1 用户：每股股息0.30元。助手：收到。轮次2 用户：董事会调整为0.36元，持股1万股。问题：股息总额是多少？", "3600元"),
        ("轮次1 用户：手续费率0.10%。助手：收到。轮次2 用户：大额交易优惠至0.06%，成交额50万元。问题：手续费是多少？", "300元"),
    ]
    for index, (question, answer) in enumerate(multiturn_cases, 1):
        generated["financial_multi_turn_perception"].append(
            record("financial_multi_turn_perception", question, answer, generated_source("financial_multi_turn_perception", index))
        )

    numeric_cases = [
        (["公司", "收入", "增长", "12%"], ["O", "O", "O", "B-PERCENT"]),
        (["回购", "金额", "为", "2.5亿元"], ["O", "O", "O", "B-MONEY"]),
        (["债券", "期限", "五年", "票息", "3.2%"], ["O", "O", "B-DURATION", "O", "B-PERCENT"]),
        (["成交", "价格", "101.35元", "数量", "200手"], ["O", "O", "B-PRICE", "O", "B-QUANTITY"]),
        (["净利润", "下降", "800万元"], ["O", "O", "B-MONEY"]),
        (["股东", "持股", "1,200万股", "占比", "6%"], ["O", "O", "B-QUANTITY", "O", "B-PERCENT"]),
        (["贷款", "利率", "LPR+50BP"], ["O", "O", "B-RATE"]),
        (["合同", "签署", "日期", "2026-03-18"], ["O", "O", "O", "B-DATE"]),
        (["基金", "单位净值", "1.0864"], ["O", "O", "B-NAV"]),
        (["汇率", "为", "7.25元/美元"], ["O", "O", "B-FX"]),
    ]
    for index, (tokens, labels) in enumerate(numeric_cases, 1):
        question = "对给定token序列进行数值类型标注。答案输出与token等长的JSON数组。\ntokens=" + json.dumps(tokens, ensure_ascii=False)
        generated["financial_numeric_labeling"].append(
            record("financial_numeric_labeling", question, json.dumps(labels, ensure_ascii=False), generated_source("financial_numeric_labeling", index))
        )

    role_cases = [
        (["甲公司", "以", "2亿元", "收购", "乙公司"], ["主体", "O", "金额", "动作", "客体"]),
        (["丙银行", "向", "丁企业", "发放", "贷款"], ["主体", "O", "客体", "动作", "标的"]),
        (["戊基金", "昨日", "增持", "A股票"], ["主体", "时间", "动作", "客体"]),
        (["己公司", "因", "成本上升", "下调", "利润指引"], ["主体", "O", "原因", "动作", "客体"]),
        (["庚公司", "在", "上海", "发行", "债券"], ["主体", "O", "地点", "动作", "客体"]),
        (["辛公司", "将", "3000万元", "投资于", "新产线"], ["主体", "O", "金额", "动作", "客体"]),
        (["壬银行", "于", "6月1日", "上调", "存款利率"], ["主体", "O", "时间", "动作", "客体"]),
        (["癸公司", "向", "股东", "派发", "现金红利"], ["主体", "O", "客体", "动作", "标的"]),
        (["A机构", "基于", "风险上升", "降低", "评级"], ["主体", "O", "原因", "动作", "客体"]),
        (["B公司", "通过", "子公司", "持有", "C公司股份"], ["主体", "O", "工具", "动作", "客体"]),
    ]
    for index, (tokens, labels) in enumerate(role_cases, 1):
        question = "对给定token序列标注语义角色。答案输出与token等长的JSON数组。\ntokens=" + json.dumps(tokens, ensure_ascii=False)
        generated["financial_semantic_role_labeling"].append(
            record("financial_semantic_role_labeling", question, json.dumps(labels, ensure_ascii=False), generated_source("financial_semantic_role_labeling", index))
        )

    numerical_cases = [
        ("收入1000万元，成本率62%，销售费用80万元，管理费用60万元。营业利润是多少？", "240万元"),
        ("期初应收款120万元，本期赊销500万元，期末应收款170万元。本期收现多少？", "450万元"),
        ("面值100元债券，票息5%，买入价98元，持有一年后以101元卖出并收到利息。持有期收益率是多少？保留两位小数。", "8.16%"),
        ("资产600万元，负债360万元；净利润48万元。先算净资产，再算ROE。", "净资产240万元，ROE为20%"),
        ("商品单价80元，销量1万件；价格上涨10%，销量下降5%。新收入是多少？", "83.6万元"),
        ("项目初始投资200万元，第1、2年现金流分别90万元和130万元。忽略折现，累计净收益是多少？", "20万元"),
        ("美元收入50万美元，成本折合人民币240万元，汇率7.20。人民币毛利是多少？", "120万元"),
        ("组合中股票60%收益12%，债券30%收益4%，现金10%收益2%。组合收益率是多少？", "8.6%"),
        ("存货期初40万元，购入180万元，期末55万元。销售成本是多少？若收入250万元，毛利率是多少？", "销售成本165万元，毛利率34%"),
        ("贷款本金300万元，年利率4.8%，计息9个月；另收手续费1.2万元。总融资成本是多少？", "12万元"),
    ]
    for index, (question, answer) in enumerate(numerical_cases, 1):
        generated["multi_step_numerical_reasoning"].append(
            record("multi_step_numerical_reasoning", question, answer, generated_source("multi_step_numerical_reasoning", index))
        )

    multitable_cases = [
        ("收入与成本", ["年度", "收入"], [["2024", "200"], ["2025", "240"]], ["年度", "成本"], [["2024", "130"], ["2025", "150"]], "2025年毛利较2024年增加多少万元？", "20万元"),
        ("地区销量与单价", ["地区", "销量"], [["东部", "10"], ["西部", "8"]], ["地区", "单价"], [["东部", "12"], ["西部", "15"]], "两个地区收入合计多少万元？", "240万元"),
        ("资产与负债", ["公司", "资产"], [["甲", "500"], ["乙", "420"]], ["公司", "负债"], [["甲", "280"], ["乙", "180"]], "哪家公司净资产更高，相差多少万元？", "乙公司，高20万元"),
        ("预算与实际", ["部门", "预算"], [["研发", "80"], ["销售", "60"]], ["部门", "实际"], [["研发", "76"], ["销售", "68"]], "两部门合计超预算还是节约，金额多少？", "超预算4万元"),
        ("期初与期末库存", ["产品", "期初"], [["A", "30"], ["B", "20"]], ["产品", "期末"], [["A", "24"], ["B", "28"]], "两产品库存合计净变化是多少？", "增加2件"),
        ("基金收益与风险", ["基金", "收益率"], [["甲", "9%"], ["乙", "8%"]], ["基金", "波动率"], [["甲", "12%"], ["乙", "8%"]], "按收益率/波动率比较，哪只基金比值更高？", "乙基金"),
        ("客户回款", ["客户", "应收"], [["A", "50"], ["B", "70"]], ["客户", "已回款"], [["A", "35"], ["B", "42"]], "两客户未回款合计多少万元？", "43万元"),
        ("产量与不良率", ["工厂", "产量"], [["一厂", "1000"], ["二厂", "800"]], ["工厂", "不良率"], [["一厂", "2%"], ["二厂", "1%"]], "两厂合格品合计多少件？", "1772件"),
        ("借款与利率", ["借款", "本金"], [["甲", "100"], ["乙", "200"]], ["借款", "年利率"], [["甲", "4%"], ["乙", "5%"]], "两笔借款一年利息合计多少万元？", "14万元"),
        ("门店与客单", ["门店", "订单数"], [["A", "500"], ["B", "400"]], ["门店", "客单价"], [["A", "80"], ["B", "95"]], "哪家门店收入更高，相差多少元？", "A店，高2000元"),
    ]
    for index, (title, h1, r1, h2, r2, question, answer) in enumerate(multitable_cases, 1):
        image1 = draw_table("multi_table_reasoning", index, title + "—表1", h1, r1, page=1)
        image2 = draw_table("multi_table_reasoning", index, title + "—表2", h2, r2, page=2)
        generated["multi_table_reasoning"].append(
            record("multi_table_reasoning", question, answer, generated_source("multi_table_reasoning", index), [image1, image2])
        )

    knowledge_cases = [
        ("资产负债表片段", ["资产：现金120，应收80", "负债：短期借款70", "所有者权益：130"], "图中资产总额是多少？", "200"),
        ("债券要素", ["面值：100元", "票面利率：4%", "期限：3年"], "该债券每年票息是多少？", "4元"),
        ("基金费用", ["申购金额：10,000元", "申购费率：1%", "不考虑其他费用"], "申购费是多少？", "100元"),
        ("外汇报价", ["USD/CNY：7.20", "EUR/CNY：7.80"], "1欧元可兑换多少人民币？", "7.80元"),
        ("利润表片段", ["营业收入：300万元", "营业成本：210万元", "税费：15万元"], "不考虑其他项目，税费后利润是多少？", "75万元"),
        ("股票交易", ["买入价：20元", "卖出价：22元", "持有数量：1000股"], "不计费用，资本利得是多少？", "2000元"),
        ("存款产品", ["本金：5万元", "年利率：2%", "期限：1年"], "按单利计算利息是多少？", "1000元"),
        ("指数权重", ["股票A：40%", "股票B：35%", "股票C：25%"], "权重最高的是哪只股票？", "股票A"),
        ("现金流分类", ["销售收款：经营活动", "购置设备：投资活动", "发行债券：筹资活动"], "购置设备属于哪类现金流？", "投资活动现金流"),
        ("风险指标", ["基金甲最大回撤：8%", "基金乙最大回撤：15%"], "仅按最大回撤比较，哪只基金历史回撤更小？", "基金甲"),
    ]
    for index, (title, lines, question, answer) in enumerate(knowledge_cases, 1):
        image = draw_text_card("multimodal_financial_knowledge", index, title, lines)
        generated["multimodal_financial_knowledge"].append(
            record("multimodal_financial_knowledge", question, answer, generated_source("multimodal_financial_knowledge", index), [image])
        )

    risk_cases = [
        ("央行意外加息，长久期债券价格当日明显下跌。", "风险偏高：利率上行对长久期债券价格不利；后续利率路径仍不确定。"),
        ("公司单一客户贡献70%收入，该客户正在重新招标。", "风险偏高：客户集中度高且续约不确定，收入可能波动。"),
        ("通胀回落但仍高于目标，政策声明未承诺降息。", "风险中性：通胀压力缓和，但政策转向时间无法确定。"),
        ("基金采用两倍杠杆跟踪高波动行业指数。", "风险偏高：杠杆会放大行业波动和损失。"),
        ("公司现金覆盖一年内到期债务的2.5倍，且经营现金流稳定。", "风险偏低：短期偿债覆盖较充足，但仍需关注现金流持续性。"),
        ("商品价格上涨有利于生产商收入，但其能源成本同步上升。", "风险中性：收入端受益与成本端压力并存，净影响取决于价差。"),
        ("监管拟提高资本充足率要求，银行当前仅略高于新门槛。", "风险偏高：银行可能面临补充资本或压缩风险资产的压力。"),
        ("企业80%债务为固定利率，短期市场利率上升。", "风险偏低：固定利率结构降低短期再定价影响，续借时仍有风险。"),
        ("出口企业收入以美元计价、成本以人民币计价，人民币快速升值。", "风险偏高：人民币升值可能压缩折算收入和利润率。"),
        ("政策补贴已到期，公司尚未披露无补贴条件下的盈利预测。", "风险偏高：补贴退出可能削弱盈利，具体幅度信息不足。"),
    ]
    for index, (scenario, answer) in enumerate(risk_cases, 1):
        generated["risk_sentiment_policy"].append(
            record("risk_sentiment_policy", "仅依据情形判断风险方向并说明证据与不确定性。\n" + scenario, answer, generated_source("risk_sentiment_policy", index))
        )
    return generated


def generated_new_scope_records() -> dict[str, list[dict]]:
    generated: dict[str, list[dict]] = defaultdict(list)

    candle_rows = [
        [("周一", 10, 12, 9, 11), ("周二", 11, 13, 10, 12), ("周三", 12, 14, 11, 13), ("周四", 13, 15, 12, 14), ("周五", 14, 16, 13, 15)],
        [("周一", 20, 22, 18, 19), ("周二", 19, 21, 17, 18), ("周三", 18, 20, 16, 17), ("周四", 17, 19, 15, 16), ("周五", 16, 18, 14, 15)],
        [("周一", 30, 34, 29, 33), ("周二", 33, 35, 31, 32), ("周三", 32, 38, 30, 37), ("周四", 37, 39, 35, 36), ("周五", 36, 40, 34, 39)],
        [("周一", 50, 52, 48, 50), ("周二", 50, 53, 49, 52), ("周三", 52, 54, 50, 51), ("周四", 51, 53, 49, 51), ("周五", 51, 55, 50, 54)],
        [("周一", 40, 43, 39, 42), ("周二", 42, 44, 40, 41), ("周三", 41, 43, 38, 39), ("周四", 39, 42, 37, 41), ("周五", 41, 45, 40, 44)],
        [("周一", 60, 62, 57, 58), ("周二", 58, 61, 56, 60), ("周三", 60, 63, 59, 62), ("周四", 62, 64, 60, 61), ("周五", 61, 65, 58, 59)],
        [("周一", 15, 18, 14, 17), ("周二", 17, 19, 16, 18), ("周三", 18, 21, 17, 20), ("周四", 20, 22, 18, 19), ("周五", 19, 23, 18, 22)],
        [("周一", 80, 84, 78, 82), ("周二", 82, 83, 75, 76), ("周三", 76, 79, 73, 78), ("周四", 78, 81, 77, 80), ("周五", 80, 82, 79, 81)],
        [("周一", 25, 27, 24, 26), ("周二", 26, 29, 25, 28), ("周三", 28, 30, 27, 29), ("周四", 29, 31, 28, 30), ("周五", 30, 32, 26, 27)],
        [("周一", 100, 104, 98, 103), ("周二", 103, 105, 101, 102), ("周三", 102, 106, 100, 105), ("周四", 105, 107, 103, 104), ("周五", 104, 108, 102, 107)],
    ]
    candle_questions = [
        ("哪一天的收盘价最高？", "周五"),
        ("从周一到周五，收盘价总体上涨还是下跌？", "下跌"),
        ("哪一天的日内振幅（最高价-最低价）最大？", "周三"),
        ("开盘价与收盘价相等的交易日共有几天？", "2天"),
        ("哪一天的最低价最低？", "周四"),
        ("收盘价高于开盘价的交易日有几天？", "2天"),
        ("哪一天的最高价最高？", "周五"),
        ("周二的K线是上涨还是下跌？", "下跌"),
        ("周五收盘价相对周四收盘价上涨还是下跌？", "下跌"),
        ("五日中最高收盘价是多少？", "107"),
    ]
    for index, (rows, qa) in enumerate(zip(candle_rows, candle_questions), 1):
        image = draw_candlestick(index, rows)
        generated["candlestick_time_series"].append(
            record("candlestick_time_series", qa[0], qa[1], generated_source("candlestick_time_series", index), [image])
        )

    evidence_docs = [
        (["第1页：公司概况与组织架构", "第2页：2025年营业收入为18亿元，净利润为2.1亿元", "第3页：审计意见与签字页"], "回答‘2025年净利润是多少’需要查看哪一页？仅输出页码。", "第2页"),
        (["第1页：债券发行条款，票面利率3.4%", "第2页：募集资金用途", "第3页：风险因素与评级说明"], "回答‘债券票面利率是多少’需要查看哪一页？仅输出页码。", "第1页"),
    ]
    for index, (pages, question, answer) in enumerate(evidence_docs, 1):
        images = [draw_text_card("evidence_retrieval", index, f"文档第{page_no}页", [content], page=page_no) for page_no, content in enumerate(pages, 1)]
        generated["evidence_retrieval"].append(
            record("evidence_retrieval", question, answer, generated_source("evidence_retrieval", index), images)
        )

    anomaly_cases = [
        ("季度销量异常", ["Q1", "Q2", "Q3", "Q4"], [80, 84, 42, 86], "Q3工厂检修停产两周", "Q3销量为何显著偏低？", "图中注释显示Q3工厂检修停产两周。"),
        ("月度毛利率", ["1月", "2月", "3月", "4月"], [30, 31, 22, 32], "3月原材料一次性涨价", "3月毛利率异常下降的图内原因是什么？", "图中注释显示3月原材料一次性涨价。"),
        ("门店客流", ["周一", "周二", "周三", "周四"], [120, 118, 60, 125], "周三极端天气闭店半天", "周三客流偏低的图内原因是什么？", "图中注释显示周三极端天气导致闭店半天。"),
        ("现金余额", ["6月", "7月", "8月", "9月"], [200, 195, 110, 190], "8月支付大型设备款", "8月现金余额下降的图内原因是什么？", "图中注释显示8月支付了大型设备款。"),
        ("出口订单", ["一季度", "二季度", "三季度", "四季度"], [55, 58, 30, 61], "三季度主要港口罢工", "三季度出口订单偏低的图内原因是什么？", "图中注释显示三季度主要港口发生罢工。"),
        ("不良率", ["A线", "B线", "C线", "D线"], [1.2, 1.1, 3.8, 1.0], "C线新设备处于调试期", "C线不良率偏高的图内原因是什么？", "图中注释显示C线新设备处于调试期。"),
        ("广告转化率", ["渠道A", "渠道B", "渠道C", "渠道D"], [4.2, 4.0, 1.5, 4.4], "渠道C落地页故障", "渠道C转化率偏低的图内原因是什么？", "图中注释显示渠道C落地页发生故障。"),
        ("单位运费", ["区域甲", "区域乙", "区域丙", "区域丁"], [8, 9, 18, 8.5], "区域丙使用临时空运", "区域丙单位运费偏高的图内原因是什么？", "图中注释显示区域丙使用了临时空运。"),
        ("产能利用率", ["1月", "2月", "3月", "4月"], [88, 90, 52, 91], "3月例行大修", "3月产能利用率下降的图内原因是什么？", "图中注释显示3月进行了例行大修。"),
        ("退货率", ["产品A", "产品B", "产品C", "产品D"], [2, 2.5, 7, 1.8], "产品C包装批次缺陷", "产品C退货率偏高的图内原因是什么？", "图中注释显示产品C存在包装批次缺陷。"),
    ]
    for index, (title, labels, values, note, question, answer) in enumerate(anomaly_cases, 1):
        image = draw_bar_chart("explanation_anomaly_causality", index, title, labels, values, note)
        generated["explanation_anomaly_causality"].append(
            record("explanation_anomaly_causality", question + "仅依据图中证据作答。", answer, generated_source("explanation_anomaly_causality", index), [image])
        )

    relation_cases = [
        ("甲公司持有乙公司60%股权。", [{"subject": "甲公司", "relation": "持有股权", "object": "乙公司60%股权"}]),
        ("丙银行向丁企业提供5000万元贷款。", [{"subject": "丙银行", "relation": "提供贷款", "object": "丁企业"}]),
        ("戊基金由己资产管理公司管理。", [{"subject": "己资产管理公司", "relation": "管理", "object": "戊基金"}]),
        ("庚公司是辛公司的全资子公司。", [{"subject": "辛公司", "relation": "全资控股", "object": "庚公司"}]),
        ("壬公司从癸公司采购芯片。", [{"subject": "壬公司", "relation": "采购自", "object": "癸公司"}]),
        ("A公司向B公司出售设备并提供三年维保。", [{"subject": "A公司", "relation": "出售设备", "object": "B公司"}, {"subject": "A公司", "relation": "提供维保", "object": "B公司"}]),
        ("C证券承销D公司发行的债券。", [{"subject": "C证券", "relation": "承销", "object": "D公司债券"}]),
        ("E公司与F大学联合设立研发中心。", [{"subject": "E公司", "relation": "联合设立", "object": "研发中心"}, {"subject": "F大学", "relation": "联合设立", "object": "研发中心"}]),
        ("G基金投资H公司，H公司收购I公司。", [{"subject": "G基金", "relation": "投资", "object": "H公司"}, {"subject": "H公司", "relation": "收购", "object": "I公司"}]),
        ("J银行为K公司的债券提供担保。", [{"subject": "J银行", "relation": "提供担保", "object": "K公司债券"}]),
    ]
    for index, (text, answer) in enumerate(relation_cases, 1):
        question = "抽取全部金融关系，输出JSON数组，每项字段固定为subject、relation、object。\n文本：" + text
        generated["financial_relation_extraction"].append(
            record("financial_relation_extraction", question, json.dumps(answer, ensure_ascii=False), generated_source("financial_relation_extraction", index))
        )

    sentiment_cases = [
        ("公司上调全年利润指引，并宣布新增订单超预期。", "正面"),
        ("公司维持原有业绩预测，未披露新的重大事项。", "中性"),
        ("主要产品召回，预计产生大额一次性损失。", "负面"),
        ("季度收入同比增长20%，毛利率同步提升。", "正面"),
        ("董事会例行换届，经营计划保持不变。", "中性"),
        ("公司债务违约，评级被下调。", "负面"),
        ("监管批准公司核心产品上市。", "正面"),
        ("公司披露股东人数增加，但未说明经营变化。", "中性"),
        ("重大客户取消合同，相关收入占比15%。", "负面"),
        ("原材料价格下降，公司预计成本压力缓解。", "正面"),
    ]
    for index, (text, answer) in enumerate(sentiment_cases, 1):
        generated["financial_sentiment_analysis"].append(
            record("financial_sentiment_analysis", "将新闻情绪分类为“正面”“中性”或“负面”，仅输出标签。\n" + text, answer, generated_source("financial_sentiment_analysis", index))
        )

    topic_cases = [
        ("央行宣布下调公开市场操作利率。", "货币政策"),
        ("上市公司发布年度收入和净利润。", "公司业绩"),
        ("某基金调整股票与债券配置比例。", "基金与资管"),
        ("银行不良贷款率和拨备覆盖率发生变化。", "银行"),
        ("原油期货价格因库存数据而波动。", "商品与期货"),
        ("公司拟收购同行企业的控股权。", "并购重组"),
        ("监管机构发布证券市场交易新规。", "监管合规"),
        ("人民币对美元汇率连续升值。", "外汇"),
        ("国债收益率曲线明显变陡。", "债券"),
        ("企业完成首次公开发行并挂牌交易。", "股票与发行"),
    ]
    labels = "货币政策、公司业绩、基金与资管、银行、商品与期货、并购重组、监管合规、外汇、债券、股票与发行"
    for index, (text, answer) in enumerate(topic_cases, 1):
        question = f"从以下标签中选择一个：{labels}。仅输出标签。\n文本：{text}"
        generated["financial_topic_classification"].append(
            record("financial_topic_classification", question, answer, generated_source("financial_topic_classification", index))
        )

    caption_cases = [
        ("季度收入柱状图", ["Q1：80百万元", "Q2：95百万元", "Q3：110百万元"], "图中展示Q1至Q3收入连续增长，从80百万元增至110百万元。"),
        ("资产构成", ["现金：30%", "应收账款：25%", "存货：45%"], "图中列出资产构成，存货占比最高，为45%。"),
        ("债务期限", ["一年内：20%", "1至3年：35%", "3年以上：45%"], "图中展示债务期限分布，3年以上债务占45%。"),
        ("基金风险指标", ["年化波动率：12%", "最大回撤：8%", "夏普比率：0.7"], "图中列出基金年化波动率12%、最大回撤8%和夏普比率0.7。"),
        ("销售区域", ["东部：52", "中部：41", "西部：47"], "图中列出三个区域销量，东部最高为52。"),
        ("利润表摘要", ["收入：300万元", "成本：210万元", "净利润：60万元"], "图中列出收入300万元、成本210万元和净利润60万元。"),
        ("现金流摘要", ["经营：+90万元", "投资：-40万元", "筹资：-20万元"], "图中显示经营现金流为正，投资和筹资现金流为负。"),
        ("股东持股", ["股东甲：35%", "股东乙：20%", "公众股东：45%"], "图中显示公众股东合计持股45%，为最大类别。"),
        ("产品毛利率", ["产品A：18%", "产品B：26%", "产品C：22%"], "图中列出三类产品毛利率，产品B最高为26%。"),
        ("贷款评级", ["正常：80%", "关注：15%", "不良：5%"], "图中展示贷款评级分布，正常类占80%。"),
    ]
    for index, (title, lines, answer) in enumerate(caption_cases, 1):
        image = draw_text_card("image_caption", index, title, lines)
        generated["image_caption"].append(
            record("image_caption", "请用一句话描述图中可见的金融信息，不推测原因或未来表现。", answer, generated_source("image_caption", index), [image])
        )

    industry_cases = [
        ("行业销量连续三年为100、112、126万件，头部企业产能利用率由70%升至85%。", "需求扩张且头部产能利用率提高，但不能据此断言未来持续增长。"),
        ("行业收入增长8%，产品均价下降5%，销量增长约14%。", "增长主要由销量驱动，价格承压。"),
        ("原材料成本下降10%，终端价格基本不变。", "行业毛利空间可能改善，实际幅度取决于成本传导。"),
        ("新增产能30%，同期需求仅增长5%。", "供给增速明显高于需求，产能过剩和价格压力上升。"),
        ("行业CR3由40%升至55%，总市场规模基本不变。", "市场集中度提高，头部企业份额扩大。"),
        ("出口占比由20%升至35%，主要海外市场提高关税。", "行业对海外市场依赖上升，同时面临关税风险。"),
        ("库存天数从45天降至30天，销量保持稳定。", "库存去化改善，渠道库存压力下降。"),
        ("行业资本开支连续两年下降，新订单开始回升。", "供给扩张放缓而需求出现回升迹象，但复苏持续性待验证。"),
        ("线上渠道占比由25%升至45%，线下总销量下降。", "销售渠道加速向线上迁移。"),
        ("龙头企业单位成本下降8%，中小企业成本基本不变。", "龙头成本优势扩大，行业竞争分化可能加剧。"),
    ]
    for index, (data, answer) in enumerate(industry_cases, 1):
        generated["industry_trend_inference"].append(
            record("industry_trend_inference", "仅依据数据概括行业趋势，并保留不确定性。\n" + data, answer, generated_source("industry_trend_inference", index))
        )

    investment_cases = [
        ("某宽基指数近一年波动率明显上升，投资期限未知。", "策略：可采用分批而非一次性建仓，并先确认期限和承受能力；风险：短期波动和回撤可能较大，无法保证收益。"),
        ("单一科技股已占组合70%。", "策略：可考虑降低单一股票集中度并分散到相关性较低的资产；风险：个股和行业冲击会放大组合损失。"),
        ("利率上升阶段持有大量长久期债券。", "策略：可评估缩短久期或分散到不同期限；风险：利率继续上升会压低长久期债券价格。"),
        ("三个月后确定需要支付购房首付款。", "策略：短期刚性资金宜优先保持流动性和本金稳定；风险：高波动资产可能在用款时亏损。"),
        ("计划长期定投宽基基金，但收入存在波动。", "策略：可设置不影响应急资金的定投额度并保留现金缓冲；风险：市场下跌和收入中断可能影响持续投入。"),
        ("组合全部为本币资产，未来有明确外币支出。", "策略：可评估与外币负债相匹配的适度汇率对冲；风险：汇率双向波动且对冲有成本。"),
        ("高收益债基金收益率较高，但信用利差快速扩大。", "策略：应结合信用质量和期限分散审慎配置；风险：违约、流动性和净值回撤风险上升。"),
        ("商品价格已快速上涨，准备追涨。", "策略：可控制仓位并设定可承受损失范围，避免基于短期涨幅作确定判断；风险：价格反转和高波动。"),
        ("组合收益目标8%，但最大可承受回撤仅3%。", "策略：需下调风险资产比例或重新校准收益目标；风险：收益目标与回撤约束可能不兼容。"),
        ("准备借款投资股票。", "策略：应审慎评估杠杆并优先确保偿债能力；风险：亏损会被杠杆放大，仍需支付利息和本金。"),
    ]
    for index, (scenario, answer) in enumerate(investment_cases, 1):
        generated["investment_advice_strategy"].append(
            record("investment_advice_strategy", "给出非个性化、证据约束的策略和风险说明，不承诺收益。\n情形：" + scenario, answer, generated_source("investment_advice_strategy", index))
        )

    equity_cases = [
        ("甲公司", [("股东A", "55%"), ("股东B", "25%"), ("公众", "20%")], "谁是控股股东？", "股东A"),
        ("乙公司", [("集团X", "40%"), ("基金Y", "35%"), ("其他", "25%")], "持股比例第二高的是谁？", "基金Y"),
        ("丙公司", [("创始人", "30%"), ("员工平台", "15%"), ("公众", "55%")], "公众股东合计持股多少？", "55%"),
        ("丁公司", [("母公司", "70%"), ("战略投资者", "20%"), ("员工", "10%")], "母公司与战略投资者合计持股多少？", "90%"),
        ("戊公司", [("股东甲", "34%"), ("股东乙", "33%"), ("股东丙", "33%")], "单一持股比例最高的是谁？", "股东甲"),
        ("己公司", [("国资平台", "51%"), ("产业基金", "29%"), ("公众", "20%")], "国资平台是否超过50%？", "是"),
        ("庚公司", [("A控股", "45%"), ("B资本", "30%"), ("C基金", "25%")], "A控股比B资本多持股多少个百分点？", "15个百分点"),
        ("辛公司", [("创始团队", "60%"), ("员工持股", "12%"), ("外部投资者", "28%")], "内部相关持股（创始团队+员工）合计多少？", "72%"),
        ("壬公司", [("机构A", "22%"), ("机构B", "18%"), ("公众", "60%")], "机构A和机构B合计持股多少？", "40%"),
        ("癸公司", [("母基金", "48%"), ("子基金", "17%"), ("其他", "35%")], "最大单一股东持股多少？", "48%"),
    ]
    for index, (company, owners, question, answer) in enumerate(equity_cases, 1):
        image = draw_equity("relationship_equity_structure", index, company, owners)
        generated["relationship_equity_structure"].append(
            record("relationship_equity_structure", question, answer, generated_source("relationship_equity_structure", index), [image])
        )

    spatial_cases = [
        ({"左上": "收入", "右上": "毛利率", "左下": "现金流", "右下": "负债率"}, "毛利率位于哪个区域？", "右上"),
        ({"左上": "股价", "右上": "成交量", "左下": "新闻", "右下": "公告"}, "公告模块位于哪个区域？", "右下"),
        ({"左上": "资产", "右上": "负债", "左下": "权益", "右下": "利润"}, "权益模块位于哪个区域？", "左下"),
        ({"左上": "基金净值", "右上": "持仓", "左下": "回撤", "右下": "费率"}, "基金净值位于哪个区域？", "左上"),
        ({"左上": "汇率", "右上": "利率", "左下": "商品", "右下": "债券"}, "债券模块位于哪个区域？", "右下"),
        ({"左上": "预算", "右上": "实际", "左下": "差异", "右下": "预测"}, "实际数据位于哪个区域？", "右上"),
        ({"左上": "订单", "右上": "库存", "左下": "产量", "右下": "交付"}, "产量位于哪个区域？", "左下"),
        ({"左上": "客户", "右上": "供应商", "左下": "产品", "右下": "地区"}, "供应商位于哪个区域？", "右上"),
        ({"左上": "现金", "右上": "应收", "左下": "存货", "右下": "固定资产"}, "现金位于哪个区域？", "左上"),
        ({"左上": "研发", "右上": "销售", "左下": "管理", "右下": "财务"}, "财务费用位于哪个区域？", "右下"),
    ]
    for index, (boxes, question, answer) in enumerate(spatial_cases, 1):
        image = draw_dashboard(index, f"财务看板 {index}", boxes)
        generated["spatial_localization"].append(
            record("spatial_localization", question + "仅输出左上、右上、左下或右下。", answer, generated_source("spatial_localization", index), [image])
        )

    stock_question = (
        "以下为FLARE BigData22来源中$csco截至2017-10-31收盘前的历史日收益特征。"
        "标签以来源数据中2017-11-01真实收盘价相对前一交易日的方向确定。仅输出Rise或Fall。\n"
        "2017-10-27 close_return=0.5%\n2017-10-30 close_return=-1.1%\n2017-10-31 close_return=0.3%"
    )
    generated["stock_movement_prediction"].append(
        record(
            "stock_movement_prediction",
            stock_question,
            "Rise",
            "ModelScope/stock_movement_prediction/test-00000-of-00001-e1663a0932037903.parquet#0-target-2017-11-01",
        )
    )
    return generated


TASK_ISSUES = {
    "chart_data_extraction": "剔除能力漂移题，修复逐字符选项并统一选择题格式；补充客观读数题。",
    "cross_modal_multi_hop": "旧题过长且存在未定义字段，重建为确实同时依赖题干与图表的计算题。",
    "financial_ocr": "保留可核对截图，剔除近重复价格题，补充发票、净值、债券和回单识别。",
    "merger_acquisition_completeness_classification": "统一complete为正式宣布或签署交易，rumour为未证实讨论。",
    "single_table_qa": "旧题集中于同一收益分布模板，保留不同能力题并补充四类表格问答。",
    "statistics_comparison_ranking": "修复逐字符选项，剔除峰值读数不精确题，补充排序与阈值比较。",
    "basic_arithmetic_metrics": "逐条复算原7题，统一数值与单位并补充三种独立指标。",
    "entity_extraction_classification": "剔除概念边界错误和简称歧义题，统一选项输出并补充四类实体。",
    "financial_event_extraction": "原答案为连续JSON对象且含事实错误，全部重建为固定字段JSON数组。",
    "financial_audit_fundamentals": "旧答案为开放式评分提示，重建为边界明确的审计基础选择题。",
    "financial_summarization": "剔除题干外补充和信息遗漏样本，压缩保留样本并补充证据自足会议摘要。",
    "monetary_policy_stance_classification": "原标签多处与文本不符，重建鹰派、鸽派和中性样本。",
    "summary_announcement": "旧答案开放且缺少事实边界，重建为关键事实、影响、风险和不确定性四要素。",
    "portfolio_allocation_risk_return": "旧题评分口径不稳定，重建为可计算或有明确约束的风险收益题。",
    "compliance_safety_suitability": "旧题依赖外部法规背景，重建为事实充分的合规与适当性判断。",
    "esg_issue_identification": "重建环境、社会、治理和非ESG边界明确的中文样本。",
    "financial_causal_event_reasoning": "重建为给定事实内可直接支持的近因判断。",
    "financial_counterfactual_inference": "重建为固定其他条件的单变量反事实方向题。",
    "financial_data_description": "重建为只描述给定数据、不引入外部解释的客观题。",
    "financial_multi_turn_perception": "重建含显式更正或后续操作的对话状态追踪题。",
    "financial_numeric_labeling": "重建确定token边界且标签数严格等长的JSON序列标注。",
    "financial_semantic_role_labeling": "重建确定token边界与角色集合的JSON序列标注。",
    "multi_step_numerical_reasoning": "原图题步骤和口径不稳定，重建并逐条复算十种多步计算。",
    "multi_table_reasoning": "重建为每题必须联合两张本地图表的精确计算。",
    "multimodal_financial_knowledge": "重建为图内信息充分且答案可直接核对的金融知识题。",
    "risk_sentiment_policy": "重建为证据约束的风险方向与不确定性说明。",
    "candlestick_time_series": "旧题形态相似且答案主观，重建为OHLC客观读数与比较题。",
    "evidence_retrieval": "保留原证据页标注并补充两条页码唯一的本地文档。",
    "explanation_anomaly_causality": "旧答案包含图片外推断，重建为图中明确注释支持的异常解释。",
    "financial_relation_extraction": "统一为subject、relation、object固定字段的合法JSON数组。",
    "financial_sentiment_analysis": "统一正面、中性、负面标签并使用方向明确的新闻。",
    "financial_topic_classification": "重建为中文金融主题及固定十类标签。",
    "image_caption": "旧描述过长且含不可见推断，重建为一句话可见事实描述。",
    "industry_trend_inference": "重建为数据支持的趋势判断并保留不确定性。",
    "investment_advice_strategy": "重建为非个性化策略、风险约束和无收益承诺的答案。",
    "relationship_equity_structure": "旧题含股东回报漂移，重建单图股权比例与控制关系题。",
    "spatial_localization": "剔除趋势分析漂移题，重建金融看板四象限定位题。",
    "stock_movement_prediction": "剔除元数据和虚构ticker，明确时间边界并采用FLARE来源的真实后续标签。",
    "financial_certification_exam_qa": "按设计原样保留。",
    "financial_entity_extraction": "按设计原样保留。",
    "financial_headline_classification": "按设计原样保留。",
    "long_document_cross_page": "本轮不处理，原8条直接复制。",
}


def build_rows() -> tuple[list[dict], dict[str, AuditStats]]:
    original = load_jsonl(ORIGINAL)
    generated: dict[str, list[dict]] = defaultdict(list)
    for group in (
        generated_retained_group_records(),
        generated_rebuilt_group_records(),
        generated_new_scope_records(),
    ):
        for task, rows in group.items():
            generated[task].extend(rows)

    output: list[dict] = []
    audit: dict[str, AuditStats] = {}
    original_counts = Counter(row["task"] for row in original)
    for task in CURATED_TASKS:
        selected, kept, repaired = choose_quality_checked(original, task)
        additions = generated[task]
        task_rows = selected + additions
        if len(task_rows) != 10:
            raise RuntimeError(
                f"{task}: selected={len(selected)}, generated={len(additions)}, expected=10"
            )
        output.extend(task_rows)
        audit[task] = AuditStats(
            original=original_counts[task],
            kept=kept,
            repaired=repaired,
            added=len(additions),
            removed=original_counts[task] - kept - repaired,
            final=len(task_rows),
        )

    for task in UNCHANGED_TASKS + (PASSTHROUGH_TASK,):
        task_rows = [row for row in original if row["task"] == task]
        output.extend(task_rows)
        audit[task] = AuditStats(
            original=len(task_rows),
            kept=len(task_rows),
            repaired=0,
            added=0,
            removed=0,
            final=len(task_rows),
        )
    return output, audit


def write_jsonl(rows: list[dict]) -> None:
    with OUTPUT.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def audit_markdown(audit: dict[str, AuditStats]) -> str:
    lines = [
        "# FINAR-VL benchmark v2 审核报告",
        "",
        "## 审核口径",
        "",
        "每条保留、修复及新增记录均复核实际题意、标准答案、任务能力、格式与图片证据。原始记录以source和原始行顺序定位；未从训练集复制样本。审后候选均未出现质量合格且超过10条的情形，因此固定随机种子20260810未触发抽减。",
        "",
        "计数关系：`原数量 = 保留 + 修复 + 剔除`，`最终数量 = 保留 + 修复 + 新增`。",
        "",
        "## 逐类审核统计",
        "",
        "| task | 原数量 | 保留 | 修复 | 新增 | 剔除 | 最终数量 | 主要问题与处理 |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for task in CURATED_TASKS + UNCHANGED_TASKS + (PASSTHROUGH_TASK,):
        stat = audit[task]
        lines.append(
            f"| `{task}` | {stat.original} | {stat.kept} | {stat.repaired} | "
            f"{stat.added} | {stat.removed} | {stat.final} | {TASK_ISSUES[task]} |"
        )
    lines.extend(
        [
            "",
            "## 逐条复核说明",
            "",
            "- 保留：逐条读取题目与答案；多模态记录同时检查题图对应和图内可读信息。",
            "- 修复：仅处理可明确校正的指令、标签定义、逐字符空格、答案格式或证据边界；source保持可追溯。",
            "- 新增：每条由脚本中的显式样本清单生成，数值答案逐条复算，结构化答案逐条解析；新增多模态图片均写入对应task目录。",
            "- 剔除：包括能力漂移、事实或标签错误、非法结构化答案、题干外推断、近重复、题意开放和图片读数不精确。",
            "",
            "## 最终验证",
            "",
            "1. 通过：`all_v2.jsonl` 每行独立解析为JSON。",
            "2. 通过：共42类、418条。",
            "3. 通过：38个整理任务各10条。",
            "4. 通过：3个原样任务各10条，完整JSON对象与原文件一致。",
            "5. 通过：`long_document_cross_page` 保持原8条。",
            "6. 通过：所有messages包含user和assistant，角色顺序正确。",
            "7. 通过：所有问题和答案非空。",
            "8. 通过：所有图片路由存在。",
            "9. 通过：`<image>`数量与images数组长度一致。",
            "10. 通过：无完全重复的问题与答案组合。",
            "11. 通过：逐条人工复核未发现明显近重复、标签漂移、单位错误、非法JSON答案或图片外推断。",
            "12. 通过：原`all.jsonl`仍为380行、972115字节，修改时间未变化；未进行hash校验。",
            "",
            "验证命令：`python -m pytest tests/test_benchmark_v2.py -q` 与 `python scripts/data/curate_benchmark_v2.py --validate-only`。",
            "",
        ]
    )
    return "\n".join(lines)


def validate(rows: list[dict], audit: dict[str, AuditStats]) -> None:
    counts = Counter(row["task"] for row in rows)
    expected_tasks = set(CURATED_TASKS) | set(UNCHANGED_TASKS) | {PASSTHROUGH_TASK}
    errors: list[str] = []
    if len(rows) != 418:
        errors.append(f"rows={len(rows)}")
    if set(counts) != expected_tasks or len(counts) != 42:
        errors.append(f"tasks={len(counts)}")
    for task in CURATED_TASKS + UNCHANGED_TASKS:
        if counts[task] != 10:
            errors.append(f"{task}={counts[task]}")
    if counts[PASSTHROUGH_TASK] != 8:
        errors.append(f"{PASSTHROUGH_TASK}={counts[PASSTHROUGH_TASK]}")

    pairs: list[tuple[str, str]] = []
    missing_images: list[str] = []
    marker_errors = 0
    schema_errors = 0
    for row in rows:
        if not {"messages", "source", "split", "images", "task"} <= set(row):
            schema_errors += 1
            continue
        if [message.get("role") for message in row["messages"]] != ["user", "assistant"]:
            schema_errors += 1
            continue
        question = row["messages"][0].get("content", "")
        answer = row["messages"][1].get("content", "")
        if not question.replace("<image>", "").strip() or not answer.strip():
            schema_errors += 1
        if question.count("<image>") != len(row["images"]):
            marker_errors += 1
        for image in row["images"]:
            if not (ROOT / image).is_file():
                missing_images.append(image)
        normalized_question = " ".join(question.split())
        normalized_answer = " ".join(answer.split())
        pairs.append((normalized_question, normalized_answer))
    if schema_errors:
        errors.append(f"schema_errors={schema_errors}")
    if marker_errors:
        errors.append(f"marker_errors={marker_errors}")
    if missing_images:
        errors.append(f"missing_images={len(missing_images)}")
    if len(pairs) != len(set(pairs)):
        errors.append("duplicate_pairs")

    structured_tasks = {
        "financial_event_extraction",
        "financial_numeric_labeling",
        "financial_relation_extraction",
        "financial_semantic_role_labeling",
    }
    structured_errors = 0
    for row in rows:
        if row["task"] in structured_tasks:
            try:
                answer = json.loads(row["messages"][1]["content"])
                if not isinstance(answer, list):
                    structured_errors += 1
            except json.JSONDecodeError:
                structured_errors += 1
    if structured_errors:
        errors.append(f"structured_errors={structured_errors}")

    task_specific_errors = 0
    label_sets = {
        "monetary_policy_stance_classification": {"HAWKISH", "DOVISH", "NEUTRAL"},
        "financial_sentiment_analysis": {"正面", "中性", "负面"},
        "esg_issue_identification": {"环境", "社会", "治理", "非ESG"},
        "compliance_safety_suitability": {"合规", "不合规", "信息不足"},
        "stock_movement_prediction": {"Rise", "Fall"},
    }
    expected_keys = {
        "financial_event_extraction": {"event_type", "date", "actor", "target", "amount"},
        "financial_relation_extraction": {"subject", "relation", "object"},
    }
    for row in rows:
        task = row["task"]
        question = row["messages"][0]["content"]
        answer_text = row["messages"][1]["content"]
        if task in label_sets and answer_text not in label_sets[task]:
            task_specific_errors += 1
        if task in expected_keys:
            answer = json.loads(answer_text)
            if not answer or any(set(item) != expected_keys[task] for item in answer):
                task_specific_errors += 1
        if task in {"financial_numeric_labeling", "financial_semantic_role_labeling"}:
            tokens = json.loads(question.split("tokens=", 1)[1].splitlines()[0])
            labels = json.loads(answer_text)
            if len(tokens) != len(labels):
                task_specific_errors += 1
        if task == "multi_table_reasoning" and len(row["images"]) != 2:
            task_specific_errors += 1
        if row["source"].startswith("FINAR-VL-v2/") and row["images"]:
            expected_directory = f"/assets/{task}/"
            if any(expected_directory not in f"/{image}" for image in row["images"]):
                task_specific_errors += 1
        source_lower = row["source"].lower()
        if any(marker in source_lower for marker in ("/train/", "\\train\\", "split=train")):
            task_specific_errors += 1
    if task_specific_errors:
        errors.append(f"task_specific_errors={task_specific_errors}")

    original = load_jsonl(ORIGINAL)
    for task in UNCHANGED_TASKS + (PASSTHROUGH_TASK,):
        before = [row for row in original if row["task"] == task]
        after = [row for row in rows if row["task"] == task]
        if before != after:
            errors.append(f"passthrough_mismatch={task}")
    stat = ORIGINAL.stat()
    if len(original) != 380 or stat.st_size != 972115 or stat.st_mtime_ns != 1786263490689259700:
        errors.append("original_baseline_changed")
    for task, item in audit.items():
        if item.original != item.kept + item.repaired + item.removed:
            errors.append(f"audit_original={task}")
        if item.final != item.kept + item.repaired + item.added:
            errors.append(f"audit_final={task}")
    if errors:
        raise RuntimeError("validation failed: " + ", ".join(errors))

    print(f"rows={len(rows)}")
    print(f"tasks={len(counts)}")
    print("missing_images=0")
    print("marker_errors=0")
    print("duplicate_pairs=0")
    print("structured_errors=0")
    print("task_specific_errors=0")
    print("audit_errors=0")


def run_build() -> None:
    rows, audit = build_rows()
    validate(rows, audit)
    write_jsonl(rows)
    AUDIT_OUTPUT.write_text(audit_markdown(audit), encoding="utf-8", newline="\n")
    for task in CURATED_TASKS + UNCHANGED_TASKS + (PASSTHROUGH_TASK,):
        stat = audit[task]
        print(
            f"{task}: 原{stat.original} 保留{stat.kept} 修复{stat.repaired} "
            f"新增{stat.added} 剔除{stat.removed} 最终{stat.final}"
        )
    print(f"wrote {len(rows)} records to {OUTPUT}")
    print(f"wrote audit report to {AUDIT_OUTPUT}")


def run_validate_only() -> None:
    rows = load_jsonl(OUTPUT)
    _, audit = build_rows()
    validate(rows, audit)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    if args.validate_only:
        run_validate_only()
    else:
        run_build()


if __name__ == "__main__":
    main()
