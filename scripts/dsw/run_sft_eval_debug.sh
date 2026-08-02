#!/usr/bin/env bash
set -euo pipefail

ROOT="${QWEN3VL_ROOT:-/mnt/nas/bihaoran/qwen3vl}"
cd "$ROOT"
source "$ROOT/scripts/dlc/dlc_env.sh"
BASE_MODEL="$ROOT/models/qwen4"
RUN_ID="${SFT_DSW_RUN_ID:-sft_eval_$(date +%Y%m%d_%H%M%S)}"
RUN_DIR="${SFT_DSW_OUTPUT_DIR:-$ROOT/output/sft_eval/$RUN_ID}"
export TMPDIR=/tmp
export TMP="$TMPDIR"
export TEMP="$TMPDIR"
export WANDB_DISABLED=true
export WANDB_MODE=disabled
export SFT_EVAL_MAX_SAMPLES=1
export SFT_BENCHMARK="${SFT_BENCHMARK:-$ROOT/data/benchmark/my_benchmark/all.jsonl}"
export SFT_EVAL_OUTPUT="$RUN_DIR/eval"
SFT_JUDGE_PORT="${SFT_JUDGE_PORT:-8001}"
export SFT_JUDGE_URL="${SFT_JUDGE_URL:-http://127.0.0.1:$SFT_JUDGE_PORT}"

PYTHON_BIN="${PYTHON_BIN:-/opt/ac2/bin/python}"
mkdir -p "$RUN_DIR/eval"
test -f "$BASE_MODEL/config.json" || { echo "missing model: $BASE_MODEL" >&2; exit 1; }
test -f "$SFT_BENCHMARK" || { echo "missing benchmark: $SFT_BENCHMARK" >&2; exit 1; }

CUDA_VISIBLE_DEVICES=2,3 "$PYTHON_BIN" -m vllm.entrypoints.openai.api_server \
  --model "$BASE_MODEL" --served-model-name qwen4-judge --tensor-parallel-size 2 \
  --dtype bfloat16 --gpu-memory-utilization 0.5 --max-num-seqs 8 --max-model-len 8192 \
  --host 127.0.0.1 --port "$SFT_JUDGE_PORT" >/tmp/qwen4-judge.log 2>&1 &
JUDGE_PID=$!
trap 'kill "$JUDGE_PID" 2>/dev/null || true' EXIT

for _ in $(seq 1 120); do
  if "$PYTHON_BIN" -c "import urllib.request; urllib.request.urlopen('$SFT_JUDGE_URL/health', timeout=2)" >/dev/null 2>&1; then break; fi
  sleep 1
done
"$PYTHON_BIN" -c "import urllib.request; urllib.request.urlopen('$SFT_JUDGE_URL/health', timeout=2)" >/dev/null 2>&1 || { echo "qwen4-judge vLLM did not become ready" >&2; exit 1; }

export CUDA_VISIBLE_DEVICES=0
"$PYTHON_BIN" "$ROOT/scripts/sft/run_eval_only.py" \
  --model "$BASE_MODEL" --model_type qwen3_vl --infer_backend transformers \
  --torch_dtype bfloat16 --attn_impl sdpa --device_map cuda:0
