"""Task-routed KL retention for SFT.

Only samples selected by the existing FINAR task route (default task ==
"generation") use this loss.  Generation samples skip SFT cross entropy and
optimize only a GRPO-style k3 KL distance to the frozen base model.

The reference model is served on the otherwise-unused GPU 6.  Within each
sequence-parallel group only SP rank 0 requests reference log-probabilities;
the result is broadcast to the partner rank, so SP2 with three DP replicas
creates at most three concurrent reference requests per node.
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
from contextlib import contextmanager
from pathlib import Path
from typing import Any


try:
    from swift.callbacks import TrainerCallback, callbacks_map
except ImportError:  # Pure-python tests may import the plugin without ms-swift.
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
        str(_env_int("SFT_REF_MAX_MODEL_LEN", 49152)),
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


def _reference_prompt_logps(input_ids: list[int], target_positions: list[int]) -> list[float]:
    """Score exact pre-tokenized prompt tokens with the frozen base model."""
    if not target_positions:
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
            logprobs = (choices[0].get("logprobs") or {}).get("token_logprobs")
            if not isinstance(logprobs, list) or len(logprobs) < len(input_ids):
                raise RuntimeError(
                    "reference server did not return prompt token logprobs: "
                    f"got={None if logprobs is None else len(logprobs)} expected>={len(input_ids)}"
                )
            result: list[float] = []
            for position in target_positions:
                value = logprobs[position]
                if value is None:
                    raise RuntimeError(f"reference logprob is None at supervised token position {position}")
                result.append(float(value))
            return result
        except (OSError, ValueError, RuntimeError, urllib.error.URLError) as exc:
            last_error = exc
            if attempt < 2:
                time.sleep(1 + attempt)
    raise RuntimeError(f"reference logprob request failed after retries: {last_error}")


def _sp_group_info():
    """Return (process_group, local_sp_rank, source_global_rank) when SP is active."""
    try:
        import torch.distributed as dist
        from swift.sequence_parallel import sequence_parallel

        if not (dist.is_available() and dist.is_initialized()):
            return None, 0, 0
        group = getattr(sequence_parallel, "sp_group", None)
        world_size = int(getattr(sequence_parallel, "world_size", 1) or 1)
        if group is None or world_size <= 1:
            return None, 0, dist.get_rank()
        local_rank = int(dist.get_rank(group))
        if hasattr(dist, "get_global_rank"):
            source_global_rank = int(dist.get_global_rank(group, 0))
        else:
            source_global_rank = int(dist.get_rank()) - local_rank
        return group, local_rank, source_global_rank
    except (ImportError, AttributeError, RuntimeError, ValueError):
        return None, 0, 0


def _reference_logps_for_sp(input_ids, target_positions, *, device):
    import torch
    import torch.distributed as dist

    positions = [int(value) for value in target_positions.detach().cpu().tolist()]
    group, sp_rank, source_global_rank = _sp_group_info()
    if group is None:
        values = _reference_prompt_logps(input_ids[0].detach().cpu().tolist(), positions)
        return torch.tensor(values, dtype=torch.float32, device=device)

    result = torch.empty(len(positions), dtype=torch.float32, device=device)
    if sp_rank == 0:
        values = _reference_prompt_logps(input_ids[0].detach().cpu().tolist(), positions)
        result.copy_(torch.tensor(values, dtype=torch.float32, device=device))
    dist.broadcast(result, src=source_global_rank, group=group)
    return result


@contextmanager
def _suspend_sequence_parallel():
    """Run a short text-only retention forward on one GPU per SP rank."""
    try:
        from swift.sequence_parallel import sequence_parallel
    except ImportError:
        yield
        return
    original_world_size = getattr(sequence_parallel, "world_size", 1)
    if original_world_size is None or int(original_world_size) <= 1:
        yield
        return
    sequence_parallel.world_size = 1
    try:
        yield
    finally:
        sequence_parallel.world_size = original_world_size


def _generation_kl_loss(model, inputs: dict[str, Any], trainer, *, return_outputs: bool = False):
    """Compute generation-only k3 KL; no cross-entropy term is evaluated."""
    import torch
    import torch.nn.functional as F

    route = getattr(trainer, "_finar_kl_route", {}) or {}
    if str(route.get("modality") or "text") != "text":
        raise RuntimeError(
            "task=generation KL currently requires text-only samples because the reference "
            "server receives exact input_ids without multimodal tensors"
        )

    input_ids = inputs.get("input_ids")
    labels = inputs.get("labels")
    if not torch.is_tensor(input_ids) or not torch.is_tensor(labels):
        raise RuntimeError("generation KL requires tensor input_ids and labels")
    if input_ids.ndim != 2 or labels.ndim != 2 or int(input_ids.shape[0]) != 1 or int(labels.shape[0]) != 1:
        raise RuntimeError("generation KL currently requires per_device_train_batch_size=1")

    target_positions = torch.nonzero(labels[0].ne(-100), as_tuple=False).flatten()
    target_positions = target_positions[target_positions.gt(0)]
    if target_positions.numel() == 0:
        raise RuntimeError("task=generation has no supervised assistant tokens after masking")
    prediction_positions = target_positions - 1
    target_ids = labels[0].index_select(0, target_positions).long()

    max_length = _env_int("SFT_KL_MAX_LENGTH", 0)
    if max_length > 0 and int(input_ids.shape[1]) > max_length:
        raise RuntimeError(
            f"task=generation sequence length {int(input_ids.shape[1])} exceeds SFT_KL_MAX_LENGTH={max_length}"
        )

    reference_logps = _reference_logps_for_sp(input_ids, target_positions, device=input_ids.device)

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
    }
    forward_inputs = {key: value for key, value in inputs.items() if key in allowed_keys}
    forward_inputs["logits_to_keep"] = prediction_positions
    forward_inputs["use_cache"] = False

    with _suspend_sequence_parallel():
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

    student_logps = F.log_softmax(logits[0].float(), dim=-1).gather(1, target_ids[:, None]).squeeze(1)
    if student_logps.shape != reference_logps.shape:
        raise RuntimeError(
            f"generation KL student/reference shape mismatch: {tuple(student_logps.shape)} vs {tuple(reference_logps.shape)}"
        )

    # k3 estimator used by GRPO-style KL monitoring: exp(d) - d - 1,
    # d = log p_ref - log p_student.  Clamp only to prevent overflow.
    log_ratio = (reference_logps.detach() - student_logps).clamp(min=-20.0, max=20.0)
    per_token_kl = torch.exp(log_ratio) - log_ratio - 1.0
    beta = _env_float("SFT_KL_BETA", 1.0)
    loss = per_token_kl.mean() * beta

    trainer._finar_last_kl = {
        "task": str(getattr(trainer, "_finar_current_task", "")),
        "tokens": int(target_ids.numel()),
        "kl": float(per_token_kl.detach().mean().item()),
        "weighted_kl": float(loss.detach().item()),
        "beta": beta,
        "ce": 0.0,
    }
    return (loss, outputs) if return_outputs else loss


class FinarKLRetentionCallback(TrainerCallback):
    """Replace CE with base-model KL only for task == generation."""

    def __init__(self, args, trainer):
        super().__init__(args, trainer)
        self._owns_reference = _local_rank() == 0
        _ensure_reference_server(trainer)
        original_compute_loss = trainer.compute_loss

        def kl_routed_compute_loss(model, inputs, *compute_args, **compute_kwargs):
            if not bool(getattr(trainer, "_finar_use_kl", False)):
                return original_compute_loss(model, inputs, *compute_args, **compute_kwargs)
            return_outputs = bool(compute_kwargs.pop("return_outputs", False))
            return _generation_kl_loss(model, inputs, trainer, return_outputs=return_outputs)

        trainer.compute_loss = kl_routed_compute_loss

    def on_train_begin(self, args, state, control, **kwargs):
        if state.is_world_process_zero:
            print(
                "INFO     | >> kl_retention tasks="
                f"{os.environ.get('SFT_KL_TASKS', 'generation')} objective=kl_only "
                f"beta={_env_float('SFT_KL_BETA', 1.0):g} reference={_reference_url()}",
                flush=True,
            )
        return control

    def on_train_end(self, args, state, control, **kwargs):
        if self._owns_reference:
            _cleanup_reference_server()
        return control


callbacks_map["finar_kl"] = FinarKLRetentionCallback
