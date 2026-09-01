import json

from move_pure_text_from_train_multi import move_pure_text


def test_move_rows_without_images(tmp_path):
    source = tmp_path / "train_multi_sft.jsonl"
    destination = tmp_path / "train_text_sft_final.jsonl"
    rows = [
        {"id": "multi-1", "images": ["a.png"]},
        {"id": "text-1"},
        {"id": "text-2", "images": []},
        {"id": "multi-2", "images": ["b.png"]},
    ]
    source.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )
    destination.write_text(
        json.dumps({"id": "existing"}, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    result = move_pure_text(source, destination)

    remaining = [json.loads(line) for line in source.read_text(encoding="utf-8").splitlines()]
    text_rows = [json.loads(line) for line in destination.read_text(encoding="utf-8").splitlines()]
    assert [row["id"] for row in remaining] == ["multi-1", "multi-2"]
    assert [row["id"] for row in text_rows] == ["existing", "text-1", "text-2"]
    assert result == {"total": 4, "moved": 2, "remaining": 2}
