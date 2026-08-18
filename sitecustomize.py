"""FINAR-VL Python startup hooks.

The SFT launcher sets FINAR_SFT_DDP_TIMEOUT_PATCH=1 before starting ms-swift.
That marker is inherited by torchrun workers, so the timeout hook no longer
relies only on argv shape. RL/GSPO launchers do not set the marker.
"""

from __future__ import annotations

import inspect
import os
import sys
from datetime import timedelta
from functools import wraps
from typing import Any


_DEFAULT_SFT_DDP_TIMEOUT_SECONDS = 86400
_TORCH_PATCH_ATTR = "_finar_sft_ddp_timeout_patch"
_DEEPSPEED_PATCH_ATTR = "_finar_sft_deepspeed_timeout_patch"
_MISSING = object()


def _is_swift_sft_process(argv: list[str] | tuple[str, ...] | None = None) -> bool:
    """Return True only for an ms-swift SFT launcher/worker argv."""
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


def _sft_timeout_patch_enabled(
    argv: list[str] | tuple[str, ...] | None = None,
    environ: dict[str, str] | os._Environ[str] | None = None,
) -> bool:
    """Prefer the explicit launcher marker, while keeping direct `swift sft` usable."""
    env = os.environ if environ is None else environ
    marker = str(env.get("FINAR_SFT_DDP_TIMEOUT_PATCH", "")).strip().lower()
    if marker in {"1", "true", "yes", "on"}:
        return True
    if marker in {"0", "false", "no", "off"}:
        return False
    return _is_swift_sft_process(argv)


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


def _raise_torch_default_timeouts(minimum: timedelta) -> None:
    """Raise PyTorch's Python-side default PG timeouts as a second line of defense."""
    try:
        import torch.distributed.constants as constants
        from torch.distributed import distributed_c10d
    except (ImportError, AttributeError):
        return

    for module in (constants, distributed_c10d):
        for name in ("default_pg_timeout", "default_pg_nccl_timeout"):
            current = getattr(module, name, _MISSING)
            if current is _MISSING or current is None:
                continue
            if _timeout_is_shorter(current, minimum):
                try:
                    setattr(module, name, minimum)
                except (AttributeError, TypeError):
                    pass


def _raise_backend_timeout(backend: Any, minimum: timedelta) -> Any:
    """Raise an already-created backend timeout and return the observed value."""
    options = getattr(backend, "options", None)
    current = getattr(options, "_timeout", None) if options is not None else None
    if current is not None and not _timeout_is_shorter(current, minimum):
        return current

    # Newer distributed backends may expose a dynamic timeout setter.
    setter = getattr(backend, "_set_default_timeout", None)
    if callable(setter):
        try:
            setter(minimum)
        except (TypeError, RuntimeError, AttributeError):
            pass

    # ProcessGroupNCCL keeps the same Options object; WorkNCCL snapshots the
    # timeout from it when each work item is created. Updating this before
    # preprocessing collectives therefore protects against an initializer that
    # silently constructed the PG with the 600s NCCL default.
    options = getattr(backend, "options", None)
    if options is not None:
        observed = getattr(options, "_timeout", None)
        if _timeout_is_shorter(observed, minimum):
            try:
                options._timeout = minimum
            except (AttributeError, TypeError, RuntimeError):
                pass
    return getattr(getattr(backend, "options", None), "_timeout", None)


def _enforce_existing_default_pg_timeout(minimum: timedelta) -> Any:
    """Verify/fix the actual NCCL backend after the default PG is initialized."""
    try:
        import torch
        import torch.distributed as dist
        from torch.distributed import distributed_c10d
    except (ImportError, AttributeError):
        return None

    if not dist.is_available() or not dist.is_initialized():
        return None

    try:
        pg = distributed_c10d._get_default_group()
        if not torch.cuda.is_available():
            return None
        device = torch.device("cuda", torch.cuda.current_device())
        backend = pg._get_backend(device)
    except (AttributeError, RuntimeError, ValueError):
        return None

    observed = _raise_backend_timeout(backend, minimum)
    if observed is not None and _timeout_is_shorter(observed, minimum):
        raise RuntimeError(
            "[FINAR-SFT] default NCCL process group still has a short timeout "
            f"after enforcement: observed={observed!r} required>={minimum!r}"
        )
    return observed


def _install_torch_timeout_patch(minimum: timedelta) -> bool:
    try:
        import torch.distributed as dist
    except (ImportError, AttributeError):
        return False

    _raise_torch_default_timeouts(minimum)

    original = getattr(dist, "init_process_group", None)
    if not callable(original):
        return False
    if getattr(original, _TORCH_PATCH_ATTR, False):
        return True

    @wraps(original)
    def init_process_group_with_finar_timeout(*args: Any, **kwargs: Any):
        call_args, call_kwargs = _apply_min_timeout(args, kwargs, minimum)
        result = original(*call_args, **call_kwargs)
        _enforce_existing_default_pg_timeout(minimum)
        return result

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
        result = original(*call_args, **call_kwargs)
        _enforce_existing_default_pg_timeout(minimum)
        return result

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
    if not _sft_timeout_patch_enabled():
        return False

    seconds = _configured_timeout_seconds()
    minimum = timedelta(seconds=seconds)
    torch_patched = _install_torch_timeout_patch(minimum)
    deepspeed_patched = _install_deepspeed_timeout_patch(minimum)
    observed = _enforce_existing_default_pg_timeout(minimum)

    print(
        "[FINAR-SFT] process-group minimum timeout "
        f"patched to {seconds}s torch={torch_patched} deepspeed={deepspeed_patched} "
        f"observed={observed!r}",
        file=sys.stderr,
        flush=True,
    )
    return torch_patched or deepspeed_patched


_install_sft_ddp_timeout_patch()
