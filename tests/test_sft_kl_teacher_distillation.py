import json

import pytest

import scripts.sft.kl_retention_plugin as kl_plugin
from scripts.sft.kl_retention_plugin import (
    _content_with_images,
    _inject_teacher_token_ids,
    _local_image_uri,
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


def test_teacher_relative_image_falls_back_to_current_media_root(monkeypatch, tmp_path):
    media_root = tmp_path / "train_multi"
    image = media_root / "assets" / "chart_qa" / "12814.png"
    image.parent.mkdir(parents=True)
    image.write_bytes(b"fake-image-bytes")

    normalized = tmp_path / "runtime" / "train_data" / "train_multi.jsonl"
    normalized.parent.mkdir(parents=True)
    normalized.write_text("{}\n", encoding="utf-8")

    monkeypatch.setenv("QWEN3VL_ROOT", str(tmp_path / "repo-root-without-assets"))
    monkeypatch.setenv("SFT_REF_ALLOWED_MEDIA_PATH", str(tmp_path))
    monkeypatch.chdir(media_root)

    assert _local_image_uri("assets/chart_qa/12814.png", data_file=normalized) == image.resolve().as_uri()


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


def test_teacher_token_ids_replace_retokenized_supervised_span_exactly():
    encoded = {
        "input_ids": [10, 11, 20, 21, 22, 99],
        "labels": [-100, -100, 20, 21, 22, 99],
        "loss_scale": [0.0, 0.0, 1.0, 1.0, 1.0, 1.0],
        "attention_mask": [1, 1, 1, 1, 1, 1],
        "mm_token_type_ids": [1, 1, 0, 0, 0, 0],
        "position_ids": [0, 1, 2, 3, 4, 5],
    }
    teacher_ids = [20, 777, 888, 889, 2]

    updated = _inject_teacher_token_ids(encoded, teacher_ids)

    assert updated["input_ids"] == [10, 11, *teacher_ids]
    assert updated["labels"] == [-100, -100, *teacher_ids]
    assert updated["loss_scale"] == [0.0, 0.0, 1.0, 1.0, 1.0, 1.0, 1.0]
    assert updated["attention_mask"] == [1, 1, 1, 1, 1, 1, 1]
    assert updated["mm_token_type_ids"] == [1, 1, 0, 0, 0, 0, 0]
    assert "position_ids" not in updated


def test_teacher_token_ids_preserve_masked_suffix_outside_response_span():
    encoded = {
        "input_ids": [10, 11, 20, 21, 90],
        "labels": [-100, -100, 20, 21, -100],
        "loss_scale": [0.0, 0.0, 1.0, 1.0, 0.0],
    }

    updated = _inject_teacher_token_ids(encoded, [31, 32, 33])

    assert updated["input_ids"] == [10, 11, 31, 32, 33, 90]
    assert updated["labels"] == [-100, -100, 31, 32, 33, -100]
    assert updated["loss_scale"] == [0.0, 0.0, 1.0, 1.0, 1.0, 0.0]


def test_teacher_token_ids_reject_noncontiguous_supervision():
    encoded = {
        "input_ids": [10, 20, 30, 40],
        "labels": [-100, 20, -100, 40],
    }

    with pytest.raises(RuntimeError, match="non-contiguous"):
        _inject_teacher_token_ids(encoded, [50, 51])
