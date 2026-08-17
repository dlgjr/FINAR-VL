#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FINAR-VL common retention downloader
VERSION = single_node_aria2_v8_mm60

Single node only.
- ModelScope China endpoint only.
- aria2c does the actual concurrent downloads.
- final output = up to exactly 30,000 samples:
    text 12,000:
      alpaca_en    4,000
      alpaca_zh    4,000
      gsm8k        4,000
    multimodal 18,000:
      coco_caption 6,000
      chartqa      6,000
      scienceqa    6,000
- raw/cache live on NAS.
- raw/cache are deleted after successful conversion.
- task is always "generation".

Run:
  python /mnt/nas/bihaoran/qwen3vl/download_common_data.py
"""

import argparse
import csv
import hashlib
import io
import json
import os
import random
import shutil
import subprocess
import time
import urllib.parse
from pathlib import Path

VERSION = "single_node_aria2_v8_mm60"
DEFAULT_ROOT = "/mnt/nas/bihaoran/qwen3vl"
ENDPOINT = "https://modelscope.cn"
REVISION = "master"

SOURCES = {
    "alpaca_en": {
        "repo": "AI-ModelScope/alpaca-gpt4-data-en",
        "modality": "text",
        "target": 4000,
    },
    "alpaca_zh": {
        "repo": "AI-ModelScope/alpaca-gpt4-data-zh",
        "modality": "text",
        "target": 4000,
    },
    "gsm8k": {
        "repo": "AI-ModelScope/gsm8k",
        "modality": "text",
        "target": 4000,
    },
    "coco_caption": {
        "repo": "modelscope/coco_2014_caption",
        "modality": "multimodal",
        "target": 6000,
    },
    "chartqa": {
        "repo": "lmms-lab/ChartQA",
        "modality": "multimodal",
        "target": 6000,
    },
    "scienceqa": {
        "repo": "swift/ScienceQA",
        "modality": "multimodal",
        "target": 6000,
    },
}

DATA_SUFFIXES = (".parquet", ".jsonl", ".json", ".csv")


def log(msg):
    print(msg, flush=True)


def clean(v):
    return "" if v is None else str(v).strip()


def require_binary(name):
    p = shutil.which(name)
    if not p:
        raise RuntimeError(
            f"{name} not found. Install: apt-get update && apt-get install -y aria2"
        )
    return p


def make_hub_api():
    try:
        from modelscope_hub import HubApi
    except Exception as e:
        raise RuntimeError(
            "modelscope-hub missing. Install: pip install -U modelscope-hub"
        ) from e

    token = (
        os.environ.get("MODELSCOPE_API_TOKEN")
        or os.environ.get("MODELSCOPE_API_KEY")
        or None
    )
    return HubApi(token=token, endpoint=ENDPOINT), token


def normalize_file(item):
    if isinstance(item, str):
        return item
    if isinstance(item, dict):
        for key in ("path", "rfilename", "name", "file_path", "Path", "Name"):
            if item.get(key):
                return str(item[key])
        return None
    for key in ("path", "rfilename", "name", "file_path"):
        value = getattr(item, key, None)
        if value:
            return str(value)
    return None


def list_repo_data_files(api, repo_id):
    items = api.list_repo_files(repo_id, "dataset")
    files = []
    for item in items or []:
        path = normalize_file(item)
        if path and path.lower().endswith(DATA_SUFFIXES):
            files.append(path)
    return sorted(set(files))


def prefer_train_files(files):
    train = []
    for p in files:
        lower = p.lower()
        name = Path(lower).name
        if (
            "/train/" in lower
            or "/train-" in lower
            or name.startswith("train")
            or "_train" in name
            or "train-" in name
        ):
            train.append(p)
    return train if train else files


def direct_url(repo_id, file_path):
    owner, name = repo_id.split("/", 1)
    return (
        f"{ENDPOINT}/api/v1/datasets/{owner}/{name}/repo"
        f"?Revision={urllib.parse.quote_plus(REVISION)}"
        f"&FilePath={urllib.parse.quote_plus(file_path)}"
    )


def probe_url(url, token):
    import requests

    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    headers["Range"] = "bytes=0-0"

    r = requests.get(
        url,
        headers=headers,
        allow_redirects=True,
        stream=True,
        timeout=30,
    )
    try:
        if r.status_code not in (200, 206):
            raise RuntimeError(f"HTTP {r.status_code}: {url}")
    finally:
        r.close()


def safe_rel(path):
    return Path(*[x for x in Path(path).parts if x not in ("", ".", "..", "/")])


def build_plan(api, token):
    plan = []

    for source, cfg in SOURCES.items():
        files = list_repo_data_files(api, cfg["repo"])
        if not files:
            raise RuntimeError(f"No data files found in {cfg['repo']}")

        files = prefer_train_files(files)
        probe_url(direct_url(cfg["repo"], files[0]), token)

        log(f"[plan] {source}: {cfg['repo']} -> {len(files)} train/data file(s)")

        for remote in files:
            plan.append({
                "source": source,
                "repo": cfg["repo"],
                "remote": remote,
                "url": direct_url(cfg["repo"], remote),
            })

    return plan


def write_aria2_input(plan, raw_root, input_path, token):
    input_path.parent.mkdir(parents=True, exist_ok=True)

    with input_path.open("w", encoding="utf-8") as f:
        for item in plan:
            rel = safe_rel(item["remote"])
            out_dir = raw_root / item["source"] / rel.parent
            out_dir.mkdir(parents=True, exist_ok=True)

            f.write(item["url"] + "\n")
            f.write(f"  dir={out_dir}\n")
            f.write(f"  out={rel.name}\n")
            if token:
                f.write(f"  header=Authorization: Bearer {token}\n")
            f.write("\n")


def run_aria2(input_path, concurrent, connections):
    aria2c = require_binary("aria2c")
    cmd = [
        aria2c,
        "--input-file", str(input_path),
        "--continue=true",
        "--auto-file-renaming=false",
        "--allow-overwrite=true",
        "--file-allocation=none",
        "--max-tries=0",
        "--retry-wait=2",
        "--connect-timeout=30",
        "--timeout=120",
        "--lowest-speed-limit=10K",
        "--summary-interval=10",
        f"--max-concurrent-downloads={concurrent}",
        f"--max-connection-per-server={connections}",
        f"--split={connections}",
        "--min-split-size=1M",
    ]

    log("[aria2] " + " ".join(cmd))
    rc = subprocess.run(cmd).returncode
    if rc != 0:
        raise RuntimeError(f"aria2c failed: exit={rc}")


def iter_parquet(path):
    import pyarrow.parquet as pq

    pf = pq.ParquetFile(path)
    for batch in pf.iter_batches(batch_size=256):
        for row in batch.to_pylist():
            yield row


def iter_jsonl(path):
    with path.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except Exception:
                continue


def iter_json(path):
    with path.open("r", encoding="utf-8", errors="replace") as f:
        obj = json.load(f)

    if isinstance(obj, list):
        yield from obj
        return

    if isinstance(obj, dict):
        for key in ("data", "train", "examples", "items"):
            value = obj.get(key)
            if isinstance(value, list):
                yield from value
                return
        yield obj


def iter_csv(path):
    with path.open("r", encoding="utf-8", errors="replace", newline="") as f:
        yield from csv.DictReader(f)


def iter_source_rows(source_dir):
    files = [
        p for p in source_dir.rglob("*")
        if p.is_file() and p.name.lower().endswith(DATA_SUFFIXES)
    ]

    for p in sorted(files):
        lower = p.name.lower()
        if lower.endswith(".parquet"):
            yield from iter_parquet(p)
        elif lower.endswith(".jsonl"):
            yield from iter_jsonl(p)
        elif lower.endswith(".json"):
            yield from iter_json(p)
        elif lower.endswith(".csv"):
            yield from iter_csv(p)


def most_common_answer(values):
    from collections import Counter

    vals = []
    for item in values or []:
        if isinstance(item, dict):
            item = item.get("answer") or item.get("text")
        item = clean(item)
        if item:
            vals.append(item)

    return Counter(vals).most_common(1)[0][0] if vals else ""


def text_convert(source, row):
    if source in ("alpaca_en", "alpaca_zh"):
        user = clean(
            row.get("instruction")
            or row.get("prompt")
            or row.get("question")
        )
        inp = clean(row.get("input"))
        assistant = clean(
            row.get("output")
            or row.get("response")
            or row.get("answer")
        )
        if inp:
            user = f"{user}\n{inp}".strip()
        return (user, assistant) if user and assistant else None

    if source == "gsm8k":
        user = clean(row.get("question") or row.get("problem"))
        assistant = clean(row.get("answer") or row.get("solution"))
        return (user, assistant) if user and assistant else None

    return None


def get_image(row):
    for key in ("image", "img", "picture"):
        if row.get(key) is not None:
            return row[key]
    images = row.get("images")
    if isinstance(images, (list, tuple)) and images:
        return images[0]
    return None


def multimodal_convert(source, row):
    image = get_image(row)
    if image is None:
        return None

    if source == "coco_caption":
        caption = row.get("caption") or row.get("text") or row.get("answer")
        if isinstance(caption, (list, tuple)):
            caption = caption[0] if caption else ""
        caption = clean(caption)
        if not caption:
            return None
        return "Describe this image.", caption, image

    if source == "chartqa":
        user = clean(row.get("query") or row.get("question"))
        assistant = row.get("label")
        if isinstance(assistant, (list, tuple)):
            assistant = assistant[0] if assistant else ""
        assistant = clean(assistant or row.get("answer"))
        if not assistant:
            assistant = most_common_answer(row.get("answers"))
        return (user, assistant, image) if user and assistant else None

    if source == "scienceqa":
        user = clean(row.get("question"))
        choices = [clean(x) for x in (row.get("choices") or [])]
        try:
            idx = int(row.get("answer"))
        except Exception:
            return None
        if not user or not choices or idx < 0 or idx >= len(choices):
            return None

        hint = clean(row.get("hint"))
        opts = "\n".join(f"{chr(65 + i)}. {choice}" for i, choice in enumerate(choices))
        user = (hint + "\n" if hint else "") + user + "\n" + opts
        return user, choices[idx], image

    return None


def image_to_pil(obj, source_dir):
    from PIL import Image

    if obj is None:
        return None

    if isinstance(obj, Image.Image):
        return obj

    if isinstance(obj, (bytes, bytearray, memoryview)):
        return Image.open(io.BytesIO(bytes(obj)))

    if isinstance(obj, dict):
        raw = obj.get("bytes")
        if raw:
            return Image.open(io.BytesIO(bytes(raw)))

        path = obj.get("path")
        if path:
            p = Path(str(path))
            if not p.is_absolute():
                p = source_dir / p
            if p.exists():
                return Image.open(p)

    if isinstance(obj, str):
        p = Path(obj)
        if not p.is_absolute():
            p = source_dir / p
        if p.exists():
            return Image.open(p)

    return None


def save_image(obj, source_dir, assets_root, source):
    image = image_to_pil(obj, source_dir)
    if image is None:
        return None

    if image.mode not in ("RGB", "RGBA"):
        image = image.convert("RGB")

    buf = io.BytesIO()
    image.save(buf, format="PNG")
    data = buf.getvalue()
    digest = hashlib.sha1(data).hexdigest()

    out_dir = assets_root / source
    out_dir.mkdir(parents=True, exist_ok=True)
    dst = out_dir / f"{digest}.png"
    if not dst.exists():
        dst.write_bytes(data)

    return f"assets/common_image/{source}/{digest}.png"


def make_row(source, user, assistant, image=None):
    if image:
        user = "<image>" + user
        images = [image]
    else:
        images = []

    return {
        "messages": [
            {"role": "user", "content": user},
            {"role": "assistant", "content": assistant},
        ],
        "source": f"common_{source}",
        "split": "train",
        "images": images,
        "task": "generation",
    }


def convert(raw_root, common_root, seed):
    assets_root = common_root / "assets" / "common_image"
    assets_root.mkdir(parents=True, exist_ok=True)

    text_rows = []
    mm_rows = []
    stats = []

    for source, cfg in SOURCES.items():
        target = cfg["target"]
        source_dir = raw_root / source
        written = 0
        skipped = 0

        log(f"[convert] {source}: target={target}")

        for row in iter_source_rows(source_dir):
            if written >= target:
                break

            try:
                if cfg["modality"] == "text":
                    converted = text_convert(source, row)
                    if not converted:
                        skipped += 1
                        continue

                    user, assistant = converted
                    text_rows.append(
                        make_row(source, user, assistant)
                    )

                else:
                    converted = multimodal_convert(source, row)
                    if not converted:
                        skipped += 1
                        continue

                    user, assistant, image_obj = converted
                    image_rel = save_image(
                        image_obj,
                        source_dir,
                        assets_root,
                        source,
                    )
                    if not image_rel:
                        skipped += 1
                        continue

                    mm_rows.append(
                        make_row(source, user, assistant, image_rel)
                    )

                written += 1

                if written % 500 == 0:
                    log(f"[convert] {source}: {written}/{target}")

            except Exception as e:
                skipped += 1
                if skipped <= 5:
                    log(f"[convert] {source}: skip {type(e).__name__}: {e}")

        stats.append({
            "source": source,
            "repo": cfg["repo"],
            "modality": cfg["modality"],
            "target": target,
            "written": written,
            "skipped": skipped,
        })

        log(f"[convert] {source}: done {written}/{target}")

    random.Random(seed).shuffle(text_rows)
    random.Random(seed + 1).shuffle(mm_rows)

    common_root.mkdir(parents=True, exist_ok=True)

    text_path = common_root / "common_text.jsonl"
    mm_path = common_root / "common_multimodal.jsonl"
    manifest_path = common_root / "manifest.json"

    with text_path.open("w", encoding="utf-8") as f:
        for row in text_rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    with mm_path.open("w", encoding="utf-8") as f:
        for row in mm_rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    manifest = {
        "version": VERSION,
        "task": "generation",
        "requested_total": sum(cfg["target"] for cfg in SOURCES.values()),
        "text_total": len(text_rows),
        "multimodal_total": len(mm_rows),
        "total": len(text_rows) + len(mm_rows),
        "sources": stats,
    }

    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return manifest


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=DEFAULT_ROOT)
    parser.add_argument("--aria-concurrent", type=int, default=12)
    parser.add_argument("--aria-connections", type=int, default=16)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--keep-cache", action="store_true")
    args = parser.parse_args()

    require_binary("aria2c")

    root = Path(args.root)
    common_root = root / "data" / "common"
    run_root = root / ".cache" / f"common_single_aria2_{int(time.time())}"
    raw_root = run_root / "raw"
    raw_root.mkdir(parents=True, exist_ok=True)

    os.environ["MODELSCOPE_ENDPOINT"] = ENDPOINT
    os.environ["MODELSCOPE_CACHE"] = str(run_root / "modelscope_cache")
    os.environ["MODELSCOPE_HOME"] = str(run_root / "modelscope_home")
    os.environ["HF_HOME"] = str(run_root / "hf_safety_cache")
    os.environ["XDG_CACHE_HOME"] = str(run_root / "xdg_cache")

    print(f"VERSION={VERSION}", flush=True)
    log(f"[paths] temporary raw/cache: {run_root}")
    log(f"[paths] final common data: {common_root}")
    text_target = sum(v["target"] for v in SOURCES.values() if v["modality"] == "text")
    mm_target = sum(v["target"] for v in SOURCES.values() if v["modality"] == "multimodal")
    log(f"[target] text={text_target}, multimodal={mm_target}, total={text_target + mm_target}")
    log(f"[target] multimodal_ratio={mm_target / (text_target + mm_target):.1%}")

    api, token = make_hub_api()
    plan = build_plan(api, token)

    aria_input = run_root / "aria2_input.txt"
    write_aria2_input(plan, raw_root, aria_input, token)

    log(
        f"[download] aria2 files={len(plan)}, "
        f"concurrent={args.aria_concurrent}, "
        f"connections/file={args.aria_connections}"
    )

    run_aria2(
        aria_input,
        concurrent=args.aria_concurrent,
        connections=args.aria_connections,
    )

    manifest = convert(raw_root, common_root, args.seed)
    print(json.dumps(manifest, ensure_ascii=False, indent=2), flush=True)

    if manifest["total"] < 30000:
        log(
            f"[warning] got {manifest['total']}/30000 valid examples. "
            f"See manifest.json for the source that was short."
        )

    if not args.keep_cache:
        log(f"[cleanup] deleting temporary raw/cache: {run_root}")
        shutil.rmtree(run_root, ignore_errors=False)

    log("[done] finished")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
