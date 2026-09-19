#!/usr/bin/env python3
"""Apply the Qwen3-VL GSPO logprob-parity patch to an installed vLLM.

The patch is intentionally limited to vLLM 0.18-style sources used by the DLC
image.  It is idempotent and fails when an expected upstream source fragment
cannot be found.
"""

from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path


SAMPLER_MARKER = "training-style temperature scaling"
SAMPLER_PROMPT_MARKER = "training-style prompt scoring"
LINEAR_MARKER = "_gspo_fp32_tp_reduce"
QWEN3_VL_MARKER = "GSPO_VLLM_LOGPROB_PARITY"
PARITY_MODE_MARKER = "gspo_parity_modes"
NORM_MARKER = "_gspo_unfused_residual_norm"
TRACE_MARKER = "GSPO_VLLM_PARITY_TRACE_DIR"
TRACE_DETAIL_MARKER = "attention_core"
FLASH_ATTN_SPLITS_MARKER = "GSPO_VLLM_FLASH_ATTN_NUM_SPLITS"
TRAINING_SDPA_MARKER = "_gspo_training_sdpa"
PROMPT_LOGPROB_MARKER = "training-aligned prompt logprobs"
ROPE_MODE_MARKER = "rotary_emb.forward_native"
HF_ROPE_MARKER = "_gspo_hf_forward"
HF_ACTIVATION_MARKER = "_gspo_hf_activation"
HF_FINAL_NORM_MARKER = "_gspo_unfused_final_norm"
HF_FULL_PROJECTION_MARKER = "_gspo_hf_full_projection"


def training_aligned_logprobs(logits, temperature=None):
    """Match the training-side BF16 temperature/log_softmax ordering."""
    import torch

    if temperature is None:
        return torch.nn.functional.log_softmax(logits, dim=-1)
    scaled = logits.clone()
    scaled.div_(temperature.unsqueeze(dim=1))
    return torch.nn.functional.log_softmax(scaled, dim=-1)


def _replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected one source fragment, found {count}")
    return text.replace(old, new, 1)


def _patch_sampler(text: str) -> str:
    if SAMPLER_MARKER not in text:
        old = '''        # NOTE(woosuk): Use the original logits (before any penalties or
        # temperature scaling) for the top-k logprobs.
        # This is different from the V0 sampler, which uses the logits that
        # is used for sampling (after penalties and temperature scaling).
        num_logprobs = sampling_metadata.max_num_logprobs
        if num_logprobs is not None:
            if logprobs_mode == "raw_logprobs":
                raw_logprobs = self.compute_logprobs(logits)
'''
        new = '''        # Compute generated-token logprobs from original-dtype logits after
        # training-style temperature scaling. Sampling itself remains FP32.
        num_logprobs = sampling_metadata.max_num_logprobs
        if num_logprobs is not None:
            if logprobs_mode in ("raw_logprobs", "processed_logprobs"):
                raw_logprobs = self.compute_logprobs(
                    logits, sampling_metadata.temperature
                )
'''
        text = _replace_once(text, old, new, "sampler forward")
        text = _replace_once(
            text,
            '''        if processed_logprobs is not None:
            raw_logprobs = processed_logprobs
''',
            '''        if (
            processed_logprobs is not None
            and logprobs_mode != "processed_logprobs"
        ):
            raw_logprobs = processed_logprobs
''',
            "processed logprobs selection",
        )
        text = _replace_once(
            text,
            '''    def compute_logprobs(logits: torch.Tensor) -> torch.Tensor:
        return logits.log_softmax(dim=-1, dtype=torch.float32)
''',
            '''    def compute_logprobs(
        logits: torch.Tensor,
        temperature: torch.Tensor | None = None,
    ) -> torch.Tensor:
        if temperature is None:
            return logits.log_softmax(dim=-1, dtype=torch.float32)
        logits = logits.clone()
        logits.div_(temperature.unsqueeze(dim=1))
        return torch.nn.functional.log_softmax(logits, dim=-1)
''',
            "sampler compute_logprobs",
        )
    if SAMPLER_PROMPT_MARKER not in text:
        if "import os\n" not in text:
            text = _replace_once(
                text, "import torch\n", "import os\n\nimport torch\n", "sampler os import"
            )
        text = _replace_once(
            text,
            '''        if temperature is None:
            return logits.log_softmax(dim=-1, dtype=torch.float32)
''',
            '''        if temperature is None:
            if "sdpa" in os.environ.get("GSPO_VLLM_LOGPROB_PARITY", "").lower():
                # Match training-style prompt scoring for post-rollout parity.
                return torch.nn.functional.log_softmax(logits, dim=-1)
            return logits.log_softmax(dim=-1, dtype=torch.float32)
''',
            "sampler prompt logprobs",
        )
    return text


def _patch_topk_topp(text: str) -> str:
    old = '''        elif self.logprobs_mode == "processed_logprobs":
            logits_to_return = logits.log_softmax(dim=-1, dtype=torch.float32)
'''
    new = '''        elif self.logprobs_mode == "processed_logprobs":
            # Sampler already computed training-aligned generated-token logprobs.
            logits_to_return = None
'''
    if new in text:
        return text
    count = text.count(old)
    if count != 2:
        raise RuntimeError(
            f"top-k/top-p processed logprobs: expected two source fragments, found {count}"
        )
    return text.replace(old, new)


def _patch_prompt_logprobs(text: str) -> str:
    if PROMPT_LOGPROB_MARKER in text:
        return text
    if "import os\n" not in text:
        text = _replace_once(
            text,
            "from collections.abc import Callable\n",
            "from collections.abc import Callable\nimport os\n",
            "prompt logprobs os import",
        )
    old = '''        prompt_logprobs = compute_topk_logprobs(
            prompt_logits,
            0,  # num_logprobs
            prompt_token_ids[start_idx:end_idx],
        )
        logprobs.append(prompt_logprobs.logprobs)
'''
    new = '''        prompt_logprobs = compute_topk_logprobs(
            prompt_logits,
            0,  # num_logprobs
            prompt_token_ids[start_idx:end_idx],
        )
        if "sdpa" in os.environ.get("GSPO_VLLM_LOGPROB_PARITY", "").lower():
            # Use training-aligned prompt logprobs for the post-rollout
            # teacher-force scoring pass; ranks remain computed by vLLM.
            selected = torch.nn.functional.log_softmax(
                prompt_logits, dim=-1
            ).gather(
                1, prompt_token_ids[start_idx:end_idx].unsqueeze(1)
            ).float()
            logprobs.append(selected)
        else:
            logprobs.append(prompt_logprobs.logprobs)
'''
    return _replace_once(text, old, new, "training-aligned prompt logprobs")


def _patch_linear(text: str) -> str:
    if LINEAR_MARKER in text:
        return text
    old = '''        output_parallel = self.quant_method.apply(self, input_parallel, bias_)
        if NVTX_PROFILE:
            nvtx_pop_range_for_gemm(output_parallel)
        if self.reduce_results and self.tp_size > 1:
            output = tensor_model_parallel_all_reduce(output_parallel)
        else:
            output = output_parallel
'''
    new = '''        gspo_fp32_tp_reduce = (
            getattr(self, "_gspo_fp32_tp_reduce", False)
            and self.tp_size > 1
            and input_parallel.dtype == torch.bfloat16
            and self.weight.dtype == torch.bfloat16
            and self.quant_method.__class__.__name__ == "UnquantizedLinearMethod"
        )
        if gspo_fp32_tp_reduce:
            output_parallel = torch.mm(
                input_parallel, self.weight.t(), out_dtype=torch.float32
            )
        else:
            output_parallel = self.quant_method.apply(self, input_parallel, bias_)
        if NVTX_PROFILE:
            nvtx_pop_range_for_gemm(output_parallel)
        if self.reduce_results and self.tp_size > 1:
            output = tensor_model_parallel_all_reduce(output_parallel)
        else:
            output = output_parallel
        if gspo_fp32_tp_reduce:
            output = output.to(dtype=input_parallel.dtype)
'''
    return _replace_once(text, old, new, "RowParallelLinear forward")


def _patch_qwen3_decoder(text: str) -> str:
    if NORM_MARKER in text:
        return text
    old = '''        # Self Attention
        if residual is None:
            residual = hidden_states
            hidden_states = self.input_layernorm(hidden_states)
        else:
            hidden_states, residual = self.input_layernorm(hidden_states, residual)
        hidden_states = self.self_attn(
            positions=positions,
            hidden_states=hidden_states,
        )

        # Fully Connected
        hidden_states, residual = self.post_attention_layernorm(hidden_states, residual)
        hidden_states = self.mlp(hidden_states)
        return hidden_states, residual
'''
    new = '''        # Qwen3-VL parity mode follows Transformers' explicit BF16 residual
        # addition followed by the standalone RMSNorm implementation.
        gspo_unfused_norm = getattr(self, "_gspo_unfused_residual_norm", False)
        # Self Attention
        if residual is None:
            residual = hidden_states
            hidden_states = self.input_layernorm(hidden_states)
        elif gspo_unfused_norm:
            hidden_states = hidden_states + residual
            residual = hidden_states
            hidden_states = self.input_layernorm(hidden_states)
        else:
            hidden_states, residual = self.input_layernorm(hidden_states, residual)
        hidden_states = self.self_attn(
            positions=positions,
            hidden_states=hidden_states,
        )

        # Fully Connected
        if gspo_unfused_norm:
            hidden_states = hidden_states + residual
            residual = hidden_states
            hidden_states = self.post_attention_layernorm(hidden_states)
        else:
            hidden_states, residual = self.post_attention_layernorm(hidden_states, residual)
        hidden_states = self.mlp(hidden_states)
        return hidden_states, residual
'''
    return _replace_once(text, old, new, "Qwen3 decoder residual/RMSNorm ordering")


def _patch_flash_attention(text: str) -> str:
    if "import os\n" not in text:
        text = _replace_once(
            text, "import copy\n", "import copy\nimport os\n", "FlashAttention os import"
        )
    if FLASH_ATTN_SPLITS_MARKER not in text:
        old = "                    num_splits=attn_metadata.max_num_splits,\n"
        if text.count(old) < 1:
            raise RuntimeError("FlashAttention num_splits: source fragment not found")
        new = '''                    num_splits=(
                        int(os.environ.get("GSPO_VLLM_FLASH_ATTN_NUM_SPLITS", "0"))
                        or attn_metadata.max_num_splits
                    ),
'''
        text = text.replace(old, new, 1)
    old_flattened_output = '''                output[query_start:query_end].copy_(
                    result[0, :, -query_len:].transpose(0, 1).reshape(
                        query_len, -1
                    )
                )
'''
    if old_flattened_output in text:
        text = text.replace(
            old_flattened_output,
            '''                output[query_start:query_end].copy_(
                    result[0, :, -query_len:].transpose(0, 1)
                )
''',
            1,
        )
    if "_gspo_hf_full_attention" in text and "padded_query.contiguous()" not in text:
        text = text.replace(
            "tensor_model_parallel_all_gather(\n                        padded_query, dim=1\n",
            "tensor_model_parallel_all_gather(\n                        padded_query.contiguous(), dim=1\n",
            1,
        )
        text = text.replace(
            "tensor_model_parallel_all_gather(dense_key, dim=1)",
            "tensor_model_parallel_all_gather(dense_key.contiguous(), dim=1)",
            1,
        )
        text = text.replace(
            "tensor_model_parallel_all_gather(\n                        dense_value, dim=1\n",
            "tensor_model_parallel_all_gather(\n                        dense_value.contiguous(), dim=1\n",
            1,
        )
    # Remove the earlier all-head TP experiment. Attention heads are independent;
    # Transformers SDPA performs the same calculation on each local head slice.
    text = text.replace(
        '''            from vllm.distributed.communication_op import tensor_model_parallel_all_gather
            from vllm.distributed.parallel_state import get_tensor_model_parallel_rank

            tp_rank = get_tensor_model_parallel_rank()
''',
        "",
        1,
    )
    text = text.replace(
        '''                dense_key = tensor_model_parallel_all_gather(
                    key_cache.index_select(0, block_ids).reshape(
                        -1, self.num_kv_heads, self.head_size
                    )[:seq_len],
                    dim=1,
                )
                dense_value = tensor_model_parallel_all_gather(
                    value_cache.index_select(0, block_ids).reshape(
                        -1, self.num_kv_heads, self.head_size
                    )[:seq_len],
                    dim=1,
                )
''',
        '''                dense_key = key_cache.index_select(0, block_ids).reshape(
                    -1, self.num_kv_heads, self.head_size
                )[:seq_len]
                dense_value = value_cache.index_select(0, block_ids).reshape(
                    -1, self.num_kv_heads, self.head_size
                )[:seq_len]
''',
        1,
    )
    direct_kv_old = '''                dense_key = key_cache.index_select(0, block_ids).reshape(
                    -1, self.num_kv_heads, self.head_size
                )[:seq_len]
                dense_value = value_cache.index_select(0, block_ids).reshape(
                    -1, self.num_kv_heads, self.head_size
                )[:seq_len]
'''
    direct_kv_new = '''                if query_len == seq_len:
                    # Transformers teacher-force attention consumes the K/V
                    # produced by this forward directly, before any KV-cache
                    # layout conversion.
                    dense_key = key[query_start:query_end]
                    dense_value = value[query_start:query_end]
                else:
                    dense_key = key_cache.index_select(0, block_ids).reshape(
                        -1, self.num_kv_heads, self.head_size
                    )[:seq_len]
                    dense_value = value_cache.index_select(0, block_ids).reshape(
                        -1, self.num_kv_heads, self.head_size
                    )[:seq_len]
'''
    if "if query_len == seq_len:" not in text and direct_kv_old in text:
        text = text.replace(direct_kv_old, direct_kv_new, 1)
    if "_gspo_hf_full_attention" not in text and TRAINING_SDPA_MARKER in text:
        text = _replace_once(
            text,
            '''            import torch.nn.functional as F
            query_start_loc = attn_metadata.query_start_loc
''',
            '''            import torch.nn.functional as F
            from vllm.distributed import (
                get_tensor_model_parallel_rank,
                tensor_model_parallel_all_gather,
            )
            full_attention = getattr(layer, "_gspo_hf_full_attention", False)
            tp_rank = get_tensor_model_parallel_rank()
            query_start_loc = attn_metadata.query_start_loc
''',
            "Transformers full-head SDPA imports",
        )
        text = _replace_once(
            text,
            '''                padded_query[-query_len:] = query[query_start:query_end]
                result = F.scaled_dot_product_attention(
''',
            '''                padded_query[-query_len:] = query[query_start:query_end]
                if full_attention:
                    padded_query = tensor_model_parallel_all_gather(
                        padded_query.contiguous(), dim=1
                    )
                    dense_key = tensor_model_parallel_all_gather(
                        dense_key.contiguous(), dim=1
                    )
                    dense_value = tensor_model_parallel_all_gather(
                        dense_value.contiguous(), dim=1
                    )
                result = F.scaled_dot_product_attention(
''',
            "Transformers full-head SDPA inputs",
        )
        text = _replace_once(
            text,
            '''                    enable_gqa=self.num_heads != self.num_kv_heads,
                )
                output[query_start:query_end].copy_(
                    result[0, :, -query_len:].transpose(0, 1)
                )
''',
            '''                    enable_gqa=(padded_query.shape[1] != dense_key.shape[1]),
                )
                result = result[0, :, -query_len:].transpose(0, 1)
                if full_attention:
                    head_start = tp_rank * self.num_heads
                    result = result[:, head_start : head_start + self.num_heads]
                output[query_start:query_end].copy_(result)
''',
            "Transformers full-head SDPA output",
        )
    text = text.replace(
        '''                padded_query = tensor_model_parallel_all_gather(
                    padded_query, dim=1
                )
''',
        "",
        1,
    )
    text = text.replace(
        '''                    result[
                        0,
                        tp_rank * self.num_heads : (tp_rank + 1) * self.num_heads,
                        -query_len:,
                    ].transpose(0, 1)
''',
        '''                    result[0, :, -query_len:].transpose(0, 1)
''',
        1,
    )
    if TRAINING_SDPA_MARKER in text:
        return text
    old = '''        if not attn_metadata.use_cascade:
            cu_seqlens_q = attn_metadata.query_start_loc
'''
    new = '''        if getattr(layer, "_gspo_training_sdpa", False):
            import torch.nn.functional as F
            from vllm.distributed import (
                get_tensor_model_parallel_rank,
                tensor_model_parallel_all_gather,
            )
            full_attention = getattr(layer, "_gspo_hf_full_attention", False)
            tp_rank = get_tensor_model_parallel_rank()
            query_start_loc = attn_metadata.query_start_loc
            block_table = attn_metadata.block_table
            block_size = key_cache.shape[1]
            for seq_index in range(attn_metadata.seq_lens.shape[0]):
                query_start = int(query_start_loc[seq_index].item())
                query_end = int(query_start_loc[seq_index + 1].item())
                query_len = query_end - query_start
                seq_len = int(attn_metadata.seq_lens[seq_index].item())
                num_blocks = (seq_len + block_size - 1) // block_size
                block_ids = block_table[seq_index, :num_blocks].long()
                if query_len == seq_len:
                    # Transformers teacher-force attention consumes the K/V
                    # produced by this forward directly, before any KV-cache
                    # layout conversion.
                    dense_key = key[query_start:query_end]
                    dense_value = value[query_start:query_end]
                else:
                    dense_key = key_cache.index_select(0, block_ids).reshape(
                        -1, self.num_kv_heads, self.head_size
                    )[:seq_len]
                    dense_value = value_cache.index_select(0, block_ids).reshape(
                        -1, self.num_kv_heads, self.head_size
                    )[:seq_len]
                padded_query = query.new_zeros(
                    seq_len, self.num_heads, self.head_size
                )
                padded_query[-query_len:] = query[query_start:query_end]
                if full_attention:
                    padded_query = tensor_model_parallel_all_gather(
                        padded_query.contiguous(), dim=1
                    )
                    dense_key = tensor_model_parallel_all_gather(
                        dense_key.contiguous(), dim=1
                    )
                    dense_value = tensor_model_parallel_all_gather(
                        dense_value.contiguous(), dim=1
                    )
                result = F.scaled_dot_product_attention(
                    padded_query.transpose(0, 1).unsqueeze(0),
                    dense_key.transpose(0, 1).unsqueeze(0),
                    dense_value.transpose(0, 1).unsqueeze(0),
                    dropout_p=0.0,
                    is_causal=True,
                    scale=self.scale,
                    enable_gqa=(padded_query.shape[1] != dense_key.shape[1]),
                )
                result = result[0, :, -query_len:].transpose(0, 1)
                if full_attention:
                    head_start = tp_rank * self.num_heads
                    result = result[:, head_start : head_start + self.num_heads]
                output[query_start:query_end].copy_(result)
            return output

        if not attn_metadata.use_cascade:
            cu_seqlens_q = attn_metadata.query_start_loc
'''
    return _replace_once(text, old, new, "training-style decoder SDPA")


def _patch_mrope(text: str) -> str:
    if HF_ROPE_MARKER in text:
        return text
    old = '''        cos_sin_cache = self._match_cos_sin_cache_dtype(query)
        num_tokens = positions.shape[-1]
'''
    new = '''        if getattr(self, "_gspo_hf_forward", False):
            # Match Qwen3VLTextRotaryEmbedding.forward and
            # apply_rotary_pos_emb from Transformers operation-for-operation.
            if positions.ndim == 1:
                positions = positions.unsqueeze(0).expand(3, -1)
            num_tokens = positions.shape[-1]
            inv_freq = 1.0 / (
                self.base
                ** (
                    torch.arange(
                        0, self.rotary_dim, 2, dtype=torch.float32, device="cpu"
                    )
                    / self.rotary_dim
                )
            )
            inv_freq = inv_freq.to(query.device)
            inv_freq_expanded = inv_freq[None, None, :, None].float().expand(
                3, 1, -1, 1
            )
            position_ids_expanded = positions[:, None, None, :].float()
            with torch.autocast(device_type=query.device.type, enabled=False):
                freqs = (
                    inv_freq_expanded.float() @ position_ids_expanded.float()
                ).transpose(2, 3)
                freqs_t = freqs[0]
                for dim, offset in enumerate((1, 2), start=1):
                    length = self.mrope_section[dim] * 3
                    index = slice(offset, length, 3)
                    freqs_t[..., index] = freqs[dim, ..., index]
                emb = torch.cat((freqs_t, freqs_t), dim=-1)
                cos = emb.cos().to(query.dtype).unsqueeze(1)
                sin = emb.sin().to(query.dtype).unsqueeze(1)

            def rotate_half(x):
                x1, x2 = x.chunk(2, dim=-1)
                return torch.cat((-x2, x1), dim=-1)

            query_shape = query.shape
            q = query.view(num_tokens, -1, self.head_size).transpose(0, 1).unsqueeze(0)
            q = (q * cos) + (rotate_half(q) * sin)
            query = q.squeeze(0).transpose(0, 1).reshape(query_shape)

            key_shape = key.shape
            k = key.view(num_tokens, -1, self.head_size).transpose(0, 1).unsqueeze(0)
            k = (k * cos) + (rotate_half(k) * sin)
            key = k.squeeze(0).transpose(0, 1).reshape(key_shape)
            return query, key

        cos_sin_cache = self._match_cos_sin_cache_dtype(query)
        num_tokens = positions.shape[-1]
'''
    if text.count(old) < 1:
        raise RuntimeError("Transformers-style MRoPE: source fragment not found")
    return text.replace(old, new, 1)


def _patch_qwen2_model(text: str) -> str:
    if HF_FINAL_NORM_MARKER not in text:
        old = '''        hidden_states, _ = self.norm(hidden_states, residual)
'''
        new = '''        if getattr(self, "_gspo_unfused_final_norm", False):
            hidden_states = self.norm(hidden_states + residual)
        else:
            hidden_states, _ = self.norm(hidden_states, residual)
'''
        text = _replace_once(
            text, old, new, "Qwen3-VL final residual/RMSNorm ordering"
        )
    if HF_FULL_PROJECTION_MARKER in text:
        return text
    text = _replace_once(
        text,
        '''from vllm.distributed import get_pp_group, get_tensor_model_parallel_world_size
''',
        '''from vllm.distributed import (
    get_pp_group,
    get_tensor_model_parallel_world_size,
    tensor_model_parallel_all_gather,
)
''',
        "Qwen2 full-projection import",
    )
    old = '''    def forward(self, x):
        gate_up, _ = self.gate_up_proj(x)
        x = self.act_fn(gate_up)
        x, _ = self.down_proj(x)
        return x
'''
    new = '''    def forward(self, x):
        if getattr(self, "_gspo_hf_full_projection", False):
            # Reconstruct the Transformers dense projections. This removes the
            # TP-dependent GEMM and reduction order from logprob scoring.
            local_gate, local_up = self.gate_up_proj.weight.chunk(2, dim=0)
            gate_weight = tensor_model_parallel_all_gather(local_gate, dim=0)
            up_weight = tensor_model_parallel_all_gather(local_up, dim=0)
            gate = torch.nn.functional.linear(x, gate_weight)
            up = torch.nn.functional.linear(x, up_weight)
            activated = torch.nn.functional.silu(gate) * up
            down_weight = tensor_model_parallel_all_gather(
                self.down_proj.weight, dim=1
            )
            return torch.nn.functional.linear(activated, down_weight)
        gate_up, _ = self.gate_up_proj(x)
        x = self.act_fn(gate_up)
        x, _ = self.down_proj(x)
        return x
'''
    return _replace_once(text, old, new, "Qwen3-VL full MLP projections")


def _patch_qwen3_full_projection(text: str) -> str:
    if HF_FULL_PROJECTION_MARKER in text:
        return text
    text = _replace_once(
        text,
        '''from vllm.distributed import get_pp_group, get_tensor_model_parallel_world_size
''',
        '''from vllm.distributed import (
    get_pp_group,
    get_tensor_model_parallel_rank,
    get_tensor_model_parallel_world_size,
    tensor_model_parallel_all_gather,
)
''',
        "Qwen3 full-projection imports",
    )
    old = '''        qkv, _ = self.qkv_proj(hidden_states)
        q, k, v = qkv.split([self.q_size, self.kv_size, self.kv_size], dim=-1)
        # Add qk-norm
'''
    new = '''        if getattr(self, "_gspo_hf_full_projection", False):
            local_q, local_k, local_v = self.qkv_proj.weight.split(
                [self.q_size, self.kv_size, self.kv_size], dim=0
            )
            q_weight = tensor_model_parallel_all_gather(local_q, dim=0)
            k_weight = tensor_model_parallel_all_gather(local_k, dim=0)
            v_weight = tensor_model_parallel_all_gather(local_v, dim=0)
            full_q = torch.nn.functional.linear(hidden_states, q_weight)
            full_k = torch.nn.functional.linear(hidden_states, k_weight)
            full_v = torch.nn.functional.linear(hidden_states, v_weight)
            rank = get_tensor_model_parallel_rank()
            q_start = rank * self.q_size
            kv_start = rank * self.kv_size
            q = full_q[..., q_start : q_start + self.q_size]
            k = full_k[..., kv_start : kv_start + self.kv_size]
            v = full_v[..., kv_start : kv_start + self.kv_size]
        else:
            qkv, _ = self.qkv_proj(hidden_states)
            q, k, v = qkv.split([self.q_size, self.kv_size, self.kv_size], dim=-1)
        # Add qk-norm
'''
    text = _replace_once(text, old, new, "Qwen3-VL full QKV projections")
    old = '''        output, _ = self.o_proj(attn_output)
        return output
'''
    new = '''        if getattr(self, "_gspo_hf_full_projection", False):
            full_attn = tensor_model_parallel_all_gather(attn_output, dim=-1)
            full_weight = tensor_model_parallel_all_gather(
                self.o_proj.weight, dim=1
            )
            return torch.nn.functional.linear(full_attn, full_weight)
        output, _ = self.o_proj(attn_output)
        return output
'''
    text = _replace_once(text, old, new, "Qwen3-VL full attention output projection")
    old = '''        logits = self.logits_processor(self.lm_head, hidden_states)
        return logits
'''
    new = '''        if getattr(self, "_gspo_hf_full_projection", False):
            full_weight = tensor_model_parallel_all_gather(
                self.lm_head.weight, dim=0
            )
            return torch.nn.functional.linear(
                hidden_states, full_weight
            )[..., : self.config.vocab_size]
        logits = self.logits_processor(self.lm_head, hidden_states)
        return logits
'''
    return _replace_once(text, old, new, "Qwen3-VL full LM head projection")


def _patch_qwen3(text: str) -> str:
    return _patch_qwen3_full_projection(_patch_qwen3_decoder(text))


def _patch_qwen3_vl(text: str) -> str:
    if QWEN3_VL_MARKER not in text:
        text = _replace_once(text, "from itertools import islice\n", "from itertools import islice\nimport os\n", "qwen3_vl os import")
        old = '''        with self._mark_language_model(vllm_config):
            self.language_model = Qwen3LLMForCausalLM(
                vllm_config=vllm_config.with_hf_config(config.text_config),
                prefix=maybe_prefix(prefix, "language_model"),
            )

'''
        new = '''        with self._mark_language_model(vllm_config):
            self.language_model = Qwen3LLMForCausalLM(
                vllm_config=vllm_config.with_hf_config(config.text_config),
                prefix=maybe_prefix(prefix, "language_model"),
            )

        if (
            os.environ.get("GSPO_VLLM_LOGPROB_PARITY", "false").lower() == "true"
            and quant_config is None
        ):
            for layer in self.language_model.model.layers:
                layer.self_attn.o_proj._gspo_fp32_tp_reduce = True
                layer.mlp.down_proj._gspo_fp32_tp_reduce = True

'''
        text = _replace_once(text, old, new, "Qwen3-VL parity layer selection")
    if HF_FULL_PROJECTION_MARKER not in text and "gspo_parity_modes.update" in text:
        text = _replace_once(
            text,
            '''        if gspo_parity_modes and quant_config is None:
            if "norm" in gspo_parity_modes:
''',
            '''        if gspo_parity_modes and quant_config is None:
            if "hf" in gspo_parity_modes:
                self.language_model._gspo_hf_full_projection = True
            if "norm" in gspo_parity_modes:
''',
            "Qwen3-VL full LM projection selection",
        )
        text = _replace_once(
            text,
            '''            for layer in self.language_model.model.layers:
                if "attention" in gspo_parity_modes:
''',
            '''            for layer in self.language_model.model.layers:
                if "hf" in gspo_parity_modes:
                    layer.self_attn._gspo_hf_full_projection = True
                    layer.self_attn.attn._gspo_hf_full_attention = True
                    layer.mlp._gspo_hf_full_projection = True
                if "attention" in gspo_parity_modes:
''',
            "Qwen3-VL full layer projection selection",
        )
    if "_gspo_hf_full_attention" not in text and HF_FULL_PROJECTION_MARKER in text:
        text = _replace_once(
            text,
            '''                    layer.self_attn._gspo_hf_full_projection = True
                    layer.mlp._gspo_hf_full_projection = True
''',
            '''                    layer.self_attn._gspo_hf_full_projection = True
                    layer.self_attn.attn._gspo_hf_full_attention = True
                    layer.mlp._gspo_hf_full_projection = True
''',
            "Qwen3-VL full-head attention selection",
        )
    if "gspo_parity_modes.update" not in text and PARITY_MODE_MARKER in text:
        old = '''        gspo_parity_mode = os.environ.get(
            "GSPO_VLLM_LOGPROB_PARITY", "false"
        ).lower()
        gspo_parity_modes = {
            mode.strip() for mode in gspo_parity_mode.split(",") if mode.strip()
        }
        if "true" in gspo_parity_modes or "all" in gspo_parity_modes:
            gspo_parity_modes = {"attention", "mlp", "norm"}
        if gspo_parity_modes and quant_config is None:
            for layer in self.language_model.model.layers:
                if "attention" in gspo_parity_modes:
                    layer.self_attn.o_proj._gspo_fp32_tp_reduce = True
                if "mlp" in gspo_parity_modes:
                    layer.mlp.down_proj._gspo_fp32_tp_reduce = True
                if "norm" in gspo_parity_modes:
                    layer._gspo_unfused_residual_norm = True
                if "sdpa" in gspo_parity_modes:
                    layer.self_attn.attn._gspo_training_sdpa = True
                if "rope" in gspo_parity_modes:
                    layer.self_attn.rotary_emb.forward = (
                        layer.self_attn.rotary_emb.forward_native
                    )

'''
        new = '''        gspo_parity_mode = os.environ.get(
            "GSPO_VLLM_LOGPROB_PARITY", "false"
        ).lower()
        gspo_parity_modes = {
            mode.strip() for mode in gspo_parity_mode.split(",") if mode.strip()
        }
        if "true" in gspo_parity_modes or "all" in gspo_parity_modes:
            gspo_parity_modes = {"hf"}
        if "hf" in gspo_parity_modes:
            gspo_parity_modes.update({"norm", "sdpa", "rope", "activation"})
        if gspo_parity_modes and quant_config is None:
            if "hf" in gspo_parity_modes:
                self.language_model._gspo_hf_full_projection = True
            if "norm" in gspo_parity_modes:
                self.language_model.model._gspo_unfused_final_norm = True
                self.language_model.model.norm.forward = (
                    self.language_model.model.norm.forward_native
                )
            for layer in self.language_model.model.layers:
                if "hf" in gspo_parity_modes:
                    layer.self_attn._gspo_hf_full_projection = True
                    layer.self_attn.attn._gspo_hf_full_attention = True
                    layer.mlp._gspo_hf_full_projection = True
                if "attention" in gspo_parity_modes:
                    layer.self_attn.o_proj._gspo_fp32_tp_reduce = True
                if "mlp" in gspo_parity_modes:
                    layer.mlp.down_proj._gspo_fp32_tp_reduce = True
                if "norm" in gspo_parity_modes:
                    layer._gspo_unfused_residual_norm = True
                    layer.input_layernorm.forward = layer.input_layernorm.forward_native
                    layer.post_attention_layernorm.forward = (
                        layer.post_attention_layernorm.forward_native
                    )
                    layer.self_attn.q_norm.forward = layer.self_attn.q_norm.forward_native
                    layer.self_attn.k_norm.forward = layer.self_attn.k_norm.forward_native
                if "sdpa" in gspo_parity_modes:
                    layer.self_attn.attn._gspo_training_sdpa = True
                if "rope" in gspo_parity_modes:
                    layer.self_attn.rotary_emb._gspo_hf_forward = True
                    layer.self_attn.rotary_emb.forward = (
                        layer.self_attn.rotary_emb.forward_native
                    )
                if "activation" in gspo_parity_modes:
                    layer.mlp.act_fn.forward = layer.mlp.act_fn.forward_native

'''
        text = _replace_once(text, old, new, "Qwen3-VL parity scorer upgrade")
    if PARITY_MODE_MARKER not in text:
        old_v1 = '''        gspo_parity_mode = os.environ.get(
            "GSPO_VLLM_LOGPROB_PARITY", "false"
        ).lower()
        if gspo_parity_mode == "true":
            gspo_parity_mode = "all"
        if gspo_parity_mode in {"attention", "mlp", "all"} and quant_config is None:
            for layer in self.language_model.model.layers:
                if gspo_parity_mode in {"attention", "all"}:
                    layer.self_attn.o_proj._gspo_fp32_tp_reduce = True
                if gspo_parity_mode in {"mlp", "all"}:
                    layer.mlp.down_proj._gspo_fp32_tp_reduce = True

'''
        old_boolean = '''        if (
            os.environ.get("GSPO_VLLM_LOGPROB_PARITY", "false").lower() == "true"
            and quant_config is None
        ):
            for layer in self.language_model.model.layers:
                layer.self_attn.o_proj._gspo_fp32_tp_reduce = True
                layer.mlp.down_proj._gspo_fp32_tp_reduce = True

'''
        old = old_v1 if old_v1 in text else old_boolean
        new = '''        gspo_parity_mode = os.environ.get(
            "GSPO_VLLM_LOGPROB_PARITY", "false"
        ).lower()
        gspo_parity_modes = {
            mode.strip() for mode in gspo_parity_mode.split(",") if mode.strip()
        }
        if "true" in gspo_parity_modes or "all" in gspo_parity_modes:
            gspo_parity_modes = {"hf"}
        if "hf" in gspo_parity_modes:
            gspo_parity_modes.update({"norm", "sdpa", "rope", "activation"})
        if gspo_parity_modes and quant_config is None:
            if "hf" in gspo_parity_modes:
                self.language_model._gspo_hf_full_projection = True
            if "norm" in gspo_parity_modes:
                self.language_model.model._gspo_unfused_final_norm = True
                self.language_model.model.norm.forward = (
                    self.language_model.model.norm.forward_native
                )
            for layer in self.language_model.model.layers:
                if "hf" in gspo_parity_modes:
                    layer.self_attn._gspo_hf_full_projection = True
                    layer.self_attn.attn._gspo_hf_full_attention = True
                    layer.mlp._gspo_hf_full_projection = True
                if "attention" in gspo_parity_modes:
                    layer.self_attn.o_proj._gspo_fp32_tp_reduce = True
                if "mlp" in gspo_parity_modes:
                    layer.mlp.down_proj._gspo_fp32_tp_reduce = True
                if "norm" in gspo_parity_modes:
                    layer._gspo_unfused_residual_norm = True
                    layer.input_layernorm.forward = layer.input_layernorm.forward_native
                    layer.post_attention_layernorm.forward = (
                        layer.post_attention_layernorm.forward_native
                    )
                    layer.self_attn.q_norm.forward = layer.self_attn.q_norm.forward_native
                    layer.self_attn.k_norm.forward = layer.self_attn.k_norm.forward_native
                if "sdpa" in gspo_parity_modes:
                    layer.self_attn.attn._gspo_training_sdpa = True
                if "rope" in gspo_parity_modes:
                    layer.self_attn.rotary_emb._gspo_hf_forward = True
                    layer.self_attn.rotary_emb.forward = (
                        layer.self_attn.rotary_emb.forward_native
                    )
                if "activation" in gspo_parity_modes:
                    layer.mlp.act_fn.forward = layer.mlp.act_fn.forward_native

'''
        text = _replace_once(text, old, new, "Qwen3-VL parity mode selection")
    if TRAINING_SDPA_MARKER not in text:
        old = '''                if "norm" in gspo_parity_modes:
                    layer._gspo_unfused_residual_norm = True

'''
        new = '''                if "norm" in gspo_parity_modes:
                    layer._gspo_unfused_residual_norm = True
                if "sdpa" in gspo_parity_modes:
                    layer.self_attn.attn._gspo_training_sdpa = True
                if "rope" in gspo_parity_modes:
                    layer.self_attn.rotary_emb.forward = (
                        layer.self_attn.rotary_emb.forward_native
                    )

'''
        text = _replace_once(text, old, new, "Qwen3-VL training SDPA selection")
    if ROPE_MODE_MARKER not in text:
        old = '''                if "sdpa" in gspo_parity_modes:
                    layer.self_attn.attn._gspo_training_sdpa = True

'''
        new = '''                if "sdpa" in gspo_parity_modes:
                    layer.self_attn.attn._gspo_training_sdpa = True
                if "rope" in gspo_parity_modes:
                    layer.self_attn.rotary_emb.forward = (
                        layer.self_attn.rotary_emb.forward_native
                    )

'''
        text = _replace_once(text, old, new, "Qwen3-VL training RoPE selection")
    if TRACE_MARKER in text:
        pass
    else:
        old = '''                if "norm" in gspo_parity_modes:
                    layer._gspo_unfused_residual_norm = True
                if "sdpa" in gspo_parity_modes:
                    layer.self_attn.attn._gspo_training_sdpa = True
                if "rope" in gspo_parity_modes:
                    layer.self_attn.rotary_emb.forward = (
                        layer.self_attn.rotary_emb.forward_native
                    )

'''
        new = '''                if "norm" in gspo_parity_modes:
                    layer._gspo_unfused_residual_norm = True
                if "sdpa" in gspo_parity_modes:
                    layer.self_attn.attn._gspo_training_sdpa = True
                if "rope" in gspo_parity_modes:
                    layer.self_attn.rotary_emb.forward = (
                        layer.self_attn.rotary_emb.forward_native
                    )

        trace_dir = os.environ.get("GSPO_VLLM_PARITY_TRACE_DIR")
        if trace_dir and parallel_state.get_tensor_model_parallel_rank() == 0:
            from pathlib import Path

            trace_root = Path(trace_dir)
            trace_root.mkdir(parents=True, exist_ok=True)
            trace_counts = {}
            trace_rows = int(os.environ.get("GSPO_VLLM_PARITY_TRACE_ROWS", "0"))

            def register_trace(module, name):
                def save_trace(_module, _inputs, output):
                    tensor = output[0] if isinstance(output, tuple) else output
                    if not isinstance(tensor, torch.Tensor):
                        return
                    if trace_rows and tensor.shape[0] != trace_rows:
                        return
                    index = trace_counts.get(name, 0)
                    trace_counts[name] = index + 1
                    torch.save(
                        tensor.detach().float().cpu(),
                        trace_root / f"{name}.{index:03d}.pt",
                    )

                module.register_forward_hook(save_trace)

            register_trace(self.language_model.model.embed_tokens, "embedding")
            for index, layer in enumerate(self.language_model.model.layers):
                register_trace(layer.input_layernorm, f"layer_{index:02d}.input_norm")
                register_trace(layer.self_attn.o_proj, f"layer_{index:02d}.attention_row")
                register_trace(
                    layer.post_attention_layernorm,
                    f"layer_{index:02d}.post_attention_norm",
                )
                register_trace(layer.mlp.down_proj, f"layer_{index:02d}.mlp_row")
            register_trace(self.language_model.model.norm, "final_norm")
            register_trace(self.language_model.lm_head, "lm_head")

'''
        text = _replace_once(text, old, new, "Qwen3-VL parity tracing")
    if TRACE_DETAIL_MARKER in text:
        return text
    old = '''                register_trace(layer.input_layernorm, f"layer_{index:02d}.input_norm")
                register_trace(layer.self_attn.o_proj, f"layer_{index:02d}.attention_row")
'''
    new = '''                register_trace(layer.input_layernorm, f"layer_{index:02d}.input_norm")
                register_trace(layer.self_attn.qkv_proj, f"layer_{index:02d}.qkv")
                register_trace(layer.self_attn.q_norm, f"layer_{index:02d}.q_norm")
                register_trace(layer.self_attn.k_norm, f"layer_{index:02d}.k_norm")
                register_trace(layer.self_attn.attn, f"layer_{index:02d}.attention_core")
                register_trace(layer.self_attn.o_proj, f"layer_{index:02d}.attention_row")
'''
    return _replace_once(text, old, new, "Qwen3-VL detailed attention tracing")


def _vllm_root() -> Path:
    spec = importlib.util.find_spec("vllm")
    if spec is None or spec.submodule_search_locations is None:
        raise RuntimeError("vLLM is not installed in the selected Python environment")
    return Path(next(iter(spec.submodule_search_locations)))


def apply_patch(check: bool = False) -> list[Path]:
    root = _vllm_root()
    transforms = {
        root / "v1/sample/sampler.py": _patch_sampler,
        root / "v1/sample/ops/topk_topp_sampler.py": _patch_topk_topp,
        root / "v1/worker/gpu/sample/prompt_logprob.py": _patch_prompt_logprobs,
        root / "model_executor/layers/linear.py": _patch_linear,
        root / "v1/attention/backends/flash_attn.py": _patch_flash_attention,
        root / "model_executor/layers/rotary_embedding/mrope.py": _patch_mrope,
        root / "model_executor/models/qwen2.py": _patch_qwen2_model,
        root / "model_executor/models/qwen3.py": _patch_qwen3,
        root / "model_executor/models/qwen3_vl.py": _patch_qwen3_vl,
    }
    changed: list[Path] = []
    for path, transform in transforms.items():
        original = path.read_text(encoding="utf-8")
        patched = transform(original)
        if patched != original:
            changed.append(path)
            if not check:
                path.write_text(patched, encoding="utf-8")
    if check and changed:
        raise RuntimeError("vLLM patch is not applied: " + ", ".join(map(str, changed)))
    return changed


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    changed = apply_patch(check=args.check)
    action = "checked" if args.check else "patched"
    print(f"vLLM GSPO parity {action}; changed_files={len(changed)}")


if __name__ == "__main__":
    main()
