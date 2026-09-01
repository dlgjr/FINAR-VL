from scripts.rl.audit_programmatic_data import audit_record


def test_pass_at_k_does_not_affect_programmatic_data_acceptance():
    row = {
        "messages": [{"role": "user", "content": "1+1?"}, {"role": "assistant", "content": "2"}],
        "output_format": "number_or_free_text",
        "_pass_at_k": {"correct_count": 0, "result_index": "x"},
    }
    result = audit_record(row, 1)
    assert result["status"] == "clean"
    assert result["reasons"] == []
    assert result["has_independent_reference"] is False


def test_convfinqa_original_program_prefix_counts_as_independent_verification():
    row = {
        "messages": [{"role": "user", "content": "q"}, {"role": "assistant", "content": "23"}],
        "output_format": "numeric_or_short_text",
        "source": "convfinqa_rendered_rl_verified",
        "metadata": {
            "program": "multiply(24, const_m1), add(#0, 47)",
            "original_program": "multiply(24, const_m1), add(A0, 47), divide(A1, const_2)",
            "gold_readable_answer": "23",
        },
    }
    result = audit_record(row, 1)
    assert result["status"] == "clean"
    assert result["has_independent_reference"] is True


def test_bad_program_reference_is_retained_as_suspicious():
    row = {
        "messages": [{"role": "user", "content": "average?"}, {"role": "assistant", "content": "5399"}],
        "output_format": "numeric_or_short_text",
        "metadata": {
            "program": "add(2074, 1622), add(1703, #0)",
            "operation_count": 2,
            "program_execution_result": "5399.0",
            "gold_execution_answer": "5399.0",
            "gold_readable_answer": "1799.7",
        },
    }
    result = audit_record(row, 1)
    assert result["status"] == "suspicious"
    assert result["reasons"] == ["gold_readable_answer_mismatch"]
