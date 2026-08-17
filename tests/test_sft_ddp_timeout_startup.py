from __future__ import annotations

import importlib.util
import sys
import types
from datetime import timedelta
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("finar_sitecustomize_test", ROOT / "sitecustomize.py")
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_timeout_patch_is_sft_only() -> None:
    assert MODULE._is_swift_sft_process(("/opt/ac2/bin/swift", "sft", "--model", "qwen"))
    assert MODULE._is_swift_sft_process(("/site-packages/swift/cli/sft.py", "--model", "qwen"))
    assert not MODULE._is_swift_sft_process(("/opt/ac2/bin/swift", "rlhf", "--model", "qwen"))
    assert not MODULE._is_swift_sft_process(("/site-packages/swift/cli/rlhf.py", "--model", "qwen"))


def test_timeout_patch_raises_missing_or_short_keyword_timeout() -> None:
    minimum = timedelta(seconds=7200)

    args, kwargs = MODULE._apply_min_timeout((), {}, minimum)
    assert args == ()
    assert kwargs["timeout"] == minimum

    args, kwargs = MODULE._apply_min_timeout((), {"timeout": timedelta(seconds=600)}, minimum)
    assert args == ()
    assert kwargs["timeout"] == minimum

    larger = timedelta(seconds=86400)
    args, kwargs = MODULE._apply_min_timeout((), {"timeout": larger}, minimum)
    assert args == ()
    assert kwargs["timeout"] == larger


def test_timeout_patch_handles_positional_timeout() -> None:
    minimum = timedelta(seconds=7200)
    args, kwargs = MODULE._apply_min_timeout(("nccl", None, timedelta(seconds=600), 24, 3), {}, minimum)

    assert args[0] == "nccl"
    assert args[2] == minimum
    assert kwargs == {}


def test_deepspeed_timeout_patch_handles_keyword_and_positional_timeout() -> None:
    minimum = timedelta(seconds=7200)

    def init_distributed(
        dist_backend=None,
        auto_mpi_discovery=True,
        distributed_port=29500,
        verbose=True,
        timeout=timedelta(seconds=600),
        init_method=None,
    ):
        return dist_backend, timeout

    args, kwargs = MODULE._apply_named_min_timeout(init_distributed, (), {}, minimum)
    assert args == ()
    assert kwargs["timeout"] == minimum

    args, kwargs = MODULE._apply_named_min_timeout(
        init_distributed,
        (),
        {"timeout": timedelta(seconds=600)},
        minimum,
    )
    assert kwargs["timeout"] == minimum

    positional = ("nccl", False, 29500, True, timedelta(seconds=600), None)
    args, kwargs = MODULE._apply_named_min_timeout(init_distributed, positional, {}, minimum)
    assert args[4] == minimum
    assert kwargs == {}

    larger = timedelta(seconds=86400)
    args, kwargs = MODULE._apply_named_min_timeout(init_distributed, (), {"timeout": larger}, minimum)
    assert kwargs["timeout"] == larger


def test_deepspeed_timeout_patch_updates_all_public_aliases(monkeypatch) -> None:
    calls = []

    def init_distributed(
        dist_backend=None,
        auto_mpi_discovery=True,
        distributed_port=29500,
        verbose=True,
        timeout=timedelta(seconds=600),
        init_method=None,
    ):
        calls.append(timeout)
        return timeout

    deepspeed = types.ModuleType("deepspeed")
    deepspeed_comm = types.ModuleType("deepspeed.comm")
    deepspeed_comm_impl = types.ModuleType("deepspeed.comm.comm")

    deepspeed_comm_impl.init_distributed = init_distributed
    deepspeed_comm.init_distributed = init_distributed
    deepspeed_comm.comm = deepspeed_comm_impl
    deepspeed.comm = deepspeed_comm
    deepspeed.init_distributed = init_distributed

    monkeypatch.setitem(sys.modules, "deepspeed", deepspeed)
    monkeypatch.setitem(sys.modules, "deepspeed.comm", deepspeed_comm)
    monkeypatch.setitem(sys.modules, "deepspeed.comm.comm", deepspeed_comm_impl)

    minimum = timedelta(seconds=7200)
    assert MODULE._install_deepspeed_timeout_patch(minimum)

    assert deepspeed.init_distributed is deepspeed_comm.init_distributed
    assert deepspeed_comm.init_distributed is deepspeed_comm_impl.init_distributed

    assert deepspeed_comm.init_distributed(timeout=timedelta(seconds=600)) == minimum
    assert calls[-1] == minimum


def test_sft_launcher_exposes_repo_root_for_sitecustomize() -> None:
    launcher = (ROOT / "scripts/dlc/start_sft.sh").read_text(encoding="utf-8")
    env_script = (ROOT / "scripts/dlc/dlc_env.sh").read_text(encoding="utf-8")

    assert 'source "$ROOT/scripts/dlc/dlc_env.sh"' in launcher
    assert 'export PYTHONPATH="$QWEN3VL_ROOT:$PYTHON_USER_SITE' in env_script
