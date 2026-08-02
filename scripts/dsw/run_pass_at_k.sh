#!/usr/bin/env bash

ROOT="${QWEN3VL_ROOT:-/mnt/nas/bihaoran/qwen3vl}"
source "$ROOT/scripts/common/env.sh"

PYTHON_BIN="${PYTHON_BIN:-python}"
NPROC_PER_NODE="${NPROC_PER_NODE:-4}"
OUTPUT_DIR="${PASS_AT_K_OUTPUT_DIR:-$ROOT/output/pass_at_k/qwen4_k8_dsw_smoke}"
MAX_RECORDS_PER_RANK="${MAX_RECORDS_PER_RANK:-2}"
LOG_DIR="$ROOT/logs/pass_at_k/dsw"

mkdir -p "$OUTPUT_DIR" "$LOG_DIR"

worker_extra_args=()
if [[ "$MAX_RECORDS_PER_RANK" != "all" ]]; then
  worker_extra_args+=(--max-records-per-rank "$MAX_RECORDS_PER_RANK")
fi

pids=()
for ((local_rank = 0; local_rank < NPROC_PER_NODE; local_rank++)); do
  rank_log="$LOG_DIR/rank_${local_rank}_$(date +%Y%m%d_%H%M%S).log"
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
      --rank "$local_rank" \
      --world-size "$NPROC_PER_NODE" \
      "${worker_extra_args[@]}"
  ) >"$rank_log" 2>&1 &
  pids+=("$!")
done

for index in "${!pids[@]}"; do
  wait "${pids[$index]}" || true
done

"$PYTHON_BIN" "$ROOT/scripts/pass_at_k.py" merge \
  --root "$ROOT" \
  --output-dir "$OUTPUT_DIR" \
  --world-size "$NPROC_PER_NODE"

echo "PASS_AT_K_DSW_OK output=$OUTPUT_DIR"
