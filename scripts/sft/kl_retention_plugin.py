"""Online base-model distillation for FINAR SFT generation samples.

Default routing is inherited from swift_sft_plugin.py and matches only
task == "generation".

For generation samples:
  1. Ignore the dataset-provided assistant answer.
  2. Ask the frozen base model on GPU 6 to generate a fresh answer from the
     original prompt, including all images.
  3. Re-encode the sample with the generated answer through the normal
     ms-swift train template/data collator so multimodal preprocessing, M-RoPE
     position ids and sequence-parallel label preparation are identical to SFT.
  4. Optimize only a sampled forward KL, KL(base || student), on the teacher
     tokens. No SFT cross-entropy term is evaluated.

For all other tasks, the normal SFT loss is unchanged.

With the current 3 x SP2 student topology, only SP rank 0 of each pair calls
the reference server and then broadcasts the teacher rollout to its partner.
Therefore GPU 6 sees at most three concurrent unique requests per node.
"""

from __future__ import annotations

import atexit
import base64
import copy
import json
import mimetypes
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from functools import lru_cache
from pathlib import Path
from typing import Any


try:
    from swift.callbacks import TrainerCallback, callbacks_map
except ImportError:  # Pure-python tests may import without ms-swift.
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


def _allowed_media_root() -> Path:
    raw = os.environ.get("SFT_REF_ALLOWED_MEDIA_PATH") or os.environ.get("QWEN3VL_ROOT") or "/"
    return Path(raw).expanduser().resolve()


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
        raise RuntimeError("SFT online distillation requires SFT_REF_MODEL or BASE_MODEL")

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
        "--allowed-local-media-path",
        str(_allowed_media_root()),
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


def _data_file_for_modality(modality: str) -> Path:
    if modality == "multi":
        explicit = os.environ.get("NORMALIZED_TRAIN_MULTI")
        fallback = Path(os.environ["TMPDIR"]) / "train_data" / "train_multi.jsonl"
    elif modality == "text":
        explicit = os.environ.get("NORMALIZED_TRAIN_TEXT")
        fallback = Path(os.environ["TMPDIR"]) / "train_data" / "train_text.jsonl"
    else:
        raise RuntimeError(f"unknown sample-plan modality for online distillation: {modality!r}")
    path = Path(explicit).expanduser() if explicit else fallback
    if not path.is_file():
        raise RuntimeError(f"normalized SFT data file not found for modality={modality}: {path}")
    return path


@lru_cache(maxsize=4)
def _jsonl_offsets(path_str: str) -> tuple[int, ...]:
    offsets: list[int] = []
    position = 0
    with Path(path_str).open("rb") as handle:
        for line in handle:
            if line.strip():
                offsets.append(position)
            position += len(line)
    return tuple(offsets)


def _jsonl_record(path: Path, index: int) -> dict[str, Any]:
    offsets = _jsonl_offsets(str(path))
    if index < 0 or index >= len(offsets):
        raise IndexError(f"JSONL index out of range: index={index} rows={len(offsets)} path={path}")
    with path.open("rb") as handle:
        handle.seek(offsets[index])
        raw = handle.readline()
    record = json.loads(raw.decode("utf-8"))
    if not isinstance(record, dict):
        raise RuntimeError(f"normalized row is not an object: {path} index={index}")
    return record


def _route_record(route: dict[str, Any]) -> tuple[dict[str, Any], Path]:
    modality = str(route.get("modality") or "")
    # `index` is the post-filter dataset index used by the training dataloader.
    # Re-reading the normalized JSONL must use the original non-empty-line index,
    # otherwise any max-length/encoding deletion before this row shifts the teacher prompt.
    raw_index = int(route.get("raw_index", route.get("index", -1)))
    path = _data_file_for_modality(modality)
    return _jsonl_record(path, raw_index), path


def _local_image_uri(value: str, *, data_file: Path) -> str:
    raw = str(value)
    if raw.startswith(("http://", "https://", "data:", "file://")):
        return raw

    candidate = Path(raw).expanduser()
    candidates = [candidate] if candidate.is_absolute() else [
        Path(os.environ.get("QWEN3VL_ROOT", ".")).expanduser() / candidate,
        data_file.parent / candidate,
        candidate,
    ]
    resolved = next((path.resolve() for path in candidates if path.exists()), None)
    if resolved is None or not resolved.is_file():
        raise RuntimeError(f"generation image not found: {raw}")

    allowed_root = _allowed_media_root()
    try:
        resolved.relative_to(allowed_root)
    except ValueError:
        mime = mimetypes.guess_type(resolved.name)[0] or "application/octet-stream"
        encoded = base64.b64encode(resolved.read_bytes()).decode("ascii")
        return f"data:{mime};base64,{encoded}"
    return resolved.as_uri()


_IMAGE_TAG_RE = re.compile(r"(<image>)")


def _content_with_images(text: str, image_urls: list[str]) -> list[dict[str, Any]]:
    """Interleave <image> placeholders with OpenAI image_url parts."""
    text = str(text)
    parts: list[dict[str, Any]] = []
    image_index = 0
    if "<image>" in text:
        for piece in _IMAGE_TAG_RE.split(text):
            if not piece:
                continue
            if piece == "<image>":
                if image_index >= len(image_urls):
                    raise RuntimeError("more <image> placeholders than images in generation sample")
                parts.append({"type": "image_url", "image_url": {"url": image_urls[image_index]}})
                image_index += 1
            else:
                parts.append({"type": "text", "text": piece})
    else:
        for url in image_urls:
            parts.append({"type": "image_url", "image_url": {"url": url}})
            image_index += 1
        if text:
            parts.append({"type": "text", "text": text})

    # Preserve source image order if a record contains more images than explicit
    # placeholders. The previous insert-at-zero loop reversed these extras.
    for url in image_urls[image_index:]:
        parts.append({"type": "image_url", "image_url": {"url": url}})
    return parts


def _teacher_messages(record: dict[str, Any], *, data_file: Path) -> list[dict[str, Any]]:
    messages = copy.deepcopy(record.get("messages") or [])
    if messages and str(messages[-1].get("role") or "") == "assistant":
        messages = messages[:-1]
    if not messages:
        raise RuntimeError("task=generation record has no prompt messages")

    raw_images = record.get("images") or []
    if raw_images is None:
        raw_images = []
    if not isinstance(raw_images, list):
        raise RuntimeError("generation record images must be a list")
    image_urls = [_local_image_uri(str(value), data_file=data_file) for value in raw_images]

    if image_urls:
        user_indices = [i for i, message in enumerate(messages) if str(message.get("role") or "") == "user"]
        if not user_indices:
            raise RuntimeError("multimodal generation sample has images but no user message")
        target_index = user_indices[-1]
        content = messages[target_index].get("content")
        if isinstance(content, str):
            messages[target_index]["content"] = _content_with_images(content, image_urls)
        elif isinstance(content, list):
            messages[target_index]["content"] = [
                {"type": "image_url", "image_url": {"url": url}} for url in image_urls
            ] + copy.deepcopy(content)
        else:
            messages[target_index]["content"] = _content_with_images(str(content or ""), image_urls)
    return messages


def _teacher_generate(record: dict[str, Any], *, data_file: Path) -> dict[str, Any]:
    """Generate one fresh teacher answer and return token IDs + sampled-token logps."""
    payload = {
        "model": _reference_model_name(),
        "messages": _teacher_messages(record, data_file=data_file),
        "max_tokens": _env_int("SFT_TEACHER_MAX_TOKENS", 512),
        "temperature": _env_float("SFT_TEACHER_TEMPERATURE", 1.0),
        "top_p": _env_float("SFT_TEACHER_TOP_P", 1.0),
        "logprobs": True,
        "top_logprobs": 1,
        "return_tokens_as_token_ids": True,
        "return_token_ids": True,
    }
    timeout = _env_float("SFT_REF_REQUEST_TIMEOUT", 600.0)
    last_error: Exception | None = None
    for attempt in range(3):
        try:
            response = _http_json(f"{_reference_url()}/v1/chat/completions", payload, timeout=timeout)
            choices = response.get("choices") or []
            if not choices:
                raise RuntimeError(f"teacher response has no choices: {response}")
            choice = choices[0]
            message = choice.get("message") or {}
            text = message.get("content")
            if text is None:
                raise RuntimeError(f"teacher response has no message content: {choice}")
            token_ids = choice.get("token_ids")
            logprob_items = ((choice.get("logprobs") or {}).get("content") or [])
            if not isinstance(token_ids, list) or not token_ids:
                parsed_ids: list[int] = []
                for item in logprob_items if isinstance(logprob_items, list) else []:
                    token = item.get("token") if isinstance(item, dict) else None
                    match = re.fullmatch(r"token_id:(\d+)", str(token or ""))
                    if match is None:
                        parsed_ids = []
                        break
                    parsed_ids.append(int(match.group(1)))
                token_ids = parsed_ids
            if not isinstance(token_ids, list) or not token_ids:
                raise RuntimeError(
                    "teacher response did not return generated token_ids; "
                    "the installed vLLM must support return_token_ids or return_tokens_as_token_ids"
                )
            if not isinstance(logprob_items, list) or len(logprob_items) != len(token_ids):
                raise RuntimeError(
                    "teacher token/logprob length mismatch: "
                    f"token_ids={len(token_ids) if isinstance(token_ids, list) else None} "
                    f"logprobs={len(logprob_items) if isinstance(logprob_items, list) else None}"
                )
            logps = []
            for item in logprob_items:
                value = item.get("logprob") if isinstance(item, dict) else None
                if value is None:
                    raise RuntimeError("teacher response contains a token without logprob")
                logps.append(float(value))
            return {
                "text": str(text),
                "token_ids": [int(value) for value in token_ids],
                "logps": logps,
                "finish_reason": choice.get("finish_reason"),
                "prompt_token_ids": response.get("prompt_token_ids"),
            }
        except (OSError, ValueError, RuntimeError, urllib.error.URLError) as exc:
            last_error = exc
            if attempt < 2:
                time.sleep(1 + attempt)
    raise RuntimeError(f"teacher generation failed after retries: {last_error}")


def _sp_state():
    from swift.sequence_parallel import sequence_parallel

    world_size = int(getattr(sequence_parallel, "world_size", 1) or 1)
    sp_world_size = int(getattr(sequence_parallel, "sp_world_size", 1) or 1)
    rp_world_size = int(getattr(sequence_parallel, "rp_world_size", 1) or 1)
    sp_rank = int(getattr(sequence_parallel, "sp_rank", 0) or 0)
    return sequence_parallel, world_size, sp_world_size, rp_world_size, sp_rank


def _broadcast_teacher(payload: dict[str, Any] | None) -> dict[str, Any]:
    import torch.distributed as dist

    sequence_parallel, world_size, _, rp_world_size, sp_rank = _sp_state()
    if rp_world_size != 1:
        raise RuntimeError(
            "generation online distillation currently supports Ulysses SP only "
            f"(rp_world_size=1), got {rp_world_size}"
        )
    if world_size <= 1:
        if payload is None:
            raise RuntimeError("teacher payload missing without sequence parallel")
        return payload

    group = sequence_parallel.sp_group
    if group is None:
        raise RuntimeError("sequence parallel enabled but sp_group is unavailable")
    objects = [payload if sp_rank == 0 else None]
    if hasattr(dist, "get_global_rank"):
        source_global_rank = int(dist.get_global_rank(group, 0))
    else:
        source_global_rank = int(dist.get_rank()) - sp_rank
    dist.broadcast_object_list(objects, src=source_global_rank, group=group)
    result = objects[0]
    if not isinstance(result, dict):
        raise RuntimeError("failed to broadcast teacher rollout inside SP group")
    return result


def _replace_assistant_with_teacher(record: dict[str, Any], teacher_text: str) -> dict[str, Any]:
    updated = copy.deepcopy(record)
    messages = copy.deepcopy(updated.get("messages") or [])
    if messages and str(messages[-1].get("role") or "") == "assistant":
        messages[-1]["content"] = teacher_text
    else:
        messages.append({"role": "assistant", "content": teacher_text})
    updated["messages"] = messages
    return updated


def _prepare_teacher_inputs(trainer, record: dict[str, Any], teacher_text: str) -> dict[str, Any]:
    """Re-encode through the normal train template so multimodal/SP state stays correct."""
    encoded = trainer.template.encode(_replace_assistant_with_teacher(record, teacher_text))
    if not isinstance(encoded, dict) or "input_ids" not in encoded or "labels" not in encoded:
        raise RuntimeError("template.encode failed for teacher-generated generation sample")
    batch = trainer.data_collator([encoded])
    prepared = trainer._prepare_inputs(batch)
    if not isinstance(prepared, dict):
        raise RuntimeError("trainer._prepare_inputs did not return a dict for teacher sample")
    return prepared


def _gather_rolled_labels(local_labels):
    """Undo only the SP split; labels remain in ms-swift's shifted form."""
    sequence_parallel, world_size, _, rp_world_size, _ = _sp_state()
    if world_size <= 1:
        return local_labels
    if rp_world_size != 1:
        raise RuntimeError("generation distillation does not support ring parallel")
    return sequence_parallel.gather(local_labels.contiguous(), dim=-1)


def _teacher_alignment(local_labels, teacher_token_ids: list[int], teacher_logps: list[float]):
    """Map teacher rollout tokens to this SP rank's already-shifted labels."""
    import torch

    if len(teacher_token_ids) != len(teacher_logps) or not teacher_token_ids:
        raise RuntimeError("teacher rollout token IDs/logprobs are empty or misaligned")

    sequence_parallel, world_size, sp_world_size, rp_world_size, sp_rank = _sp_state()
    if rp_world_size != 1:
        raise RuntimeError("generation distillation does not support ring parallel")

    full_labels = _gather_rolled_labels(local_labels)
    supervised_positions = torch.nonzero(full_labels[0].ne(-100), as_tuple=False).flatten()
    supervised_ids = full_labels[0].index_select(0, supervised_positions).detach().cpu().tolist()
    teacher_ids = [int(value) for value in teacher_token_ids]

    best_start = -1
    best_length = 0
    for start in range(len(supervised_ids)):
        length = 0
        while (
            length < len(teacher_ids)
            and start + length < len(supervised_ids)
            and int(supervised_ids[start + length]) == teacher_ids[length]
        ):
            length += 1
        if length > best_length:
            best_start = start
            best_length = length
        if length == len(teacher_ids):
            break

    min_required = max(1, len(teacher_ids) - 2)
    if best_start < 0 or best_length < min_required:
        raise RuntimeError(
            "teacher/student response tokenization mismatch: "
            f"teacher_tokens={len(teacher_ids)} best_match={best_length}"
        )

    matched_positions = supervised_positions[best_start : best_start + best_length]
    matched_teacher_ids = teacher_ids[:best_length]
    matched_teacher_logps = teacher_logps[:best_length]

    local_length = int(local_labels.shape[-1])
    global_offset = sp_rank * local_length if sp_world_size > 1 else 0
    local_begin = global_offset
    local_end = global_offset + local_length

    local_positions: list[int] = []
    local_target_ids: list[int] = []
    local_ref_logps: list[float] = []
    for global_position, token_id, ref_logp in zip(
        matched_positions.detach().cpu().tolist(),
        matched_teacher_ids,
        matched_teacher_logps,
    ):
        if local_begin <= int(global_position) < local_end:
            local_positions.append(int(global_position) - global_offset)
            local_target_ids.append(int(token_id))
            local_ref_logps.append(float(ref_logp))

    device = local_labels.device
    return (
        torch.tensor(local_positions, dtype=torch.long, device=device),
        torch.tensor(local_target_ids, dtype=torch.long, device=device),
        torch.tensor(local_ref_logps, dtype=torch.float32, device=device),
        best_length,
    )


def _teacher_rollout_for_route(trainer, route: dict[str, Any], record: dict[str, Any], data_file: Path) -> dict[str, Any]:
    _, world_size, _, rp_world_size, sp_rank = _sp_state()
    if rp_world_size != 1:
        raise RuntimeError("generation distillation does not support ring parallel")
    payload = None
    if world_size <= 1 or sp_rank == 0:
        try:
            payload = _teacher_generate(record, data_file=data_file)
        except Exception as exc:
            # If the SP leader raises before entering the broadcast, its partner
            # would otherwise block forever in broadcast_object_list(). Broadcast
            # the failure as data so every rank in the SP pair exits coherently.
            payload = {"_finar_teacher_error": f"{type(exc).__name__}: {exc}"}
    payload = _broadcast_teacher(payload)
    teacher_error = payload.pop("_finar_teacher_error", None)
    if teacher_error:
        raise RuntimeError(f"teacher generation failed on SP leader: {teacher_error}")
    payload["modality"] = str(route.get("modality") or "")
    payload["index"] = int(route.get("index", -1))
    payload["raw_index"] = int(route.get("raw_index", route.get("index", -1)))
    return payload


def _generation_distill_loss(model, trainer, route: dict[str, Any], *, return_outputs: bool = False):
    """Online teacher generation + sampled KL(base || student), with zero CE."""
    import torch
    import torch.nn.functional as F

    record, data_file = _route_record(route)
    teacher = _teacher_rollout_for_route(trainer, route, record, data_file)
    teacher_inputs = _prepare_teacher_inputs(trainer, record, str(teacher["text"]))

    input_ids = teacher_inputs.get("input_ids")
    labels = teacher_inputs.get("labels")
    if not torch.is_tensor(input_ids) or not torch.is_tensor(labels):
        raise RuntimeError("teacher re-encoding did not produce tensor input_ids/labels")
    if input_ids.ndim != 2 or labels.ndim != 2 or int(input_ids.shape[0]) != 1 or int(labels.shape[0]) != 1:
        raise RuntimeError("generation distillation requires per_device_train_batch_size=1")

    max_length = _env_int("SFT_KL_MAX_LENGTH", 0)
    if max_length > 0 and int(input_ids.shape[1]) > max_length:
        raise RuntimeError(
            f"teacher generation sequence length {int(input_ids.shape[1])} exceeds SFT_KL_MAX_LENGTH={max_length}"
        )

    local_positions, target_ids, reference_logps, matched_tokens = _teacher_alignment(
        labels,
        [int(value) for value in teacher["token_ids"]],
        [float(value) for value in teacher["logps"]],
    )

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
    forward_inputs = {key: value for key, value in teacher_inputs.items() if key in allowed_keys}
    forward_inputs["use_cache"] = False
    forward_inputs["logits_to_keep"] = local_positions

    outputs = model(**forward_inputs)
    logits = getattr(outputs, "logits", None)
    if logits is None and isinstance(outputs, (tuple, list)) and outputs:
        logits = outputs[0]
    if not torch.is_tensor(logits):
        raise RuntimeError("generation distillation forward did not return logits")
    if logits.ndim != 3 or int(logits.shape[0]) != 1 or int(logits.shape[1]) != int(target_ids.numel()):
        raise RuntimeError(
            "generation distillation logits/target mismatch: "
            f"logits={tuple(logits.shape)} targets={int(target_ids.numel())}"
        )

    if target_ids.numel() > 0:
        student_logps = F.log_softmax(logits[0].float(), dim=-1).gather(1, target_ids[:, None]).squeeze(1)
        if student_logps.shape != reference_logps.shape:
            raise RuntimeError(
                "generation distillation student/reference shape mismatch: "
                f"{tuple(student_logps.shape)} vs {tuple(reference_logps.shape)}"
            )
        log_ratio = (student_logps - reference_logps.detach()).clamp(min=-20.0, max=20.0)
        per_token_kl = torch.exp(log_ratio) - log_ratio - 1.0
        local_kl_sum = per_token_kl.sum()
        local_token_count = torch.tensor(float(per_token_kl.numel()), device=local_kl_sum.device)
    else:
        local_kl_sum = logits.float().sum() * 0.0
        local_token_count = torch.zeros((), dtype=torch.float32, device=logits.device)

    sequence_parallel, world_size, sp_world_size, _, _ = _sp_state()
    total_token_count = local_token_count.detach().clone()
    if world_size > 1:
        import torch.distributed as dist

        dist.all_reduce(total_token_count, op=dist.ReduceOp.SUM, group=sequence_parallel.sp_group)
    if float(total_token_count.item()) <= 0:
        raise RuntimeError("task=generation produced zero matched teacher tokens across the SP group")

    sp_scale = float(sp_world_size if world_size > 1 else 1)
    beta = _env_float("SFT_KL_BETA", 1.0)
    loss = local_kl_sum * (sp_scale / total_token_count) * beta

    trainer._finar_last_kl = {
        "task": "generation",
        "modality": str(route.get("modality") or ""),
        "index": int(route.get("index", -1)),
        "raw_index": int(route.get("raw_index", route.get("index", -1))),
        "teacher_tokens": len(teacher["token_ids"]),
        "matched_teacher_tokens": int(matched_tokens),
        "local_tokens": int(local_token_count.item()),
        "group_tokens": int(total_token_count.item()),
        "weighted_local_loss": float(loss.detach().item()),
        "beta": beta,
        "ce": 0.0,
        "teacher_finish_reason": teacher.get("finish_reason"),
    }
    return (loss, outputs) if return_outputs else loss


def _current_route_from_plan(trainer) -> tuple[str, bool, dict[str, Any]]:
    tracker = getattr(trainer, "_finar_plan_tracker", None)
    entry = None
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
        route = {
            "task": task,
            "use_kl": bool(use_kl),
            "modality": str(entry.get("modality") or ""),
            "index": int(entry.get("index", -1)),
            "raw_index": int(entry.get("raw_index", entry.get("index", -1))),
        }
        return task, bool(use_kl), route

    task = str(getattr(trainer, "_finar_current_task", "") or "")
    use_kl = bool(getattr(trainer, "_finar_use_kl", False))
    route = dict(getattr(trainer, "_finar_kl_route", {}) or {})
    route.setdefault("task", task)
    route.setdefault("use_kl", use_kl)
    route.setdefault("raw_index", route.get("index", -1))
    return task, use_kl, route


class FinarKLRetentionCallback(TrainerCallback):
    """Use online base-generated KL-only distillation for task == generation."""

    def __init__(self, args, trainer):
        super().__init__(args, trainer)
        self._owns_reference = _local_rank() == 0
        _ensure_reference_server(trainer)
        original_compute_loss = trainer.compute_loss

        def kl_routed_compute_loss(model, inputs, *compute_args, **compute_kwargs):
            task, use_kl, route = _current_route_from_plan(trainer)
            trainer._finar_current_task = task
            trainer._finar_use_kl = use_kl
            trainer._finar_kl_route = route
            if not use_kl:
                return original_compute_loss(model, inputs, *compute_args, **compute_kwargs)
            return_outputs = bool(compute_kwargs.pop("return_outputs", False))
            return _generation_distill_loss(model, trainer, route, return_outputs=return_outputs)

        trainer.compute_loss = kl_routed_compute_loss

    def on_train_begin(self, args, state, control, **kwargs):
        if state.is_world_process_zero:
            print(
                "INFO     | >> kl_retention tasks="
                f"{os.environ.get('SFT_KL_TASKS', 'generation')} "
                "objective=online_teacher_kl_base_to_student ce=0 "
                f"beta={_env_float('SFT_KL_BETA', 1.0):g} "
                f"teacher_temperature={_env_float('SFT_TEACHER_TEMPERATURE', 1.0):g} "
                f"teacher_max_tokens={_env_int('SFT_TEACHER_MAX_TOKENS', 512)} "
                f"reference={_reference_url()} multimodal_images=true",
                flush=True,
            )
        return control

    def on_train_end(self, args, state, control, **kwargs):
        if self._owns_reference:
            _cleanup_reference_server()
        return control


callbacks_map["finar_kl"] = FinarKLRetentionCallback