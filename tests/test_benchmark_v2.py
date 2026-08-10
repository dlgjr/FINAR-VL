from __future__ import annotations

from collections import Counter
import json
from pathlib import Path

from scripts.data.curate_benchmark_v2 import bar_geometry


ROOT = Path(__file__).resolve().parents[1]
BENCHMARK_ROOT = ROOT / "data" / "benchmark" / "my_benchmark"
ORIGINAL = BENCHMARK_ROOT / "all.jsonl"
OUTPUT = BENCHMARK_ROOT / "all_v2.jsonl"
AUDIT = BENCHMARK_ROOT / "all_v2_audit.md"

CURATED_TASKS = {
    "basic_arithmetic_metrics",
    "candlestick_time_series",
    "chart_data_extraction",
    "compliance_safety_suitability",
    "cross_modal_multi_hop",
    "entity_extraction_classification",
    "esg_issue_identification",
    "evidence_retrieval",
    "explanation_anomaly_causality",
    "financial_audit_fundamentals",
    "financial_causal_event_reasoning",
    "financial_counterfactual_inference",
    "financial_data_description",
    "financial_event_extraction",
    "financial_multi_turn_perception",
    "financial_numeric_labeling",
    "financial_ocr",
    "financial_relation_extraction",
    "financial_semantic_role_labeling",
    "financial_sentiment_analysis",
    "financial_summarization",
    "financial_topic_classification",
    "image_caption",
    "industry_trend_inference",
    "investment_advice_strategy",
    "merger_acquisition_completeness_classification",
    "monetary_policy_stance_classification",
    "multi_step_numerical_reasoning",
    "multi_table_reasoning",
    "multimodal_financial_knowledge",
    "portfolio_allocation_risk_return",
    "relationship_equity_structure",
    "risk_sentiment_policy",
    "single_table_qa",
    "spatial_localization",
    "statistics_comparison_ranking",
    "stock_movement_prediction",
    "summary_announcement",
}
UNCHANGED_TASKS = {
    "financial_certification_exam_qa",
    "financial_entity_extraction",
    "financial_headline_classification",
}
PASSTHROUGH_TASK = "long_document_cross_page"


def test_bar_geometry_supports_positive_and_negative_values() -> None:
    geometry = bar_geometry([72, -18], top=160, bottom=760)

    assert geometry[0][0] < geometry[0][1]
    assert geometry[1][0] < geometry[1][1]
    assert geometry[0][1] == geometry[1][0]


def load_jsonl(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def rows_for(rows: list[dict], task: str) -> list[dict]:
    return [row for row in rows if row["task"] == task]


def test_v2_has_exact_task_scope_and_counts() -> None:
    rows = load_jsonl(OUTPUT)
    counts = Counter(row["task"] for row in rows)

    assert len(CURATED_TASKS) == 38
    assert len(rows) == 418
    assert len(counts) == 42
    assert set(counts) == CURATED_TASKS | UNCHANGED_TASKS | {PASSTHROUGH_TASK}
    assert all(counts[task] == 10 for task in CURATED_TASKS)
    assert all(counts[task] == 10 for task in UNCHANGED_TASKS)
    assert counts[PASSTHROUGH_TASK] == 8


def test_v2_schema_messages_and_image_routes() -> None:
    rows = load_jsonl(OUTPUT)

    for row in rows:
        assert {"messages", "source", "split", "images", "task"} <= set(row)
        assert isinstance(row["source"], str) and row["source"].strip()
        assert isinstance(row["split"], str) and row["split"].strip()
        assert isinstance(row["images"], list)
        assert [message["role"] for message in row["messages"]] == [
            "user",
            "assistant",
        ]
        question = row["messages"][0]["content"]
        answer = row["messages"][1]["content"]
        assert isinstance(question, str) and question.replace("<image>", "").strip()
        assert isinstance(answer, str) and answer.strip()
        assert question.count("<image>") == len(row["images"])
        for image in row["images"]:
            assert image.startswith("data/benchmark/my_benchmark/assets/")
            assert (ROOT / image).is_file()


def test_unchanged_and_passthrough_tasks_match_original_exactly() -> None:
    original = load_jsonl(ORIGINAL)
    output = load_jsonl(OUTPUT)

    for task in sorted(UNCHANGED_TASKS | {PASSTHROUGH_TASK}):
        assert rows_for(output, task) == rows_for(original, task)


def test_no_exact_question_answer_duplicates() -> None:
    rows = load_jsonl(OUTPUT)
    pairs = [
        (
            " ".join(row["messages"][0]["content"].split()),
            " ".join(row["messages"][1]["content"].split()),
        )
        for row in rows
    ]

    assert len(pairs) == len(set(pairs))


def test_required_structured_answers_are_valid_json_arrays() -> None:
    rows = load_jsonl(OUTPUT)
    structured_tasks = {
        "financial_event_extraction",
        "financial_numeric_labeling",
        "financial_relation_extraction",
        "financial_semantic_role_labeling",
    }

    for task in structured_tasks:
        for row in rows_for(rows, task):
            answer = json.loads(row["messages"][1]["content"])
            assert isinstance(answer, list)


def test_task_specific_labels_structures_and_multimodal_routes() -> None:
    rows = load_jsonl(OUTPUT)
    label_sets = {
        "monetary_policy_stance_classification": {"HAWKISH", "DOVISH", "NEUTRAL"},
        "financial_sentiment_analysis": {"正面", "中性", "负面"},
        "esg_issue_identification": {"环境", "社会", "治理", "非ESG"},
        "compliance_safety_suitability": {"合规", "不合规", "信息不足"},
        "stock_movement_prediction": {"Rise", "Fall"},
    }
    for task, allowed in label_sets.items():
        assert all(row["messages"][1]["content"] in allowed for row in rows_for(rows, task))

    expected_keys = {
        "financial_event_extraction": {"event_type", "date", "actor", "target", "amount"},
        "financial_relation_extraction": {"subject", "relation", "object"},
    }
    for task, keys in expected_keys.items():
        for row in rows_for(rows, task):
            answer = json.loads(row["messages"][1]["content"])
            assert answer and all(set(item) == keys for item in answer)

    for task in ("financial_numeric_labeling", "financial_semantic_role_labeling"):
        for row in rows_for(rows, task):
            question = row["messages"][0]["content"]
            tokens = json.loads(question.split("tokens=", 1)[1].splitlines()[0])
            labels = json.loads(row["messages"][1]["content"])
            assert len(tokens) == len(labels)

    assert all(len(row["images"]) == 2 for row in rows_for(rows, "multi_table_reasoning"))
    for row in rows:
        if row["source"].startswith("FINAR-VL-v2/") and row["images"]:
            expected_directory = f"/assets/{row['task']}/"
            assert all(expected_directory in f"/{image}" for image in row["images"])


def test_no_training_source_references() -> None:
    rows = load_jsonl(OUTPUT)
    forbidden = ("/train/", "\\train\\", "split=train")

    assert all(not any(marker in row["source"].lower() for marker in forbidden) for row in rows)


def test_original_file_baseline_is_unchanged() -> None:
    stat = ORIGINAL.stat()

    assert len(ORIGINAL.read_text(encoding="utf-8").splitlines()) == 380
    assert stat.st_size == 972115
    assert stat.st_mtime_ns == 1786263490689259700


def test_audit_report_covers_every_task_and_validation_item() -> None:
    report = AUDIT.read_text(encoding="utf-8")
    all_tasks = CURATED_TASKS | UNCHANGED_TASKS | {PASSTHROUGH_TASK}

    for task in all_tasks:
        assert f"`{task}`" in report
    for heading in ("原数量", "保留", "修复", "新增", "剔除", "最终数量"):
        assert heading in report
    for item in range(1, 13):
        assert f"{item}." in report
