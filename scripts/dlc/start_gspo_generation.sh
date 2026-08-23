#!/usr/bin/env bash
set -euo pipefail

ROOT="${QWEN3VL_ROOT:-/mnt/nas/bihaoran/qwen3vl}"
: "${SFT_MODEL:?SFT_MODEL must point to the shared full SFT checkpoint}"
: "${GENERATION_RL_DATA:?GENERATION_RL_DATA must point to the generation RL JSONL}"
: "${GENERATION_RL_OUTPUT_DIR:?GENERATION_RL_OUTPUT_DIR must be shared by all DLC nodes}"

export GSPO_MODEL="$SFT_MODEL"
export GSPO_SOURCE_DATA="$GENERATION_RL_DATA"
export GSPO_ROUTE_MODE=generation
export GSPO_OUTPUT_DIR="$GENERATION_RL_OUTPUT_DIR"

exec bash "$ROOT/scripts/dlc/start_gspo.sh"
