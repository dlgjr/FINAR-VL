import json

from scripts.rl.prepare_gspo_data import prepare_record


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
    assert "<answer>" not in prepared["messages"][0]["content"]
    assert prepared["solution"] == "2"
    assert prepared["verifier_type"] == "numeric"
    assert prepared["gold_atoms"] == ["2"]
    assert prepared["estimated_cost"] > 0


def test_prepare_record_uses_line_number_and_requires_claims_for_open_answer():
    row = {
        "messages": [{"role": "user", "content": "Explain the policy."}, {"role": "assistant", "content": "It works."}],
        "output_format": "free_text",
        "task": "long_document_reasoning",
    }
    prepared = prepare_record(row, line_number=11, claims=["G1", "G2"])
    assert prepared["sample_id"] == "line:11"
    assert prepared["verifier_type"] == "model_judge"
    assert prepared["gold_claims"] == ["G1", "G2"]
    assert prepared["gold_claim_details"][0]["id"] == "G1"
    assert "assistant" not in {m["role"] for m in prepared["messages"]}


def test_prepare_record_uses_final_solution_line_as_gold_atom():
    row = {
        "messages": [
            {"role": "user", "content": "问题：增长率？"},
            {"role": "assistant", "content": "计算 9%-0.83%=38.17%\n38.17%"},
        ],
        "output_format": "number_or_free_text",
    }
    assert prepare_record(row, line_number=1)["gold_atoms"] == ["38.17%"]
