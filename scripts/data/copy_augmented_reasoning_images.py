"""Copy only images referenced by augmented reasoning calculation rows."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path


AUGMENTATION_VERSION = "reasoning_calculation_augmentation_v1"


def collect_image_mapping(dataset: Path) -> dict[str, str]:
    mapping: dict[str, str] = {}
    with dataset.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            routing = row.get("_reward_routing") or {}
            if routing.get("version") != AUGMENTATION_VERSION:
                continue
            original_images = list(routing.get("original_images") or [])
            rewritten_images = list(row.get("images") or [])
            if len(original_images) != len(rewritten_images):
                raise ValueError(
                    f"image mapping length mismatch at source line {routing.get('source_line')}"
                )
            for original, rewritten in zip(original_images, rewritten_images):
                original, rewritten = str(original), str(rewritten)
                previous = mapping.setdefault(original, rewritten)
                if previous != rewritten:
                    raise ValueError(f"conflicting destination for {original}")
    return mapping


def copy_images(dataset: Path, source_root: Path, target_root: Path) -> int:
    mapping = collect_image_mapping(dataset)
    for original, rewritten in mapping.items():
        source = source_root / original
        target = target_root / rewritten
        if not source.is_file():
            raise FileNotFoundError(source)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    return len(mapping)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument(
        "--source-root",
        type=Path,
        default=Path("/mnt/nas/bihaoran/qwen3vl/data/benchmark"),
    )
    parser.add_argument(
        "--target-root",
        type=Path,
        default=Path("/mnt/nas/bihaoran/qwen3vl/data/train_multi"),
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    copied = copy_images(args.dataset, args.source_root, args.target_root)
    print(
        f"CALCULATION_IMAGES_COPIED count={copied} "
        f"source_root={args.source_root} target_root={args.target_root}"
    )


if __name__ == "__main__":
    main()
