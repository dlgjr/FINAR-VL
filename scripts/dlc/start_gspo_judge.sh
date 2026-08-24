#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "$0")" && pwd)/gspo_env.sh"
: "${GSPO_JUDGE_MODEL:?GSPO_JUDGE_MODEL must point to Qwen3-VL-235B weights}"
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
  --tensor-parallel-size "$GSPO_JUDGE_TENSOR_PARALLEL_SIZE"
  --tokenizer-mode "$GSPO_JUDGE_TOKENIZER_MODE"
  --allowed-local-media-path "$GSPO_JUDGE_ALLOWED_MEDIA_PATH"
  --limit-mm-per-prompt "{\"image\":$GSPO_JUDGE_MAX_IMAGES,\"video\":0}"
  --kv-cache-dtype "$GSPO_JUDGE_KV_CACHE_DTYPE"
  --block-size "$GSPO_JUDGE_BLOCK_SIZE"
  --gpu-memory-utilization "$GSPO_JUDGE_GPU_MEMORY_UTILIZATION"
  --trust-remote-code
)
if [[ "$GSPO_JUDGE_EXPERT_PARALLEL" == "true" ]]; then ARGS+=(--enable-expert-parallel); fi
if [[ "$GSPO_JUDGE_ENFORCE_EAGER" == "true" ]]; then ARGS+=(--enforce-eager); fi
exec "$PYTHON_BIN" "${ARGS[@]}"
