#!/usr/bin/env python3
"""Check-only version of validate_train_multi_images_v2.py.

复用 v2 的图片解析逻辑（多候选路径 + basename 索引 + file:// 归一化），
只做校验统计，不移动文件、不重写 JSONL。
"""

from __future__ import annotations

import argparse
import collections
import json
import os
from pathlib import Path
from typing import Any

DEFAULT_JSONL = Path("/mnt/nas/bihaoran/qwen3vl/data/train_multi/train_multi_sft.jsonl")
DEFAULT_ASSETS = Path("/mnt/nas/bihaoran/qwen3vl/data/train_multi/assets")


def is_under(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def normalize_ref(value: str) -> str:
    value = value.strip()
    return value[7:] if value.startswith("file://") else value


def collect_image_refs(row: dict[str, Any]) -> list[tuple[Any, Any, str]]:
    refs: list[tuple[Any, Any, str]] = []
    seen: set[tuple[int, Any]] = set()

    def add(container: Any, key: Any, value: Any) -> None:
        if not isinstance(value, str) or not value.strip():
            return
        marker = (id(container), key)
        if marker in seen:
            return
        seen.add(marker)
        refs.append((container, key, value))

    def walk(obj: Any) -> None:
        if isinstance(obj, dict):
            obj_type = str(obj.get("type", "")).lower()
            for key, value in list(obj.items()):
                key_l = str(key).lower()

                if key_l in {"image", "image_path", "image_file"}:
                    if isinstance(value, str):
                        add(obj, key, value)
                    elif isinstance(value, list):
                        for i, item in enumerate(value):
                            if isinstance(item, str):
                                add(value, i, item)

                elif key_l in {"images", "image_paths", "image_files"} and isinstance(value, list):
                    for i, item in enumerate(value):
                        if isinstance(item, str):
                            add(value, i, item)
                        elif isinstance(item, dict):
                            walk(item)

                elif key_l == "image_url":
                    if isinstance(value, str):
                        add(obj, key, value)
                    elif isinstance(value, dict):
                        for subkey in ("url", "path", "image"):
                            if isinstance(value.get(subkey), str):
                                add(value, subkey, value[subkey])
                                break

                elif obj_type in {"image", "image_url", "input_image"} and key_l in {"url", "path", "source"}:
                    if isinstance(value, str):
                        add(obj, key, value)

            for value in obj.values():
                if isinstance(value, (dict, list)):
                    walk(value)

        elif isinstance(obj, list):
            for item in obj:
                if isinstance(item, (dict, list)):
                    walk(item)

    walk(row)
    return refs


def count_image_placeholders(obj: Any) -> int:
    if isinstance(obj, str):
        return obj.count("<image>")
    if isinstance(obj, dict):
        return sum(count_image_placeholders(v) for v in obj.values())
    if isinstance(obj, list):
        return sum(count_image_placeholders(v) for v in obj)
    return 0


def build_basename_index(root: Path) -> dict[str, list[Path]]:
    index: dict[str, list[Path]] = {}
    for dirpath, _, filenames in os.walk(root):
        for name in filenames:
            path = Path(dirpath) / name
            if path.name == "error.jsonl" or path.suffix in {".tmp", ".bak"}:
                continue
            index.setdefault(name, []).append(path)
    return index


def resolve_image(raw: str, jsonl_dir: Path, assets_dir: Path, basename_index: dict[str, list[Path]]):
    ref = normalize_ref(raw)
    if ref.startswith(("http://", "https://", "data:")):
        return None, f"non-local image reference: {raw}"

    p = Path(ref)
    candidates: list[Path] = []

    if p.is_absolute():
        candidates.append(p)
    else:
        parts = p.parts
        if "assets" in parts:
            assets_pos = parts.index("assets")
            tail = parts[assets_pos + 1:]
            if tail:
                candidates.append(assets_dir.joinpath(*tail))

        candidates.append(jsonl_dir / p)
        candidates.append(jsonl_dir.parent.parent / p)
        candidates.append(assets_dir / p)

    seen: set[str] = set()
    for candidate in candidates:
        key = str(candidate)
        if key in seen:
            continue
        seen.add(key)
        if candidate.is_file():
            return candidate.resolve(), None

    matches = [x.resolve() for x in basename_index.get(p.name, []) if x.is_file()]
    unique = {str(x): x for x in matches}
    if len(unique) == 1:
        return next(iter(unique.values())), None
    if len(unique) > 1:
        return None, f"basename is ambiguous: {raw} -> {sorted(unique)}"

    return None, f"image not found: {raw}"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--jsonl", type=Path, default=DEFAULT_JSONL)
    parser.add_argument("--assets-dir", type=Path, default=DEFAULT_ASSETS)
    parser.add_argument(
        "--root",
        type=Path,
        default=None,
        help="ms-swift 加载时的基准目录（默认取 jsonl 的上级上级目录，即仓库 ROOT）。"
        "相对路径按 ROOT/相对路径 解析，等价于 cwd=ROOT 或 ROOT_IMAGE_DIR=ROOT。",
    )
    args = parser.parse_args()

    jsonl = args.jsonl.resolve()
    assets_dir = args.assets_dir.resolve()
    jsonl_dir = jsonl.parent
    root = (args.root or jsonl_dir.parent.parent).resolve()

    if not jsonl.is_file():
        raise FileNotFoundError(jsonl)

    print(f"jsonl      : {jsonl}")
    print(f"assets_dir : {assets_dir}")
    print("building basename index...")
    basename_index = build_basename_index(jsonl_dir)

    total = parse_bad = no_ref_rows = ref_placeholder_mismatch = 0
    refs_total = loadable_now = repairable = missing = 0
    rows_loadable = rows_repairable = rows_missing = 0
    repairable_by_source: collections.Counter[str] = collections.Counter()
    missing_by_source: collections.Counter[str] = collections.Counter()
    repairable_by_prefix: collections.Counter[str] = collections.Counter()
    missing_by_prefix: collections.Counter[str] = collections.Counter()
    error_kinds: collections.Counter[str] = collections.Counter()
    distinct_missing: set[str] = set()
    sample_repairable: dict[str, str] = {}
    sample_missing: dict[str, str] = {}

    with jsonl.open("r", encoding="utf-8") as fin:
        for line_no, line in enumerate(fin, 1):
            if not line.strip():
                continue
            total += 1
            try:
                row = json.loads(line)
            except Exception as exc:
                parse_bad += 1
                print(f"parse error line {line_no}: {exc}")
                continue

            refs = collect_image_refs(row)
            placeholders = count_image_placeholders(row)
            refs_total += len(refs)

            if placeholders > 0 and not refs:
                ref_placeholder_mismatch += 1
            elif not refs:
                no_ref_rows += 1

            row_has_repairable = row_has_missing = False
            for _container, _key, raw in refs:
                ref = normalize_ref(raw)
                # ms-swift 实际加载语义：cwd=ROOT（或 ROOT_IMAGE_DIR=ROOT）时按 ROOT/相对路径打开。
                if not ref.startswith(("http://", "https://", "data:")) and os.path.exists(
                    os.path.join(root, ref)
                ):
                    loadable_now += 1
                    continue
                _src, err = resolve_image(raw, jsonl_dir, assets_dir, basename_index)
                if err:
                    row_has_missing = True
                    error_kinds["ambiguous" if "ambiguous" in err else "not_found"] += 1
                    missing += 1
                    distinct_missing.add(raw)
                    prefix = "/".join(Path(normalize_ref(raw)).parts[:3])
                    missing_by_prefix[prefix] += 1
                    src_name = str(row.get("source"))
                    missing_by_source[src_name] += 1
                    if src_name not in sample_missing:
                        sample_missing[src_name] = raw
                else:
                    row_has_repairable = True
                    repairable += 1
                    prefix = "/".join(Path(ref).parts[:3])
                    repairable_by_prefix[prefix] += 1
                    src_name = str(row.get("source"))
                    repairable_by_source[src_name] += 1
                    if src_name not in sample_repairable:
                        sample_repairable[src_name] = raw

            if row_has_missing:
                rows_missing += 1
            elif row_has_repairable:
                rows_repairable += 1
            else:
                rows_loadable += 1

            if total % 10000 == 0:
                print(
                    f"processed={total} refs={refs_total} loadable={loadable_now} "
                    f"repairable={repairable} missing={missing}"
                )

    print("=" * 60)
    print("total rows              :", total)
    print("parse errors            :", parse_bad)
    print("rows without image ref  :", no_ref_rows)
    print("placeholder/ref mismatch:", ref_placeholder_mismatch)
    print("image refs              :", refs_total)
    print(f"loadable now (root={root}):", loadable_now)
    print("repairable by v2 rules   :", repairable)
    print("missing (not found)      :", missing)
    print("distinct missing paths  :", len(distinct_missing))
    print("rows fully loadable      :", rows_loadable)
    print("rows need v2 repair      :", rows_repairable)
    print("rows with missing images :", rows_missing)
    print("error kinds             :", dict(error_kinds))
    if loadable_now == 0 and repairable > 0:
        print("HINT: 引用可能是相对 jsonl 目录（如 assets/...），ms-swift 按 cwd/ROOT_IMAGE_DIR 解析。")
        print(f"      尝试 --root {jsonl_dir} 验证；训练时设 ROOT_IMAGE_DIR={jsonl_dir}，")
        print("      或把 jsonl 引用改为相对 ROOT 的 data/train_multi/assets/... 形式。")
    print("-" * 60)
    if repairable_by_source:
        print("repairable by source (top 20):")
        for src, cnt in repairable_by_source.most_common(20):
            print(f"  {src:<55} {cnt}  e.g. {sample_repairable[src]}")
        print("-" * 60)
        print("repairable by path prefix (top 15):")
        for prefix, cnt in repairable_by_prefix.most_common(15):
            print(f"  {prefix:<70} {cnt}")
        print("-" * 60)
    if missing_by_source:
        print("missing by source (top 20):")
        for src, cnt in missing_by_source.most_common(20):
            print(f"  {src:<55} {cnt}  e.g. {sample_missing[src]}")
        print("-" * 60)
        print("missing by path prefix (top 15):")
        for prefix, cnt in missing_by_prefix.most_common(15):
            print(f"  {prefix:<70} {cnt}")
    print("DONE (read-only, nothing modified)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
