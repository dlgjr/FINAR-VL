#!/usr/bin/env bash

ROOT="${QWEN3VL_ROOT:-/mnt/nas/bihaoran/qwen3vl}"
source "$ROOT/scripts/common/env.sh"

PYTHON_BIN="${PYTHON_BIN:-python}"
MODEL="${FINANCE_QA_MODEL:-/mnt/nas/bihaoran/model/qwen30}"
INPUT="${FINANCE_QA_INPUT:-$ROOT/data/finance_qa/all.jsonl}"
PROMPTS="${FINANCE_QA_PROMPTS:-$ROOT/data/finance_qa/prompts/financial_multimodal_prompt_library.md}"
RUN_ID="${FINANCE_QA_RUN_ID:-dsw_smoke}"
OUTPUT_DIR="${FINANCE_QA_OUTPUT_DIR:-$ROOT/output/finance_qa/runs/$RUN_ID}"
MAX_RECORDS_PER_TYPE="${MAX_RECORDS_PER_TYPE:-2}"
MAX_MODEL_CALLS="${FINANCE_QA_MAX_MODEL_CALLS:-5}"
TARGET_ACCEPTED="${FINANCE_QA_TARGET_ACCEPTED:-2}"
LOG_DIR="$ROOT/logs/finance_qa/dsw"

mkdir -p "$OUTPUT_DIR" "$LOG_DIR"
export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}"
export VLLM_WORKER_MULTIPROC_METHOD=spawn
export OMP_NUM_THREADS=1
export TOKENIZERS_PARALLELISM=false
export WANDB_DISABLED=true
unset RANK WORLD_SIZE LOCAL_RANK MASTER_ADDR MASTER_PORT

worker_log="$LOG_DIR/${RUN_ID}_worker_$(date +%Y%m%d_%H%M%S).log"
"$PYTHON_BIN" "$ROOT/scripts/generate_finance_qa.py" worker \
  --root "$ROOT" \
  --model "$MODEL" \
  --input "$INPUT" \
  --prompts "$PROMPTS" \
  --output-dir "$OUTPUT_DIR" \
  --rank 0 \
  --world-size 1 \
  --tensor-parallel-size 1 \
  --batch-size "${FINANCE_QA_BATCH_SIZE:-1}" \
  --max-model-len "${FINANCE_QA_MAX_MODEL_LEN:-65536}" \
  --max-num-seqs "${FINANCE_QA_MAX_NUM_SEQS:-1}" \
  --question-max-tokens "${FINANCE_QA_QUESTION_MAX_TOKENS:-9216}" \
  --answer-max-tokens "${FINANCE_QA_ANSWER_MAX_TOKENS:-16384}" \
  --question-min-images "${FINANCE_QA_QUESTION_MIN_IMAGES:-6}" \
  --question-max-images "${FINANCE_QA_QUESTION_MAX_IMAGES:-10}" \
  --question-temperature "${FINANCE_QA_QUESTION_TEMPERATURE:-0.9}" \
  --answer-temperature "${FINANCE_QA_ANSWER_TEMPERATURE:-0.6}" \
  --top-p "${FINANCE_QA_TOP_P:-0.95}" \
  --max-records-per-type "$MAX_RECORDS_PER_TYPE" \
  --target-accepted "$TARGET_ACCEPTED" \
  --max-model-calls "$MAX_MODEL_CALLS" \
  >"$worker_log" 2>&1 || true

"$PYTHON_BIN" "$ROOT/scripts/generate_finance_qa.py" merge \
  --output-dir "$OUTPUT_DIR" \
  --world-size 1

echo "FINANCE_QA_DSW_OK output=$OUTPUT_DIR"
