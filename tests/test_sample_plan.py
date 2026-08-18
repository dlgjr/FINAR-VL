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

    assert alpha_for_step(0) == 0.65
    assert alpha_for_step(999) == 0.65
    assert alpha_for_step(1000) == 0.60
    assert alpha_for_step(2999) == 0.60
    assert alpha_for_step(3000) == 0.55
    assert alpha_for_step(99999) == 0.55


def test_text_only_scan_uses_assistant_labels_and_keeps_raw_rows(monkeypatch, tmp_path: Path):
    import scripts.sft.sample_plan as sample_plan

    class Template:
        def encode(self, row):
            assert row["images"] == []
            assert row["videos"] == []
            assert row["audios"] == []
            assert all("<image>" not in message["content"] for message in row["messages"])
            if row["task"] == "zero":
                return {"labels": [-100, -100]}
            return {"labels": [-100, 3, -100, 4]}

    monkeypatch.setattr(sample_plan, "_load_training_template", lambda *args: Template())
    path = tmp_path / "multi.jsonl"
    rows = [
        {"task": "generation", "messages": [{"content": "<image> answer"}], "images": ["missing.jpg"]},
        {"task": "zero", "messages": [{"content": "text"}], "images": ["missing.jpg"]},
        {"task": "other", "messages": [{"content": "text"}], "images": ["missing.jpg"]},
    ]
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")

    task_index, retained, eligible, cache, stats = sample_plan.scan_encoded_index(
        path,
        modality="multi",
        model="test-model",
        max_length=1,
    )

    assert retained == 3
    assert eligible == 2
    assert stats["deleted"] == 0
    assert stats["encoding_failed"] == 0
    assert [row["raw_index"] for row in cache] == [0, 1, 2]
    assert [row["assistant_token_count"] for row in cache] == [2, 0, 2]
    assert list(task_index) == ["generation", "other"]
    assert rows[0]["images"] == ["missing.jpg"]


def test_generate_plan_uses_raw_indices_and_writes_candidate_pools(tmp_path: Path):
    from scripts.sft.sample_plan import generate_plan

    multi = tmp_path / "multi.jsonl"
    text = tmp_path / "text.jsonl"
    _write_rows(multi, ["generation"], 2)
    _write_rows(text, ["dialogue"], 2)
    plan_dir = tmp_path / "plan"
    meta = generate_plan(
        train_multi=multi,
        train_text=text,
        output_dir=plan_dir,
        global_batch_size=2,
        dp_world_size=1,
        grad_acc=2,
        seed=17,
        multi_ratio=0.5,
        max_steps=1,
    )

    pools = json.loads((plan_dir / "replacement_pools.json").read_text(encoding="utf-8"))
    entries = [json.loads(line) for line in (plan_dir / "block_0000.jsonl").read_text(encoding="utf-8").splitlines()]
    assert meta["dataset_index_mode"] == "raw"
    assert meta["replacement_pools"] == "replacement_pools.json"
    assert pools["multi"]["generation"] == [0, 1]
    assert pools["text"]["dialogue"] == [0, 1]
    assert all(entry["index"] == entry["raw_index"] for entry in entries)
    assert all("effective_token_count" not in entry for entry in entries)


def test_generate_plan_blocks_align_with_alpha_boundaries(tmp_path: Path):
    from scripts.sft.sample_plan import generate_plan

    multi = tmp_path / "multi.jsonl"
    text = tmp_path / "text.jsonl"
    _write_rows(multi, [f"m{i}" for i in range(10)], 20)
    _write_rows(text, [f"t{i}" for i in range(10)], 20)
    meta = generate_plan(
        train_multi=multi,
        train_text=text,
        output_dir=tmp_path / "plan",
        global_batch_size=4,
        dp_world_size=2,
        grad_acc=2,
        seed=42,
        max_steps=2200,
    )
    assert meta["steps_per_block"] == 200
    assert meta["total_blocks"] == 11
    assert [(block["start_step"], block["alpha"]) for block in meta["blocks"]][4] == (800, 0.65)
    assert [(block["start_step"], block["alpha"]) for block in meta["blocks"]][10] == (2000, 0.60)


def test_task_b_weight_defaults_and_tables():
    from scripts.sft.sample_plan import task_b_weight

    assert task_b_weight("unlisted_task", "multi") == 1.0
    assert task_b_weight("unlisted_task", "text") == 1.0
    assert task_b_weight("financial_headline_classification", "text") == 0.55
    assert task_b_weight("financial_event_extraction", "text") == 0.55
    assert task_b_weight("stock_movement_prediction", "text") == 0.55
    assert task_b_weight("multi_step_numerical_reasoning", "multi") == 0.90
    assert task_b_weight("multi_step_numerical_reasoning", "text") == 0.90
    assert task_b_weight("evidence_retrieval", "multi") == 1.05
    assert task_b_weight("evidence_retrieval", "text") == 0.85
    assert task_b_weight("image_caption", "multi") == 0.80


def test_allocate_quotas_respects_caps_and_sum():
    from scripts.sft.sample_plan import allocate_quotas

    counts = {f"big{i}": 30000 for i in range(25)}
    counts["mid"] = 200
    counts["small"] = 50
    allocations, tiny_quota, tiny_tasks = allocate_quotas(counts, 6000, alpha=0.7, modality="text")
    assert sum(allocations.values()) + tiny_quota == 6000
    assert all(allocations[task] <= int(6000 * 0.05) for task in allocations if task != "mid")
    assert allocations["mid"] <= int(6000 * 0.02)
    assert tiny_quota <= int(6000 * 0.005)
    assert tiny_tasks == ["small"]


def test_allocate_quotas_tiny_size_boundary():
    from scripts.sft.sample_plan import allocate_quotas, task_cap

    assert task_cap("ordinary", 99, 6000) == int(6000 * 0.005)
    assert task_cap("ordinary", 100, 6000) == int(6000 * 0.02)
    assert task_cap("financial_counterfactual_inference", 499, 6000) == int(6000 * 0.02)
    assert task_cap("ordinary", 499, 6000) == int(6000 * 0.02)
    assert task_cap("ordinary", 500, 6000) == int(6000 * 0.05)


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
    assert meta["total_blocks"] == 5
    for block_id in range(5):
        entries = [
            json.loads(line)
            for line in (output / f"block_{block_id:04d}.jsonl").read_text(
                encoding="utf-8"
            ).splitlines()
        ]
        assert len(entries) == 200 * 24
        assert sum(entry["modality"] == "multi" for entry in entries) == 1728
        assert sum(entry["modality"] == "text" for entry in entries) == 3072
        by_micro = {}
        for entry in entries:
            by_micro.setdefault(entry["micro_step"], []).append(entry)
        assert len(by_micro) == 400
        for micro_entries in by_micro.values():
            assert len(micro_entries) == 12
            assert len({entry["position_in_micro_step"] for entry in micro_entries}) == 12
            tokens = [entry["assistant_token_count"] for entry in micro_entries]
            assert tokens == sorted(tokens, reverse=True)
            assert all("effective_token_count" not in entry for entry in micro_entries)
        for rank in range(12):
            assert sum(
                entry["position_in_micro_step"] == rank for entry in entries
            ) == len(entries) // 12


def test_build_block_groups_long_samples_together():
    from scripts.sft.sample_plan import build_block

    def rows(task, count, base):
        return [
            {
                "index": index,
                "raw_index": index,
                "task": task,
                "family": task,
                "assistant_token_count": base - index,
            }
            for index in range(count)
        ]

    # 每个任务 200 行（非 tiny），30 个任务保证配额可分配；multi/text 长度区间接近，
    # 避免 multi effective-token 比例超过 0.60 硬上限。
    multi_index = {f"mt{i}": rows(f"mt{i}", 200, 4000 - i * 50) for i in range(30)}
    text_index = {f"tt{i}": rows(f"tt{i}", 200, 3800 - i * 50) for i in range(30)}
    entries, block_info, _ = build_block(
        block_id=0,
        start_step=0,
        steps=2,
        global_batch_size=24,
        dp_world_size=12,
        per_device_batch=1,
        grad_acc=2,
        seed=42,
        multi_ratio=0.5,
        multi_index=multi_index,
        text_index=text_index,
        tiny_usage={},
    )
    assert len(entries) == 48
    assert sum(entry["modality"] == "multi" for entry in entries) == 24
    assert sum(entry["modality"] == "text" for entry in entries) == 24
    by_micro = {}
    for entry in entries:
        by_micro.setdefault(entry["micro_step"], []).append(entry)
    assert len(by_micro) == 4
    for micro_entries in by_micro.values():
        assert len(micro_entries) == 12
        assert sorted(entry["position_in_micro_step"] for entry in micro_entries) == list(range(12))
        tokens = [entry["assistant_token_count"] for entry in micro_entries]
        assert tokens == sorted(tokens, reverse=True)
    # 组步按长度降序：微步最大值跨微步不增，全局最长样本位于第 0 个微步的 position 0。
    maxima = [
        max(entry["assistant_token_count"] for entry in micro_entries)
        for micro_entries in by_micro.values()
    ]
    assert maxima == sorted(maxima, reverse=True)
    first = sorted(by_micro[0], key=lambda entry: entry["position_in_micro_step"])
    assert first[0]["assistant_token_count"] == max(
        entry["assistant_token_count"] for entry in entries
    )


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
    assert meta["total_blocks"] == 6
    entries = [
        json.loads(line)
        for line in (output / "block_0005.jsonl").read_text(encoding="utf-8").splitlines()
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
        MAX_TASK_RATIO,
        MIN_ASSISTANT_TOKENS_FOR_WEIGHT,
        TOKEN_LENGTH_BETA,
        family_for_task,
    )

    assert family_for_task("long") == "multipage_financial_reasoning"
    assert family_for_task("table_arithmetic_reasoning") == "table_reasoning"
    assert family_for_task("chart_data_extraction") == "chart_reasoning"
    assert family_for_task("financial_ocr") == "document_perception"
    assert family_for_task("financial_consistency_error_detection") == "accounting_valuation"
    assert family_for_task("financial_definition_scope_reasoning") == "accounting_valuation"
    assert family_for_task("financial_scenario_sensitivity_analysis") == "accounting_valuation"
    assert family_for_task("temporal_financial_reasoning") == "numerical_statistics"
    assert family_for_task("financial_evidence_reconciliation") == "retrieval_grounding"
    assert family_for_task("insufficient_information_detection") == "retrieval_grounding"
    assert family_for_task("valuation_reasoning") == "accounting_valuation"
    assert MAX_TASK_RATIO == 0.05
    assert TOKEN_LENGTH_BETA == 0.5
    assert MIN_ASSISTANT_TOKENS_FOR_WEIGHT == 8
