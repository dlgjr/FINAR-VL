from __future__ import annotations

import json
from pathlib import Path

import pytest


def _write_jsonl(path: Path, count: int) -> None:
    path.write_text(
        "".join(json.dumps({"messages": [], "task": f"t{i}"}) + "\n" for i in range(count)),
        encoding="utf-8",
    )


def test_materialize_lazy_plan_uses_stable_raw_indices(tmp_path: Path) -> None:
    from scripts.sft.materialize_lazy_plan_indices import materialize_lazy_plan_indices

    multi = tmp_path / "multi.jsonl"
    text = tmp_path / "text.jsonl"
    _write_jsonl(multi, 4)
    _write_jsonl(text, 3)

    plan_dir = tmp_path / "plan"
    plan_dir.mkdir()
    meta = {
        "N_multi": 3,
        "N_text": 2,
        "total_blocks": 1,
        "dataset_stats": {
            "multi": {"raw": 4, "retained": 3, "eligible": 3},
            "text": {"raw": 3, "retained": 2, "eligible": 2},
        },
    }
    (plan_dir / "meta.json").write_text(json.dumps(meta) + "\n", encoding="utf-8")
    entries = [
        {
            "modality": "multi",
            "index": 2,
            "raw_index": 3,
            "position_in_micro_step": 0,
        },
        {
            "modality": "text",
            "index": 1,
            "raw_index": 2,
            "position_in_micro_step": 1,
        },
    ]
    (plan_dir / "block_0000.jsonl").write_text(
        "".join(json.dumps(entry) + "\n" for entry in entries),
        encoding="utf-8",
    )

    converted = materialize_lazy_plan_indices(plan_dir, train_multi=multi, train_text=text)

    assert converted["dataset_index_mode"] == "raw"
    assert converted["filtered_N_multi"] == 3
    assert converted["filtered_N_text"] == 2
    assert converted["N_multi"] == 4
    assert converted["N_text"] == 3

    rows = [json.loads(line) for line in (plan_dir / "block_0000.jsonl").read_text().splitlines()]
    assert rows[0]["filtered_index"] == 2
    assert rows[0]["index"] == rows[0]["raw_index"] == 3
    assert rows[1]["filtered_index"] == 1
    assert rows[1]["index"] == rows[1]["raw_index"] == 2

    # Existing PlanSampler maps text as N_multi + index, so after conversion the
    # physical lazy-dataset positions are multi=3 and text=4+2=6.
    assert rows[0]["index"] == 3
    assert converted["N_multi"] + rows[1]["index"] == 6

    # Re-running after a restart is intentionally idempotent.
    second = materialize_lazy_plan_indices(plan_dir, train_multi=multi, train_text=text)
    assert second == converted


def test_materialize_lazy_plan_rejects_blank_jsonl_rows(tmp_path: Path) -> None:
    from scripts.sft.materialize_lazy_plan_indices import materialize_lazy_plan_indices

    multi = tmp_path / "multi.jsonl"
    text = tmp_path / "text.jsonl"
    multi.write_text('{}\n\n{}\n', encoding="utf-8")
    text.write_text('{}\n', encoding="utf-8")
    plan_dir = tmp_path / "plan"
    plan_dir.mkdir()
    (plan_dir / "meta.json").write_text(
        json.dumps({"N_multi": 2, "N_text": 1, "total_blocks": 0}) + "\n",
        encoding="utf-8",
    )

    with pytest.raises(RuntimeError, match="blank lines"):
        materialize_lazy_plan_indices(plan_dir, train_multi=multi, train_text=text)
