#!/usr/bin/env python3
"""按 ms-swift 4.4.2 的本地图片路径路由规则检查多模态 JSONL。

本脚本只检查图片引用最终是否指向现有文件，不加载模型、不解码图片，
也不移动图片或改写 JSONL。
"""

from __future__ import annotations

import argparse
import json
import os
from collections import Counter
from pathlib import Path
from typing import Any


DEFAULT_JSONL = Path("/mnt/nas/bihaoran/qwen3vl/data/train_multi/train_multi_sft.jsonl")


def count_image_placeholders(messages: Any) -> int:
    if not isinstance(messages, list):
        return 0
    return sum(
        message.get("content", "").count("<image>")
        for message in messages
        if isinstance(message, dict) and isinstance(message.get("content"), str)
    )


def resolve_local_image(
    raw: str,
    cwd: Path,
    root_image_dir: Path | None,
) -> tuple[Path | None, str]:
    """模拟 ms-swift 对本地图片路径的查找顺序。"""
    ref = raw.strip()
    if not ref:
        return None, "empty_path"
    if ref.startswith(("http://", "https://")):
        return None, "remote_reference"
    if ref.startswith("data:"):
        return None, "embedded_reference"

    path = Path(os.path.expanduser(ref))
    first_candidate = path if path.is_absolute() else cwd / path
    if first_candidate.is_file():
        return first_candidate.resolve(), "cwd"

    if root_image_dir is not None:
        second_candidate = path if path.is_absolute() else root_image_dir / path
        if second_candidate.is_file():
            return second_candidate.resolve(), "root_image_dir"

    return None, "not_found"


def parse_images(row: dict[str, Any]) -> tuple[list[str], str | None]:
    images = row.get("images")
    if not isinstance(images, list):
        return [], "images_not_list"
    if not images:
        return [], "images_empty"
    if not all(isinstance(image, str) and image.strip() for image in images):
        return [], "images_item_invalid"
    return images, None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--jsonl", type=Path, default=DEFAULT_JSONL)
    parser.add_argument(
        "--cwd",
        type=Path,
        default=Path.cwd(),
        help="训练进程的工作目录；默认使用执行本脚本时的当前目录。",
    )
    parser.add_argument(
        "--root-image-dir",
        type=Path,
        default=Path(os.environ["ROOT_IMAGE_DIR"]) if os.environ.get("ROOT_IMAGE_DIR") else None,
        help="训练时的 ROOT_IMAGE_DIR；默认读取同名环境变量。",
    )
    parser.add_argument("--max-error-samples", type=int, default=20)
    parser.add_argument(
        "--error-output",
        type=Path,
        default=None,
        help="完整错误明细 JSONL；默认写入输入文件同目录。",
    )
    parser.add_argument(
        "--quiet-errors",
        action="store_true",
        help="不在终端逐条打印错误，完整明细仍写入错误文件。",
    )
    args = parser.parse_args()

    jsonl = args.jsonl.resolve()
    cwd = args.cwd.resolve()
    root_image_dir = args.root_image_dir.resolve() if args.root_image_dir else None
    error_output = (
        args.error_output.resolve()
        if args.error_output
        else jsonl.with_name(f"{jsonl.stem}_image_errors.jsonl")
    )

    if not jsonl.is_file():
        raise FileNotFoundError(jsonl)
    if not cwd.is_dir():
        raise NotADirectoryError(cwd)
    if root_image_dir is not None and not root_image_dir.is_dir():
        raise NotADirectoryError(root_image_dir)

    counters: Counter[str] = Counter()
    missing_samples: list[dict[str, Any]] = []
    schema_samples: list[dict[str, Any]] = []

    with jsonl.open("r", encoding="utf-8-sig") as handle, error_output.open(
        "w", encoding="utf-8", newline="\n"
    ) as error_handle:
        def emit_error(error: dict[str, Any]) -> None:
            error_handle.write(json.dumps(error, ensure_ascii=False, separators=(",", ":")) + "\n")
            counters["error_records"] += 1
            if not args.quiet_errors:
                print(json.dumps(error, ensure_ascii=False))

        for line_number, raw_line in enumerate(handle, 1):
            if not raw_line.strip():
                continue
            counters["rows"] += 1
            try:
                row = json.loads(raw_line)
            except json.JSONDecodeError as exc:
                counters["json_errors"] += 1
                error = {"line": line_number, "error": "invalid_json", "detail": str(exc)}
                emit_error(error)
                if len(schema_samples) < args.max_error_samples:
                    schema_samples.append(error)
                continue

            images, schema_error = parse_images(row)
            if schema_error is not None:
                counters[schema_error] += 1
                error = {
                    "line": line_number,
                    "source": row.get("source"),
                    "error": schema_error,
                }
                emit_error(error)
                if len(schema_samples) < args.max_error_samples:
                    schema_samples.append(error)
                continue

            counters["multimodal_rows"] += 1
            placeholder_count = count_image_placeholders(row.get("messages"))
            if placeholder_count != len(images):
                counters["placeholder_mismatch_rows"] += 1

            row_missing = False
            for image in images:
                counters["image_refs"] += 1
                resolved, route = resolve_local_image(image, cwd, root_image_dir)
                counters[route] += 1
                if route == "not_found":
                    row_missing = True
                    error = {
                        "line": line_number,
                        "source": row.get("source"),
                        "error": "image_not_found",
                        "image": image,
                    }
                    emit_error(error)
                    if len(missing_samples) < args.max_error_samples:
                        missing_samples.append(error)
                elif resolved is not None:
                    counters["local_files_found"] += 1

            if row_missing:
                counters["rows_with_missing_images"] += 1
            else:
                counters["rows_without_missing_images"] += 1

    report = {
        "jsonl": str(jsonl),
        "cwd": str(cwd),
        "root_image_dir": str(root_image_dir) if root_image_dir else None,
        "error_output": str(error_output),
        "counts": dict(counters),
        "missing_samples": missing_samples,
        "schema_samples": schema_samples,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))

    failed = any((
        counters["json_errors"],
        counters["images_not_list"],
        counters["images_empty"],
        counters["images_item_invalid"],
        counters["not_found"],
    ))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
