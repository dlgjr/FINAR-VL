from pathlib import Path

from scripts.data.import_external_multimodal_finance import (
    iter_mme_finance_rows,
    normalize_cfbenchmark_row,
    normalize_chart_to_text_row,
    normalize_mme_finance_row,
    qa_fingerprint,
)
from scripts.data.select_benchmark_aligned_tasks import assess_row, review_alignment


def _assert_reviewed(row: dict, capability: str) -> None:
    decision = assess_row(row, capability)
    assert decision.accepted
    assert review_alignment(row, capability, decision)[0]


def test_normalize_cfbenchmark_entity_disambiguation_matches_operation():
    raw = {
        "id": "17",
        "question": "你是一个实体消岐助手。请指出以下内容中提及的“示例股份”是不是公司。请给出正确选项。\n示例股份有限公司发布年度报告。",
        "A": "是",
        "B": "不是",
        "C": "不确定",
        "answer": "A",
    }

    row = normalize_cfbenchmark_row(raw, "entity_extraction_classification")

    assert "A. 是" in row["messages"][0]["content"]
    assert row["messages"][1]["content"] == "A"
    assert row["task_original"] == "CFBenchmark/financial-entity-disambiguation"
    _assert_reviewed(row, "entity_extraction_classification")


def test_normalize_cfbenchmark_criteria_form_supported_analysis_answer():
    raw = {
        "id": 2,
        "question": (
            "你是一个金融分析师，基金甲和基金乙的风险收益指标如下，请比较两只基金的绩效表现。\n"
            "|基金|收益|风险|\n|:--|--:|--:|\n|基金甲|8%|4%|\n|基金乙|6%|2%|"
        ),
        "criterium1": {"content": "基金甲收益更高。", "score": "0.5"},
        "criterium2": {"content": "基金乙风险更低。", "score": "0.5"},
    }

    row = normalize_cfbenchmark_row(raw, "portfolio_allocation_risk_return")

    assert row["messages"][1]["content"] == "基金甲收益更高。\n基金乙风险更低。"
    _assert_reviewed(row, "portfolio_allocation_risk_return")


def test_normalize_chart_to_text_creates_holistic_financial_caption_row():
    row = normalize_chart_to_text_row(
        item_id="123",
        title="Average annual revenue of banks worldwide from 2018 to 2023",
        caption="The chart shows that bank revenue increased from 2018 through 2023, with the highest value in 2023.",
        image_path=Path("data/external_multimodal/chart_to_text/statista_dataset/dataset/imgs/123.png"),
        subset="statista",
    )

    assert row["images"] == [
        "data/external_multimodal/chart_to_text/statista_dataset/dataset/imgs/123.png"
    ]
    assert row["external_image_local"] is True
    assert row["task_original"] == "Chart-to-Text/chart-summarization"
    _assert_reviewed(row, "image_caption")


def test_normalize_mme_finance_keeps_original_category_without_target_label(tmp_path):
    raw = {
        "index": "12",
        "image_path": "candlestick/3/a.png",
        "image_type": "candlestick",
        "image_style": "PC",
        "task_category": "Investment Advice",
        "question": "解读该K线走势，给出投资建议",
        "answer": "图中K线放量突破均线，可小仓位跟进，并在前低下方设置止损。",
        "background": "",
    }

    row = normalize_mme_finance_row(raw, tmp_path / "MMfin_CN")

    assert row["messages"][0]["content"].startswith("<image>")
    assert row["images"] == [(tmp_path / "MMfin_CN/candlestick/3/a.png").as_posix()]
    assert row["task_original"] == "MME-Finance/Investment Advice"
    assert "target_capability" not in row
    _assert_reviewed(row, "investment_advice_strategy")


def test_iter_mme_finance_excludes_benchmark_qa_variants(tmp_path):
    tsv = tmp_path / "MMfin_CN.tsv"
    tsv.write_text(
        "index\timage_path\timage_type\timage_style\ttask_category\tquestion\tanswer\tbackground\n"
        "1\tcandlestick/1/a.png\tcandlestick\tPC\tExplain Reason\t为何股价大幅下降？\t由于盈利下降。\t\n"
        "2\tcandlestick/2/a.png\tcandlestick\tPC\tInvestment Advice\t如何操作？\t建议观望。\t\n",
        encoding="utf-8",
    )
    excluded = {qa_fingerprint("<image>为何股价大幅下降？", "由于盈利下降。")}

    rows = list(iter_mme_finance_rows(tsv, tmp_path / "MMfin_CN", excluded))

    assert len(rows) == 1
    assert "如何操作" in rows[0]["messages"][0]["content"]
