from __future__ import annotations

import importlib.util
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
