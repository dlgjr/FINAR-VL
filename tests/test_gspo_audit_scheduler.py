from scripts.rl.gspo_audit import DEFAULT_AUDIT_COUNT, analyze_completion, build_audit_records, select_high_reward_samples
from scripts.rl.rollout_scheduler import cost_balanced_batches


def test_high_reward_sampling_is_seeded_distinct_and_stratified():
    rows = [
        {"sample_id": "a", "reward": 1.0, "completion": "答案：A", "verifier_type": "numeric", "source": "s1"},
        {"sample_id": "b", "reward": 0.9, "completion": "答案：B", "verifier_type": "numeric", "source": "s1"},
        {"sample_id": "c", "reward": 0.8, "completion": "答案：C", "verifier_type": "true_false", "source": "s2"},
        {"sample_id": "d", "reward": 0.7, "completion": "答案：D", "verifier_type": "single_choice", "source": "s3"},
    ]
    first = select_high_reward_samples(rows, seed=7, count=3)
    second = select_high_reward_samples(rows, seed=7, count=3)
    assert [row["sample_id"] for row in first] == [row["sample_id"] for row in second]
    assert len({row["sample_id"] for row in first}) == 3
    assert len({(row["_audit_stratum"]["verifier_type"], row["_audit_stratum"]["source"]) for row in first}) == 3
    assert DEFAULT_AUDIT_COUNT == 32


def test_completion_anomaly_metrics_support_chinese_and_real_truncation_signals():
    normal = analyze_completion("根据表格计算收入增长率，结果为8.59%。\n答案：8.59%")
    assert normal["abnormal_repetition"] is False
    assert normal["answer_prefix_missing"] is False

    repeated = analyze_completion("重复重复重复重复重复重复重复重复重复重复重复重复\n答案：重复")
    assert repeated["abnormal_repetition"] is True

    length_stopped = analyze_completion(
        {"content": "答案：A", "finish_reason": "length", "completion_tokens": 5}, max_completion_length=100
    )
    assert length_stopped["truncated"] is True
    normally_stopped = analyze_completion(
        {"content": "答案：A", "finish_reason": "stop", "completion_tokens": 5}, max_completion_length=100
    )
    assert normally_stopped["truncated"] is False

    replacement = analyze_completion("乱码\ufffd\n答案：A")
    assert replacement["replacement_char_count"] == 1

    missing = analyze_completion("没有规定格式")
    assert missing["answer_prefix_missing"] is True
    assert missing["parse_failed"] is True

    empty = analyze_completion("答案：  \n")
    assert empty["answer_prefix_missing"] is False
    assert empty["answer_prefix_empty"] is True


def test_audit_record_contains_prefixed_answer():
    audit = build_audit_records([{"sample_id": "x", "reward": 1.0, "completion": "分析\n答案：A,C"}], seed=1)
    assert audit[0]["answer"] == "A,C"


def test_cost_balancing_uses_fine_grained_batches():
    rows = [{"sample_id": str(i), "estimated_cost": cost} for i, cost in enumerate([100, 90, 80, 10, 10, 10])]
    assigned = cost_balanced_batches(rows, workers=2, batch_size=1)
    loads = [sum(row["estimated_cost"] for row in worker_rows) for worker_rows in assigned]
    assert max(loads) - min(loads) <= 40
