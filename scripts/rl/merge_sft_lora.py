"""Merge an SFT PEFT adapter into a standalone model for full-parameter GSPO."""

from __future__ import annotations

import argparse
from pathlib import Path


def merge(base_model: str, adapter: str, output: str) -> None:
    from peft import PeftModel
    from transformers import AutoProcessor
    try:
        from transformers import AutoModelForImageTextToText as ModelClass
    except ImportError:
        from transformers import AutoModel as ModelClass

    model = ModelClass.from_pretrained(base_model, torch_dtype="auto", trust_remote_code=True)
    merged = PeftModel.from_pretrained(model, adapter).merge_and_unload()
    output_path = Path(output)
    output_path.mkdir(parents=True, exist_ok=True)
    merged.save_pretrained(output_path, safe_serialization=True)
    try:
        AutoProcessor.from_pretrained(base_model, trust_remote_code=True).save_pretrained(output_path)
    except Exception:
        pass


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-model", required=True)
    parser.add_argument("--adapter", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    merge(args.base_model, args.adapter, args.output)


if __name__ == "__main__":
    main()
