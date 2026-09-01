#!/usr/bin/env bash

ROOT="${QWEN3VL_ROOT:-/mnt/nas/bihaoran/qwen3vl}"
NODE_WORLD_SIZE="${WORLD_SIZE:?DLC must provide WORLD_SIZE}"
NODE_RANK="${RANK:?DLC must provide RANK}"
TENSOR_PARALLEL_SIZE=4
WORKERS_PER_NODE=2
GLOBAL_WORLD_SIZE=$((NODE_WORLD_SIZE * WORKERS_PER_NODE))
source "$ROOT/scripts/common/env.sh"

export PYTHONUSERBASE="${PYTHONUSERBASE:-$ROOT/python-user}"
export PYTHON_USER_SITE="$PYTHONUSERBASE/lib/python3.12/site-packages"
export PATH="$PYTHONUSERBASE/bin:/opt/ac2/bin:$PATH"
export PYTHONPATH="$PYTHON_USER_SITE${PYTHONPATH:+:$PYTHONPATH}"
unset PYTHONNOUSERSITE VIRTUAL_ENV

PYTHON_BIN="${PYTHON_BIN:-/opt/ac2/bin/python}"
MODEL="${FINANCE_QA_MODEL:-/mnt/nas/bihaoran/model/qwen235}"
INPUT="${FINANCE_QA_INPUT:-$ROOT/data/finance_qa/all.jsonl}"
PROMPTS="${FINANCE_QA_PROMPTS:-$ROOT/data/finance_qa/prompts/financial_multimodal_prompt_library.md}"
RUN_ID="${FINANCE_QA_RUN_ID:-qwen235_full}"
OUTPUT_DIR="${FINANCE_QA_OUTPUT_DIR:-$ROOT/output/finance_qa/runs/$RUN_ID}"
LOG_DIR="$ROOT/logs/finance_qa/dlc"

mkdir -p "$OUTPUT_DIR" "$LOG_DIR"
export VLLM_WORKER_MULTIPROC_METHOD=spawn
export OMP_NUM_THREADS=1
export TOKENIZERS_PARALLELISM=false
export WANDB_DISABLED=true

device_groups=("0,1,2,3" "4,5,6,7")
pids=()
for ((local_worker = 0; local_worker < WORKERS_PER_NODE; local_worker++)); do
  global_rank=$((NODE_RANK * WORKERS_PER_NODE + local_worker))
  worker_log="$LOG_DIR/${RUN_ID}_rank_${global_rank}_$(date +%Y%m%d_%H%M%S).log"
  (
    export CUDA_VISIBLE_DEVICES="${device_groups[$local_worker]}"
    unset RANK WORLD_SIZE LOCAL_RANK MASTER_ADDR MASTER_PORT
    "$PYTHON_BIN" "$ROOT/scripts/generate_finance_qa.py" worker \
      --root "$ROOT" \
      --model "$MODEL" \
      --input "$INPUT" \
      --prompts "$PROMPTS" \
      --output-dir "$OUTPUT_DIR" \
      --rank "$global_rank" \
      --world-size "$GLOBAL_WORLD_SIZE" \
      --tensor-parallel-size "$TENSOR_PARALLEL_SIZE" \
      --batch-size "${FINANCE_QA_BATCH_SIZE:-2}" \
      --max-model-len "${FINANCE_QA_MAX_MODEL_LEN:-65536}" \
      --max-num-seqs "${FINANCE_QA_MAX_NUM_SEQS:-4}" \
      --question-max-tokens "${FINANCE_QA_QUESTION_MAX_TOKENS:-9216}" \
      --answer-max-tokens "${FINANCE_QA_ANSWER_MAX_TOKENS:-16384}" \
      --question-min-images "${FINANCE_QA_QUESTION_MIN_IMAGES:-6}" \
      --question-max-images "${FINANCE_QA_QUESTION_MAX_IMAGES:-10}" \
      --question-temperature "${FINANCE_QA_QUESTION_TEMPERATURE:-0.9}" \
      --answer-temperature "${FINANCE_QA_ANSWER_TEMPERATURE:-0.6}" \
      --top-p "${FINANCE_QA_TOP_P:-0.95}"
  ) >"$worker_log" 2>&1 &
  pids+=("$!")
done

for pid in "${pids[@]}"; do
  wait "$pid" || true
done

if ((NODE_RANK == 0)); then
  "$PYTHON_BIN" "$ROOT/scripts/generate_finance_qa.py" merge \
    --output-dir "$OUTPUT_DIR" \
    --world-size "$GLOBAL_WORLD_SIZE" \
    --wait-timeout "${FINANCE_QA_WAIT_TIMEOUT:-0}" \
    --startup-timeout "${FINANCE_QA_STARTUP_TIMEOUT:-600}" \
    --stale-timeout "${FINANCE_QA_STALE_TIMEOUT:-7200}"
fi

echo "FINANCE_QA_DLC_NODE_OK node_rank=$NODE_RANK output=$OUTPUT_DIR"
