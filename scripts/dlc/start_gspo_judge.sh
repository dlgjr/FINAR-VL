#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "$0")" && pwd)/gspo_env.sh"
: "${GSPO_JUDGE_MODEL:?GSPO_JUDGE_MODEL must point to Qwen3-VL-30B-A3B-Thinking weights}"
PYTHON_BIN="${PYTHON_BIN:-/opt/ac2/bin/python}"
export CUDA_VISIBLE_DEVICES="$GSPO_JUDGE_GPU"
ARGS=(
  -m vllm.entrypoints.openai.api_server
  --model "$GSPO_JUDGE_MODEL"
  --served-model-name "$GSPO_JUDGE_SERVE_NAME"
  --host 127.0.0.1
  --port "$GSPO_JUDGE_PORT"
  --dtype "$GSPO_JUDGE_DTYPE"
  --max-model-len "$GSPO_JUDGE_MAX_MODEL_LEN"
  --max-num-seqs "$GSPO_JUDGE_MAX_NUM_SEQS"
  --tensor-parallel-size 1
  --gpu-memory-utilization "$GSPO_JUDGE_GPU_MEMORY_UTILIZATION"
)
if [[ "$GSPO_JUDGE_ENFORCE_EAGER" == "true" ]]; then ARGS+=(--enforce-eager); fi
exec "$PYTHON_BIN" "${ARGS[@]}"

