#!/usr/bin/env python3
"""Merge train_multi SFT JSONL shards and relocate docmatix/cauldron images into assets."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(r"D:\FINAR-VL-main")
TRAIN_MULTI = PROJECT_ROOT / "data" / "train_multi"

INPUT_FILES = [
    TRAIN_MULTI / "correct_0_dedup.jsonl",
    TRAIN_MULTI / "correct_1.jsonl",
    TRAIN_MULTI / "correct_2.jsonl",
    TRAIN_MULTI / "correct_3.jsonl",
    TRAIN_MULTI / "correct_4.jsonl",
    TRAIN_MULTI / "correct_5.jsonl",
    TRAIN_MULTI / "correct_6.jsonl",
    TRAIN_MULTI / "correct_7_8.jsonl",
    TRAIN_MULTI / "docmatix_selected_sft.jsonl",
    TRAIN_MULTI / "cauldron" / "cauldron_selected_sft.jsonl",
    TRAIN_MULTI / "cauldron" / "chartqa_selected_sft.jsonl",
    TRAIN_MULTI / "cauldron" / "clevr_math_selected_sft.jsonl",
    TRAIN_MULTI / "cauldron" / "figureqa_selected_sft.jsonl",
    TRAIN_MULTI / "cauldron" / "tabmwp_selected_sft.jsonl",
]

OUTPUT = TRAIN_MULTI / "train_multi_sft_clean.json"

DOCMATIX_PREFIX = "data/train_multi/docmatix/images/"
CAULDRON_PREFIX = "data/train_multi/cauldron/images/"
CAULDRON_SUBDIRS = (("chartqa_", "chartqa"), ("figureqa_", "figureqa"), ("tabmwp_", "tabmwp"))


def training_key(record: dict[str, Any]) -> str:
    payload = {
        "messages": record.get("messages"),
        "images": record.get("images") or [],
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def cauldron_subdir(filename: str) -> str:
    for prefix, subdir in CAULDRON_SUBDIRS:
        if filename.startswith(prefix):
            return subdir
    raise ValueError(f"unknown cauldron image prefix: {filename}")


def rewrite_image(path: str) -> str:
    if path.startswith(DOCMATIX_PREFIX):
        return "data/train_multi/assets/docmatix/" + path[len(DOCMATIX_PREFIX):]
    if path.startswith(CAULDRON_PREFIX):
        filename = path[len(CAULDRON_PREFIX):]
        return f"data/train_multi/assets/cauldron/{cauldron_subdir(filename)}/{filename}"
    return path


def move_images() -> int:
    moved = 0

    docmatix_src = TRAIN_MULTI / "docmatix" / "images"
    docmatix_dst = TRAIN_MULTI / "assets" / "docmatix"
    docmatix_dst.mkdir(parents=True, exist_ok=True)
    for source in docmatix_src.iterdir():
        if not source.is_file():
            continue
        target = docmatix_dst / source.name
        if target.exists():
            raise FileExistsError(f"target already exists: {target}")
        shutil.move(str(source), str(target))
        moved += 1
    docmatix_src.rmdir()

    cauldron_src = TRAIN_MULTI / "cauldron" / "images"
    for source in cauldron_src.iterdir():
        if not source.is_file():
            continue
        target_dir = TRAIN_MULTI / "assets" / "cauldron" / cauldron_subdir(source.name)
        target_dir.mkdir(parents=True, exist_ok=True)
        target = target_dir / source.name
        if target.exists():
            raise FileExistsError(f"target already exists: {target}")
        shutil.move(str(source), str(target))
        moved += 1
    cauldron_src.rmdir()

    return moved


def main() -> None:
    seen: set[str] = set()
    written = 0
    total_read = 0
    removed = 0

    with OUTPUT.open("w", encoding="utf-8", newline="\n") as output:
        for path in INPUT_FILES:
            file_read = 0
            file_dups = 0
            with path.open("r", encoding="utf-8-sig") as source:
                for line in source:
                    raw = line.strip()
                    if not raw:
                        continue
                    record = json.loads(raw)
                    file_read += 1
                    record["images"] = [rewrite_image(image) for image in record.get("images") or []]
                    key = training_key(record)
                    if key in seen:
                        file_dups += 1
                        continue
                    seen.add(key)
                    output.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")
                    written += 1
            total_read += file_read
            removed += file_dups
            print(f"{path.name}: read={file_read} duplicates_removed={file_dups}")

    images_moved = move_images()

    referenced = set()
    with OUTPUT.open("r", encoding="utf-8") as source:
        for line in source:
            record = json.loads(line)
            referenced.update(record.get("images") or [])
    missing = sum(
        1 for image in referenced if not (PROJECT_ROOT / Path(*image.split("/"))).exists()
    )

    print(f"total_read={total_read}")
    print(f"duplicates_removed={removed}")
    print(f"written={written}")
    print(f"images_moved={images_moved}")
    print(f"unique_images={len(referenced)}")
    print(f"missing_image_refs={missing}")


if __name__ == "__main__":
    main()
