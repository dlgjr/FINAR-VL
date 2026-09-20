#!/usr/bin/env bash
set -euo pipefail

ROOT="${QWEN3VL_ROOT:-/mnt/nas/bihaoran/qwen3vl}"
GENERATION_START_MODEL="${GENERATION_START_MODEL:-/mnt/nas/bihaoran/qwen3vl/output/gspo/checkpoint-700}"
: "${GENERATION_RL_DATA:?GENERATION_RL_DATA must point to the generation RL JSONL}"
: "${GENERATION_RL_OUTPUT_DIR:?GENERATION_RL_OUTPUT_DIR must be shared by all DLC nodes}"

UNIQUE_GSPO_SOURCE="$(mktemp /tmp/qwen3vl-gspo-generation-unique-ids.XXXXXX.jsonl)"
python "$ROOT/scripts/rl/ensure_unique_sample_ids.py" "$GENERATION_RL_DATA" "$UNIQUE_GSPO_SOURCE"

export GSPO_MODEL="$GENERATION_START_MODEL"
export GSPO_LEARNING_RATE="${GSPO_LEARNING_RATE:-2e-6}"
export ROOT_IMAGE_DIR="${ROOT_IMAGE_DIR:-$(dirname "$GENERATION_RL_DATA")}" 
export GSPO_SOURCE_DATA="$UNIQUE_GSPO_SOURCE"
export GSPO_ROUTE_MODE=generation
export GSPO_OUTPUT_DIR="$GENERATION_RL_OUTPUT_DIR"

LOCAL_GSPO_SCRIPT="$(mktemp /tmp/qwen3vl-start-gspo-generation.XXXXXX.sh)"
cp "$ROOT/scripts/dlc/start_gspo.sh" "$LOCAL_GSPO_SCRIPT"
exec bash "$LOCAL_GSPO_SCRIPT"
