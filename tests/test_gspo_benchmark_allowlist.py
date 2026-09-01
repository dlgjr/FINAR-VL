import json
import os
from pathlib import Path

from scripts.sft.pass_at_8_eval import GSPO_BENCHMARK_TASKS, _benchmark_programmatic_judge, _judge_generation, _make_messages, load_benchmark


def test_gspo_benchmark_allowlist_selects_exact_94_rows_without_extending_source(monkeypatch):
    monkeypatch.setenv("GSPO_BENCHMARK_ALLOWLIST", ",".join(sorted(GSPO_BENCHMARK_TASKS)))
    rows = load_benchmark(Path("data/benchmark/my_benchmark/all.jsonl"), Path("."))
    assert len(rows) == 94
    assert {row["task"] for row in rows} == GSPO_BENCHMARK_TASKS
    assert all(_benchmark_programmatic_judge(row, row["messages"][-1]["content"], f"答案：{row['messages'][-1]['content']}") for row in rows)
    first = rows[0]
    assert not _benchmark_programmatic_judge(first, first["messages"][-1]["content"], first["messages"][-1]["content"])
    assert "答案：具体答案" in _make_messages(first)[0]["content"][-1]["text"]

    monkeypatch.delenv("GSPO_BENCHMARK_ALLOWLIST")
    legacy = _judge_generation("", first, first["messages"][-1]["content"], first["messages"][-1]["content"])
    assert legacy["correct"] is True
