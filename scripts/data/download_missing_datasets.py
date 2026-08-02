#!/usr/bin/env python3
"""从项目官方 Hugging Face 仓库下载缺失数据集。"""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from dataclasses import dataclass
from pathlib import Path

from huggingface_hub import snapshot_download


@dataclass(frozen=True)
class DownloadSpec:
    name: str
    repo_id: str
    relative_dir: str
    allow_patterns: tuple[str, ...] | None = None


DOWNLOAD_SPECS = (
    DownloadSpec(
        "BizFinBench.v2",
        "HiThink-Research/BizFinBench.v2",
        "BizFinBench.v2-main/BizFinBench.v2-main/datasets",
    ),
    DownloadSpec(
        "Finch",
        "FinWorkBench/Finch",
        "Finch-main/Finch-main/dataset",
    ),
    DownloadSpec(
        "FiNER-139",
        "nlpaueb/finer-139",
        "finer-main/finer-main/data/hf_finer139",
    ),
    DownloadSpec(
        "FinMME",
        "luojunyu/FinMME",
        "FinMME-main/FinMME-main/data",
    ),
    DownloadSpec(
        "MultiHiertt",
        "yilunzhao/MultiHiertt",
        "MultiHiertt-main/MultiHiertt-main/dataset",
        ("multihiertt_data/**",),
    ),
    DownloadSpec(
        "TAT-DQA",
        "next-tat/TAT-DQA",
        "TAT-DQA-master/TAT-DQA-master/dataset",
    ),
    DownloadSpec(
        "PIXIU-fpb",
        "ChanceFocus/flare-fpb",
        "PIXIU-main/PIXIU-main/data/hf/flare-fpb-instruct",
    ),
    DownloadSpec(
        "PIXIU-fiqasa",
        "ChanceFocus/flare-fiqasa",
        "PIXIU-main/PIXIU-main/data/hf/flare-fiqasa-instruct",
    ),
    DownloadSpec(
        "PIXIU-headlines",
        "TheFinAI/flare-headlines",
        "PIXIU-main/PIXIU-main/data/hf/flare-headlines",
    ),
    DownloadSpec("PIXIU-ner", "TheFinAI/flare-ner", "PIXIU-main/PIXIU-main/data/hf/flare-ner"),
    DownloadSpec(
        "PIXIU-convfinqa",
        "TheFinAI/flare-convfinqa",
        "PIXIU-main/PIXIU-main/data/hf/flare-convfinqa",
    ),
    DownloadSpec(
        "PIXIU-sm-bigdata",
        "TheFinAI/flare-sm-bigdata",
        "PIXIU-main/PIXIU-main/data/hf/flare-sm-bigdata",
    ),
    DownloadSpec(
        "PIXIU-sm-acl",
        "TheFinAI/flare-sm-acl",
        "PIXIU-main/PIXIU-main/data/hf/flare-sm-acl",
    ),
    DownloadSpec(
        "PIXIU-sm-cikm",
        "TheFinAI/flare-sm-cikm",
        "PIXIU-main/PIXIU-main/data/hf/flare-sm-cikm",
    ),
)

DUPLICATE_EXISTING_SOURCES = {"PIXIU-finqa": "finqa"}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _snapshot_with_retry(
    spec: DownloadSpec,
    target: Path,
    *,
    attempts: int = 3,
    delay_seconds: int = 5,
) -> None:
    for attempt in range(1, attempts + 1):
        try:
            snapshot_download(
                repo_id=spec.repo_id,
                repo_type="dataset",
                local_dir=target,
                allow_patterns=list(spec.allow_patterns) if spec.allow_patterns else None,
            )
            return
        except Exception:
            if attempt == attempts:
                raise
            time.sleep(delay_seconds * attempt)


def download_all(source_root: Path) -> dict[str, object]:
    results = []
    for spec in DOWNLOAD_SPECS:
        target = source_root / spec.relative_dir
        target.mkdir(parents=True, exist_ok=True)
        print(f"Downloading {spec.name} from {spec.repo_id}", flush=True)
        _snapshot_with_retry(spec, target)
        files = []
        for path in sorted(target.rglob("*")):
            if path.is_file() and ".cache" not in path.parts:
                files.append(
                    {
                        "path": path.relative_to(source_root).as_posix(),
                        "bytes": path.stat().st_size,
                        "sha256": _sha256(path),
                    }
                )
        results.append(
            {
                "name": spec.name,
                "repo_id": spec.repo_id,
                "relative_dir": spec.relative_dir,
                "files": files,
            }
        )
    return {
        "source_root": str(source_root),
        "excluded_by_user": ["FinRAGBench-V"],
        "unavailable_official_data": ["Fin-R1"],
        "duplicate_existing_sources": DUPLICATE_EXISTING_SOURCES,
        "datasets": results,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args()
    manifest = download_all(args.source_root)
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
