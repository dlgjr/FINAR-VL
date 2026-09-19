#!/usr/bin/env python3
"""Trace and compare Qwen3-VL training/vLLM decoder intermediates on DSW."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def _save_tensor(output_dir: Path, name: str, tensor) -> None:
    import torch

    if isinstance(tensor, tuple):
        tensor = tensor[0]
    if tensor.ndim > 0 and tensor.shape[0] == 1:
        tensor = tensor.squeeze(0)
    torch.save(tensor.detach().float().cpu(), output_dir / f"{name}.pt")


def trace_hf(args: argparse.Namespace) -> None:
    import torch
    from swift.infer_engine import TransformersEngine
    from swift.template import TemplateInputs
    from swift.utils import to_device

    source = json.loads(args.sample_json.read_text(encoding="utf-8"))
    args.output_dir.mkdir(parents=True, exist_ok=True)
    engine = TransformersEngine(
        str(args.model), torch_dtype=torch.bfloat16, device_map="auto"
    )
    modules = dict(engine.model.named_modules())

    def find(suffix: str):
        matches = [module for name, module in modules.items() if name.endswith(suffix)]
        if len(matches) != 1:
            raise RuntimeError(f"{suffix}: expected one module, found {len(matches)}")
        return matches[0]

    def register(module, name: str) -> None:
        module.register_forward_hook(
            lambda _module, _inputs, output: _save_tensor(
                args.output_dir, name, output
            )
        )

    def register_input(module, name: str) -> None:
        module.register_forward_pre_hook(
            lambda _module, inputs: _save_tensor(args.output_dir, name, inputs[0])
        )

    register(find("language_model.embed_tokens"), "embedding")
    for index in args.layers:
        prefix = f"language_model.layers.{index}"
        register(find(prefix + ".input_layernorm"), f"layer_{index:02d}.input_norm")
        register(find(prefix + ".self_attn.q_proj"), f"layer_{index:02d}.q_proj")
        register(find(prefix + ".self_attn.k_proj"), f"layer_{index:02d}.k_proj")
        register(find(prefix + ".self_attn.v_proj"), f"layer_{index:02d}.v_proj")
        register(find(prefix + ".self_attn.q_norm"), f"layer_{index:02d}.q_norm")
        register(find(prefix + ".self_attn.k_norm"), f"layer_{index:02d}.k_norm")
        register_input(
            find(prefix + ".self_attn.o_proj"),
            f"layer_{index:02d}.attention_core",
        )
        register(
            find(prefix + ".self_attn.o_proj"),
            f"layer_{index:02d}.attention_row",
        )

    data = {
        "messages": source["messages"]
        + [{"role": "assistant", "content": source["token_ids"]}],
        "add_eos": False,
    }
    encoded = engine.template.encode(TemplateInputs.from_dict(data), return_length=True)
    model_inputs = engine.template.data_collator([encoded])
    model_inputs.pop("labels", None)
    model_inputs = to_device(model_inputs, engine.model.device)
    rows = int(model_inputs["input_ids"].shape[1])
    if args.expected_rows and rows != args.expected_rows:
        raise AssertionError(f"expected {args.expected_rows} rows, got {rows}")
    with torch.inference_mode(), engine.template.forward_context(
        engine.model, model_inputs
    ):
        engine.model(**model_inputs)
    print(json.dumps({"rows": rows, "output_dir": str(args.output_dir)}))


def _load_vllm(trace_dir: Path, name: str):
    import torch

    matches = sorted(trace_dir.glob(f"{name}.*.pt"))
    if not matches:
        raise FileNotFoundError(f"missing vLLM trace: {name}")
    return torch.load(matches[-1], map_location="cpu")


def _metrics(name: str, actual, expected) -> dict[str, float | str | list[int]]:
    import torch

    if actual.shape != expected.shape:
        raise AssertionError(f"{name}: {tuple(actual.shape)} != {tuple(expected.shape)}")
    error = (actual.float() - expected.float()).abs().flatten()
    return {
        "name": name,
        "shape": list(actual.shape),
        "mean": error.mean().item(),
        "p99": torch.quantile(error, 0.99).item(),
        "max": error.max().item(),
        "equal_fraction": (error == 0).float().mean().item(),
    }


def compare(args: argparse.Namespace) -> None:
    import torch

    def hf_rows(tensor):
        if args.hf_last_row and tensor.ndim > 0:
            return tensor[-1:]
        return tensor

    results = []
    hf_embedding = hf_rows(
        torch.load(args.hf_dir / "embedding.pt", map_location="cpu")
    )
    results.append(
        _metrics("embedding", _load_vllm(args.vllm_dir, "embedding"), hf_embedding)
    )
    for index in args.layers:
        prefix = f"layer_{index:02d}"
        vllm_input = _load_vllm(args.vllm_dir, prefix + ".input_norm")
        hf_input = hf_rows(
            torch.load(args.hf_dir / f"{prefix}.input_norm.pt", map_location="cpu")
        )
        results.append(_metrics(prefix + ".input_norm", vllm_input, hf_input))

        vllm_q_norm = _load_vllm(args.vllm_dir, prefix + ".q_norm")
        vllm_k_norm = _load_vllm(args.vllm_dir, prefix + ".k_norm")
        hf_q_norm = hf_rows(
            torch.load(args.hf_dir / f"{prefix}.q_norm.pt", map_location="cpu")
        )
        hf_k_norm = hf_rows(
            torch.load(args.hf_dir / f"{prefix}.k_norm.pt", map_location="cpu")
        )
        local_q_heads = vllm_q_norm.shape[-2]
        local_k_heads = vllm_k_norm.shape[-2]

        hf_q = hf_rows(
            torch.load(args.hf_dir / f"{prefix}.q_proj.pt", map_location="cpu")
        )
        hf_k = hf_rows(
            torch.load(args.hf_dir / f"{prefix}.k_proj.pt", map_location="cpu")
        )
        hf_v = hf_rows(
            torch.load(args.hf_dir / f"{prefix}.v_proj.pt", map_location="cpu")
        )
        head_dim = vllm_q_norm.shape[-1]
        q_size = local_q_heads * head_dim
        kv_size = local_k_heads * head_dim
        hf_qkv_rank0 = torch.cat(
            [hf_q[..., :q_size], hf_k[..., :kv_size], hf_v[..., :kv_size]], dim=-1
        )
        results.append(
            _metrics(prefix + ".qkv_rank0", _load_vllm(args.vllm_dir, prefix + ".qkv"), hf_qkv_rank0)
        )
        results.append(
            _metrics(prefix + ".q_norm_rank0", vllm_q_norm, hf_q_norm[..., :local_q_heads, :])
        )
        results.append(
            _metrics(prefix + ".k_norm_rank0", vllm_k_norm, hf_k_norm[..., :local_k_heads, :])
        )

        vllm_core = _load_vllm(args.vllm_dir, prefix + ".attention_core")
        hf_core = hf_rows(
            torch.load(
                args.hf_dir / f"{prefix}.attention_core.pt", map_location="cpu"
            )
        )
        results.append(
            _metrics(prefix + ".attention_core_rank0", vllm_core, hf_core[..., : vllm_core.shape[-1]])
        )
        hf_row = hf_rows(
            torch.load(
                args.hf_dir / f"{prefix}.attention_row.pt", map_location="cpu"
            )
        )
        results.append(
            _metrics(prefix + ".attention_row", _load_vllm(args.vllm_dir, prefix + ".attention_row"), hf_row)
        )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(results, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    trace_parser = subparsers.add_parser("hf-trace")
    trace_parser.add_argument("--model", type=Path, required=True)
    trace_parser.add_argument("--sample-json", type=Path, required=True)
    trace_parser.add_argument("--output-dir", type=Path, required=True)
    trace_parser.add_argument("--expected-rows", type=int, default=0)
    trace_parser.add_argument("--layers", type=int, nargs="+", default=[0])
    trace_parser.set_defaults(func=trace_hf)

    compare_parser = subparsers.add_parser("compare")
    compare_parser.add_argument("--hf-dir", type=Path, required=True)
    compare_parser.add_argument("--vllm-dir", type=Path, required=True)
    compare_parser.add_argument("--output", type=Path, required=True)
    compare_parser.add_argument("--layers", type=int, nargs="+", default=[0])
    compare_parser.add_argument("--hf-last-row", action="store_true")
    compare_parser.set_defaults(func=compare)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
