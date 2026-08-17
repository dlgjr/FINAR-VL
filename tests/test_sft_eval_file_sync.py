from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_sft_eval_uses_shared_files_before_long_tail_barrier():
    text = (ROOT / "scripts" / "sft" / "pass_at_8_eval.py").read_text(encoding="utf-8")

    assert 'os.environ.get("SFT_EVAL_SYNC_TIMEOUT", "7200")' in text
    assert 'done_dir = step_dir / "done"' in text
    assert 'marker = done_dir / f"rank_{rank:04d}.done"' in text
    assert 'if not (done_dir / f"rank_{other_rank:04d}.done").exists()' in text
    assert '_wait_for_rank_markers(done_dir, rank=rank, world_size=world_size)' in text
    assert '"eval_sync": "shared_files_then_short_barrier"' in text

    wait_index = text.index('_wait_for_rank_markers(done_dir, rank=rank, world_size=world_size)')
    barrier_index = text.index('_barrier(dist)', wait_index)
    metrics_index = text.index('metrics: dict[str, Any] | None = None', wait_index)
    assert wait_index < barrier_index < metrics_index


def test_sft_eval_clears_stale_done_markers_before_initial_barrier():
    text = (ROOT / "scripts" / "sft" / "pass_at_8_eval.py").read_text(encoding="utf-8")

    clear_index = text.index('for stale_marker in done_dir.glob("rank_*.done")')
    initial_barrier_index = text.index('_barrier(dist)', clear_index)
    eval_loop_index = text.index('while (task := queue.claim', initial_barrier_index)
    assert clear_index < initial_barrier_index < eval_loop_index
