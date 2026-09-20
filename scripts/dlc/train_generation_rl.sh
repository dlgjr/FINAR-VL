#!/usr/bin/env bash
set -euo pipefail

ROOT="${QWEN3VL_ROOT:-/mnt/nas/bihaoran/qwen3vl}"
GENERATION_START_MODEL="${GENERATION_START_MODEL:-/mnt/nas/bihaoran/qwen3vl/output/gspo/checkpoint-700}"
: "${GENERATION_RL_DATA:?GENERATION_RL_DATA must point to the generation RL JSONL}"
: "${GENERATION_RL_OUTPUT_DIR:?GENERATION_RL_OUTPUT_DIR must be shared by all DLC nodes}"

export QWEN3VL_ROOT="$ROOT"
export GSPO_ROUTE_MODE=generation
export ROOT_IMAGE_DIR="${ROOT_IMAGE_DIR:-$(dirname "$GENERATION_RL_DATA")}"
export GSPO_JUDGE_MAX_TOKENS="${GSPO_JUDGE_MAX_TOKENS:-1024}"
source "$ROOT/scripts/dlc/gspo_env.sh"
mkdir -p "$GENERATION_RL_OUTPUT_DIR"

GENERATION_RL_EVIDENCE_FACTS="${GENERATION_RL_EVIDENCE_FACTS:-$ROOT/data/synthetic/generation_rl/generation_evidence_facts.jsonl}"
GENERATION_RUBRIC_DATA="${GENERATION_RUBRIC_DATA:-$GENERATION_RL_OUTPUT_DIR/train_rl_generation_rubric.jsonl}"
GENERATION_RUBRIC_READY="$GENERATION_RL_OUTPUT_DIR/generation_rubric.ready"

if [[ "$GSPO_NODE_RANK" == "0" && ! -f "$GENERATION_RUBRIC_READY" ]]; then
  RUBRIC_JUDGE_LOG="$GENERATION_RL_OUTPUT_DIR/generation_rubric_judge.log"
  (
    export WANDB_MODE=disabled
    exec bash "$ROOT/scripts/dlc/start_gspo_judge.sh"
  ) >"$RUBRIC_JUDGE_LOG" 2>&1 &
  RUBRIC_JUDGE_PID=$!
  cleanup_rubric_judge() { kill "$RUBRIC_JUDGE_PID" 2>/dev/null || true; wait "$RUBRIC_JUDGE_PID" 2>/dev/null || true; }
  trap cleanup_rubric_judge EXIT
  for attempt in $(seq 1 1800); do
    if "${PYTHON_BIN:-/opt/ac2/bin/python}" -c "import urllib.request; urllib.request.urlopen('$GSPO_JUDGE_URL/health', timeout=2)" >/dev/null 2>&1; then break; fi
    sleep 2
  done
  "${PYTHON_BIN:-/opt/ac2/bin/python}" "$ROOT/scripts/rl/generate_generation_rubrics.py" \
    "$GENERATION_RL_DATA" "$GENERATION_RUBRIC_DATA" \
    --evidence-facts "$GENERATION_RL_EVIDENCE_FACTS" \
    --workers "${GENERATION_RUBRIC_WORKERS:-4}" \
    --max-tokens "${GENERATION_RUBRIC_MAX_TOKENS:-2048}"
  cleanup_rubric_judge
  trap - EXIT
  touch "$GENERATION_RUBRIC_READY"
elif [[ "$GSPO_NODE_RANK" != "0" ]]; then
  for attempt in $(seq 1 1800); do
    if [[ -f "$GENERATION_RUBRIC_READY" ]]; then break; fi
    sleep 1
  done
fi

UNIQUE_GSPO_SOURCE="$(mktemp /tmp/qwen3vl-gspo-generation-unique-ids.XXXXXX.jsonl)"
python "$ROOT/scripts/rl/ensure_unique_sample_ids.py" "$GENERATION_RUBRIC_DATA" "$UNIQUE_GSPO_SOURCE"

export GSPO_MODEL="$GENERATION_START_MODEL"
export GSPO_LEARNING_RATE="${GSPO_LEARNING_RATE:-2e-6}"
export GSPO_SOURCE_DATA="$UNIQUE_GSPO_SOURCE"
export GSPO_OUTPUT_DIR="$GENERATION_RL_OUTPUT_DIR"

LOCAL_GSPO_SCRIPT="$(mktemp /tmp/qwen3vl-start-gspo-generation.XXXXXX.sh)"
cp "$ROOT/scripts/dlc/start_gspo.sh" "$LOCAL_GSPO_SCRIPT"
exec bash "$LOCAL_GSPO_SCRIPT"
