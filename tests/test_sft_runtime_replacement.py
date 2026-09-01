from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace


class _Rows:
    def __init__(self, rows):
        self.rows = rows

    def __getitem__(self, index):
        return self.rows[index]

    def __len__(self):
        return len(self.rows)


class _MaxLengthError(ValueError):
    pass


class _Template:
    def __init__(self, failures):
        self.failures = failures

    def encode(self, row, *, return_length):
        row_id = int(row["id"])
        failure = self.failures.get(row_id)
        if failure == "max_length":
            raise _MaxLengthError("too long")
        if failure == "encode_failed":
            raise ValueError("bad image")
        return {
            "input_ids": [row_id, 1],
            "labels": [-100, 1],
            "length": 2,
        }


def _plan(tmp_path: Path, *, same_task_candidate: bool = False) -> Path:
    plan_dir = tmp_path / "plan"
    plan_dir.mkdir()
    generation = [0, 2] if same_task_candidate else [0]
    pools = {
        "multi": {
            "generation": generation,
            "other": [1],
            "__all__": [0, 1, 2] if same_task_candidate else [0, 1],
        },
        "text": {"__all__": [0]},
    }
    (plan_dir / "replacement_pools.json").write_text(
        json.dumps(pools) + "\n", encoding="utf-8"
    )
    return plan_dir


def test_runtime_replacement_prefers_same_task_and_logs_failures(tmp_path: Path):
    from scripts.sft.swift_sft_plugin import RuntimeReplacementDataset

    dataset = _Rows([
        {"id": 0, "task": "generation"},
        {"id": 1, "task": "other"},
        {"id": 2, "task": "generation"},
    ])
    runtime = RuntimeReplacementDataset(
        dataset,
        _Template({0: "max_length"}),
        plan_dir=_plan(tmp_path, same_task_candidate=True),
        n_multi=2,
        seed=42,
        rejection_dir=tmp_path / "rejected",
    )

    encoded = runtime[0]

    assert encoded["_finar_runtime_route"]["raw_index"] == 2
    assert encoded["_finar_runtime_route"]["task"] == "generation"
    assert encoded["_finar_runtime_route"]["replacement_reason"] == "max_length"
    rejection = list((tmp_path / "rejected").glob("*.jsonl"))[0]
    record = json.loads(rejection.read_text(encoding="utf-8").splitlines()[0])
    assert record["raw_index"] == 0
    assert record["candidate_raw_index"] == 0
    assert record["resolved_raw_index"] == 0
    assert record["reason"] == "max_length"


def test_runtime_replacement_is_deterministic(tmp_path: Path):
    from scripts.sft.swift_sft_plugin import RuntimeReplacementDataset

    dataset = _Rows([
        {"id": 0, "task": "generation"},
        {"id": 1, "task": "generation"},
    ])
    kwargs = {
        "plan_dir": _plan(tmp_path),
        "n_multi": 2,
        "seed": 123,
        "rejection_dir": tmp_path / "rejected",
    }
    first = RuntimeReplacementDataset(dataset, _Template({0: "encode_failed"}), **kwargs)
    second = RuntimeReplacementDataset(dataset, _Template({0: "encode_failed"}), **kwargs)

    assert first[0]["_finar_runtime_route"] == second[0]["_finar_runtime_route"]


def test_runtime_replacement_uses_other_task_after_same_task_pool(tmp_path: Path):
    from scripts.sft.swift_sft_plugin import RuntimeReplacementDataset

    dataset = _Rows([
        {"id": 0, "task": "generation"},
        {"id": 1, "task": "other"},
    ])
    runtime = RuntimeReplacementDataset(
        dataset,
        _Template({0: "encode_failed"}),
        plan_dir=_plan(tmp_path),
        n_multi=2,
        seed=42,
        rejection_dir=tmp_path / "rejected",
    )

    route = runtime[0]["_finar_runtime_route"]

    assert route["raw_index"] == 1
    assert route["task"] == "other"
    assert route["replacement_reason"] == "encode_failed"


def test_kl_route_prefers_runtime_resolved_route():
    from scripts.sft.kl_retention_plugin import _current_route_from_plan

    trainer = SimpleNamespace(
        _finar_runtime_route={
            "task": "generation",
            "modality": "multi",
            "index": 9,
            "raw_index": 9,
        },
        _finar_plan_tracker=None,
    )

    task, use_kl, route = _current_route_from_plan(trainer)

    assert task == "generation"
    assert use_kl is True
    assert route["raw_index"] == 9


def test_generation_teacher_reads_resolved_raw_index(monkeypatch, tmp_path: Path):
    from scripts.sft.kl_retention_plugin import _route_record

    data_path = tmp_path / "multi.jsonl"
    data_path.write_text(
        json.dumps({"task": "generation", "id": "planned"})
        + "\n"
        + json.dumps({"task": "generation", "id": "resolved"})
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("NORMALIZED_TRAIN_MULTI", str(data_path))

    record, path = _route_record(
        {"modality": "multi", "index": 0, "raw_index": 1, "task": "generation"}
    )

    assert path == data_path
    assert record["id"] == "resolved"
