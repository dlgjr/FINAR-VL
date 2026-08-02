def test_select_representative_rows_fills_confirmed_bucket_counts():
    from scripts.sft.debug_sample_selection import select_representative_rows

    rows = (
        [{"length": 100 + index} for index in range(4)]
        + [{"length": 9000 + index} for index in range(2)]
        + [{"length": 33000 + index} for index in range(2)]
    )

    selected = select_representative_rows(rows, length_fn=lambda row: row["length"])

    assert [row["length"] for row in selected] == [100, 101, 102, 103, 9000, 9001, 33000, 33001]


def test_select_representative_rows_rejects_missing_bucket():
    import pytest

    from scripts.sft.debug_sample_selection import select_representative_rows

    with pytest.raises(ValueError, match="missing representative samples"):
        select_representative_rows([{"length": 10}] * 8, length_fn=lambda row: row["length"])
