import json

import scripts.sft.kl_retention_plugin as kl_plugin
from scripts.sft.kl_retention_plugin import (
    _content_with_images,
    _replace_assistant_with_teacher,
)


def test_multimodal_teacher_content_preserves_image_order():
    parts = _content_with_images(
        "先看<image>再比较<image>。",
        ["file:///tmp/a.png", "file:///tmp/b.png"],
    )
    assert parts == [
        {"type": "text", "text": "先看"},
        {"type": "image_url", "image_url": {"url": "file:///tmp/a.png"}},
        {"type": "text", "text": "再比较"},
        {"type": "image_url", "image_url": {"url": "file:///tmp/b.png"}},
        {"type": "text", "text": "。"},
    ]


def test_multimodal_teacher_content_keeps_extra_images_in_source_order():
    parts = _content_with_images(
        "先看<image>。",
        ["file:///tmp/a.png", "file:///tmp/b.png", "file:///tmp/c.png"],
    )
    urls = [part["image_url"]["url"] for part in parts if part["type"] == "image_url"]
    assert urls == ["file:///tmp/a.png", "file:///tmp/b.png", "file:///tmp/c.png"]


def test_teacher_response_replaces_dataset_assistant_answer():
    record = {
        "messages": [
            {"role": "user", "content": "问题"},
            {"role": "assistant", "content": "数据集自带答案"},
        ],
        "task": "generation",
    }
    updated = _replace_assistant_with_teacher(record, "base自己生成的答案")
    assert updated["messages"][-1] == {"role": "assistant", "content": "base自己生成的答案"}
    assert record["messages"][-1]["content"] == "数据集自带答案"


def test_teacher_route_reloads_jsonl_by_raw_index(monkeypatch, tmp_path):
    path = tmp_path / "train_text.jsonl"
    rows = [
        {"id": "raw-0", "task": "other"},
        {"id": "raw-1", "task": "deleted-before-generation"},
        {"id": "raw-2", "task": "generation"},
    ]
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
    monkeypatch.setattr(kl_plugin, "_data_file_for_modality", lambda modality: path)

    record, returned_path = kl_plugin._route_record(
        {"modality": "text", "index": 1, "raw_index": 2}
    )

    assert returned_path == path
    assert record["id"] == "raw-2"
