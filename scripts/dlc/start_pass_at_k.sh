#!/usr/bin/env bash

ROOT="${QWEN3VL_ROOT:-/mnt/nas/bihaoran/qwen3vl}"
NODE_WORLD_SIZE="${WORLD_SIZE:?DLC must provide WORLD_SIZE}"
NODE_RANK="${RANK:?DLC must provide RANK}"
GPUS_PER_NODE="${NPROC_PER_NODE:-8}"
source "$ROOT/scripts/common/env.sh"

export PYTHONUSERBASE="${PYTHONUSERBASE:-$ROOT/python-user}"
export PYTHON_USER_SITE="$PYTHONUSERBASE/lib/python3.12/site-packages"
export PATH="$PYTHONUSERBASE/bin:/opt/ac2/bin:$PATH"
export PYTHONPATH="$PYTHON_USER_SITE${PYTHONPATH:+:$PYTHONPATH}"
unset PYTHONNOUSERSITE VIRTUAL_ENV

PYTHON_BIN="${PYTHON_BIN:-/opt/ac2/bin/python}"
GLOBAL_WORLD_SIZE=$((NODE_WORLD_SIZE * GPUS_PER_NODE))
OUTPUT_DIR="${PASS_AT_K_OUTPUT_DIR:-$ROOT/output/pass_at_k/qwen4_k8}"
WAIT_TIMEOUT="${PASS_AT_K_WAIT_TIMEOUT:-0}"
STARTUP_TIMEOUT="${PASS_AT_K_STARTUP_TIMEOUT:-600}"
STALE_TIMEOUT="${PASS_AT_K_STALE_TIMEOUT:-7200}"
MAX_IMAGES_PER_PROMPT="${PASS_AT_K_MAX_IMAGES_PER_PROMPT:-8}"
LOG_DIR="$ROOT/logs/pass_at_k/dlc"

mkdir -p "$OUTPUT_DIR" "$LOG_DIR"

pids=()
for ((local_rank = 0; local_rank < GPUS_PER_NODE; local_rank++)); do
  global_rank=$((NODE_RANK * GPUS_PER_NODE + local_rank))
  rank_log="$LOG_DIR/rank_${global_rank}_$(date +%Y%m%d_%H%M%S).log"
  (
    export CUDA_VISIBLE_DEVICES="$local_rank"
    export VLLM_WORKER_MULTIPROC_METHOD=spawn
    export OMP_NUM_THREADS=1
    export TOKENIZERS_PARALLELISM=false
    unset RANK WORLD_SIZE LOCAL_RANK MASTER_ADDR MASTER_PORT
    "$PYTHON_BIN" "$ROOT/scripts/pass_at_k.py" worker \
      --root "$ROOT" \
      --model "$ROOT/models/qwen4" \
      --train-multi "$ROOT/data/train_multi/all.jsonl" \
      --train-text "$ROOT/data/train_text/all.jsonl" \
      --output-dir "$OUTPUT_DIR" \
      --rank "$global_rank" \
      --world-size "$GLOBAL_WORLD_SIZE" \
      --max-images-per-prompt "$MAX_IMAGES_PER_PROMPT"
  ) >"$rank_log" 2>&1 &
  pids+=("$!")
done

for index in "${!pids[@]}"; do
  wait "${pids[$index]}" || true
done

if ((NODE_RANK == 0)); then
  "$PYTHON_BIN" "$ROOT/scripts/pass_at_k.py" merge \
    --root "$ROOT" \
    --output-dir "$OUTPUT_DIR" \
    --world-size "$GLOBAL_WORLD_SIZE" \
    --wait-timeout "$WAIT_TIMEOUT" \
    --startup-timeout "$STARTUP_TIMEOUT" \
    --stale-timeout "$STALE_TIMEOUT"
fi

echo "PASS_AT_K_DLC_NODE_OK node_rank=$NODE_RANK output=$OUTPUT_DIR"
