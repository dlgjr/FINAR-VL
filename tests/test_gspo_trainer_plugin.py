from scripts.dlc.gspo_trainer_plugin import GSPOEvalCallback


def test_reward_pool_paths_aggregate_all_node_files(tmp_path):
    first = tmp_path / "reward_pool_rank_0.jsonl"
    second = tmp_path / "reward_pool_rank_1.jsonl"
    first.write_text("{}\n", encoding="utf-8")
    second.write_text("{}\n", encoding="utf-8")
    assert GSPOEvalCallback._reward_pool_paths(first) == [first, second]
