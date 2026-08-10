from scripts.data.derive_entity_disambiguation import derive_entity_rows
from scripts.data.select_benchmark_aligned_tasks import assess_row, review_alignment


def _announcement(text: str) -> dict:
    return {
        "messages": [
            {"role": "user", "content": text},
            {"role": "assistant", "content": '[[0, "EquityPledge", {}]]'},
        ],
        "source": "announcement_unit_test",
    }


def _assert_reviewed(rows: list[dict]) -> None:
    for row in rows:
        decision = assess_row(row, "entity_extraction_classification")
        assert decision.accepted
        assert review_alignment(row, "entity_extraction_classification", decision)[0]


def test_derive_stock_and_company_judgments_from_explicit_announcement_identifiers():
    rows = derive_entity_rows(
        _announcement(
            "证券代码：002212 证券简称：南洋股份 公告编号：2014-024\n"
            "广东南洋电缆集团股份有限公司关于股权质押的公告。"
        ),
        line_number=25,
    )

    questions = [row["messages"][0]["content"] for row in rows]
    assert any("“南洋股份”是不是股票" in question for question in questions)
    assert any("“广东南洋电缆集团股份有限公司”是不是公司" in question for question in questions)
    assert all(row["messages"][1]["content"] == "A" for row in rows)
    _assert_reviewed(rows)


def test_derive_person_as_not_company_only_with_explicit_title_evidence():
    rows = derive_entity_rows(
        _announcement(
            "公司接到股东郑钟南先生的通知，郑钟南先生将其持有的股份质押给某银行。"
        ),
        line_number=31,
    )

    assert len(rows) == 1
    assert "“郑钟南”是不是公司" in rows[0]["messages"][0]["content"]
    assert rows[0]["messages"][1]["content"] == "B"
    _assert_reviewed(rows)
