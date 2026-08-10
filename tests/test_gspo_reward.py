import json

import pytest

from scripts.rl.gspo_reward import (
    MixedReward,
    extract_prefixed_answer,
    normalize_numeric,
    score_programmatic_answer,
    score_judge_result,
)


def test_extracts_only_last_full_or_half_width_answer_prefix():
    text = "初步结论\n答案：A,C\n修正如下\n答案: B,D"
    assert extract_prefixed_answer(text) == "B,D"


def test_missing_answer_prefix_scores_negative_point_one():
    assert extract_prefixed_answer("直接回答A") is None
    assert score_programmatic_answer("直接回答A", ["A"], verifier_type="single_choice") == -0.1


def test_empty_answer_prefix_scores_zero():
    assert extract_prefixed_answer("分析完成\n答案：   \n") == ""
    assert score_programmatic_answer("分析完成\n答案：   \n", ["A"], verifier_type="single_choice") == 0.0


def test_jaccard_handles_partial_wrong_duplicate_and_empty_answers():
    assert score_programmatic_answer("分析\n答案：A", ["A"], "single_choice") == 1.0
    assert score_programmatic_answer("答案：A,B,B", ["A", "C"], "multiple_choice") == 1 / 3
    assert score_programmatic_answer("答案：B", ["A"], "single_choice") == 0.0


def test_numeric_tolerance_and_unit_inheritance_and_conflict():
    assert normalize_numeric("￥1,000.01") == (1000.01, "元")
    assert score_programmatic_answer(
        "计算过程\n答案：10.01%", ["10%"], "numeric", question="增长率是多少（%）？"
    ) == 1.0
    assert score_programmatic_answer(
        "答案：10美元", ["10元"], "numeric", question="金额是多少（元）？"
    ) == 0.0
    assert score_programmatic_answer("答案：10", ["10%"], "numeric") == 0.0


def test_page_and_boolean_programmatic_parsing():
    assert score_programmatic_answer("证据如下\n答案：第9页、第20页", ["9", "20"], "page_numbers") == 1.0
    assert score_programmatic_answer("答案：是", ["true"], "true_false") == 1.0


def test_judge_json_strict_validation_and_formula():
    result = json.dumps({"matched_claim_ids": ["G1", "G3"], "wrong_claim_count": 1})
    assert score_judge_result(result, ["G1", "G2", "G3"]) == pytest.approx(2 / 4)
    assert score_judge_result('{"matched_claim_ids":["G9"],"wrong_claim_count":0}', ["G1"]) == 0.0
    assert score_judge_result("not json", ["G1"]) == 0.0


def test_model_judge_receives_only_prefixed_answer_and_missing_prefix_skips_judge():
    seen = []

    def judge(candidate, record):
        seen.append(candidate)
        return json.dumps({"matched_claim_ids": ["G1"], "wrong_claim_count": 0})

    reward = MixedReward(judge=judge)
    record = {"sample_id": "x", "verifier_type": "model_judge", "gold_claims": ["G1"]}
    assert reward(["分析过程\n答案：最终结论"], records=[record]) == [1.0]
    assert seen == ["最终结论"]
    assert reward(["没有规定格式"], records=[record]) == [-0.1]
    assert seen == ["最终结论"]
