"""Task-routed KL retention for FINAR SFT.

Only samples selected by the existing FINAR task route (default task ==
"generation") use this objective. Generation samples skip SFT cross entropy
entirely and optimize only a GRPO-style k3 KL penalty against the frozen base
model. All other tasks keep the normal ms-swift SFT cross-entropy loss.

GPU layout on the current 8-GPU node:
  - GPU 0..5: student full-parameter SFT, 3 DP replicas x SP2
  - GPU 6: frozen base/reference vLLM server
  - GPU 7: benchmark judge

For an SP2 pair, both ranks share the same sample. Only SP rank 0 queries the
reference server, then broadcasts the reference token log-probabilities to the
other SP rank. Thus three DP replicas create at most three unique reference
requests at once, not six.
"""

from __future__ import annotations

import atexit
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


try:
    from swift.callbacks import TrainerCallback, callbacks_map
except ImportError:  # Pure-python unit tests may import without ms-swift.
    class TrainerCallback:  # type: ignore[no-redef]
        def __init__(self, args, trainer):
            self.args = args
            self.trainer = trainer

    callbacks_map: dict[str, type] = {}


_REFERENCE_PROCESS: subprocess.Popen | None = None
_REFERENCE_LOG_HANDLE = None


def _env_float(name: str, default: float) -> float:
    return float(os.environ.get(name, str(default)))


def _env_int(name: str, default: int) -> int:
    return int(os.environ.get(name, str(default)))


def _reference_url() -> str:
    explicit = os.environ.get("SFT_REF_URL")
    if explicit:
        return explicit.rstrip("/")
    return f"http://127.0.0.1:{_env_int('SFT_REF_PORT', 8003)}"


def _reference_model_name() -> str:
    return os.environ.get("SFT_REF_SERVED_MODEL", "qwen4-ref")


def _local_rank() -> int:
    return int(os.environ.get("LOCAL_RANK", "0"))


def _http_json(url: str, payload: dict[str, Any] | None = None, *, timeout: float = 5.0) -> dict[str, Any]:
    data = None if payload is None else json.dumps(payload, separators=(",", ":")).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="GET" if data is None else "POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def _reference_ready() -> bool:
    try:
        payload = _http_json(f"{_reference_url()}/v1/models", timeout=2.0)
    except (OSError, ValueError, urllib.error.URLError):
        return False
    wanted = _reference_model_name()
    return any(str(item.get("id", "")) == wanted for item in payload.get("data", []))


def _cleanup_reference_server() -> None:
    global _REFERENCE_PROCESS, _REFERENCE_LOG_HANDLE
    process = _REFERENCE_PROCESS
    _REFERENCE_PROCESS = None
    if process is not None and process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
    if _REFERENCE_LOG_HANDLE is not None:
        try:
            _REFERENCE_LOG_HANDLE.close()
        finally:
            _REFERENCE_LOG_HANDLE = None


def _start_reference_server(trainer) -> None:
    """Start one frozen base-model vLLM service per node on physical GPU 6."""
    global _REFERENCE_PROCESS, _REFERENCE_LOG_HANDLE
    if _local_rank() != 0 or _reference_ready():
        return

    model = os.environ.get("SFT_REF_MODEL") or os.environ.get("BASE_MODEL")
    if not model:
        raise RuntimeError("SFT KL retention requires SFT_REF_MODEL or BASE_MODEL")

    log_dir = Path(str(trainer.args.output_dir)) / "reference"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / f"reference_node_{os.environ.get('NODE_RANK', '0')}.log"
    _REFERENCE_LOG_HANDLE = log_path.open("a", encoding="utf-8", buffering=1)

    env = os.environ.copy()
    env["CUDA_VISIBLE_DEVICES"] = os.environ.get("SFT_REF_GPU", "6")
    env["WANDB_DISABLED"] = "true"
    env["WANDB_MODE"] = "disabled"
    port = str(_env_int("SFT_REF_PORT", 8003))
    command = [
        sys.executable,
        "-m",
        "vllm.entrypoints.openai.api_server",
        "--model",
        model,
        "--served-model-name",
        _reference_model_name(),
        "--host",
        "127.0.0.1",
        "--port",
        port,
        "--dtype",
        "bfloat16",
        "--max-model-len",
        str(_env_int("SFT_REF_MAX_MODEL_LEN", 49153)),
        "--tensor-parallel-size",
        "1",
        "--gpu-memory-utilization",
        str(_env_float("SFT_REF_GPU_MEMORY_UTILIZATION", 0.85)),
        "--max-num-seqs",
        str(_env_int("SFT_REF_MAX_NUM_SEQS", 8)),
        "--max-logprobs",
        "1",
        "--enforce-eager",
        "--generation-config",
        "vllm",
    ]
    _REFERENCE_PROCESS = subprocess.Popen(
        command,
        env=env,
        stdout=_REFERENCE_LOG_HANDLE,
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )
    atexit.register(_cleanup_reference_server)


def _ensure_reference_server(trainer) -> None:
    _start_reference_server(trainer)
    deadline = time.monotonic() + _env_float("SFT_REF_START_TIMEOUT", 600.0)
    while time.monotonic() < deadline:
        if _reference_ready():
            return
        if _local_rank() == 0 and _REFERENCE_PROCESS is not None and _REFERENCE_PROCESS.poll() is not None:
            raise RuntimeError(
                "SFT reference server exited before becoming ready; see "
                f"{Path(str(trainer.args.output_dir)) / 'reference'}"
            )
        time.sleep(2)
    raise RuntimeError(f"SFT reference server did not become ready at {_reference_url()}")


def _reference_prompt_logps(input_ids: list[int], target_token_positions: list[int]) -> list[float]:
    """Return base log p(token_i | token_<i) at exact prompt token positions."""
    if not target_token_positions:
        raise ValueError("generation KL requires at least one supervised assistant token")
    payload = {
        "model": _reference_model_name(),
        "prompt": input_ids,
        "max_tokens": 1,
        "temperature": 0.0,
        "logprobs": 1,
        "echo": True,
    }
    timeout = _env_float("SFT_REF_REQUEST_TIMEOUT", 300.0)
    last_error: Exception | None = None
    for attempt in range(3):
        try:
            response = _http_json(f"{_reference_url()}/v1/completions", payload, timeout=timeout)
            choices = response.get("choices") or []
            if not choices:
                raise RuntimeError(f"reference response has no choices: {response}")
            token_logprobs = (choices[0].get("logprobs") or {}).get("token_logprobs")
            if not isinstance(token_logprobs, list) or len(token_logprobs) < len(input_ids):
                raise RuntimeError(
                    "reference server did not return prompt token logprobs: "
                    f"got={None if token_logprobs is None else len(token_logprobs)} expected>={len(input_ids)}"
                )
            result: list[float] = []
            for position in target_token_positions:
                value = token_logprobs[position]
                if value is None:
                    raise RuntimeError(f"reference logprob is None at supervised token position {position}")
                result.append(float(value))
            return result
        except (OSError, ValueError, RuntimeError, urllib.error.URLError) as exc:
            last_error = exc
            if attempt < 2:
                time.sleep(1 + attempt)
    raise RuntimeError(f"reference logprob request failed after retries: {last_error}")


def _sp_state():
    from swift.sequence_parallel import sequence_parallel

    world_size = int(getattr(sequence_parallel, "world_size", 1) or 1)
    sp_world_size = int(getattr(sequence_parallel, "sp_world_size", 1) or 1)
    rp_world_size = int(getattr(sequence_parallel, "rp_world_size", 1) or 1)
    sp_rank = int(getattr(sequence_parallel, "sp_rank", 0) or 0)
    return sequence_parallel, world_size, sp_world_size, rp_world_size, sp_rank


def _gather_rolled_labels(local_labels):
    """Undo only the SP split; labels remain in ms-swift's shifted form.

    ms-swift sequence parallel prepares SFT labels as:
      pad -> roll(-1) -> split(SP)
    The model logits on each SP rank align directly with these rolled labels.
    """
    sequence_parallel, world_size, _, rp_world_size, _ = _sp_state()
    if world_size <= 1:
        return local_labels
    if rp_world_size != 1:
        raise RuntimeError(
            "generation KL currently supports Ulysses sequence parallel only (rp_world_size=1); "
            f"got rp_world_size={rp_world_size}"
        )
    return sequence_parallel.gather(local_labels.contiguous(), dim=-1)


def _reference_logps_for_local_labels(input_ids, local_labels):
    """Get reference logps aligned to this SP rank's rolled local labels."""
    import torch
    import torch.distributed as dist

    sequence_parallel, world_size, sp_world_size, rp_world_size, sp_rank = _sp_state()
    if rp_world_size != 1:
        raise RuntimeError("generation KL does not support ring parallel retention batches")

    full_labels = _gather_rolled_labels(local_labels)
    input_length = int(input_ids.shape[1])
    local_length = int(local_labels.shape[-1])

    # Rolled label position p supervises the token at original prompt position p+1.
    global_prediction_positions = torch.nonzero(full_labels[0].ne(-100), as_tuple=False).flatten()
    global_prediction_positions = global_prediction_positions[
        global_prediction_positions.lt(max(0, input_length - 1))
    ]
    if global_prediction_positions.numel() == 0:
        raise RuntimeError("task=generation has no supervised assistant tokens after SP label preparation")

    target_token_positions = global_prediction_positions + 1
    reference_by_prediction_position = torch.zeros(
        input_length,
        dtype=torch.float32,
        device=input_ids.device,
    )

    if world_size <= 1 or sp_rank == 0:
        values = _reference_prompt_logps(
            input_ids[0].detach().cpu().tolist(),
            [int(value) for value in target_token_positions.detach().cpu().tolist()],
        )
        reference_by_prediction_position.index_copy_(
            0,
            global_prediction_positions.to(reference_by_prediction_position.device),
            torch.tensor(values, dtype=torch.float32, device=reference_by_prediction_position.device),
        )

    if world_size > 1:
        group = sequence_parallel.sp_group
        if group is None:
            raise RuntimeError("sequence parallel is enabled but sp_group is unavailable")
        if hasattr(dist, "get_global_rank"):
            source_global_rank = int(dist.get_global_rank(group, 0))
        else:
            source_global_rank = int(dist.get_rank()) - sp_rank
        dist.broadcast(reference_by_prediction_position, src=source_global_rank, group=group)

    local_prediction_positions = torch.nonzero(local_labels[0].ne(-100), as_tuple=False).flatten()
    global_offset = sp_rank * local_length if sp_world_size > 1 else 0
    local_global_positions = local_prediction_positions + global_offset
    valid = local_global_positions.lt(max(0, input_length - 1))
    local_prediction_positions = local_prediction_positions[valid]
    local_global_positions = local_global_positions[valid]

    target_ids = local_labels[0].index_select(0, local_prediction_positions).long()
    reference_logps = reference_by_prediction_position.index_select(0, local_global_positions.long())
    return local_prediction_positions, target_ids, reference_logps


def _generation_kl_loss(model, inputs: dict[str, Any], trainer, *, return_outputs: bool = False):
    """Compute task=generation k3 KL only; cross entropy is never evaluated."""
    import torch
    import torch.nn.functional as F

    route = getattr(trainer, "_finar_kl_route", {}) or {}
    if str(route.get("modality") or "text") != "text":
        raise RuntimeError(
            "task=generation KL currently requires text-only samples; multimodal reference scoring "
            "needs image/video inputs in addition to token ids"
        )

    input_ids = inputs.get("input_ids")
    labels = inputs.get("labels")
    if not torch.is_tensor(input_ids) or not torch.is_tensor(labels):
        raise RuntimeError("generation KL requires tensor input_ids and labels")
    if input_ids.ndim != 2 or labels.ndim != 2 or int(input_ids.shape[0]) != 1 or int(labels.shape[0]) != 1:
        raise RuntimeError("generation KL requires per_device_train_batch_size=1")

    max_length = _env_int("SFT_KL_MAX_LENGTH", 0)
    if max_length > 0 and int(input_ids.shape[1]) > max_length:
        raise RuntimeError(
            f"task=generation sequence length {int(input_ids.shape[1])} exceeds SFT_KL_MAX_LENGTH={max_length}"
        )

    local_prediction_positions, target_ids, reference_logps = _reference_logps_for_local_labels(input_ids, labels)

    # Do not pass labels: generation batches have exactly zero CE term.
    allowed_keys = {
        "input_ids",
        "attention_mask",
        "position_ids",
        "pixel_values",
        "pixel_values_videos",
        "image_grid_thw",
        "video_grid_thw",
        "mm_token_type_ids",
        "token_type_ids",
        "text_position_ids",
    }
    forward_inputs = {key: value for key, value in inputs.items() if key in allowed_keys}
    forward_inputs["use_cache"] = False
    # Qwen3-VL applies this after ms-swift splits hidden states for the SP rank.
    # Passing an empty tensor is intentional: every SP rank must still execute
    # the forward/attention collectives even if its half has zero assistant tokens.
    forward_inputs["logits_to_keep"] = local_prediction_positions
    outputs = model(**forward_inputs)
    logits = getattr(outputs, "logits", None)
    if logits is None and isinstance(outputs, (tuple, list)) and outputs:
        logits = outputs[0]
    if not torch.is_tensor(logits):
        raise RuntimeError("generation KL forward did not return logits")
    if logits.ndim != 3 or int(logits.shape[0]) != 1 or int(logits.shape[1]) != int(target_ids.numel()):
        raise RuntimeError(
            "generation KL logits/label alignment mismatch: "
            f"logits={tuple(logits.shape)} targets={int(target_ids.numel())}"
        )

    if target_ids.numel() > 0:
        student_logps = F.log_softmax(logits[0].float(), dim=-1).gather(1, target_ids[:, None]).squeeze(1)
        if student_logps.shape != reference_logps.shape:
            raise RuntimeError(
                "generation KL student/reference shape mismatch: "
                f"{tuple(student_logps.shape)} vs {tuple(reference_logps.shape)}"
            )
        # Same k3 form commonly used for GRPO reference KL.
        log_ratio = (reference_logps.detach() - student_logps).clamp(min=-20.0, max=20.0)
        per_token_kl = torch.exp(log_ratio) - log_ratio - 1.0
        local_kl_sum = per_token_kl.sum()
        local_token_count = torch.tensor(float(per_token_kl.numel()), device=local_kl_sum.device)
    else:
        # logits.sum() keeps the zero connected to this rank's forward graph.
        local_kl_sum = logits.float().sum() * 0.0
        local_token_count = torch.zeros((), dtype=torch.float32, device=logits.device)

    # Normalize over all assistant tokens in this unique SP sample. ms-swift's
    # own GatherLoss multiplies SP gradients by world size to compensate rank
    # averaging; do the same for this custom scalar loss.
    sequence_parallel, world_size, sp_world_size, _, _ = _sp_state()
    total_token_count = local_token_count.detach().clone()
    if world_size > 1:
        import torch.distributed as dist

        dist.all_reduce(total_token_count, op=dist.ReduceOp.SUM, group=sequence_parallel.sp_group)
    if float(total_token_count.item()) <= 0:
        raise RuntimeError("task=generation produced zero KL tokens across the SP group")

    sp_scale = float(sp_world_size if world_size > 1 else 1)
    beta = _env_float("SFT_KL_BETA", 1.0)
    loss = local_kl_sum * (sp_scale / total_token_count) * beta

    trainer._finar_last_kl = {
        "task": str(getattr(trainer, "_finar_current_task", "")),
        "local_tokens": int(local_token_count.item()),
        "group_tokens": int(total_token_count.item()),
        "weighted_local_loss": float(loss.detach().item()),
        "beta": beta,
        "ce": 0.0,
    }
    return (loss, outputs) if return_outputs else loss


def _current_task_from_plan(trainer) -> tuple[str, bool]:
    """Read the current task directly from the plan tracker when available."""
    tracker = getattr(trainer, "_finar_plan_tracker", None)
    if tracker is not None:
        try:
            entry = tracker.current_entry()
        except (AttributeError, AssertionError):
            entry = None
        if entry is not None:
            task = str(entry.get("task") or "")
            try:
                from scripts.sft.swift_sft_plugin import use_kl_for_task
            except ImportError:
                use_kl = task == "generation"
            else:
                use_kl = use_kl_for_task(task)
            return task, bool(use_kl)
    task = str(getattr(trainer, "_finar_current_task", "") or "")
    return task, bool(getattr(trainer, "_finar_use_kl", False))


class FinarKLRetentionCallback(TrainerCallback):
    """Replace CE with frozen-base KL only for task == generation."""

    def __init__(self, args, trainer):
        super().__init__(args, trainer)
        self._owns_reference = _local_rank() == 0
        _ensure_reference_server(trainer)
        original_compute_loss = trainer.compute_loss

        def kl_routed_compute_loss(model, inputs, *compute_args, **compute_kwargs):
            task, use_kl = _current_task_from_plan(trainer)
            trainer._finar_current_task = task
            trainer._finar_use_kl = use_kl
            if not use_kl:
                return original_compute_loss(model, inputs, *compute_args, **compute_kwargs)
            return_outputs = bool(compute_kwargs.pop("return_outputs", False))
            return _generation_kl_loss(model, inputs, trainer, return_outputs=return_outputs)

        trainer.compute_loss = kl_routed_compute_loss

    def on_train_begin(self, args, state, control, **kwargs):
        if state.is_world_process_zero:
            print(
                "INFO     | >> kl_retention tasks="
                f"{os.environ.get('SFT_KL_TASKS', 'generation')} objective=kl_only ce=0 "
                f"beta={_env_float('SFT_KL_BETA', 1.0):g} reference={_reference_url()}",
                flush=True,
            )
        return control

    def on_train_end(self, args, state, control, **kwargs):
        if self._owns_reference:
            _cleanup_reference_server()
        return control


callbacks_map["finar_kl"] = FinarKLRetentionCallback
