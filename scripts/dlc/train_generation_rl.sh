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
export GSPO_GENERATION_ACCEPT_THRESHOLD="${GSPO_GENERATION_ACCEPT_THRESHOLD:-0.75}"
export GSPO_GENERATION_LEARNABILITY_POWER="${GSPO_GENERATION_LEARNABILITY_POWER:-1.0}"
export GSPO_GENERATION_CRITERION_EPS="${GSPO_GENERATION_CRITERION_EPS:-1e-6}"
export GENERATION_RUBRIC_MIN_POINTS="${GENERATION_RUBRIC_MIN_POINTS:-2}"
export GENERATION_RUBRIC_MAX_POINTS="${GENERATION_RUBRIC_MAX_POINTS:-15}"
source "$ROOT/scripts/dlc/gspo_env.sh"
mkdir -p "$GENERATION_RL_OUTPUT_DIR"

GENERATION_RL_EVIDENCE_FACTS="${GENERATION_RL_EVIDENCE_FACTS:-$ROOT/data/synthetic/generation_rl/generation_evidence_facts.jsonl}"
GENERATION_RUBRIC_DATA="${GENERATION_RUBRIC_DATA:-$GENERATION_RL_OUTPUT_DIR/train_rl_generation_rubric_v3_dynamic.jsonl}"
GENERATION_RUBRIC_READY="$GENERATION_RL_OUTPUT_DIR/generation_rubric_v3_dynamic.ready"

if [[ "$GSPO_NODE_RANK" == "0" && ! -f "$GENERATION_RUBRIC_READY" ]]; then
  RUBRIC_JUDGE_LOG="$GENERATION_RL_OUTPUT_DIR/generation_rubric_judge.log"
  (
    export WANDB_MODE=disabled
    exec bash "$ROOT/scripts/dlc/start_gspo_judge.sh"
  ) >"$RUBRIC_JUDGE_LOG" 2>&1 &
  RUBRIC_JUDGE_PID=$!
  cleanup_rubric_judge() { kill "$RUBRIC_JUDGE_PID" 2>/dev/null || true; wait "$RUBRIC_JUDGE_PID" 2>/dev/null || true; }
  trap cleanup_rubric_judge EXIT
  RUBRIC_JUDGE_READY=false
  for attempt in $(seq 1 1800); do
    if "${PYTHON_BIN:-/opt/ac2/bin/python}" -c "import urllib.request; urllib.request.urlopen('$GSPO_JUDGE_URL/health', timeout=2)" >/dev/null 2>&1; then
      RUBRIC_JUDGE_READY=true
      break
    fi
    sleep 2
  done
  if [[ "$RUBRIC_JUDGE_READY" != "true" ]]; then
    echo "rubric judge server failed to become healthy: $RUBRIC_JUDGE_LOG" >&2
    exit 1
  fi
  "${PYTHON_BIN:-/opt/ac2/bin/python}" "$ROOT/scripts/rl/generate_generation_rubrics.py" \
    "$GENERATION_RL_DATA" "$GENERATION_RUBRIC_DATA" \
    --evidence-facts "$GENERATION_RL_EVIDENCE_FACTS" \
    --workers "${GENERATION_RUBRIC_WORKERS:-4}" \
    --max-tokens "${GENERATION_RUBRIC_MAX_TOKENS:-2048}" \
    --min-points "$GENERATION_RUBRIC_MIN_POINTS" \
    --max-points "$GENERATION_RUBRIC_MAX_POINTS"
  cleanup_rubric_judge
  trap - EXIT
  touch "$GENERATION_RUBRIC_READY"
elif [[ "$GSPO_NODE_RANK" != "0" ]]; then
  for attempt in $(seq 1 1800); do
    if [[ -f "$GENERATION_RUBRIC_READY" ]]; then break; fi
    sleep 1
  done
  test -f "$GENERATION_RUBRIC_READY" || { echo "timed out waiting for generation rubric data" >&2; exit 1; }
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
