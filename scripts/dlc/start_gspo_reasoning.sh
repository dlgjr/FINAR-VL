#!/usr/bin/env bash
set -euo pipefail

ROOT="${QWEN3VL_ROOT:-/mnt/nas/bihaoran/qwen3vl}"
REASONING_START_MODEL="${REASONING_START_MODEL:-/mnt/nas/bihaoran/qwen3vl/output/sft_test_unclean/checkpoint15500_ep2_lr1e5/checkpoint-2744}"
: "${REASONING_RL_DATA:?REASONING_RL_DATA must point to the reasoning RL JSONL}"
: "${REASONING_RL_OUTPUT_DIR:?REASONING_RL_OUTPUT_DIR must be shared by all DLC nodes}"

export GSPO_MODEL="$REASONING_START_MODEL"
export GSPO_LEARNING_RATE="${GSPO_LEARNING_RATE:-5e-7}"
export GSPO_NUM_GENERATIONS="${GSPO_NUM_GENERATIONS:-16}"
export GSPO_GENERATION_BATCH_SIZE="${GSPO_GENERATION_BATCH_SIZE:-32}"
export GSPO_STEPS_PER_GENERATION="${GSPO_STEPS_PER_GENERATION:-2}"
export GSPO_DYNAMIC_SAMPLE="${GSPO_DYNAMIC_SAMPLE:-true}"
export GSPO_TEMPERATURE="${GSPO_TEMPERATURE:-1.2}"
export GSPO_SOURCE_DATA="$REASONING_RL_DATA"
export GSPO_ROUTE_MODE=reasoning
export GSPO_OUTPUT_DIR="$REASONING_RL_OUTPUT_DIR"

LOCAL_GSPO_SCRIPT="$(mktemp /tmp/qwen3vl-start-gspo-reasoning.XXXXXX.sh)"
cp "$ROOT/scripts/dlc/start_gspo.sh" "$LOCAL_GSPO_SCRIPT"
exec bash "$LOCAL_GSPO_SCRIPT"
