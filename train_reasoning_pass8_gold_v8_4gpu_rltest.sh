#!/usr/bin/env bash

ROOT=/mnt/nas/duolg/qwen3vl
cd "$ROOT" || exit 1

export QWEN3VL_ROOT="$ROOT"

# ===== Data / model =====
REFERENCE_MODEL="$ROOT/output/sft_test_unclean/checkpoint-550"
export REASONING_RL_DATA="$ROOT/data/train_multi/train_rl_reasoning_rule_12835_gold.jsonl"
# Optional fresh branch mode: initialize policy weights from an existing model
# checkpoint without loading Trainer/optimizer/RNG state. KL remains anchored to
# the original SFT reference unless GSPO_REF_MODEL is explicitly overridden.
export GSPO_INIT_MODEL="${GSPO_INIT_MODEL:-}"
export REASONING_START_MODEL="${GSPO_INIT_MODEL:-$REFERENCE_MODEL}"
export GSPO_REF_MODEL="${GSPO_REF_MODEL:-$REFERENCE_MODEL}"

# ===== Single node, 4 GPUs =====
export GSPO_NNODES=1
export GSPO_NODE_RANK=0
export GSPO_NPROC_PER_NODE=4
export GSPO_TRAIN_GPUS=0,1,2,3
export GSPO_MASTER_ADDR=127.0.0.1
export GSPO_MASTER_PORT=29500

# ===== Reasoning / Pass@8 =====
export GSPO_ROUTE_MODE=reasoning
export GSPO_ENABLE_JUDGE=false
export GSPO_NUM_GENERATIONS=8
export GSPO_GENERATION_BATCH_SIZE=32
export GSPO_SCHEDULE_BATCH_SIZE=4

# Post-selection shaping:
# - the 3 shortest wrong/partial responses in each Pass@8 group get -0.3;
# - correct responses that fall in the shortest 3 get only -0.1;
# - reasoning >400 gets -0.3;
# - exact numeric hits get +0.4 on top of the normal tolerance-window reward;
# - the longest correct online response <=400 gets +0.2.
# DIRECT_TOKENS=100 remains only as the W&B observational too-short threshold.
export GSPO_REASONING_SHORT_TOKENS=0
export GSPO_REASONING_DIRECT_TOKENS=100
export GSPO_REASONING_LONG_TOKENS=400
export GSPO_REASONING_LENGTH_PENALTY=0.3
export GSPO_REASONING_CORRECT_SHORT_PENALTY=0.1
export GSPO_EXACT_NUMERIC_BONUS=0.4
export GSPO_REASONING_LONGEST_CORRECT_BONUS=0.2

# ===== Training =====
export GSPO_NUM_TRAIN_EPOCHS=4
export GSPO_BATCH_SIZE=1
export GSPO_GRAD_ACC=1
export GSPO_DYNAMIC_SAMPLE=true
export GSPO_MAX_RESAMPLE_TIMES=3

export GSPO_LEARNING_RATE=1e-6
export GSPO_BETA=0.01
# Keep KL anchored to the original reference model.
export GSPO_SYNC_REF_MODEL=false
export GSPO_ENTROPY_COEF=0.001
export GSPO_MAX_GRAD_NORM=1.0
export GSPO_EPSILON=0.03
export GSPO_EPSILON_HIGH=0.05

export GSPO_STEPS_PER_GENERATION=8
export GSPO_NUM_ITERATIONS=1
export GSPO_TEMPERATURE=1.2
# start_gspo.sh uses a constant scheduler; keep the legacy callback decay out of this run.
export GSPO_LR_DECAY_STEPS=1000000000

# ===== Checkpoint / logging =====
# One W&B train point per 32-completion generation batch; fixed eval every 40 steps via save.
export GSPO_LOGGING_STEPS=8
export GSPO_SAVE_STEPS=40
export GSPO_EVAL_STEPS=40
export GSPO_SAVE_TOTAL_LIMIT=30

# ===== Gold injection =====
export GSPO_GOLD_INJECT=true
export GSPO_GOLD_REWARD=1.0

# ===== Fixed RL eval set: 50 questions, 3 fixed seeds, mean Pass@k =====
export GSPO_EVAL_DATA="$ROOT/data/benchmark/reasoning_calc_seen_50_clean.jsonl"
export SFT_BENCHMARK="$GSPO_EVAL_DATA"
export GSPO_EVAL_MAX_SAMPLES=50
export GSPO_EVAL_SEEDS=17,42,73

# ===== Image roots =====
export GSPO_TRAIN_ASSET_ROOT="$ROOT/data/train_multi/assets_rl"
export GSPO_BENCH_ASSET_ROOT="$ROOT/data/benchmark/assets"
export SFT_BENCHMARK_ASSET_ROOT="$ROOT/data/benchmark/assets"
export ROOT_IMAGE_DIR="$ROOT/data/train_multi"

# ===== vLLM colocate =====
export GSPO_USE_VLLM=true
export GSPO_VLLM_MODE=colocate
export GSPO_VLLM_TENSOR_PARALLEL_SIZE=4
export GSPO_VLLM_MAX_NUM_SEQS=4
# Leave extra headroom for optimizer state and repeated eval -> vLLM sleep/wake cycles.
export GSPO_VLLM_GPU_MEMORY_UTILIZATION=0.20
export GSPO_VLLM_ENFORCE_EAGER=true
export GSPO_VLLM_MM_PROCESSOR_CACHE_GB=0
export GSPO_VLLM_SLEEP_LEVEL=1

# ===== W&B =====
export WANDB_PROJECT=FINAR-VL-GSPO
export WANDB_ENTITY="${WANDB_ENTITY:-985039081-jilindaxue}"

RESUME_CHECKPOINT="${GSPO_RESUME_FROM_CHECKPOINT:-}"
if [[ -n "$RESUME_CHECKPOINT" && -n "$GSPO_INIT_MODEL" ]]; then
  echo "Use either GSPO_RESUME_FROM_CHECKPOINT (full-state resume) or GSPO_INIT_MODEL (fresh weight-only branch), not both"
  exit 1
fi

if [[ -n "$RESUME_CHECKPOINT" ]]; then
  : "${WANDB_RUN_ID:?Set WANDB_RUN_ID before resuming}"
  export WANDB_MODE="${WANDB_MODE:-online}"
  export WANDB_RESUME="${WANDB_RESUME:-must}"
  RUN_ROOT="$(dirname "$(dirname "$RESUME_CHECKPOINT")")"
  RUN_ID="$(basename "$RUN_ROOT")"
  export REASONING_RL_OUTPUT_DIR="$RUN_ROOT"
else
  export WANDB_MODE="${WANDB_MODE:-offline}"
  if [[ -n "$GSPO_INIT_MODEL" ]]; then
    INIT_TAG="$(basename "$GSPO_INIT_MODEL")"
    RUN_ID="reasoning_pass8_gold_v8_fresh_${INIT_TAG}_$(date +%Y%m%d_%H%M%S)"
  else
    RUN_ID="reasoning_pass8_gold_v8_4gpu_$(date +%Y%m%d_%H%M%S)"
  fi
  export REASONING_RL_OUTPUT_DIR="$ROOT/output/gspo/$RUN_ID"
fi
export GSPO_RESUME_FROM_CHECKPOINT="$RESUME_CHECKPOINT"
export GSPO_RUN_ID="$RUN_ID"

# Optional W&B branch mode. When WANDB_HISTORY_SOURCE_RUN_ID is set, seed a
# fresh target run with the source run's scalar history through the checkpoint
# step, then continue logging new reward-v2 training data into that target run.
WANDB_HISTORY_SOURCE_RUN_ID="${WANDB_HISTORY_SOURCE_RUN_ID:-}"
WANDB_HISTORY_UNTIL_STEP="${WANDB_HISTORY_UNTIL_STEP:-}"
if [[ -n "$WANDB_HISTORY_SOURCE_RUN_ID" ]]; then
  if [[ -z "$RESUME_CHECKPOINT" ]]; then
    echo "WANDB history cloning requires GSPO_RESUME_FROM_CHECKPOINT"
    exit 1
  fi
  if [[ "$WANDB_MODE" != "online" ]]; then
    echo "WANDB history cloning requires WANDB_MODE=online"
    exit 1
  fi
  if [[ "$WANDB_RUN_ID" == "$WANDB_HISTORY_SOURCE_RUN_ID" ]]; then
    echo "WANDB_RUN_ID must differ from WANDB_HISTORY_SOURCE_RUN_ID"
    exit 1
  fi
  if [[ -z "$WANDB_HISTORY_UNTIL_STEP" ]]; then
    CKPT_NAME="$(basename "$RESUME_CHECKPOINT")"
    if [[ "$CKPT_NAME" != checkpoint-* || ! "${CKPT_NAME#checkpoint-}" =~ ^[0-9]+$ ]]; then
      echo "Cannot derive W&B history branch step from checkpoint: $RESUME_CHECKPOINT"
      exit 1
    fi
    WANDB_HISTORY_UNTIL_STEP="${CKPT_NAME#checkpoint-}"
  fi
  export WANDB_HISTORY_UNTIL_STEP
  export WANDB_NAME="${WANDB_NAME:-${RUN_ID}_rewardv2_from${WANDB_HISTORY_UNTIL_STEP}}"

  echo "===== W&B HISTORY BRANCH ====="
  echo "WANDB_ENTITY=$WANDB_ENTITY"
  echo "WANDB_PROJECT=$WANDB_PROJECT"
  echo "WANDB_HISTORY_SOURCE_RUN_ID=$WANDB_HISTORY_SOURCE_RUN_ID"
  echo "WANDB_HISTORY_UNTIL_STEP=$WANDB_HISTORY_UNTIL_STEP"
  echo "WANDB_TARGET_RUN_ID=$WANDB_RUN_ID"
  echo "WANDB_TARGET_NAME=$WANDB_NAME"

  /opt/ac2/bin/python "$ROOT/scripts/dlc/clone_wandb_history.py" \
    --entity "$WANDB_ENTITY" \
    --project "$WANDB_PROJECT" \
    --source-run-id "$WANDB_HISTORY_SOURCE_RUN_ID" \
    --target-run-id "$WANDB_RUN_ID" \
    --until-step "$WANDB_HISTORY_UNTIL_STEP" \
    --target-name "$WANDB_NAME" || exit $?

  # The clone helper creates/seeds the target run and closes it. Trainer then
  # reopens exactly that target run and appends post-branch history.
  export WANDB_RESUME=must
else
  export WANDB_NAME="${WANDB_NAME:-$RUN_ID}"
fi

mkdir -p "$REASONING_RL_OUTPUT_DIR"
TRAIN_LOG="$REASONING_RL_OUTPUT_DIR/train.log"
if [[ -n "$RESUME_CHECKPOINT" ]]; then
  TRAIN_LOG="$REASONING_RL_OUTPUT_DIR/train_resume_$(basename "$RESUME_CHECKPOINT").log"
fi

echo "===== RUN CONFIG ====="
echo "ROOT=$ROOT"
echo "MODEL=$REASONING_START_MODEL"
echo "REF_MODEL=$GSPO_REF_MODEL"
echo "INIT_MODEL=${GSPO_INIT_MODEL:-}"
echo "DATA=$REASONING_RL_DATA"
echo "OUTPUT=$REASONING_RL_OUTPUT_DIR"
echo "RESUME_FROM=$RESUME_CHECKPOINT"
echo "WANDB_MODE=$WANDB_MODE"
echo "WANDB_ENTITY=$WANDB_ENTITY"
echo "WANDB_RUN_ID=${WANDB_RUN_ID:-}"
echo "WANDB_NAME=${WANDB_NAME:-}"
echo "WANDB_RESUME=${WANDB_RESUME:-}"
echo "GPUS=$GSPO_TRAIN_GPUS"
echo "NPROC=$GSPO_NPROC_PER_NODE"
echo "GENERATIONS=$GSPO_NUM_GENERATIONS"
echo "GENERATION_BATCH=$GSPO_GENERATION_BATCH_SIZE  # must be 1*4*8=32"
echo "NUM_ITERATIONS=$GSPO_NUM_ITERATIONS"
echo "SAVE_EVAL_STEPS=$GSPO_SAVE_STEPS"
echo "LOGGING_STEPS=$GSPO_LOGGING_STEPS"
echo "REWARD_SHAPING=exact_numeric:+${GSPO_EXACT_NUMERIC_BONUS}, longest_correct<=${GSPO_REASONING_LONG_TOKENS}:+${GSPO_REASONING_LONGEST_CORRECT_BONUS}, shortest3_wrong:-${GSPO_REASONING_LENGTH_PENALTY}, shortest3_correct:-${GSPO_REASONING_CORRECT_SHORT_PENALTY}, reasoning>${GSPO_REASONING_LONG_TOKENS}:-${GSPO_REASONING_LENGTH_PENALTY}"
echo "KL_REFERENCE=$GSPO_REF_MODEL beta=$GSPO_BETA"
echo "EVAL_DATA=$GSPO_EVAL_DATA"
echo "EVAL_SEEDS=$GSPO_EVAL_SEEDS"
echo "EVAL_ASSET_ROOT=$GSPO_BENCH_ASSET_ROOT"

if [[ ! -f "$REASONING_START_MODEL/config.json" ]]; then
  echo "MODEL NOT FOUND: $REASONING_START_MODEL/config.json"
  exit 1
fi

if [[ ! -f "$GSPO_REF_MODEL/config.json" ]]; then
  echo "REF MODEL NOT FOUND: $GSPO_REF_MODEL/config.json"
  exit 1
fi

if [[ ! -f "$REASONING_RL_DATA" ]]; then
  echo "DATA NOT FOUND: $REASONING_RL_DATA"
  exit 1
fi

if [[ ! -f "$GSPO_EVAL_DATA" ]]; then
  echo "EVAL DATA NOT FOUND: $GSPO_EVAL_DATA"
  exit 1
fi

EVAL_ROWS=$(wc -l < "$GSPO_EVAL_DATA" | tr -d ' ')
if [[ "$EVAL_ROWS" != "50" ]]; then
  echo "EVAL DATA MUST HAVE EXACTLY 50 ROWS, got: $EVAL_ROWS"
  exit 1
fi

echo "DATA_ROWS=$(wc -l < "$REASONING_RL_DATA" | tr -d ' ')"
echo "EVAL_ROWS=$EVAL_ROWS"

TRAIN_SESSION_PID=""
kill_training_session() {
  local signal="$1"
  local pids
  [[ -n "$TRAIN_SESSION_PID" ]] || return 0
  pids="$(ps -eo pid=,sid= | awk -v sid="$TRAIN_SESSION_PID" '$2 == sid {print $1}')"
  [[ -n "$pids" ]] && kill "-$signal" $pids 2>/dev/null || true
}
cleanup_training() {
  [[ -n "$TRAIN_SESSION_PID" ]] || return 0
  kill_training_session TERM
  for _ in $(seq 1 10); do
    ps -eo sid= | awk -v sid="$TRAIN_SESSION_PID" '$1 == sid {found=1} END {exit !found}' || return 0
    sleep 0.5
  done
  kill_training_session KILL
}
trap cleanup_training INT TERM EXIT

setsid bash -c 'set -o pipefail; bash "$1" 2>&1 | tee "$2"' _ \
  "$ROOT/scripts/dlc/start_gspo_reasoning.sh" "$TRAIN_LOG" &
TRAIN_SESSION_PID=$!
wait "$TRAIN_SESSION_PID"
rc=$?
cleanup_training
trap - INT TERM EXIT

echo "training_exit_code=$rc"
exit "$rc"
