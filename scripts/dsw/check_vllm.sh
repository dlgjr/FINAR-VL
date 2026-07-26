#!/usr/bin/env bash
set -euo pipefail

ROOT=/mnt/nas/bihaoran/qwen3vl
source "$ROOT/scripts/common/env.sh"

python - <<'PY'
import importlib.metadata
import sys
import torch

print("python:", sys.executable)
print("torch:", torch.__version__)
print("device:", torch.cuda.get_device_name(0))

try:
    import vllm
except Exception as exc:
    print("VLLM_IMPORT_FAILED:", repr(exc))
    raise

version = importlib.metadata.version("vllm")

print("vllm version:", version)
print("vllm path:", vllm.__file__)

if "ppu" not in version.lower():
    print("WARNING: version string does not contain 'ppu'")

print("VLLM_IMPORT_OK")
PY

swift rlhf --help | grep -E \
  'use_vllm|vllm_mode|vllm_gpu_memory|vllm_enforce_eager' \
  | head -n 20
