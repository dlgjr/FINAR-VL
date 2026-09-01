#!/usr/bin/env bash
set -euo pipefail

ROOT="${QWEN3VL_ROOT:-/mnt/nas/bihaoran/qwen3vl}"
PYTHON_BIN="${PYTHON_BIN:-/opt/ac2/bin/python}"
source "$ROOT/scripts/dlc/dlc_env.sh"
source "$ROOT/scripts/dlc/gspo_env.sh"
export GSPO_NNODES=1
export GSPO_NPROC_PER_NODE="${GSPO_DEBUG_NPROC_PER_NODE:-4}"
export GSPO_TRAIN_GPUS="${GSPO_DEBUG_TRAIN_GPUS:-0,1,2,3}"
export GSPO_JUDGE_GPU="${GSPO_DEBUG_JUDGE_GPU:-4}"
export GSPO_EXPECTED_COUNT="${GSPO_EXPECTED_COUNT:-0}"
export GSPO_EVAL_MAX_SAMPLES="${GSPO_EVAL_MAX_SAMPLES:-4}"
export GSPO_MAX_RESAMPLE_TIMES="${GSPO_MAX_RESAMPLE_TIMES:-3}"
export GSPO_NUM_GENERATIONS="${GSPO_NUM_GENERATIONS:-4}"
export GSPO_NUM_ITERATIONS="${GSPO_NUM_ITERATIONS:-2}"
export GSPO_NUM_TRAIN_EPOCHS="${GSPO_NUM_TRAIN_EPOCHS:-1}"
export GSPO_SAVE_STEPS="${GSPO_SAVE_STEPS:-5}"
export GSPO_EVAL_STEPS="${GSPO_EVAL_STEPS:-5}"
export GSPO_OUTPUT_DIR="${GSPO_OUTPUT_DIR:-$ROOT/output/dsw-gspo-debug}"

echo "DSW GSPO debug uses train GPUs $GSPO_TRAIN_GPUS and judge GPU $GSPO_JUDGE_GPU"
echo "Run the capacity probe separately: $PYTHON_BIN $ROOT/scripts/dsw/test_gspo_judge_capacity.py --url $GSPO_JUDGE_URL"
exec bash "$ROOT/scripts/dlc/start_gspo.sh"
