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
def sample_data(tmp_path: Path):
    multi_tasks = [f"m{i}" for i in range(25)]
    text_tasks = [f"t{i}" for i in range(25)]
    multi = tmp_path / "multi.jsonl"
    text = tmp_path / "text.jsonl"
    _write_rows(multi, multi_tasks, 500)
    _write_rows(text, text_tasks, 500)
    multi_tiny = tmp_path / "multi_tiny.jsonl"
    text_tiny = tmp_path / "text_tiny.jsonl"
    _write_rows(multi_tiny, ["tiny_multi"], 3)
    _write_rows(text_tiny, ["tiny_text"], 2)
    with multi.open("a", encoding="utf-8") as handle:
        for line in multi_tiny.read_text(encoding="utf-8").splitlines():
            handle.write(line + "\n")
    with text.open("a", encoding="utf-8") as handle:
        for line in text_tiny.read_text(encoding="utf-8").splitlines():
            handle.write(line + "\n")
    return multi, text


def test_alpha_schedule_boundaries():
    from scripts.sft.sample_plan import alpha_for_step

    assert alpha_for_step(0) == 0.60
    assert alpha_for_step(999) == 0.60
    assert alpha_for_step(1000) == 0.50
    assert alpha_for_step(2999) == 0.50
    assert alpha_for_step(3000) == 0.45
    assert alpha_for_step(99999) == 0.45


def test_task_b_weight_defaults_and_tables():
    from scripts.sft.sample_plan import task_b_weight

    assert task_b_weight("unlisted_task") == 1.0
    assert task_b_weight("financial_headline_classification") == 0.45
    assert task_b_weight("financial_event_extraction") == 0.60
    assert task_b_weight("stock_movement_prediction") == 0.40
    assert task_b_weight("multi_table_reasoning") == 1.8
    assert task_b_weight("long_document_cross_page") == 1.8


def test_allocate_quotas_respects_caps_and_sum():
    from scripts.sft.sample_plan import allocate_quotas

    counts = {f"big{i}": 30000 for i in range(25)}
    counts["mid"] = 200
    counts["small"] = 50
    allocations, tiny_quota, tiny_tasks = allocate_quotas(counts, 6000, alpha=0.7)
    assert sum(allocations.values()) + tiny_quota == 6000
    assert all(allocations[task] <= int(6000 * 0.05) for task in allocations if task != "mid")
    assert allocations["mid"] <= int(6000 * 0.02)
    assert tiny_quota <= int(6000 * 0.005)
    assert tiny_tasks == ["small"]


def test_allocate_quotas_tiny_size_boundary():
    from scripts.sft.sample_plan import allocate_quotas, task_cap

    assert task_cap(99, 6000) == int(6000 * 0.005)
    assert task_cap(100, 6000) == int(6000 * 0.02)
    assert task_cap(499, 6000) == int(6000 * 0.02)
    assert task_cap(500, 6000) == int(6000 * 0.05)


def test_generate_plan_block_layout_and_ratio(tmp_path: Path, sample_data):
    from scripts.sft.sample_plan import generate_plan

    multi, text = sample_data
    output = tmp_path / "plan"
    meta = generate_plan(
        train_multi=multi,
        train_text=text,
        output_dir=output,
        global_batch_size=24,
        dp_world_size=12,
        grad_acc=2,
        seed=42,
        max_steps=1000,
    )
    assert meta["total_blocks"] == 2
    for block_id in range(2):
        entries = [
            json.loads(line)
            for line in (output / f"block_{block_id:04d}.jsonl").read_text(
                encoding="utf-8"
            ).splitlines()
        ]
        assert len(entries) == 500 * 24
        assert sum(entry["modality"] == "multi" for entry in entries) == 4800
        assert sum(entry["modality"] == "text" for entry in entries) == 7200
        by_micro = {}
        for entry in entries:
            by_micro.setdefault(entry["micro_step"], []).append(entry)
        assert len(by_micro) == 1000
        for micro_entries in by_micro.values():
            assert len(micro_entries) == 12
            assert len({entry["position_in_micro_step"] for entry in micro_entries}) == 12
            assert sum(entry["modality"] == "multi" for entry in micro_entries) in {4, 5}
        for rank in range(12):
            assert sum(
                entry["position_in_micro_step"] == rank for entry in entries
            ) == len(entries) // 12


def test_generate_plan_tiny_repeat_limit(tmp_path: Path, sample_data):
    from collections import Counter

    from scripts.sft.sample_plan import generate_plan

    multi, text = sample_data
    output = tmp_path / "plan"
    meta = generate_plan(
        train_multi=multi,
        train_text=text,
        output_dir=output,
        global_batch_size=24,
        dp_world_size=12,
        grad_acc=2,
        seed=42,
        max_steps=1000,
    )
    for modality in ("multi", "text"):
        counts = Counter()
        for block_id in range(meta["total_blocks"]):
            for line in (output / f"block_{block_id:04d}.jsonl").read_text(
                encoding="utf-8"
            ).splitlines():
                entry = json.loads(line)
                if entry["modality"] == modality and entry["pool"] == "__tiny_pool__":
                    counts[entry["index"]] += 1
        assert counts
        assert max(counts.values()) <= 2


def test_generate_plan_deterministic(tmp_path: Path, sample_data):
    from scripts.sft.sample_plan import generate_plan

    multi, text = sample_data
    output_a = tmp_path / "plan_a"
    output_b = tmp_path / "plan_b"
    generate_plan(
        train_multi=multi,
        train_text=text,
        output_dir=output_a,
        global_batch_size=24,
        dp_world_size=12,
        grad_acc=2,
        seed=42,
        max_steps=1000,
    )
    generate_plan(
        train_multi=multi,
        train_text=text,
        output_dir=output_b,
        global_batch_size=24,
        dp_world_size=12,
        grad_acc=2,
        seed=42,
        max_steps=1000,
    )
    assert (output_a / "block_0000.jsonl").read_text(encoding="utf-8") == (
        output_b / "block_0000.jsonl"
    ).read_text(encoding="utf-8")


def test_generate_plan_max_steps_inference(tmp_path: Path):
    from scripts.sft.sample_plan import generate_plan

    multi = tmp_path / "multi.jsonl"
    text = tmp_path / "text.jsonl"
    _write_rows(multi, [f"m{i}" for i in range(25)], 600)
    _write_rows(text, [f"t{i}" for i in range(25)], 700)
    output = tmp_path / "plan"
    meta = generate_plan(
        train_multi=multi,
        train_text=text,
        output_dir=output,
        global_batch_size=24,
        dp_world_size=12,
        grad_acc=2,
        seed=42,
    )
    assert meta["N_multi"] == 25 * 600
    assert meta["N_text"] == 25 * 700
    assert meta["max_steps"] == (5 * 25 * 600 + 25 * 700) // 24


def test_generate_plan_epochs_scales_max_steps(tmp_path: Path):
    from scripts.sft.sample_plan import generate_plan

    multi = tmp_path / "multi.jsonl"
    text = tmp_path / "text.jsonl"
    _write_rows(multi, [f"m{i}" for i in range(25)], 600)
    _write_rows(text, [f"t{i}" for i in range(25)], 700)
    output = tmp_path / "plan"
    meta = generate_plan(
        train_multi=multi,
        train_text=text,
        output_dir=output,
        global_batch_size=24,
        dp_world_size=12,
        grad_acc=2,
        seed=42,
        epochs=2,
    )
    assert meta["epochs"] == 2
    assert meta["max_steps"] == (5 * 25 * 600 + 25 * 700) * 2 // 24


def test_generate_plan_tail_block_incomplete(tmp_path: Path, sample_data):
    from scripts.sft.sample_plan import generate_plan

    multi, text = sample_data
    output = tmp_path / "plan"
    meta = generate_plan(
        train_multi=multi,
        train_text=text,
        output_dir=output,
        global_batch_size=24,
        dp_world_size=12,
        grad_acc=2,
        seed=42,
        max_steps=1001,
    )
    assert meta["total_blocks"] == 3
    entries = [
        json.loads(line)
        for line in (output / "block_0002.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    assert len(entries) == 1 * 24


def test_generate_plan_dsw_single_dp(tmp_path: Path, sample_data):
    from scripts.sft.sample_plan import generate_plan

    multi, text = sample_data
    output = tmp_path / "plan"
    meta = generate_plan(
        train_multi=multi,
        train_text=text,
        output_dir=output,
        global_batch_size=2,
        dp_world_size=1,
        per_device_batch=1,
        grad_acc=2,
        seed=7,
        max_steps=5,
    )
    entries = [
        json.loads(line)
        for line in (output / "block_0000.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    assert len(entries) == 5 * 2
    assert sum(entry["modality"] == "multi" for entry in entries) == 4
    assert sum(entry["modality"] == "text" for entry in entries) == 6
    assert all(entry["position_in_micro_step"] == 0 for entry in entries)


def test_generate_plan_per_device_batch_is_rejected(tmp_path: Path, sample_data):
    from scripts.sft.sample_plan import generate_plan

    multi, text = sample_data
    with pytest.raises(ValueError, match="per_device_batch=1"):
        generate_plan(
            train_multi=multi,
            train_text=text,
            output_dir=tmp_path / "plan",
            global_batch_size=8,
            dp_world_size=2,
            per_device_batch=2,
            grad_acc=2,
            seed=42,
            max_steps=2,
        )


def test_finance_family_mapping_and_sampling_constants():
    from scripts.sft.sample_plan import (
        MAX_MULTI_EFFECTIVE_TOKEN_RATIO,
        MAX_TASK_RATIO,
        MIN_ASSISTANT_TOKENS_FOR_WEIGHT,
        TOKEN_LENGTH_BETA,
        family_for_task,
    )

    assert family_for_task("long") == "multipage_financial_reasoning"
    assert family_for_task("table_arithmetic_reasoning") == "table_reasoning"
    assert family_for_task("chart_data_extraction") == "chart_reasoning"
    assert family_for_task("financial_ocr") == "document_perception"
    assert MAX_TASK_RATIO == 0.05
    assert TOKEN_LENGTH_BETA == 0.5
    assert MIN_ASSISTANT_TOKENS_FOR_WEIGHT == 8
    assert MAX_MULTI_EFFECTIVE_TOKEN_RATIO == 0.60
