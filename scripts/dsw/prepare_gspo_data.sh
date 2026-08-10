#!/usr/bin/env bash
set -euo pipefail

ROOT="${QWEN3VL_ROOT:-/mnt/nas/bihaoran/qwen3vl}"
cd "$ROOT"
export QWEN3VL_ROOT="$ROOT"
source "$ROOT/scripts/dlc/gspo_env.sh"
PYTHON_BIN="${PYTHON_BIN:-/opt/ac2/bin/python}"
SOURCE_DATA="${GSPO_SOURCE_DATA:-$ROOT/data/train_multi/train_rl_reasoning.jsonl}"
CLAIMS_CACHE="${GSPO_CLAIMS_CACHE:-$ROOT/output/gspo/gold_claims.json}"
DERIVED_DATA="${GSPO_DATA:-$ROOT/data/train_multi/train_rl_reasoning_gspo.jsonl}"
AUDIT_PATH="${GSPO_DATA_AUDIT:-$ROOT/output/gspo/train_rl_reasoning_gspo.audit.json}"
CLAIM_URL="${GSPO_CLAIM_JUDGE_URL:-http://127.0.0.1:8001}"
CLAIM_MODEL="${GSPO_JUDGE_SERVE_NAME:-qwen3-judge}"

test -f "$SOURCE_DATA" || { echo "missing source data: $SOURCE_DATA" >&2; exit 1; }
: "${GSPO_JUDGE_MODEL:?GSPO_JUDGE_MODEL must point to the Thinking judge weights}"

"$PYTHON_BIN" "$ROOT/scripts/rl/generate_gold_claims.py" "$SOURCE_DATA" "$CLAIMS_CACHE" --url "$CLAIM_URL" --model "$CLAIM_MODEL"
UNSCHEDULED_DATA="${DERIVED_DATA}.unscheduled"
"$PYTHON_BIN" -m scripts.rl.prepare_gspo_data "$SOURCE_DATA" "$UNSCHEDULED_DATA" "$AUDIT_PATH" --claims-json "$CLAIMS_CACHE"
"$PYTHON_BIN" -m scripts.rl.schedule_gspo_data "$UNSCHEDULED_DATA" "$DERIVED_DATA" --workers "$((GSPO_NNODES * GSPO_NPROC_PER_NODE))" --batch-size 7
rm -f "$UNSCHEDULED_DATA" "$UNSCHEDULED_DATA.schedule.json"
"$PYTHON_BIN" -m scripts.rl.validate_gspo_data "$DERIVED_DATA" --expected-count 6624 --root "$ROOT"
echo "GSPO_DATA_READY data=$DERIVED_DATA audit=$AUDIT_PATH claims=$CLAIMS_CACHE"
