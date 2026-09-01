from scripts.data.reclassify_rl_routes import classify_reasoning


def _row(question: str, answer: str) -> dict:
    return {
        "messages": [
            {"role": "user", "content": question},
            {"role": "assistant", "content": answer},
        ]
    }


def test_recovers_choice_label_from_option_text_and_contiguous_letters():
    single = _row("最大股东是谁？\nA. 甲公司\nB. 乙公司", "甲公司")
    assert classify_reasoning(single) == ("rule", "single_choice")
    assert single["solution"] == "A"

    multiple = _row("哪些因素成立？\nA: 政策\nB: 利率\nC: 供给\nD: 无", "结论。Answer: ABC.")
    assert classify_reasoning(multiple) == ("rule", "multiple_choice")
    assert multiple["solution"] == "ABC"


def test_semantic_text_uses_model_judge_and_punctuated_boolean_stays_programmatic():
    semantic = _row("结合图表解释风险偏好如何变化。", "风险偏好下降")
    assert classify_reasoning(semantic) == ("judge", "free_text")
    assert semantic["verifier_type"] == "model_judge"
    assert semantic["reference"] == "风险偏好下降"

    boolean = _row("Can the return increase?", "Yes.")
    assert classify_reasoning(boolean) == ("rule", "true_false")
    assert boolean["solution"] == "true"
