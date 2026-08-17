import json
from pathlib import Path

import pytest

import scripts.sft.kl_retention_plugin as kl_plugin
from scripts.sft.swift_sft_plugin import _PlanRuntimeTracker


def _distribution(task: str, samples: int, tokens: int) -> dict:
    values = {"samples": samples, "assistant_tokens": tokens}
    return {
        "samples": samples,
        "assistant_tokens": tokens,
        "sample_ratio": 0.0,
        "token_ratio": 0.0,
        "tasks": {task: dict(values)},
        "families": {task: dict(values)},
    }


def test_teacher_failure_is_propagated_as_data_before_sp_exit(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(kl_plugin, "_sp_state", lambda: (None, 1, 1, 1, 0))

    def fail_teacher(*args, **kwargs):
        raise RuntimeError("reference unavailable")

    monkeypatch.setattr(kl_plugin, "_teacher_generate", fail_teacher)

    with pytest.raises(RuntimeError, match="teacher generation failed on SP leader: RuntimeError: reference unavailable"):
        kl_plugin._teacher_rollout_for_route(
            trainer=None,
            route={"modality": "text", "index": 3, "raw_index": 7},
            record={"messages": [{"role": "user", "content": "q"}]},
            data_file=tmp_path / "train.jsonl",
        )


def test_plan_merge_counts_each_dp_sample_once_and_sums_sp_token_shards(tmp_path: Path):
    tracker = _PlanRuntimeTracker.__new__(_PlanRuntimeTracker)
    tracker.output_dir = tmp_path
    tracker.dp_world = 2

    payloads = [
        {
            "rank": 0,
            "dp_rank": 0,
            "sp_rank": 0,
            "sp_world": 2,
            "planned": _distribution("a", 1, 10),
            "actual": _distribution("a", 1, 4),
        },
        {
            "rank": 1,
            "dp_rank": 0,
            "sp_rank": 1,
            "sp_world": 2,
            "planned": _distribution("a", 1, 10),
            "actual": _distribution("a", 1, 6),
        },
        {
            "rank": 2,
            "dp_rank": 1,
            "sp_rank": 0,
            "sp_world": 2,
            "planned": _distribution("b", 1, 20),
            "actual": _distribution("b", 1, 7),
        },
        {
            "rank": 3,
            "dp_rank": 1,
            "sp_rank": 1,
            "sp_world": 2,
            "planned": _distribution("b", 1, 20),
            "actual": _distribution("b", 1, 13),
        },
    ]
    for payload in payloads:
        path = tmp_path / f"block_0000.rank_{payload['rank']:04d}.json"
        path.write_text(json.dumps(payload), encoding="utf-8")

    tracker.merge_block(0)
    merged = json.loads((tmp_path / "block_0000.json").read_text(encoding="utf-8"))

    assert merged["planned"]["samples"] == 2
    assert merged["planned"]["assistant_tokens"] == 30
    assert merged["actual"]["samples"] == 2
    assert merged["actual"]["assistant_tokens"] == 30
    assert merged["actual"]["tasks"]["a"]["samples"] == 1
    assert merged["actual"]["tasks"]["a"]["assistant_tokens"] == 10
    assert merged["actual"]["tasks"]["b"]["samples"] == 1
    assert merged["actual"]["tasks"]["b"]["assistant_tokens"] == 20
