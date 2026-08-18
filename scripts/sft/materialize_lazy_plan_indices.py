"""Keep legacy compressed SFT plans compatible with lazy raw-index datasets.

New plans are written in raw-index mode directly.  Older plans may still use
compressed post-filter indices and are converted here before training.
"""

from __future__ import annotations

import argparse
import json
import os
import tempfile
from pathlib import Path
from typing import Any


def _jsonl_row_count(path: Path) -> int:
    rows = 0
    blanks = 0
    with path.open("rb") as handle:
        for line in handle:
            if line.strip():
                rows += 1
            else:
                blanks += 1
    if blanks:
        raise RuntimeError(
            f"lazy raw-index mapping requires normalized JSONL without blank lines: "
            f"path={path} blank_lines={blanks}"
        )
    return rows


def _atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_name, path)
    except Exception:
        try:
            os.unlink(tmp_name)
        except FileNotFoundError:
            pass
        raise


def _expected_raw_count(meta: dict[str, Any], modality: str) -> int | None:
    stats = meta.get("dataset_stats")
    if not isinstance(stats, dict):
        return None
    modality_stats = stats.get(modality)
    if not isinstance(modality_stats, dict):
        return None
    value = modality_stats.get("raw")
    return None if value is None else int(value)


def materialize_lazy_plan_indices(
    plan_dir: Path,
    *,
    train_multi: Path,
    train_text: Path,
) -> dict[str, Any]:
    plan_dir = Path(plan_dir)
    meta_path = plan_dir / "meta.json"
    if not meta_path.is_file():
        raise RuntimeError(f"sample plan meta not found: {meta_path}")

    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    if str(meta.get("dataset_index_mode") or "") == "raw":
        return meta

    raw_counts = {
        "multi": _jsonl_row_count(Path(train_multi)),
        "text": _jsonl_row_count(Path(train_text)),
    }
    for modality, observed in raw_counts.items():
        expected = _expected_raw_count(meta, modality)
        if expected is not None and expected != observed:
            raise RuntimeError(
                f"sample-plan raw row count mismatch for {modality}: "
                f"plan={expected} jsonl={observed}"
            )

    total_blocks = int(meta.get("total_blocks", 0))
    for block_id in range(total_blocks):
        block_path = plan_dir / f"block_{block_id:04d}.jsonl"
        if not block_path.is_file():
            raise RuntimeError(f"sample plan block not found: {block_path}")
        converted: list[str] = []
        with block_path.open(encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                if not line.strip():
                    continue
                entry = json.loads(line)
                modality = str(entry.get("modality") or "")
                if modality not in raw_counts:
                    raise RuntimeError(
                        f"unknown modality in {block_path}:{line_number}: {modality!r}"
                    )
                filtered_index = int(entry["index"])
                raw_index = int(entry.get("raw_index", filtered_index))
                if raw_index < 0 or raw_index >= raw_counts[modality]:
                    raise IndexError(
                        f"raw plan index out of range in {block_path}:{line_number}: "
                        f"modality={modality} raw_index={raw_index} rows={raw_counts[modality]}"
                    )
                entry.setdefault("filtered_index", filtered_index)
                entry["index"] = raw_index
                entry["raw_index"] = raw_index
                converted.append(json.dumps(entry, ensure_ascii=False, separators=(",", ":")))
        _atomic_write_text(block_path, "".join(row + "\n" for row in converted))

    meta["filtered_N_multi"] = int(meta["N_multi"])
    meta["filtered_N_text"] = int(meta["N_text"])
    meta["N_multi"] = raw_counts["multi"]
    meta["N_text"] = raw_counts["text"]
    meta["dataset_index_mode"] = "raw"
    _atomic_write_text(meta_path, json.dumps(meta, ensure_ascii=False, indent=2) + "\n")
    return meta


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan-dir", type=Path, required=True)
    parser.add_argument("--train-multi", type=Path, required=True)
    parser.add_argument("--train-text", type=Path, required=True)
    args = parser.parse_args()
    meta = materialize_lazy_plan_indices(
        args.plan_dir,
        train_multi=args.train_multi,
        train_text=args.train_text,
    )
    print(
        "lazy_plan_indices "
        f"mode={meta.get('dataset_index_mode')} "
        f"raw_multi={meta.get('N_multi')} raw_text={meta.get('N_text')} "
        f"filtered_multi={meta.get('filtered_N_multi')} filtered_text={meta.get('filtered_N_text')}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
