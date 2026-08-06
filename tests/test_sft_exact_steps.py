import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


def test_extract_step_rows_uses_seeded_dp_permutation_and_stable_source_index(tmp_path):
    pytest.importorskip("torch")
    multi = tmp_path / "multi.jsonl"
    text = tmp_path / "text.jsonl"
    multi.write_text("".join(json.dumps({"id": f"m{i}"}) + "\n" for i in range(8)), encoding="utf-8")
    text.write_text("".join(json.dumps({"id": f"t{i}"}) + "\n" for i in range(8)), encoding="utf-8")

    from scripts.sft.extract_sequence_parallel_sample import extract_steps

    result = extract_steps(multi, text, [1, 2], seed=42, dp_world_size=12)
    import torch

    perm = torch.randperm(16, generator=torch.Generator().manual_seed(42)).tolist()
    assert result[0]["index"] == (perm[0] if perm[0] < 8 else perm[0] - 8)
    assert result[0]["source"] == ("train_multi" if perm[0] < 8 else "train_text")
    assert result[1]["historical_step"] == 2
    assert result[1]["index"] == (perm[12] if perm[12] < 8 else perm[12] - 8)
    assert result[1]["source"] == ("train_multi" if perm[12] < 8 else "train_text")


def test_extract_steps_scales_sampler_position_by_grad_acc(tmp_path):
    pytest.importorskip("torch")
    multi = tmp_path / "multi.jsonl"
    text = tmp_path / "text.jsonl"
    multi.write_text("".join(json.dumps({"id": f"m{i}"}) + "\n" for i in range(8)), encoding="utf-8")
    text.write_text("".join(json.dumps({"id": f"t{i}"}) + "\n" for i in range(8)), encoding="utf-8")

    from scripts.sft.extract_sequence_parallel_sample import extract_steps

    import torch

    result = extract_steps(multi, text, [1, 2], seed=42, dp_world_size=4, grad_acc=2)
    perm = torch.randperm(16, generator=torch.Generator().manual_seed(42)).tolist()
    assert result[0]["sampler_position"] == 0
    assert result[0]["index"] == (perm[0] if perm[0] < 8 else perm[0] - 8)
    assert result[0]["grad_acc"] == 2
    assert result[1]["sampler_position"] == 8
    assert result[1]["index"] == (perm[8] if perm[8] < 8 else perm[8] - 8)
    assert result[1]["source"] == ("train_multi" if perm[8] < 8 else "train_text")


def test_extract_plan_steps_returns_rank_micro_steps(tmp_path):
    import json

    from scripts.sft.extract_sequence_parallel_sample import extract_plan_steps
    from scripts.sft.sample_plan import generate_plan

    multi = tmp_path / "multi.jsonl"
    text = tmp_path / "text.jsonl"
    multi.write_text(
        "".join(json.dumps({"messages": [], "task": f"m{i}"}) + "\n" for i in range(15) for _ in range(500)),
        encoding="utf-8",
    )
    text.write_text(
        "".join(json.dumps({"messages": [], "task": f"t{i}"}) + "\n" for i in range(15) for _ in range(500)),
        encoding="utf-8",
    )
    plan_dir = tmp_path / "plan"
    generate_plan(
        train_multi=multi,
        train_text=text,
        output_dir=plan_dir,
        global_batch_size=24,
        dp_world_size=12,
        grad_acc=2,
        seed=42,
        max_steps=1000,
    )
    records = extract_plan_steps(plan_dir, [1, 2], grad_acc=2, rank=0)
    assert len(records) == 4
    assert [record["historical_step"] for record in records] == [1, 1, 2, 2]
    assert all(record["source"] in ("train_multi", "train_text") for record in records)
    assert all(0 <= record["index"] for record in records)


def test_extract_plan_steps_with_per_device_batch(tmp_path):
    import json

    from scripts.sft.extract_sequence_parallel_sample import extract_plan_steps
    from scripts.sft.sample_plan import generate_plan

    multi = tmp_path / "multi.jsonl"
    text = tmp_path / "text.jsonl"
    multi.write_text(
        "".join(json.dumps({"messages": [], "task": f"m{i}"}) + "\n" for i in range(15) for _ in range(500)),
        encoding="utf-8",
    )
    text.write_text(
        "".join(json.dumps({"messages": [], "task": f"t{i}"}) + "\n" for i in range(15) for _ in range(500)),
        encoding="utf-8",
    )
    plan_dir = tmp_path / "plan"
    generate_plan(
        train_multi=multi,
        train_text=text,
        output_dir=plan_dir,
        global_batch_size=8,
        dp_world_size=2,
        per_device_batch=2,
        grad_acc=2,
        seed=42,
        max_steps=2,
    )
    records = extract_plan_steps(
        plan_dir, [1, 2], grad_acc=2, rank=0, per_device_batch=2
    )
    assert len(records) == 8
    assert [record["historical_step"] for record in records] == [1, 1, 1, 1, 2, 2, 2, 2]


def test_launcher_defaults_exact_steps_and_single_update_without_install():
    text = (ROOT / "scripts" / "dsw" / "run_sft_exact_steps.sh").read_text(encoding="utf-8")
    for required in (
        'SFT_DEBUG_STEPS="${SFT_DEBUG_STEPS:-1049,1050}"',
        "--max_steps 1",
        "SFT_TRACE_STEPS",
        'SFT_ATTN_IMPL="${SFT_ATTN_IMPL:-sdpa}"',
        'SFT_CELOSS_PARALLEL_SIZE="${SFT_CELOSS_PARALLEL_SIZE:-4096}"',
        'SFT_PLAN_MAX_STEPS=0',
        '"$QWEN3VL_ROOT/scripts/sft/sample_plan.py"',
        "--global-batch-size 28",
        "--dp-world-size 14",
        "--per-device-batch 1",
        '--max-steps "$SFT_PLAN_MAX_STEPS"',
        '--plan-dir "$SFT_PLAN_DIR"',
        '--grad-acc 2',
        "--per_device_train_batch_size 1",
        "--sequence_parallel_size 1",
        "--deepspeed zero2",
        "--report_to none",
        "--callbacks finar_log finar_numerics",
        "import flash_attn",
    ):
        assert required in text
    assert "pip install" not in text
    assert "CUDA_VISIBLE_DEVICES=0,1" in text
    assert "independent" in text.lower() or "独立" in text
def test_launcher_persists_swift_logs_and_continues_after_a_failed_step():
    text = (ROOT / "scripts" / "dsw" / "run_sft_exact_steps.sh").read_text(encoding="utf-8")

    assert '"$SWIFT_BIN" sft \\' in text
    assert '"$RUN_DIR/run.log"' in text
    assert "set +e" in text
    assert "set -e" in text
    assert "STEP_EXIT_CODE=$?" in text
    assert 'echo "swift_exit_code=$STEP_EXIT_CODE"' in text
    assert 'exit "$OVERALL_EXIT_CODE"' in text
