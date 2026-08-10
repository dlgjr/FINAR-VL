"""Merge reviewed rows into the train_multi layout and route generated images."""

from __future__ import annotations

import argparse
import json
import re
import shutil
from collections import Counter
from pathlib import Path
from typing import Any

import orjson

from scripts.data.select_benchmark_aligned_tasks import CAPABILITIES


ALIGN_PREFIX = "data/train_multi/assets/align/"


def _is_generated(row: dict[str, Any]) -> bool:
    return bool(row.get("rendered_from", {}).get("evidence_rendered")) or bool(
        row.get("external_image_local")
    )


def _route_images(
    row: dict[str, Any],
    assets_dir: Path,
    project_root: Path,
    stats: Counter[str],
) -> None:
    images = [str(path).replace("\\", "/") for path in row.get("images", [])]
    generated = _is_generated(row)
    routed: list[str] = []
    capability = str(row.get("target_capability", "aligned")).strip() or "aligned"
    for image_path in images:
        if image_path.startswith(ALIGN_PREFIX):
            local_path = project_root / Path(image_path)
            if not local_path.exists():
                raise FileNotFoundError(f"align image is missing: {image_path}")
            routed.append(image_path)
            continue
        if not generated:
            routed.append(image_path)
            continue
        source_path = project_root / Path(image_path)
        if not source_path.exists():
            raise FileNotFoundError(f"generated image is missing: {image_path}")
        if row.get("external_image_local"):
            source_token = re.sub(r"[^0-9A-Za-z._-]+", "_", str(row.get("source", "external"))).strip("_")
            output_name = f"{capability}_{source_token}_{source_path.name}"
        else:
            output_name = f"{capability}_{source_path.name}"
        destination = assets_dir / output_name
        shutil.copy2(source_path, destination)
        routed.append(f"{ALIGN_PREFIX}{output_name}")
        stats["copied_images"] += 1
    if images:
        row["images"] = routed


def export_train_align(
    input_paths: list[Path],
    output_path: Path,
    assets_dir: Path,
    project_root: Path,
) -> dict[str, int]:
    """Write reviewed JSONL rows and copy only locally generated image assets."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    assets_dir.mkdir(parents=True, exist_ok=True)
    stats: Counter[str] = Counter()
    rows_by_content: dict[str, dict[str, Any]] = {}
    for input_path in input_paths:
        inferred_capability = input_path.stem if input_path.stem in CAPABILITIES else ""
        with input_path.open("rb") as input_handle:
            for line in input_handle:
                if not line.strip():
                    continue
                row = orjson.loads(line)
                if inferred_capability:
                    capabilities = [inferred_capability]
                    row["target_capability"] = inferred_capability
                else:
                    capabilities = [str(value) for value in row.get("target_capabilities", [])]
                    declared = str(row.get("target_capability", "")).strip()
                    if declared and declared not in capabilities:
                        capabilities.append(declared)
                content_key = json.dumps(
                    {
                        "messages": row.get("messages", []),
                        "images": [str(path).replace("\\", "/") for path in row.get("images", [])],
                    },
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                )
                if content_key in rows_by_content:
                    existing = rows_by_content[content_key]
                    existing_capabilities = existing.setdefault("target_capabilities", [])
                    for capability in capabilities:
                        if capability not in existing_capabilities:
                            existing_capabilities.append(capability)
                    stats["duplicate_rows"] += 1
                    continue
                if capabilities:
                    row["target_capabilities"] = capabilities
                    row["target_capability"] = capabilities[0]
                _route_images(row, assets_dir, project_root, stats)
                rows_by_content[content_key] = row
                stats["input_rows"] += 1
    with output_path.open("w", encoding="utf-8", buffering=1) as output_handle:
        for row in rows_by_content.values():
            output_handle.write(json.dumps(row, ensure_ascii=False) + "\n")
            stats["rows"] += 1
    return dict(stats)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", action="append", type=Path, required=True)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/train_multi/train_align.jsonl"),
    )
    parser.add_argument(
        "--assets-dir",
        type=Path,
        default=Path("data/train_multi/assets/align"),
    )
    parser.add_argument("--project-root", type=Path, default=Path("."))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    stats = export_train_align(
        args.input,
        args.output,
        args.assets_dir,
        args.project_root.resolve(),
    )
    print(json.dumps(stats, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()
