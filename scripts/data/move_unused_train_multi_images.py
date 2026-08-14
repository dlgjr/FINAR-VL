#!/usr/bin/env python3
"""Move images unused by train_multi_sft.jsonl while preserving relative paths."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


DEFAULT_JSONL = Path(
    "/mnt/nas/bihaoran/qwen3vl/data/train_multi/train_multi_sft.jsonl"
)
DEFAULT_CWD = Path("/mnt/nas/bihaoran/qwen3vl")
DEFAULT_ROOT_IMAGE_DIR = Path("/mnt/nas/bihaoran/qwen3vl/data/train_multi")
DEFAULT_ASSETS_DIR = DEFAULT_ROOT_IMAGE_DIR / "assets"
DEFAULT_DELETE_DIR = DEFAULT_ROOT_IMAGE_DIR / "images_delete"
DEFAULT_CHECK_SCRIPT = Path(
    "/mnt/nas/bihaoran/qwen3vl/scripts/data/check_train_multi_images.py"
)
IMAGE_SUFFIXES = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
    ".bmp",
    ".gif",
    ".tif",
    ".tiff",
    ".avif",
    ".jfif",
    ".heic",
    ".heif",
    ".svg",
}


def is_within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def resolve_local_image(raw: str, cwd: Path, root_image_dir: Path) -> Path | None:
    ref = raw.strip()
    if not ref or ref.startswith(("http://", "https://", "data:")):
        return None

    path = Path(os.path.expanduser(ref))
    candidates = [path if path.is_absolute() else cwd / path]
    candidates.append(path if path.is_absolute() else root_image_dir / path)
    for candidate in candidates:
        if candidate.is_file():
            return candidate.resolve()
    return None


def collect_used_images(jsonl: Path, cwd: Path, root_image_dir: Path) -> set[Path]:
    used: set[Path] = set()
    with jsonl.open("r", encoding="utf-8-sig") as handle:
        for line_number, raw_line in enumerate(handle, 1):
            if not raw_line.strip():
                continue
            try:
                row: Any = json.loads(raw_line)
            except json.JSONDecodeError as exc:
                raise RuntimeError(f"第 {line_number} 行 JSON 无效: {exc}") from exc
            if not isinstance(row, dict):
                raise RuntimeError(f"第 {line_number} 行不是 JSON 对象")
            images = row.get("images")
            if not isinstance(images, list):
                raise RuntimeError(f"第 {line_number} 行 images 不是列表")
            for image in images:
                if not isinstance(image, str) or not image.strip():
                    raise RuntimeError(f"第 {line_number} 行存在无效图片路径")
                resolved = resolve_local_image(image, cwd, root_image_dir)
                if resolved is not None:
                    used.add(resolved)
    return used


def enumerate_assets(assets_dir: Path) -> list[Path]:
    return sorted(
        path.resolve()
        for path in assets_dir.rglob("*")
        if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES
    )


def format_size(size: int) -> str:
    value = float(size)
    for unit in ("B", "KiB", "MiB", "GiB", "TiB"):
        if value < 1024 or unit == "TiB":
            return f"{value:.2f} {unit}"
        value /= 1024
    return f"{size} B"


def write_preview(path: Path, files: list[Path], assets_dir: Path) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for source in files:
            handle.write(str(source.relative_to(assets_dir)) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--jsonl", type=Path, default=DEFAULT_JSONL)
    parser.add_argument("--cwd", type=Path, default=DEFAULT_CWD)
    parser.add_argument("--root-image-dir", type=Path, default=DEFAULT_ROOT_IMAGE_DIR)
    parser.add_argument("--assets-dir", type=Path, default=DEFAULT_ASSETS_DIR)
    parser.add_argument("--delete-dir", type=Path, default=DEFAULT_DELETE_DIR)
    parser.add_argument("--check-script", type=Path, default=DEFAULT_CHECK_SCRIPT)
    parser.add_argument("--execute", action="store_true", help="确认后实际移动文件")
    args = parser.parse_args()

    jsonl = args.jsonl.resolve()
    cwd = args.cwd.resolve()
    root_image_dir = args.root_image_dir.resolve()
    assets_dir = args.assets_dir.resolve()
    delete_dir = args.delete_dir.resolve()
    check_script = args.check_script.resolve()

    for path in (jsonl, cwd, root_image_dir, assets_dir):
        if not path.exists():
            raise FileNotFoundError(path)
    if not jsonl.is_file() or not cwd.is_dir() or not root_image_dir.is_dir():
        raise NotADirectoryError("jsonl/cwd/root-image-dir 参数类型不正确")
    if not assets_dir.is_dir():
        raise NotADirectoryError(assets_dir)
    if is_within(delete_dir, assets_dir):
        raise RuntimeError("delete-dir 不能位于 assets-dir 内部")

    used = collect_used_images(jsonl, cwd, root_image_dir)
    candidates = [path for path in enumerate_assets(assets_dir) if path not in used]
    total_size = sum(path.stat().st_size for path in candidates)
    print(f"引用图片去重后: {len(used)}")
    print(f"待移动图片: {len(candidates)}")
    print(f"待移动总大小: {format_size(total_size)}")
    if not candidates:
        print("没有需要移动的图片。")
        return 0

    mappings = [(source, delete_dir / source.relative_to(assets_dir)) for source in candidates]
    collisions = [target for _, target in mappings if target.exists()]
    if collisions:
        print("目标文件已存在，已停止，未移动任何文件：", file=sys.stderr)
        for path in collisions:
            print(path, file=sys.stderr)
        return 2

    if not args.execute:
        preview_path = delete_dir.parent / "unused_train_multi_images.txt"
        write_preview(preview_path, candidates, assets_dir)
        print(f"完整清单: {preview_path}")
        print("当前为预览模式；确认后加 --execute 执行移动。")
        return 0

    delete_dir.mkdir(parents=True, exist_ok=True)
    manifest = delete_dir / "move_manifest.jsonl"
    with manifest.open("a", encoding="utf-8", newline="\n") as handle:
        for source, target in mappings:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(source), str(target))
            handle.write(
                json.dumps(
                    {"source": str(source), "target": str(target)},
                    ensure_ascii=False,
                    separators=(",", ":"),
                )
                + "\n"
            )
            handle.flush()

    print(f"已移动 {len(mappings)} 个文件。映射清单: {manifest}")
    if check_script.is_file():
        command = [
            sys.executable,
            str(check_script),
            "--jsonl",
            str(jsonl),
            "--cwd",
            str(cwd),
            "--root-image-dir",
            str(root_image_dir),
        ]
        print("开始重新校验图片引用...")
        return subprocess.run(command, check=False).returncode
    print(f"未找到校验脚本，跳过自动校验: {check_script}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"错误: {exc}", file=sys.stderr)
        raise SystemExit(1)
