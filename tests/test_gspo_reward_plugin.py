from scripts.dlc.gspo_reward_plugin import GSPOReward, records_from_kwargs


def test_reward_plugin_builds_per_sample_metadata_and_returns_equal_length():
    records = records_from_kwargs(
        {
            "source": ["s1", "s2"],
            "reward_type": ["rule", "judge"],
            "verifier_type": ["numeric", "model_judge"],
            "gold_atoms": [[], []],
            "gold_numeric": [[{"value": "2", "unit": "count"}], []],
            "gold_claims": [[], ["G1"]],
            "judge_reference_mode": ["", "gold_claims"],
            "question": ["q1", "q2"],
        },
        2,
    )
    assert records[0]["source"] == "s1"
    assert records[1]["reward_type"] == "judge"
    assert records[0]["gold_numeric"] == [{"value": "2", "unit": "count"}]
    reward = GSPOReward()
    assert reward(["答案：2项", "没有答案前缀"], records=records) == [1.0, -0.1]
    assert reward.completed_by_route == {"rule": 1, "judge": 1}
