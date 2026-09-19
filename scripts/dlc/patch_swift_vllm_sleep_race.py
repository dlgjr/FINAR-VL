#!/usr/bin/env python3
"""Patch ms-swift colocate rollout to synchronize ranks before vLLM sleep.

This is a narrow, idempotent workaround for PPU/vLLM CuMemAllocator sleep races
that can surface as invalid-page / illegal-memory-access failures after rollout.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path


MARKER = "# GSPO_PPU_SLEEP_SYNC_V1"
SLEEP_LINE = "                self.engine.engine.sleep(level=args.sleep_level)\n"
REPLACEMENT = (
    "                # GSPO_PPU_SLEEP_SYNC_V1\n"
    "                torch.cuda.synchronize()\n"
    "                if torch.distributed.is_available() and torch.distributed.is_initialized():\n"
    "                    torch.distributed.barrier()\n"
    "                torch.cuda.synchronize()\n"
    "                self.engine.engine.sleep(level=args.sleep_level)\n"
)


def locate_rollout_mixin() -> Path:
    spec = importlib.util.find_spec("swift")
    if spec is None or not spec.submodule_search_locations:
        raise RuntimeError("cannot locate installed swift package")
    path = Path(next(iter(spec.submodule_search_locations))) / "rlhf_trainers" / "rollout_mixin.py"
    if not path.is_file():
        raise FileNotFoundError(path)
    return path


def main() -> None:
    path = locate_rollout_mixin()
    text = path.read_text(encoding="utf-8")
    if MARKER in text:
        print(f"vLLM sleep-race patch already present: {path}")
        return

    fast_infer = text.find("    def _fast_infer(")
    if fast_infer < 0:
        raise RuntimeError("rollout_mixin.py: _fast_infer not found")
    next_method = text.find("\n    def ", fast_infer + 1)
    section = text[fast_infer:] if next_method < 0 else text[fast_infer:next_method]
    if section.count(SLEEP_LINE) != 1:
        raise RuntimeError(
            "rollout_mixin.py: expected exactly one colocate sleep call inside _fast_infer"
        )

    section = section.replace(SLEEP_LINE, REPLACEMENT, 1)
    patched = text[:fast_infer] + section + ("" if next_method < 0 else text[next_method:])
    path.write_text(patched, encoding="utf-8")
    compile(patched, str(path), "exec")
    print(f"patched vLLM sleep synchronization: {path}")


if __name__ == "__main__":
    main()
