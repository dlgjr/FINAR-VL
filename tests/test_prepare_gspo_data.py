import json

import pytest

from scripts.rl.prepare_gspo_data import RejectedRecord, execute_financial_program, prepare_jsonl, prepare_record


def test_prepare_record_removes_assistant_and_adds_stable_schema(tmp_path):
    row = {
        "messages": [
            {"role": "user", "content": "问题：1+1=?"},
            {"role": "assistant", "content": "2"},
        ],
        "output_format": "number_or_free_text",
        "_pass_at_k": {"result_index": "train_text:42"},
        "images": ["data/train_multi/assets/a.png"],
        "task": "basic_arithmetic_metrics",
    }
    prepared = prepare_record(row, line_number=7)
    assert prepared["sample_id"] == "train_text:42"
    assert all(message["role"] != "assistant" for message in prepared["messages"])
    assert "答案：具体答案" in prepared["messages"][0]["content"]
    assert prepared["solution"] == "2"
    assert prepared["verifier_type"] == "numeric"
    assert prepared["gold_atoms"] == []
    assert prepared["gold_numeric"] == [{"value": "2", "unit": ""}]
    assert prepared["gold_source"] == "assistant.final_answer"
    assert prepared["gold_verification"]["status"] == "source_only"
    assert prepared["estimated_cost"] > 0


def test_prepare_record_uses_line_number_and_ignores_claims_for_open_answer():
    row = {
        "messages": [{"role": "user", "content": "Explain the policy."}, {"role": "assistant", "content": "It works."}],
        "output_format": "free_text",
        "task": "long_document_reasoning",
    }
    prepared = prepare_record(row, line_number=11, claims=["G1", "G2"])
    assert prepared["sample_id"] == "line:11"
    assert prepared["verifier_type"] == "model_judge"
    assert prepared["gold_claims"] == []
    assert prepared["gold_claim_details"] == []
    assert prepared["gold_source"] == "question_only"
    assert prepared["judge_reference_mode"] == "question_only"
    assert prepared["judge_reference"] == ""
    assert "assistant" not in {m["role"] for m in prepared["messages"]}


def test_prepare_record_uses_last_numeric_from_final_answer_not_years():
    row = {
        "messages": [
            {"role": "user", "content": "问题：2021到2023 CAGR？"},
            {"role": "assistant", "content": "分析...\n答案:The 2021–2023 revenue CAGR was approximately 21.4%."},
        ],
        "output_format": "number_or_free_text",
    }
    assert prepare_record(row, line_number=1)["gold_numeric"] == [{"value": "21.4", "unit": "%"}]


def test_program_execution_recomputes_and_preserves_verified_display_scale():
    good = {
        "messages": [{"role": "user", "content": "q"}, {"role": "assistant", "content": "0.0859"}],
        "output_format": "numeric_or_short_text",
        "metadata": {
            "program": "subtract(108.59, 100.00), divide(#0, 100.00)",
            "operation_count": 2,
            "program_execution_result": "0.08590000000000003",
            "gold_execution_answer": "0.0859",
            "gold_readable_answer": "8.59%",
        },
    }
    prepared = prepare_record(good, 1)
    assert prepared["gold_source"] == "metadata.gold_readable_answer+program_verified"
    assert prepared["gold_verification"]["status"] == "verified"
    assert prepared["gold_numeric"][0]["value"] == "8.59"
    assert prepared["gold_numeric"][0]["unit"] == "%"
    assert prepared["gold_numeric"][0]["aliases"] == [{"value": "0.0859", "unit": ""}]

    broken = json.loads(json.dumps(good))
    broken["metadata"].update(
        {
            "program": "add(2074, 1622), add(1703, #0)",
            "program_execution_result": "5399.0",
            "gold_execution_answer": "5399.0",
            "gold_readable_answer": "1799.7",
        }
    )
    prepared_broken = prepare_record(broken, 1)
    assert prepared_broken["gold_numeric"] == [{"value": "1799.7", "unit": ""}]
    assert "program_conflict:gold_readable_answer_mismatch" in prepared_broken["gold_source"]
    assert prepared_broken["gold_verification"]["status"] == "source_only"


def test_convfinqa_program_must_match_original_program_prefix():
    row = {
        "messages": [{"role": "user", "content": "q"}, {"role": "assistant", "content": "23"}],
        "output_format": "numeric_or_short_text",
        "metadata": {
            "program": "multiply(24, const_m1), add(#0, 47)",
            "original_program": "multiply(24, const_m1), add(A0, 47), divide(A1, const_2)",
            "gold_readable_answer": "23",
        },
    }
    prepared = prepare_record(row, 1)
    assert prepared["gold_verification"]["status"] == "verified"
    assert prepared["gold_numeric"][0]["value"] == "23"

    broken = json.loads(json.dumps(row))
    broken["metadata"]["program"] = "add(1, 2)"
    with pytest.raises(RejectedRecord, match="original_program_prefix_mismatch"):
        prepare_record(broken, 1)


def test_page_numbers_use_independent_evidence_pages_and_cross_check_answer():
    row = {
        "messages": [{"role": "user", "content": "<image><image>找证据"}, {"role": "assistant", "content": "答案：第2页"}],
        "images": ["a.png", "b.png"],
        "output_format": "page_numbers",
        "metadata": {"evidence_pages": [2]},
    }
    prepared = prepare_record(row, 1)
    assert prepared["gold_atoms"] == ["2"]
    assert prepared["gold_source"] == "metadata.evidence_pages"
    assert prepared["gold_verification"]["status"] == "verified"

    broken = json.loads(json.dumps(row))
    broken["messages"][-1]["content"] = "答案：第1页"
    with pytest.raises(RejectedRecord, match="evidence_pages_answer_mismatch"):
        prepare_record(broken, 1)


def test_execute_financial_program_supports_dataset_operations_constants_and_a_refs():
    assert execute_financial_program("multiply(24, const_m1), add(#0, 47)") == 23
    assert execute_financial_program("add(118, 145), add(#0, 88), divide(#1, const_3)") == 117
    assert execute_financial_program("add(118, 145), add(A0, 88), divide(A1, const_3)") == 117


def test_prepare_jsonl_retains_readable_gold_when_program_display_conflicts(tmp_path):
    good = {
        "messages": [{"role": "user", "content": "q"}, {"role": "assistant", "content": "2"}],
        "output_format": "number_or_free_text",
    }
    bad = {
        "messages": [{"role": "user", "content": "q"}, {"role": "assistant", "content": "5399"}],
        "output_format": "numeric_or_short_text",
        "metadata": {
            "program": "add(2074, 1622), add(1703, #0)",
            "program_execution_result": "5399.0",
            "gold_execution_answer": "5399.0",
            "gold_readable_answer": "1799.7",
        },
    }
    source = tmp_path / "input.jsonl"
    source.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in (good, bad)) + "\n", encoding="utf-8")
    report = prepare_jsonl(source, tmp_path / "out.jsonl", tmp_path / "audit.json")
    assert report["written"] == 2
    assert report["rejected_count"] == 0
    assert report["rejected_by_reason"] == {}
    rows = [json.loads(line) for line in (tmp_path / "out.jsonl").read_text(encoding="utf-8").splitlines()]
    assert rows[1]["gold_numeric"] == [{"value": "1799.7", "unit": ""}]


def test_explicit_routes_override_free_text_format_and_ignore_reference_for_judge():
    numeric = {
        "messages": [{"role": "user", "content": "计算差额"}, {"role": "assistant", "content": "计算：2-37=-35\n-35%"}],
        "output_format": "free_text",
        "reward_type": "rule",
        "reward_subtype": "numeric_final",
        "verifier_type": "numeric_final",
    }
    prepared_numeric = prepare_record(numeric, 1)
    assert prepared_numeric["verifier_type"] == "numeric_final"
    assert prepared_numeric["gold_numeric"] == [{"value": "-35", "unit": "%"}]

    judged = {
        "messages": [{"role": "user", "content": "解释政策影响"}],
        "solution": "政策会影响利率预期。",
        "reference": "政策会影响利率预期。",
        "reward_type": "judge",
        "reward_subtype": "free_text",
        "verifier_type": "model_judge",
        "_reward_routing": {"reference_mode": "reference"},
    }
    prepared_judged = prepare_record(judged, 2)
    assert prepared_judged["judge_reference_mode"] == "question_only"
    assert prepared_judged["judge_reference"] == ""


def test_composite_numeric_builds_distinct_gold_and_text_routes_are_rejected():
    composite = {
        "messages": [
            {"role": "user", "content": "q"},
            {"role": "assistant", "content": "答案：-2.5%，100万元"},
        ],
        "reward_type": "rule",
        "reward_subtype": "composite_numeric",
        "verifier_type": "composite_numeric",
    }
    assert prepare_record(composite, 1)["gold_numeric"] == [
        {"value": "-2.5", "unit": "%"},
        {"value": "100", "unit": "万元"},
    ]
    composite["messages"][-1]["content"] = "答案：1.28个百分点，1.28个百分点"
    assert prepare_record(composite, 1)["gold_numeric"] == [{"value": "1.28", "unit": "百分点"}]

    short = {
        "messages": [{"role": "user", "content": "q"}, {"role": "assistant", "content": "A, B remain related"}],
        "reward_type": "rule",
        "reward_subtype": "short_text",
        "verifier_type": "short_text",
    }
    with pytest.raises(ValueError, match="unknown verifier_type"):
        prepare_record(short, 2)

    text_set = {
        "messages": [{"role": "user", "content": "q"}, {"role": "assistant", "content": "现金, 存货"}],
        "reward_type": "rule",
        "reward_subtype": "text_set",
        "verifier_type": "text_set",
    }
    with pytest.raises(ValueError, match="unknown verifier_type"):
        prepare_record(text_set, 3)
