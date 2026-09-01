import importlib
import json
import types
from pathlib import Path

import pytest

import scripts.sft.kl_retention_plugin as kl_plugin
import scripts.sft.swift_sft_plugin as sft_plugin
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


def test_runtime_replacement_is_deferred_until_train_dataloader(monkeypatch, tmp_path: Path):
    class Trainer:
        pass

    trainer = Trainer()
    tracker = object()
    events = []

    # This is the callback-construction phase that crashed in DLC: the trainer
    # does not have train_dataset yet. Deferral must not touch that attribute.
    sft_plugin._defer_runtime_replacement(trainer, tmp_path, tracker)
    assert not hasattr(trainer, "train_dataset")
    assert trainer._finar_runtime_replacement_pending == (tmp_path, tracker)
    assert trainer._finar_runtime_replacement_installed is False

    def fake_install_plan_dataloader(target):
        def planned_get_train_dataloader(self, skip_batches=0):
            events.append(("planned", self.train_dataset, int(skip_batches)))
            return "loader"

        target.get_train_dataloader = types.MethodType(planned_get_train_dataloader, target)
        return True

    def fake_install_runtime_replacement(target, plan_dir, seen_tracker):
        events.append(("replacement", Path(plan_dir), seen_tracker, target.train_dataset))
        target.train_dataset = "wrapped"

    monkeypatch.setattr(sft_plugin, "_ORIGINAL_INSTALL_PLAN_DATALOADER", fake_install_plan_dataloader)
    monkeypatch.setattr(sft_plugin, "_ORIGINAL_INSTALL_RUNTIME_REPLACEMENT", fake_install_runtime_replacement)

    assert sft_plugin._install_plan_dataloader_deferred(trainer) is True
    # Trainer.__init__ finishes after callback construction.
    trainer.train_dataset = "ready"

    assert trainer.get_train_dataloader(skip_batches=2) == "loader"
    assert events == [
        ("replacement", tmp_path, tracker, "ready"),
        ("planned", "wrapped", 2),
    ]
    assert trainer._finar_runtime_replacement_installed is True
    assert trainer._finar_runtime_replacement_pending is None

    # Rebuilding a dataloader for resume/epoch transitions must not wrap twice.
    assert trainer.get_train_dataloader(skip_batches=3) == "loader"
    assert events[-1] == ("planned", "wrapped", 3)
    assert [event for event in events if event[0] == "replacement"] == [
        ("replacement", tmp_path, tracker, "ready")
    ]


def test_runtime_replacement_shim_reload_keeps_true_original_installers():
    original_runtime = sft_plugin._impl._finar_original_install_runtime_replacement
    original_plan = sft_plugin._impl._finar_original_install_plan_dataloader

    reloaded = importlib.reload(sft_plugin)

    assert reloaded._ORIGINAL_INSTALL_RUNTIME_REPLACEMENT is original_runtime
    assert reloaded._ORIGINAL_INSTALL_PLAN_DATALOADER is original_plan
    assert reloaded._impl._install_runtime_replacement is reloaded._defer_runtime_replacement
    assert reloaded._impl._install_plan_dataloader is reloaded._install_plan_dataloader_deferred
