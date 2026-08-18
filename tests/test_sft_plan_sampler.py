import json
from pathlib import Path

import pytest


def _write_rows(path: Path, tasks, count: int) -> None:
    rows = []
    for task in tasks:
        rows.extend({"messages": [], "task": task} for _ in range(count))
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )


@pytest.fixture()
def plan_dir(tmp_path: Path) -> Path:
    from scripts.sft.sample_plan import generate_plan

    multi = tmp_path / "multi.jsonl"
    text = tmp_path / "text.jsonl"
    _write_rows(multi, [f"m{i}" for i in range(10)], 50)
    _write_rows(text, [f"t{i}" for i in range(10)], 50)
    output = tmp_path / "plan"
    generate_plan(
        train_multi=multi,
        train_text=text,
        output_dir=output,
        global_batch_size=4,
        dp_world_size=2,
        grad_acc=2,
        seed=42,
        max_steps=2,
    )
    return output


def test_plan_sampler_len_and_rank_slice(plan_dir: Path):
    from scripts.sft.swift_sft_plugin import PlanSampler

    meta = json.loads((plan_dir / "meta.json").read_text(encoding="utf-8"))
    dataset_len = meta["N_multi"] + meta["N_text"]
    entries = [
        json.loads(line)
        for line in (plan_dir / "block_0000.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    for rank in range(2):
        sampler = PlanSampler(plan_dir=plan_dir, rank=rank, dataset_len=dataset_len)
        expected = [
            (
                entry["index"]
                if entry["modality"] == "multi"
                else meta["N_multi"] + entry["index"]
            )
            for entry in entries
            if entry["position_in_micro_step"] == rank
        ]
        assert list(sampler) == expected
        assert len(sampler) == len(expected)


def test_plan_sampler_rejects_out_of_range_index(tmp_path: Path):
    from scripts.sft.sample_plan import generate_plan
    from scripts.sft.swift_sft_plugin import PlanSampler

    multi = tmp_path / "multi.jsonl"
    text = tmp_path / "text.jsonl"
    _write_rows(multi, [f"m{i}" for i in range(10)], 50)
    _write_rows(text, [f"t{i}" for i in range(10)], 50)
    output = tmp_path / "plan"
    generate_plan(
        train_multi=multi,
        train_text=text,
        output_dir=output,
        global_batch_size=4,
        dp_world_size=2,
        grad_acc=2,
        seed=42,
        max_steps=2,
    )
    sampler = PlanSampler(plan_dir=output, rank=0, dataset_len=100)
    with pytest.raises(IndexError):
        list(sampler)


def test_plan_sampler_missing_meta_is_rejected(tmp_path: Path):
    from scripts.sft.swift_sft_plugin import PlanSampler

    empty = tmp_path / "empty"
    empty.mkdir()
    with pytest.raises(RuntimeError):
        PlanSampler(plan_dir=empty, rank=0, dataset_len=10)


def test_install_plan_dataloader_disabled_without_env(monkeypatch):
    from scripts.sft.swift_sft_plugin import _install_plan_dataloader

    monkeypatch.delenv("SFT_PLAN_DIR", raising=False)
    assert _install_plan_dataloader(object()) is False


def test_plan_sampler_rejects_per_device_batch_above_one(tmp_path: Path):
    from scripts.sft.sample_plan import generate_plan

    multi = tmp_path / "multi.jsonl"
    text = tmp_path / "text.jsonl"
    _write_rows(multi, [f"m{i}" for i in range(10)], 50)
    _write_rows(text, [f"t{i}" for i in range(10)], 50)
    output = tmp_path / "plan"
    with pytest.raises(ValueError, match="per_device_batch=1"):
        generate_plan(
            train_multi=multi,
            train_text=text,
            output_dir=output,
            global_batch_size=8,
            dp_world_size=2,
            per_device_batch=2,
            grad_acc=2,
            seed=42,
            max_steps=2,
        )
