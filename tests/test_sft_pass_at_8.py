import json
from pathlib import Path


def test_programmatic_judge_accepts_choices_numbers_dates_and_page_lists():
    from scripts.sft.pass_at_8_eval import programmatic_judge

    assert programmatic_judge("答案：C", "c") is True
    assert programmatic_judge("100", "100.9") is True
    assert programmatic_judge("0", "0.0001") is False
    assert programmatic_judge("2023-09-01", "2023/9/1") is True
    assert programmatic_judge("第1页、第3页", "第3页, 第1页") is True


def test_programmatic_judge_scans_full_response_for_choice_and_numeric_answers():
    from scripts.sft.pass_at_8_eval import programmatic_judge

    assert programmatic_judge("A", "经过分析，正确选项是 A。") is True
    assert programmatic_judge("A", "经过分析，正确选项是 a。") is True
    assert programmatic_judge("A", "CAT") is False
    assert programmatic_judge("A,C", "综合判断应选择 a 和 c。") is True
    assert programmatic_judge("A,C", "综合判断应选择 ac。") is True
    assert programmatic_judge("AC", "综合判断应选择选项AC。") is True
    assert programmatic_judge("A,C", "综合判断应选择 ABC。") is False
    assert programmatic_judge("A,C", "综合判断只选择 a。") is False
    assert programmatic_judge("A,C", "zzczz") is False
    assert programmatic_judge("A,C", "xyz") is False
    assert programmatic_judge("14.18", "计算过程略，最终结果为 14.18%。") is True
    assert programmatic_judge("14.18", "最终结果为14.18，符合要求。") is True
    assert programmatic_judge("1090.0", "因此答案是 1090.0 万元。") is True
    assert programmatic_judge("14.18", "计算得到 7.09，最终结果为 14.18。") is True
    assert programmatic_judge("14.18", "计算得到 7.09，最终结果为 14.19。") is True
    assert programmatic_judge("14.18", "计算得到 7.09，最终结果为 14.40。") is False


def test_programmatic_judge_accepts_bare_page_numbers_and_json_code_fences():
    from scripts.sft.pass_at_8_eval import programmatic_judge

    assert programmatic_judge("第1页、第20页", "答案在 1, 20。") is True
    assert programmatic_judge("1,20", "答案在第1页和第20页。", task="evidence_retrieval") is True
    assert programmatic_judge("1,20", "第1页和第20页，另见2024年数据。", task="evidence_retrieval") is True
    assert programmatic_judge("1,20", "第10页和第20页。", task="evidence_retrieval") is False
    assert programmatic_judge('{"a": 1}', '```json\n{"a": 1}\n```') is True


def test_programmatic_judge_routes_open_answers_to_model_judge():
    from scripts.sft.pass_at_8_eval import programmatic_judge

    assert programmatic_judge("这是一段开放式摘要", "另一段摘要") is None
    assert programmatic_judge("2024年公司收入增长", "另一段带年份的开放答案") is None


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


def test_make_messages_requires_answer_only(monkeypatch):
    from scripts.sft.pass_at_8_eval import _make_messages

    monkeypatch.delenv("GSPO_BENCHMARK_ALLOWLIST", raising=False)
    row = {
        "messages": [{"role": "user", "content": "问题"}],
        "image_paths": [],
    }

    prompt = _make_messages(row)[0]["content"][-1]["text"]

    assert "只输出最终答案本身" in prompt
    assert "不要输出分析过程或额外解释" in prompt


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
