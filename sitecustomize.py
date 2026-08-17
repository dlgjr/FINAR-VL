"""FINAR-VL Python startup hooks.

Only the SFT worker process uses the hook below.  The repository root is already
on PYTHONPATH through scripts/dlc/dlc_env.sh, so Python imports sitecustomize
before ms-swift/Accelerate creates the default distributed process group.
"""

from __future__ import annotations

import os
import sys
from datetime import timedelta
from functools import wraps
from typing import Any


_DEFAULT_SFT_DDP_TIMEOUT_SECONDS = 7200
_PATCH_ATTR = "_finar_sft_ddp_timeout_patch"
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
    """Raise init_process_group timeout to at least ``minimum``.

    ``timeout`` is the third positional parameter in torch.distributed
    init_process_group, so handle both positional and keyword callers.
    """
    positional = list(args)
    updated = dict(kwargs)
    keyword_timeout = updated.get("timeout", _MISSING)
    if keyword_timeout is not _MISSING:
        if _timeout_is_shorter(keyword_timeout, minimum):
            updated["timeout"] = minimum
        return tuple(positional), updated

    timeout_position = 2
    if len(positional) > timeout_position:
        if _timeout_is_shorter(positional[timeout_position], minimum):
            positional[timeout_position] = minimum
    else:
        updated["timeout"] = minimum
    return tuple(positional), updated


def _install_sft_ddp_timeout_patch() -> bool:
    if not _is_swift_sft_process():
        return False

    try:
        import torch.distributed as dist
    except (ImportError, AttributeError):
        return False

    original = getattr(dist, "init_process_group", None)
    if not callable(original):
        return False
    if getattr(original, _PATCH_ATTR, False):
        return True

    seconds = _configured_timeout_seconds()
    minimum = timedelta(seconds=seconds)

    @wraps(original)
    def init_process_group_with_finar_timeout(*args: Any, **kwargs: Any):
        call_args, call_kwargs = _apply_min_timeout(args, kwargs, minimum)
        return original(*call_args, **call_kwargs)

    setattr(init_process_group_with_finar_timeout, _PATCH_ATTR, True)
    setattr(init_process_group_with_finar_timeout, "_finar_original", original)
    dist.init_process_group = init_process_group_with_finar_timeout

    # Some callers import the implementation from distributed_c10d directly.
    try:
        from torch.distributed import distributed_c10d
    except (ImportError, AttributeError):
        distributed_c10d = None
    if distributed_c10d is not None:
        distributed_c10d.init_process_group = init_process_group_with_finar_timeout

    print(
        f"[FINAR-SFT] process-group minimum timeout patched to {seconds}s",
        file=sys.stderr,
        flush=True,
    )
    return True


_install_sft_ddp_timeout_patch()
