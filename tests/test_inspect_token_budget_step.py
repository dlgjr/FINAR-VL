import json


def test_reconstructs_the_exact_dp_batch_for_a_one_based_step(tmp_path):
    from scripts.sft.inspect_token_budget_step import inspect_steps

    lengths = [10, 20, 30, 40, 9000, 10000, 40000, 50000]
    results = tmp_path / "token_length_scan" / "results"
    results.mkdir(parents=True)
    (results / "rank_0000.json").write_text(json.dumps({"lengths": list(enumerate(lengths)), "errors": []}), encoding="utf-8")
    report = inspect_steps(results_dir=results, steps=[1, 2], seed=42, dp_world_size=2, sp_size=2,
                           global_ranks=[0, 1, 2, 3])
    assert report["steps"][0]["step"] == 1
    assert report["rank_mapping"] == {"0": 0, "1": 0, "2": 1, "3": 1}


def test_report_is_json_serializable(tmp_path):
    from scripts.sft.inspect_token_budget_step import inspect_steps

    results = tmp_path / "results"
    results.mkdir()
    (results / "rank_0000.json").write_text(json.dumps({"lengths": [[0, 100], [1, 200], [2, 9000], [3, 10000]], "errors": []}), encoding="utf-8")
    json.dumps(inspect_steps(results_dir=results, steps=[1], seed=42, dp_world_size=2, sp_size=2,
                              global_ranks=[8, 9]), ensure_ascii=False)
