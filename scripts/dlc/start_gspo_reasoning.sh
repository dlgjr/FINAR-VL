#!/usr/bin/env bash
set -euo pipefail

ROOT="${QWEN3VL_ROOT:-/mnt/nas/bihaoran/qwen3vl}"
: "${SFT_MODEL:?SFT_MODEL must point to the shared full SFT checkpoint}"
: "${REASONING_RL_DATA:?REASONING_RL_DATA must point to the reasoning RL JSONL}"
: "${REASONING_RL_OUTPUT_DIR:?REASONING_RL_OUTPUT_DIR must be shared by all DLC nodes}"

export GSPO_MODEL="$SFT_MODEL"
export GSPO_SOURCE_DATA="$REASONING_RL_DATA"
export GSPO_ROUTE_MODE=reasoning
export GSPO_OUTPUT_DIR="$REASONING_RL_OUTPUT_DIR"

LOCAL_GSPO_SCRIPT="$(mktemp /tmp/qwen3vl-start-gspo-reasoning.XXXXXX.sh)"
cp "$ROOT/scripts/dlc/start_gspo.sh" "$LOCAL_GSPO_SCRIPT"
exec bash "$LOCAL_GSPO_SCRIPT"
