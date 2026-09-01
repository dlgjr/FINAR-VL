import json
from pathlib import Path

from PIL import Image

from scripts.data.render_financial_evidence_images import (
    generate_rendered_candidates,
    make_multimodal_row,
    render_text_pages,
    split_prompt_evidence,
)
from scripts.data.select_benchmark_aligned_tasks import (
    _content_hash,
    assess_row,
    review_alignment,
)


def _row(question: str, answer: str) -> dict:
    return {
        "messages": [
            {"role": "user", "content": question},
            {"role": "assistant", "content": answer},
        ],
        "source": "unit_test",
        "split": "test",
        "task": "drifted_label",
    }


def test_split_financial_event_news_keeps_fields_and_moves_article():
    question = (
        "请从金融资讯中抽取下列实体：['中标公司', '招标方', '中标金额']。"
        "资讯：宏润建设收到杭州市地铁集团中标通知书，中标金额为132927.19万元。抽取结果："
    )

    instruction, evidence = split_prompt_evidence(question, "financial_event_extraction")

    assert "中标公司" in instruction
    assert "<image>" in instruction
    assert "宏润建设收到" not in instruction
    assert "宏润建设收到" in evidence
    assert "抽取结果" not in evidence


def test_split_financial_event_schema_prompt_moves_announcement():
    question = "从以下公告中抽取金融事件及其字段: 某上市公司控股股东将400万股质押给某银行。"

    instruction, evidence = split_prompt_evidence(question, "financial_event_extraction")

    assert "抽取金融事件及其字段" in instruction
    assert "400万股" not in instruction
    assert "400万股" in evidence


def test_split_entity_disambiguation_moves_context_but_keeps_options():
    question = (
        "请指出以下内容中提及的“新动力”是不是股票。请给出正确选项。"
        "新动力(300152.SZ)发布监管公告。A. 是 B. 不是 C. 不确定"
    )

    instruction, evidence = split_prompt_evidence(question, "entity_extraction_classification")

    assert "新动力”是不是股票" in instruction
    assert "A. 是 B. 不是 C. 不确定" in instruction
    assert "300152.SZ" not in instruction
    assert "300152.SZ" in evidence


def test_split_announcement_moves_announcement_body():
    question = (
        "请根据以下内容分析公司回购股份对公司经营及股价的影响。"
        "公司公告拟使用20亿元至30亿元回购股份，用于员工持股计划。"
    )

    instruction, evidence = split_prompt_evidence(question, "summary_announcement")

    assert "经营及股价的影响" in instruction
    assert "20亿元" not in instruction
    assert "20亿元" in evidence


def test_split_stock_research_event_moves_body_after_blank_line():
    question = (
        "你是一个个股研究员。请根据以下内容分析公司实行股权激励的目的。\n\n"
        "公司拟向核心技术人员授予限制性股票，并设置未来三年的营业收入考核目标。"
    )

    instruction, evidence = split_prompt_evidence(question, "summary_announcement")

    assert "股权激励的目的" in instruction
    assert "营业收入考核目标" not in instruction
    assert "营业收入考核目标" in evidence


def test_split_markdown_table_moves_table_for_portfolio_comparison():
    question = (
        "请比较两只基金的绩效表现。\n"
        "|基金|平均回报|最低回报|\n|:--|--:|--:|\n|A|2.0%|-1.0%|\n|B|1.0%|-3.0%|"
    )

    instruction, evidence = split_prompt_evidence(question, "portfolio_allocation_risk_return")

    assert "比较两只基金" in instruction
    assert "|A|2.0%" not in instruction
    assert "|A|2.0%" in evidence


def test_split_compliance_multiple_choice_moves_full_rule_question_to_image():
    question = (
        "依据《商业银行资本管理办法》，核心一级资本充足率最低监管要求是多少？\n"
        "选项:\nA. 3%\nB. 5%\nC. 8%\nD. 10%"
    )

    instruction, evidence = split_prompt_evidence(question, "compliance_safety_suitability")

    assert "<image>" in instruction
    assert "监管要求" in instruction
    assert "核心一级资本" not in instruction
    assert "核心一级资本" in evidence
    assert "B. 5%" in evidence


def test_render_text_pages_creates_readable_png(tmp_path):
    pages = render_text_pages("审计证据显示应收款存在减值风险。" * 20, tmp_path, "audit_1")

    assert pages
    with Image.open(pages[0]) as image:
        assert image.format == "PNG"
        assert image.width > 0
        assert image.height > 0


def test_render_text_pages_rejects_excessive_page_count(tmp_path):
    pages = render_text_pages(
        "很长的财务证据。" * 1000,
        tmp_path,
        "too_long",
        height=300,
        max_pages=1,
    )

    assert pages == []
    assert not list(tmp_path.glob("too_long*.png"))


def test_make_multimodal_row_preserves_answer_and_records_provenance(tmp_path):
    row = _row(
        "请根据以下内容分析公司回购股份对公司经营及股价的影响。"
        "公司公告拟回购股份并用于员工持股计划。",
        "回购可能稳定股价并改善员工激励。",
    )

    converted = make_multimodal_row(
        row,
        "summary_announcement",
        "train_text",
        17,
        tmp_path,
        image_path_prefix="data/benchmark_aligned_declining_tasks/rendered_images",
    )

    assert converted is not None
    assert converted["messages"][-1]["content"] == row["messages"][-1]["content"]
    assert converted["messages"][0]["content"].startswith("<image>")
    assert converted["images"][0].startswith("data/benchmark_aligned_declining_tasks/rendered_images/")
    assert converted["rendered_from"]["input_name"] == "train_text"
    assert converted["rendered_from"]["line_number"] == 17
    assert Path(tmp_path, Path(converted["images"][0]).name).exists()


def test_generate_rendered_candidates_skips_exact_benchmark_content(tmp_path):
    row = _row(
        "你是一个个股研究员。请根据以下内容分析公司实行股权激励的目的。\n\n"
        "公司拟向核心人员授予限制性股票，并设置营业收入考核目标。",
        "股权激励有助于稳定人才队伍，并推动公司实现收入增长目标。",
    )
    source = tmp_path / "source.jsonl"
    source.write_text(json.dumps(row, ensure_ascii=False) + "\n", encoding="utf-8")

    counts = generate_rendered_candidates(
        source,
        tmp_path / "rendered.jsonl",
        tmp_path / "images",
        ("summary_announcement",),
        10,
        input_name="external",
        image_path_prefix="data/train_multi/assets/align",
        excluded_content_hashes={_content_hash(row)},
    )

    assert counts["summary_announcement"] == 0
    assert (tmp_path / "rendered.jsonl").read_text(encoding="utf-8") == ""


def test_rendered_fundamentals_table_remains_content_reviewable(tmp_path):
    row = _row(
        "你是一个金融分析师，以下是某公司的主要会计数据，请分析公司的经营情况。\n"
        "|年度|营业收入|净利润|\n|:--|--:|--:|\n|2022|1000|80|\n|2023|1200|70|",
        "营业收入增长，但净利润下降，说明盈利能力承压并存在成本控制风险。",
    )

    converted = make_multimodal_row(
        row,
        "financial_audit_fundamentals",
        "external",
        4,
        tmp_path,
        image_path_prefix="data/train_multi/assets/align",
    )

    assert converted is not None
    decision = assess_row(converted, "financial_audit_fundamentals")
    assert decision.accepted
    assert review_alignment(converted, "financial_audit_fundamentals", decision)[0]
