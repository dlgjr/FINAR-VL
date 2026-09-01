#!/usr/bin/env bash
set -euo pipefail

ROOT="${QWEN3VL_ROOT:-/mnt/nas/bihaoran/qwen3vl}"
PYTHON_BIN="${PYTHON_BIN:-/opt/ac2/bin/python}"
BASE_MODEL="${BASE_MODEL:-$ROOT/models/qwen4}"
SFT_ADAPTER="${SFT_ADAPTER:?SFT_ADAPTER must point to the completed SFT LoRA adapter}"
GSPO_MODEL="${GSPO_MODEL:?GSPO_MODEL is the output directory for the merged model}"

test -f "$BASE_MODEL/config.json" || { echo "missing base model: $BASE_MODEL" >&2; exit 1; }
test -f "$SFT_ADAPTER/adapter_config.json" || { echo "missing LoRA adapter: $SFT_ADAPTER/adapter_config.json" >&2; exit 1; }
"$PYTHON_BIN" -m scripts.rl.merge_sft_lora --base-model "$BASE_MODEL" --adapter "$SFT_ADAPTER" --output "$GSPO_MODEL"
test -f "$GSPO_MODEL/config.json" || { echo "merged model was not created: $GSPO_MODEL" >&2; exit 1; }
test ! -f "$GSPO_MODEL/adapter_config.json" || { echo "merged model still contains adapter_config.json" >&2; exit 1; }
echo "MERGED_FULL_MODEL_OK model=$GSPO_MODEL"

