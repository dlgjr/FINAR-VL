#!/usr/bin/env bash
set -euo pipefail

ROOT="${QWEN3VL_ROOT:-/mnt/nas/bihaoran/qwen3vl}"
cd "$ROOT"
export QWEN3VL_ROOT="$ROOT"
source "$ROOT/scripts/dlc/gspo_env.sh"
PYTHON_BIN="${PYTHON_BIN:-/opt/ac2/bin/python}"
SOURCE_DATA="${GSPO_SOURCE_DATA:?GSPO_SOURCE_DATA must point to one routed RL JSONL}"
DERIVED_DATA="${GSPO_DATA:-$ROOT/data/train_multi/train_rl_reasoning_gspo.jsonl}"
AUDIT_PATH="${GSPO_DATA_AUDIT:-$ROOT/output/gspo/train_rl_reasoning_gspo.audit.json}"

test -f "$SOURCE_DATA" || { echo "missing source data: $SOURCE_DATA" >&2; exit 1; }

UNSCHEDULED_DATA="${DERIVED_DATA}.unscheduled"
"$PYTHON_BIN" -m scripts.rl.prepare_gspo_data "$SOURCE_DATA" "$UNSCHEDULED_DATA" "$AUDIT_PATH"
"$PYTHON_BIN" -m scripts.rl.schedule_gspo_data "$UNSCHEDULED_DATA" "$DERIVED_DATA" --workers "$((GSPO_NNODES * GSPO_NPROC_PER_NODE))" --batch-size "$GSPO_SCHEDULE_BATCH_SIZE"
rm -f "$UNSCHEDULED_DATA" "$UNSCHEDULED_DATA.schedule.json"
EXPECTED_COUNT="$(wc -l < "$DERIVED_DATA" | tr -d ' ')"
"$PYTHON_BIN" -m scripts.rl.validate_gspo_data "$DERIVED_DATA" --expected-count "$EXPECTED_COUNT" --root "$ROOT" --route-mode "$GSPO_ROUTE_MODE" --report "${AUDIT_PATH%.json}.validation.json"
echo "GSPO_DATA_READY data=$DERIVED_DATA audit=$AUDIT_PATH route_mode=$GSPO_ROUTE_MODE count=$EXPECTED_COUNT"
