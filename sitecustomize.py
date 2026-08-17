"""FINAR-VL Python startup hooks.

Only the SFT worker process uses the hook below.  The repository root is already
on PYTHONPATH through scripts/dlc/dlc_env.sh, so Python imports sitecustomize
before ms-swift/Accelerate/DeepSpeed creates the default distributed process
group.
"""

from __future__ import annotations

import inspect
import os
import sys
from datetime import timedelta
from functools import wraps
from typing import Any


_DEFAULT_SFT_DDP_TIMEOUT_SECONDS = 7200
_TORCH_PATCH_ATTR = "_finar_sft_ddp_timeout_patch"
_DEEPSPEED_PATCH_ATTR = "_finar_sft_deepspeed_timeout_patch"
_MISSING = object()


def _is_swift_sft_process(argv: list[str] | tuple[str, ...] | None = None) -> bool:
    """Return True only for the ms-swift SFT launcher/worker process."""
    values = list(sys.argv if argv is None else argv)
    if not values:
        return False
    command = str(values[0]).replace("\\", "/")
    if command.endswith("/swift/cli/sft.py") or command.endswith("/swift/cli/sft.pyc"):
        return True
    basename = os.path.basename(command)
    if len(values) > 1 and str(values[1]) == "sft":
        return basename == "swift" or command == "-m" or command.endswith("/swift/cli/__main__.py")
    return False


def _configured_timeout_seconds() -> int:
    raw = os.environ.get("SFT_DDP_TIMEOUT", str(_DEFAULT_SFT_DDP_TIMEOUT_SECONDS))
    try:
        seconds = int(raw)
    except (TypeError, ValueError):
        seconds = _DEFAULT_SFT_DDP_TIMEOUT_SECONDS
        print(
            f"[FINAR-SFT] invalid SFT_DDP_TIMEOUT={raw!r}; using {seconds}s",
            file=sys.stderr,
            flush=True,
        )
    if seconds <= 0:
        print(
            f"[FINAR-SFT] non-positive SFT_DDP_TIMEOUT={seconds}; "
            f"using {_DEFAULT_SFT_DDP_TIMEOUT_SECONDS}s",
            file=sys.stderr,
            flush=True,
        )
        seconds = _DEFAULT_SFT_DDP_TIMEOUT_SECONDS
    return seconds


def _timeout_is_shorter(current: Any, minimum: timedelta) -> bool:
    if current is None:
        return True
    try:
        return bool(current < minimum)
    except TypeError:
        return False


def _apply_min_timeout(
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
    minimum: timedelta,
) -> tuple[tuple[Any, ...], dict[str, Any]]:
    """Raise torch.distributed.init_process_group timeout to at least minimum."""
    positional = list(args)
    updated = dict(kwargs)
    keyword_timeout = updated.get("timeout", _MISSING)
    if keyword_timeout is not _MISSING:
        if _timeout_is_shorter(keyword_timeout, minimum):
            updated["timeout"] = minimum
        return tuple(positional), updated

    # torch.distributed.init_process_group(..., timeout=...) uses position 2.
    timeout_position = 2
    if len(positional) > timeout_position:
        if _timeout_is_shorter(positional[timeout_position], minimum):
            positional[timeout_position] = minimum
    else:
        updated["timeout"] = minimum
    return tuple(positional), updated


def _apply_named_min_timeout(
    target: Any,
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
    minimum: timedelta,
    *,
    parameter_name: str = "timeout",
) -> tuple[tuple[Any, ...], dict[str, Any]]:
    """Raise a named timeout argument while preserving positional callers."""
    positional = list(args)
    updated = dict(kwargs)
    keyword_timeout = updated.get(parameter_name, _MISSING)
    if keyword_timeout is not _MISSING:
        if _timeout_is_shorter(keyword_timeout, minimum):
            updated[parameter_name] = minimum
        return tuple(positional), updated

    try:
        parameters = list(inspect.signature(target).parameters.values())
    except (TypeError, ValueError):
        parameters = []

    positional_names = [
        parameter.name
        for parameter in parameters
        if parameter.kind in (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD)
    ]
    if parameter_name in positional_names:
        timeout_position = positional_names.index(parameter_name)
        if len(positional) > timeout_position:
            if _timeout_is_shorter(positional[timeout_position], minimum):
                positional[timeout_position] = minimum
            return tuple(positional), updated

    updated[parameter_name] = minimum
    return tuple(positional), updated


def _install_torch_timeout_patch(minimum: timedelta) -> bool:
    try:
        import torch.distributed as dist
    except (ImportError, AttributeError):
        return False

    original = getattr(dist, "init_process_group", None)
    if not callable(original):
        return False
    if getattr(original, _TORCH_PATCH_ATTR, False):
        return True

    @wraps(original)
    def init_process_group_with_finar_timeout(*args: Any, **kwargs: Any):
        call_args, call_kwargs = _apply_min_timeout(args, kwargs, minimum)
        return original(*call_args, **call_kwargs)

    setattr(init_process_group_with_finar_timeout, _TORCH_PATCH_ATTR, True)
    setattr(init_process_group_with_finar_timeout, "_finar_original", original)
    dist.init_process_group = init_process_group_with_finar_timeout

    # Some callers import the implementation from distributed_c10d directly.
    try:
        from torch.distributed import distributed_c10d
    except (ImportError, AttributeError):
        distributed_c10d = None
    if distributed_c10d is not None:
        distributed_c10d.init_process_group = init_process_group_with_finar_timeout
    return True


def _install_deepspeed_timeout_patch(minimum: timedelta) -> bool:
    """Patch the DeepSpeed path used by Accelerate for ZeRO training."""
    try:
        import deepspeed
        import deepspeed.comm as deepspeed_comm
        from deepspeed.comm import comm as deepspeed_comm_impl
    except (ImportError, AttributeError):
        return False

    original = getattr(deepspeed_comm_impl, "init_distributed", None)
    if not callable(original):
        original = getattr(deepspeed_comm, "init_distributed", None)
    if not callable(original):
        return False
    if getattr(original, _DEEPSPEED_PATCH_ATTR, False):
        return True

    @wraps(original)
    def init_distributed_with_finar_timeout(*args: Any, **kwargs: Any):
        call_args, call_kwargs = _apply_named_min_timeout(original, args, kwargs, minimum)
        return original(*call_args, **call_kwargs)

    setattr(init_distributed_with_finar_timeout, _DEEPSPEED_PATCH_ATTR, True)
    setattr(init_distributed_with_finar_timeout, "_finar_original", original)

    # Accelerate imports `deepspeed.comm as dist`; other code may call the
    # top-level alias or the implementation module directly. Keep all three
    # references on the same wrapper.
    deepspeed_comm_impl.init_distributed = init_distributed_with_finar_timeout
    deepspeed_comm.init_distributed = init_distributed_with_finar_timeout
    if hasattr(deepspeed, "init_distributed"):
        deepspeed.init_distributed = init_distributed_with_finar_timeout
    return True


def _install_sft_ddp_timeout_patch() -> bool:
    if not _is_swift_sft_process():
        return False

    seconds = _configured_timeout_seconds()
    minimum = timedelta(seconds=seconds)
    torch_patched = _install_torch_timeout_patch(minimum)
    deepspeed_patched = _install_deepspeed_timeout_patch(minimum)

    print(
        "[FINAR-SFT] process-group minimum timeout "
        f"patched to {seconds}s torch={torch_patched} deepspeed={deepspeed_patched}",
        file=sys.stderr,
        flush=True,
    )
    return torch_patched or deepspeed_patched


_install_sft_ddp_timeout_patch()
