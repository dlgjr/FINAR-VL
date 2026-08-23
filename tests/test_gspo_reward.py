import json

import pytest

from scripts.rl.gspo_reward import (
    MixedReward,
    extract_prefixed_answer,
    normalize_numeric,
    numeric_gold_from_text,
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
    assert score_programmatic_answer("答案：BDE", ["B", "D", "E"], "multiple_choice") == 1.0


def test_composite_numeric_uses_numeric_set_and_text_verifiers_are_disabled():
    composite = [{"value": "-2.5", "unit": "%"}, {"value": "100", "unit": "万元"}]
    assert score_programmatic_answer("答案：100万元，-2.5%", [], "composite_numeric", gold_numeric=composite) == 1.0
    assert score_programmatic_answer("答案：-2.5%", [], "composite_numeric", gold_numeric=composite) == 0.5
    scalar_set = [{"value": "1", "unit": ""}, {"value": "2024", "unit": ""}, {"value": "1.94", "unit": ""}]
    assert score_programmatic_answer("答案：1，2024，1.94", [], "composite_numeric", gold_numeric=scalar_set) == 1.0
    assert score_programmatic_answer("答案：来源二更高", ["来源二更高"], "short_text") == 0.0
    assert score_programmatic_answer("答案：存货,现金", ["现金", "存货"], "text_set") == 0.0


def test_numeric_units_are_longest_match_and_convert_compatible_currency_scales():
    assert normalize_numeric("￥1,000.01") == (1000.01, "元")
    assert normalize_numeric("43.48万亿元") == (43.48, "万亿元")
    gold = [{"value": "43.48", "unit": "万亿元"}]
    assert score_programmatic_answer("答案：43.48万亿元", [], "numeric", gold_numeric=gold) == 1.0
    assert score_programmatic_answer("答案：43480000000000元", [], "numeric", gold_numeric=gold) == 1.0
    assert score_programmatic_answer("答案：43.48万", [], "numeric", gold_numeric=gold) == 0.0
    assert score_programmatic_answer("答案：43.48元", [], "numeric", gold_numeric=gold) == 0.0


def test_unitless_numeric_accepts_display_or_base_value_and_compound_chinese_units():
    percent = numeric_gold_from_text("8%")
    assert score_programmatic_answer("答案：0.08", [], "numeric", gold_numeric=percent) == 1.0
    assert score_programmatic_answer("答案：8", [], "numeric", gold_numeric=percent) == 1.0
    assert score_programmatic_answer("答案：0.8", [], "numeric", gold_numeric=percent) == 0.0

    ten_million = numeric_gold_from_text("8千万")
    assert ten_million == [{"value": "8", "unit": "千万"}]
    assert score_programmatic_answer("答案：80000000", [], "numeric", gold_numeric=ten_million) == 1.0
    assert score_programmatic_answer("答案：8000000", [], "numeric", gold_numeric=ten_million) == 0.0

    million_cny = numeric_gold_from_text("170748百万元")
    assert million_cny == [{"value": "170748", "unit": "百万元"}]
    assert score_programmatic_answer("答案：170748000000", [], "numeric", gold_numeric=million_cny) == 1.0


def test_numeric_does_not_inherit_units_from_question_and_count_unit_is_optional():
    gold = [{"value": "2", "unit": "count"}]
    assert score_programmatic_answer("答案：2项", [], "numeric", question="阈值为5.4%，有多少项？", gold_numeric=gold) == 1.0
    assert score_programmatic_answer("答案：2", [], "numeric", question="阈值为5.4%，有多少项？", gold_numeric=gold) == 1.0
    assert score_programmatic_answer("答案：2%", [], "numeric", question="阈值为5.4%，有多少项？", gold_numeric=gold) == 0.0


def test_percentage_points_are_not_plain_percentages():
    assert numeric_gold_from_text("下降2个百分点") == [{"value": "2", "unit": "百分点"}]
    gold = [{"value": "2", "unit": "百分点"}]
    assert score_programmatic_answer("答案：2个百分点", [], "numeric", gold_numeric=gold) == 1.0
    assert score_programmatic_answer("答案：2 percentage points", [], "numeric", gold_numeric=gold) == 1.0
    assert score_programmatic_answer("答案：2%", [], "numeric", gold_numeric=gold) == 0.0


def test_scientific_notation_is_one_numeric_atom():
    assert numeric_gold_from_text("1e-05") == [{"value": "0.00001", "unit": ""}]
    assert numeric_gold_from_text("4.65856e+06") == [{"value": "4.65856E+6", "unit": ""}]
    gold = [{"value": "0.00001", "unit": ""}]
    assert score_programmatic_answer("答案：1e-05", [], "numeric", gold_numeric=gold) == 1.0


def test_ratio_tolerance_is_tighter_than_one_percentage_point():
    gold = [{"value": "0.0859", "unit": ""}]
    assert score_programmatic_answer("答案：0.08595", [], "numeric", gold_numeric=gold) == 1.0
    assert score_programmatic_answer("答案：0.0959", [], "numeric", gold_numeric=gold) == 0.0


def test_explicit_tolerance_can_be_tightened_per_gold():
    gold = [{"value": "100", "unit": "", "abs_tol": "0", "rel_tol": "0"}]
    assert score_programmatic_answer("答案：100", [], "numeric", gold_numeric=gold) == 1.0
    assert score_programmatic_answer("答案：100.00001", [], "numeric", gold_numeric=gold) == 0.0


def test_verified_numeric_alias_accepts_explicit_program_equivalent_scale():
    gold = [{"value": "8.59", "unit": "%", "aliases": [{"value": "0.0859", "unit": ""}]}]
    assert score_programmatic_answer("答案：8.59%", [], "numeric", gold_numeric=gold) == 1.0
    assert score_programmatic_answer("答案：0.0859", [], "numeric", gold_numeric=gold) == 1.0
    assert score_programmatic_answer("答案：8.59", [], "numeric", gold_numeric=gold) == 1.0


def test_page_and_boolean_programmatic_parsing_is_exact():
    assert score_programmatic_answer("证据如下\n答案：第9页、第20页", ["9", "20"], "page_numbers") == 1.0
    assert score_programmatic_answer("答案：是", ["true"], "true_false") == 1.0
    assert score_programmatic_answer("答案：不正确", ["false"], "true_false") == 1.0
    assert score_programmatic_answer("答案：不是", ["false"], "true_false") == 1.0
    assert score_programmatic_answer("答案：不对", ["false"], "true_false") == 1.0
    assert score_programmatic_answer("答案：不正确", ["true"], "true_false") == 0.0


def test_judge_json_strict_validation_and_formula():
    result = json.dumps({"matched_claim_ids": ["G1", "G3"], "wrong_claim_count": 1})
    assert score_judge_result(result, ["G1", "G2", "G3"]) == pytest.approx(2 / 4)
    assert score_judge_result('{"matched_claim_ids":["G9"],"wrong_claim_count":0}', ["G1"]) == 0.0
    assert score_judge_result("not json", ["G1"]) == 0.0
    assert score_judge_result('{"score":0.75}', []) == 0.75
    assert score_judge_result('{"score":1.5}', []) == 0.0


def test_model_judge_receives_only_prefixed_answer_and_missing_prefix_skips_judge():
    seen = []

    def judge(candidate, record):
        seen.append(candidate)
        return json.dumps({"score": 1.0})

    reward = MixedReward(judge=judge)
    record = {"sample_id": "x", "verifier_type": "model_judge", "gold_claims": []}
    assert reward(["分析过程\n答案：最终结论"], records=[record]) == [1.0]
    assert seen == ["最终结论"]
    assert reward(["没有规定格式"], records=[record]) == [-0.1]
    assert seen == ["最终结论"]
