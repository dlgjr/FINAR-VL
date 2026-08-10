from scripts.rl.gspo_audit import analyze_completion, build_audit_records, select_high_reward_samples
from scripts.rl.rollout_scheduler import cost_balanced_batches


def test_high_reward_sampling_is_seeded_and_distinct():
    rows = [
        {"sample_id": "a", "reward": 1.0, "completion": "答案：A"},
        {"sample_id": "b", "reward": 1.0, "completion": "答案：B"},
        {"sample_id": "c", "reward": 0.5, "completion": "答案：C"},
        {"sample_id": "d", "reward": 0.2, "completion": "答案：D"},
    ]
    first = select_high_reward_samples(rows, seed=7, count=3)
    second = select_high_reward_samples(rows, seed=7, count=3)
    assert [row["sample_id"] for row in first] == [row["sample_id"] for row in second]
    assert len({row["sample_id"] for row in first}) == 3
    assert {row["sample_id"] for row in first[:2]} == {"a", "b"}


def test_completion_anomaly_metrics():
    metrics = analyze_completion("乱码\ufffd\n答案：重复 重复 重复", max_completion_length=10)
    assert metrics["replacement_char_count"] == 1
    assert metrics["truncated"] is True
    assert metrics["answer_prefix_missing"] is False
    assert metrics["answer_prefix_empty"] is False

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
