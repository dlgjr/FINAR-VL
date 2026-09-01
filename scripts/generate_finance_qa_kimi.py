#!/usr/bin/env python3
"""通过魔搭 API-Inference 在本地生成金融多模态问答数据。"""

from __future__ import annotations

import argparse
import base64
import io
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Sequence

from PIL import Image


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.generate_finance_qa import (  # noqa: E402
    merge_parts,
    parse_prompt_library,
    process_shard,
)
from scripts.pass_at_k import (  # noqa: E402
    JsonlRecordError,
    ensure_run_config,
    iter_jsonl_shard,
)


DEFAULT_MODELS = (
    "Qwen/Qwen3.5-397B-A17B",
    "Qwen/Qwen3-VL-235B-A22B-Instruct",
)
DEFAULT_BASE_URL = "https://api-inference.modelscope.cn/v1"
DEFAULT_INPUT = str(PROJECT_ROOT / "data" / "finance_qa" / "all.jsonl")
DEFAULT_PROMPTS = str(
    PROJECT_ROOT
    / "data"
    / "finance_qa"
    / "prompts"
    / "financial_multimodal_prompt_library.md"
)
DEFAULT_OUTPUT = str(
    PROJECT_ROOT / "output" / "finance_qa" / "runs" / "modelscope_dual_1500"
)
MAX_MODELSCOPE_SEED = 2**31 - 1
RATE_LIMIT_RETRIES = 4


def require_modelscope_token() -> str:
    token = os.environ.get("MODELSCOPE_SDK_TOKEN", "").strip()
    if not token:
        raise RuntimeError("missing MODELSCOPE_SDK_TOKEN environment variable")
    return token


def _image_data_url(image: Any) -> str:
    prepared = image.copy()
    prepared.thumbnail((2048, 2048), Image.Resampling.LANCZOS)
    buffer = io.BytesIO()
    prepared.save(buffer, format="PNG")
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def _api_messages(prompt_input: dict[str, Any]) -> list[dict[str, Any]]:
    images = iter((prompt_input.get("multi_modal_data") or {}).get("image") or [])
    messages = []
    for message in prompt_input["prompt"]:
        content = message["content"]
        if isinstance(content, list):
            converted = []
            for part in content:
                if part.get("type") == "image":
                    converted.append(
                        {
                            "type": "image_url",
                            "image_url": {"url": _image_data_url(next(images))},
                        }
                    )
                else:
                    converted.append(dict(part))
            content = converted
        messages.append({**message, "content": content})
    return messages


def _modelscope_seed(seed: int) -> int:
    return (seed - 1) % MAX_MODELSCOPE_SEED + 1


def _is_rate_limit_error(error: Exception) -> bool:
    status_code = getattr(error, "status_code", None)
    if status_code is None:
        status_code = getattr(getattr(error, "response", None), "status_code", None)
    return status_code == 429


class PassthroughProcessor:
    def apply_chat_template(
        self,
        messages: list[dict[str, Any]],
        **_: Any,
    ) -> list[dict[str, Any]]:
        return messages


class ModelScopeGenerator:
    def __init__(
        self,
        *,
        client: Any,
        model_assignments: dict[str, str],
        concurrency: int,
        temperature: float,
        top_p: float,
        max_tokens: int,
    ) -> None:
        self._client = client
        self._model_assignments = model_assignments
        self._concurrency = concurrency
        self._temperature = temperature
        self._top_p = top_p
        self._max_tokens = max_tokens

    def _generate_one(self, prompt_input: dict[str, Any], seed: int) -> str:
        bundle_id = str(prompt_input["_resolved_bundle"]["bundle_id"])
        messages = _api_messages(prompt_input)
        for attempt in range(RATE_LIMIT_RETRIES + 1):
            try:
                stream = self._client.chat.completions.create(
                    model=self._model_assignments[bundle_id],
                    messages=messages,
                    temperature=self._temperature,
                    top_p=self._top_p,
                    max_tokens=self._max_tokens,
                    seed=_modelscope_seed(seed),
                    stream=True,
                )
                parts = []
                for chunk in stream:
                    if not chunk.choices:
                        continue
                    content = chunk.choices[0].delta.content
                    if content:
                        parts.append(content)
                return "".join(parts)
            except Exception as error:
                if not _is_rate_limit_error(error) or attempt == RATE_LIMIT_RETRIES:
                    raise
                time.sleep(2 ** (attempt + 1))
        raise RuntimeError("unreachable")

    def generate_batch(
        self,
        inputs: Sequence[dict[str, Any]],
        seeds: Sequence[int],
    ) -> list[str]:
        with ThreadPoolExecutor(max_workers=self._concurrency) as executor:
            return list(executor.map(self._generate_one, inputs, seeds))


def build_model_assignments(
    input_path: Path,
    models: Sequence[str],
) -> dict[str, str]:
    assignments = {}
    for index, (_, row) in enumerate(iter_jsonl_shard(input_path, 0, 1)):
        if isinstance(row, JsonlRecordError):
            continue
        assignments[str(row["bundle_id"])] = models[index % len(models)]
    return assignments


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate hard financial multimodal QA via ModelScope API-Inference"
    )
    parser.add_argument("--root", default=str(PROJECT_ROOT))
    parser.add_argument(
        "--models",
        "--model",
        nargs="+",
        default=list(DEFAULT_MODELS),
    )
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--input", default=DEFAULT_INPUT)
    parser.add_argument("--prompts", default=DEFAULT_PROMPTS)
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT)
    parser.add_argument("--concurrency", type=int, default=1)
    parser.add_argument("--temperature", type=float, default=0.7)
    parser.add_argument("--top-p", type=float, default=0.9)
    parser.add_argument("--max-tokens", type=int, default=8192)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--max-records", type=int)
    parser.add_argument("--max-records-per-type", type=int)
    parser.add_argument("--target-accepted", type=int, default=1500)
    return parser


def _run_config(args: argparse.Namespace) -> dict[str, Any]:
    return {
        "models": args.models,
        "model_assignment": "input_order_round_robin",
        "base_url": args.base_url,
        "input": str(Path(args.input)),
        "prompts": str(Path(args.prompts)),
        "world_size": 1,
        "concurrency": args.concurrency,
        "temperature": args.temperature,
        "top_p": args.top_p,
        "max_tokens": args.max_tokens,
        "base_seed": args.seed,
        "max_records": args.max_records,
        "max_records_per_type": args.max_records_per_type,
        "target_accepted": args.target_accepted,
    }


def run_local(
    args: argparse.Namespace,
    *,
    client: Any | None = None,
) -> dict[str, Any]:
    token = require_modelscope_token()
    if client is None:
        from openai import OpenAI

        client = OpenAI(api_key=token, base_url=args.base_url)

    project_root = Path(args.root).resolve()
    input_path = Path(args.input).resolve()
    prompt_path = Path(args.prompts).resolve()
    output_dir = Path(args.output_dir).resolve()
    ensure_run_config(output_dir, _run_config(args))
    library = parse_prompt_library(prompt_path)
    model_assignments = build_model_assignments(input_path, args.models)
    generator = ModelScopeGenerator(
        client=client,
        model_assignments=model_assignments,
        concurrency=args.concurrency,
        temperature=args.temperature,
        top_p=args.top_p,
        max_tokens=args.max_tokens,
    )
    counters = process_shard(
        input_path=input_path,
        project_root=project_root,
        output_dir=output_dir,
        rank=0,
        world_size=1,
        library=library,
        processor=PassthroughProcessor(),
        generate_batch=generator.generate_batch,
        batch_size=args.concurrency,
        base_seed=args.seed,
        max_records=args.max_records,
        max_records_per_type=args.max_records_per_type,
        target_accepted=args.target_accepted,
    )
    summary = merge_parts(output_dir, world_size=1)
    return {"worker": counters, "summary": summary}


def main(argv: Sequence[str] | None = None) -> int:
    os.environ["WANDB_DISABLED"] = "true"
    args = build_parser().parse_args(argv)
    result = run_local(args)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    summary = result["summary"]
    accepted = summary.get("accepted_multi", 0) + summary.get("accepted_text", 0)
    return 0 if accepted >= args.target_accepted else 1


if __name__ == "__main__":
    raise SystemExit(main())
