from collections import Counter
import json
from pathlib import Path

from scripts.data.build_my_benchmark import TASK_QUOTAS


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "data" / "benchmark" / "my_benchmark" / "all.jsonl"


def load_rows():
    return [
        json.loads(line)
        for line in OUTPUT.read_text(encoding="utf-8").splitlines()
    ]


def test_my_benchmark_matches_train_multi_schema_and_quotas():
    assert {path.name for path in OUTPUT.parent.iterdir()} == {
        "all.jsonl",
        "assets",
    }
    rows = load_rows()

    assert len(rows) == 200
    assert Counter(row["task"] for row in rows) == Counter(TASK_QUOTAS)
    assert len({row["source"] for row in rows}) == 200

    for row in rows:
        assert list(row) == ["messages", "source", "split", "images", "task"]
        assert row["split"] == "test"
        assert [message["role"] for message in row["messages"]] == [
            "user",
            "assistant",
        ]
        assert row["messages"][0]["content"].count("<image>") == len(
            row["images"]
        )
        assert row["messages"][0]["content"].replace("<image>", "").strip()
        assert not row["messages"][0]["content"].lower().startswith(
            "<image>nan"
        )
        assert row["messages"][1]["content"].strip()
        for image in row["images"]:
            assert image.startswith("data/benchmark/my_benchmark/assets/")
            assert (ROOT / image).is_file()


def test_multi_table_samples_have_multiple_media_or_explicit_page_evidence():
    rows = [
        row for row in load_rows() if row["task"] == "multi_table_reasoning"
    ]

    assert len(rows) == 20
    for row in rows:
        question = row["messages"][0]["content"]
        assert (
            len(row["images"]) >= 2
            or "页面" in question
            or "page" in question.lower()
        )


def test_cross_modal_answers_are_valid_and_not_single_class():
    answers = {
        row["messages"][1]["content"].strip().lower()
        for row in load_rows()
        if row["task"] == "cross_modal_multi_hop"
    }

    assert "none" not in answers
    assert len(answers) >= 3
