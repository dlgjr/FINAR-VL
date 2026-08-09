import json
from pathlib import Path


def test_programmatic_judge_accepts_choices_numbers_dates_and_page_lists():
    from scripts.sft.pass_at_8_eval import programmatic_judge

    assert programmatic_judge("答案：C", "c") is True
    assert programmatic_judge("100", "100.9") is True
    assert programmatic_judge("0", "0.0001") is False
    assert programmatic_judge("2023-09-01", "2023/9/1") is True
    assert programmatic_judge("第1页、第3页", "第3页, 第1页") is True


def test_programmatic_judge_routes_open_answers_to_model_judge():
    from scripts.sft.pass_at_8_eval import programmatic_judge

    assert programmatic_judge("这是一段开放式摘要", "另一段摘要") is None


def test_pass_at_8_counts_errors_as_incorrect():
    from scripts.sft.pass_at_8_eval import summarize_results

    summary = summarize_results(
        [
            {"task": "numeric", "correct_count": 1, "first_correct": False},
            {"task": "numeric", "correct_count": 0, "first_correct": False},
            {"task": "open", "correct_count": 2, "first_correct": True},
        ],
        total=4,
        errors=[{"sample_id": "my_benchmark:000003"}],
    )

    assert summary["pass_at_8"] == 0.5
    assert summary["pass_at_1"] == 0.25
    assert summary["coverage"] == 0.75
    assert summary["error_count"] == 1
    assert summary["tasks"]["numeric"]["pass_at_8"] == 0.5


def test_filesystem_queue_claims_each_stable_id_once(tmp_path: Path):
    from scripts.sft.pass_at_8_eval import EvaluationQueue

    queue = EvaluationQueue(tmp_path, [
        {"sample_id": "my_benchmark:000001", "cost": 3.0},
        {"sample_id": "my_benchmark:000002", "cost": 1.0},
    ])
    queue.initialize()

    first = queue.claim("rank_0000")
    second = queue.claim("rank_0001")
    third = queue.claim("rank_0002")

    assert [first["sample_id"], second["sample_id"]] == [
        "my_benchmark:000001",
        "my_benchmark:000002",
    ]
    assert third is None


def test_load_benchmark_preserves_multi_image_rows(tmp_path: Path):
    from scripts.sft.pass_at_8_eval import load_benchmark

    data = {
        "messages": [
            {"role": "user", "content": "<image><image>问题"},
            {"role": "assistant", "content": "A"},
        ],
        "source": "demo",
        "split": "test",
        "images": ["a.png", "b.png"],
        "task": "choice",
    }
    path = tmp_path / "all.jsonl"
    path.write_text(json.dumps(data, ensure_ascii=False) + "\n", encoding="utf-8")

    rows = load_benchmark(path, tmp_path)

    assert rows[0]["sample_id"] == "my_benchmark:000000"
    assert rows[0]["image_paths"] == [tmp_path / "a.png", tmp_path / "b.png"]


def test_generate_candidates_uses_supported_generation_seed_path():
    source = (Path(__file__).resolve().parents[1] / "scripts/sft/pass_at_8_eval.py").read_text(
        encoding="utf-8"
    )
    assert "torch.manual_seed(seed)" in source
    assert "generator=generator" not in source


def test_pass_at_1_uses_low_temperature_sampling_and_pass_at_8_stays_sampling():
    source = (Path(__file__).resolve().parents[1] / "scripts/sft/pass_at_8_eval.py").read_text(
        encoding="utf-8"
    )
    pass_at_1_call = source.split("pass_at_1_candidate = _generate_candidates", 1)[1].split(")[0]", 1)[0]
    pass_at_8_call = source.split("pass_at_8_candidates = _generate_candidates", 1)[1].split(")", 1)[0]
    assert "do_sample=True" in pass_at_1_call
    assert "PASS_AT_1_TEMPERATURE" in pass_at_1_call
    assert "num_return_sequences=1" in pass_at_1_call
    assert "do_sample=True" in pass_at_8_call
    assert "PASS_AT_8_TEMPERATURE" in pass_at_8_call
    assert "num_return_sequences=8" in pass_at_8_call
    assert '"pass_at_1_greedy": False' in source
    assert '"pass_at_1_temperature": PASS_AT_1_TEMPERATURE' in source
