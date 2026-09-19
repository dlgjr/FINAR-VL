#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

DEFAULT_ORIG = "/mnt/nas/duolg/qwen3vl/data/train_multi/train_rl_reasoning_with_pass8.jsonl"
DEFAULT_VALID = "/mnt/nas/duolg/qwen3vl/data/benchmark/test_pass0_valid.jsonl"
DEFAULT_RESCUED = "/mnt/nas/duolg/qwen3vl/data/benchmark/test_pass0_invalid_trainable_final_strict.jsonl"
DEFAULT_OUT = "/mnt/nas/duolg/qwen3vl/data/benchmark/test_pass0_trainable_all.jsonl"


def text_content(c: Any) -> str:
    if isinstance(c, str):
        return c
    if isinstance(c, list):
        return "\n".join(
            x.get("text", "") if isinstance(x, dict) else str(x)
            for x in c
        )
    return ""


def question_text(r: dict[str, Any]) -> str:
    v = r.get("question")
    if isinstance(v, str) and v.strip():
        return v.strip()

    for m in reversed(r.get("messages") or []):
        if isinstance(m, dict) and str(m.get("role", "")).lower() in {"user", "human"}:
            t = text_content(m.get("content"))
            if t.strip():
                return t.strip()

    return ""


def stable_key(r: dict[str, Any]) -> tuple:
    return (
        question_text(r),
        r.get("task"),
        r.get("source"),
        tuple(r.get("images") or []),
        r.get("verifier_type"),
        r.get("sample_id"),
    )


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for lineno, line in enumerate(f, 1):
            if not line.strip():
                continue
            obj = json.loads(line)
            if not isinstance(obj, dict):
                raise ValueError(f"{path}:{lineno}: non-object JSON")
            rows.append(obj)
    return rows


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--orig", default=DEFAULT_ORIG)
    ap.add_argument("--valid", default=DEFAULT_VALID)
    ap.add_argument("--rescued", default=DEFAULT_RESCUED)
    ap.add_argument("--out", default=DEFAULT_OUT)
    args = ap.parse_args()

    orig_path = Path(args.orig)
    valid_path = Path(args.valid)
    rescued_path = Path(args.rescued)
    out_path = Path(args.out)

    for p in (orig_path, valid_path, rescued_path):
        if not p.is_file():
            raise SystemExit(f"FATAL: missing input: {p}")

    orig = load_jsonl(orig_path)
    valid = load_jsonl(valid_path)
    rescued = load_jsonl(rescued_path)

    orig_index = {}
    for i, r in enumerate(orig):
        k = stable_key(r)
        if k in orig_index:
            raise RuntimeError(f"duplicate stable key in original dataset: source_index={i}")
        orig_index[k] = i

    merged = {}
    origin = {}

    for label, rows in (("original_valid", valid), ("rescued_invalid", rescued)):
        for r in rows:
            k = stable_key(r)
            if k not in orig_index:
                raise RuntimeError(f"{label}: row not found in original dataset")

            idx = orig_index[k]
            if idx in merged:
                raise RuntimeError(
                    f"duplicate source_index across trainable inputs: idx={idx}, "
                    f"first={origin[idx]}, second={label}"
                )

            merged[idx] = r
            origin[idx] = label

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        for idx in sorted(merged):
            f.write(json.dumps(merged[idx], ensure_ascii=False) + "\n")

    print(f"[VALID]   {len(valid)}")
    print(f"[RESCUED] {len(rescued)}")
    print(f"[TOTAL]   {len(merged)}")
    print(f"[OUT]     {out_path}")

    if len(valid) == 2344 and len(rescued) == 124:
        if len(merged) != 2468:
            raise RuntimeError("expected 2468 rows but got a different total")
        print("[CHECK] 2344 + 124 = 2468 OK")
    else:
        print("[CHECK] counts differ from the previously observed 2344/124; "
              "the script used the actual current files and still checked duplicates.")


if __name__ == "__main__":
    main()
