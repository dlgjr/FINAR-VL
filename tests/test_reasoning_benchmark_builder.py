from __future__ import annotations

from collections import Counter

from scripts.data import build_reasoning_benchmark as builder


def _row(task: str, source: str, *, images: int = 0) -> dict:
    image_paths = [f"dummy/{task}/{index}.png" for index in range(images)]
    prompt = "".join("<image>\n" for _ in range(images)) + "original prompt"
    return {
        "messages": [
            {"role": "user", "content": prompt},
            {"role": "assistant", "content": "original answer"},
        ],
        "source": source,
        "split": "test",
        "images": image_paths,
        "task": task,
    }


def test_transform_replaces_open_ended_tasks_and_preserves_24x10() -> None:
    rows: list[dict] = []

    for source in builder._VISUAL_REPLACEMENTS:
        rows.append(_row(builder.VISUAL_SOURCE_TASK, source, images=1))
    for source in builder._SUMMARY_REPLACEMENTS:
        rows.append(_row(builder.SUMMARY_SOURCE_TASK, source))
    for source in builder._ENTITY_REPLACEMENTS:
        rows.append(_row(builder.ENTITY_SOURCE_TASK, source))

    for task_index in range(21):
        task = f"unchanged_task_{task_index:02d}"
        for row_index in range(10):
            rows.append(_row(task, f"dummy/{task}/{row_index:02d}"))

    output = builder.transform(rows)
    counts = Counter(str(row["task"]) for row in output)

    assert len(output) == 240
    assert len(counts) == 24
    assert set(counts.values()) == {10}

    assert builder.VISUAL_SOURCE_TASK not in counts
    assert builder.SUMMARY_SOURCE_TASK not in counts
    assert builder.ENTITY_SOURCE_TASK not in counts
    assert counts[builder.VISUAL_TARGET_TASK] == 10
    assert counts[builder.SUMMARY_TARGET_TASK] == 10
    assert counts[builder.ENTITY_TARGET_TASK] == 10

    choice_rows = [
        row
        for row in output
        if row["task"]
        in {builder.SUMMARY_TARGET_TASK, builder.ENTITY_TARGET_TASK}
    ]
    assert len(choice_rows) == 20
    assert all(row["messages"][-1]["content"] in {"A", "B", "C", "D"} for row in choice_rows)

    visual_rows = [row for row in output if row["task"] == builder.VISUAL_TARGET_TASK]
    assert all(row["messages"][0]["content"].count("<image>") == 1 for row in visual_rows)
