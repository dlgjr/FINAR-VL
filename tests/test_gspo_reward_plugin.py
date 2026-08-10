from scripts.dlc.gspo_reward_plugin import GSPOReward, records_from_kwargs


def test_reward_plugin_builds_per_sample_metadata_and_returns_equal_length():
    records = records_from_kwargs(
        {
            "verifier_type": ["single_choice", "model_judge"],
            "gold_atoms": [["A"], []],
            "gold_claims": [[], ["G1"]],
            "question": ["q1", "q2"],
        },
        2,
    )
    assert records[0]["gold_atoms"] == ["A"]
    reward = GSPOReward()
    assert reward(["答案：A", "没有答案前缀"], records=records) == [1.0, -0.1]
