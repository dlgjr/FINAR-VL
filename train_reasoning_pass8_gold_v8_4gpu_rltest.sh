#!/usr/bin/env bash

ROOT=/mnt/nas/duolg/qwen3vl
cd "$ROOT" || exit 1

export QWEN3VL_ROOT="$ROOT"

# ===== Data / model =====
REFERENCE_MODEL="$ROOT/output/sft/visual_repair_from_ckpt120_20260912_013822/v0-20260912-013855/checkpoint-556"
export REASONING_RL_DATA="$ROOT/data/train_multi/train_rl_reasoning_rule_12835_gold.jsonl"
# Optional fresh branch mode: initialize policy weights from an existing model
# checkpoint without loading Trainer/optimizer/RNG state. A weight-only branch
# uses that same init checkpoint as its fixed KL reference by default; explicit
# GSPO_REF_MODEL still overrides this behavior.
export GSPO_INIT_MODEL="${GSPO_INIT_MODEL:-}"
export REASONING_START_MODEL="${GSPO_INIT_MODEL:-$REFERENCE_MODEL}"
export GSPO_REF_MODEL="${GSPO_REF_MODEL:-${GSPO_INIT_MODEL:-$REFERENCE_MODEL}}"

# ===== Single node, 4 GPUs =====
export GSPO_NNODES=1
export GSPO_NODE_RANK=0
export GSPO_NPROC_PER_NODE=4
export GSPO_TRAIN_GPUS=0,1,2,3
export GSPO_MASTER_ADDR=127.0.0.1
export GSPO_MASTER_PORT=29500

# ===== Direct-answer / Pass@8 =====
export GSPO_ROUTE_MODE=reasoning
export GSPO_ENABLE_JUDGE=false
export GSPO_NUM_GENERATIONS=8
export GSPO_GENERATION_BATCH_SIZE=32
export GSPO_SCHEDULE_BATCH_SIZE=4

# The rollout policy is patched to direct-answer mode in
# scripts/dlc/gspo_reasoning_policy_plugin.py. No response-length reward shaping.
export GSPO_DIRECT_ANSWER=true

# ===== Training =====
export GSPO_NUM_TRAIN_EPOCHS=4
export GSPO_BATCH_SIZE=1
export GSPO_GRAD_ACC=1
export GSPO_DYNAMIC_SAMPLE=true
export GSPO_MAX_RESAMPLE_TIMES=1

export GSPO_LEARNING_RATE=1e-6
export GSPO_BETA=0.01
# Keep the selected KL reference fixed throughout each run.
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

# ===== Multimodal budget =====
export IMAGE_MAX_TOKEN_NUM=16384

# ===== Online group curriculum (computed from each live 8-way rollout) =====
# Correct means raw verifier reward > 0.5. These are RL advantage multipliers.
export GSPO_GROUP_WEIGHT_K0=0.0
export GSPO_GROUP_WEIGHT_K1=1.0
export GSPO_GROUP_WEIGHT_K2=1.0
export GSPO_GROUP_WEIGHT_K3=1.0
export GSPO_GROUP_WEIGHT_K4=1.0
export GSPO_GROUP_WEIGHT_K5=1.0
export GSPO_GROUP_WEIGHT_K6=0.7
export GSPO_GROUP_WEIGHT_K7=0.35
export GSPO_GROUP_WEIGHT_K8=0.0

# Hard-group supervised fallback. The gold completion gets an auxiliary CE loss
# whose weight acts like a local SFT learning-rate multiplier without changing
# the optimizer LR for the rest of the batch.
export GSPO_GOLD_INJECT=true
export GSPO_GOLD_SFT_MAX_CORRECT=2
export GSPO_GOLD_SFT_WEIGHT_K0=2.0
export GSPO_GOLD_SFT_WEIGHT_K1=1.0
export GSPO_GOLD_SFT_WEIGHT_K2=0.5
export GSPO_GOLD_SFT_COEF=1.0

# ===== Checkpoint / logging =====
# One W&B train point per 32-completion generation batch; fixed eval every 40 steps via save.
export GSPO_LOGGING_STEPS=8
export GSPO_SAVE_STEPS=40
export GSPO_EVAL_STEPS=40
export GSPO_SAVE_TOTAL_LIMIT=30

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
WANDB_STEP_OFFSET_INPUT="${GSPO_WANDB_STEP_OFFSET:-}"
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
  if [[ -z "$WANDB_STEP_OFFSET_INPUT" && -f "$RUN_ROOT/wandb_step_offset.txt" ]]; then
    export GSPO_WANDB_STEP_OFFSET="$(tr -d '[:space:]' < "$RUN_ROOT/wandb_step_offset.txt")"
  fi
else
  export WANDB_MODE="${WANDB_MODE:-offline}"
  if [[ -n "$GSPO_INIT_MODEL" ]]; then
    INIT_TAG="$(basename "$GSPO_INIT_MODEL")"
    RUN_ID="direct_token_grpo_gold_${INIT_TAG}_$(date +%Y%m%d_%H%M%S)"
  else
    RUN_ID="direct_token_grpo_gold_4gpu_$(date +%Y%m%d_%H%M%S)"
  fi
  export REASONING_RL_OUTPUT_DIR="$ROOT/output/gspo/$RUN_ID"
fi
export GSPO_RESUME_FROM_CHECKPOINT="$RESUME_CHECKPOINT"
export GSPO_RUN_ID="$RUN_ID"

# Optional W&B branch mode. Seed a fresh target run with source scalar history
# through the branch point. For a full-state resume the Trainer step already
# equals that branch point. For a weight-only branch the Trainer restarts at 0,
# so W&B receives a logical step offset equal to the source checkpoint step.
WANDB_HISTORY_SOURCE_RUN_ID="${WANDB_HISTORY_SOURCE_RUN_ID:-}"
WANDB_HISTORY_UNTIL_STEP="${WANDB_HISTORY_UNTIL_STEP:-}"
if [[ -n "$WANDB_HISTORY_SOURCE_RUN_ID" ]]; then
  if [[ -z "$RESUME_CHECKPOINT" && -z "$GSPO_INIT_MODEL" ]]; then
    echo "WANDB history cloning requires either GSPO_RESUME_FROM_CHECKPOINT or GSPO_INIT_MODEL"
    exit 1
  fi
  if [[ "$WANDB_MODE" != "online" ]]; then
    echo "WANDB history cloning requires WANDB_MODE=online"
    exit 1
  fi
  : "${WANDB_RUN_ID:?Set a fresh WANDB_RUN_ID for history branch mode}"
  if [[ "$WANDB_RUN_ID" == "$WANDB_HISTORY_SOURCE_RUN_ID" ]]; then
    echo "WANDB_RUN_ID must differ from WANDB_HISTORY_SOURCE_RUN_ID"
    exit 1
  fi
  BRANCH_MODEL_PATH="${RESUME_CHECKPOINT:-$GSPO_INIT_MODEL}"
  if [[ -z "$WANDB_HISTORY_UNTIL_STEP" ]]; then
    CKPT_NAME="$(basename "$BRANCH_MODEL_PATH")"
    if [[ "$CKPT_NAME" != checkpoint-* || ! "${CKPT_NAME#checkpoint-}" =~ ^[0-9]+$ ]]; then
      echo "Cannot derive W&B history branch step from checkpoint: $BRANCH_MODEL_PATH"
      exit 1
    fi
    WANDB_HISTORY_UNTIL_STEP="${CKPT_NAME#checkpoint-}"
  fi
  if [[ ! "$WANDB_HISTORY_UNTIL_STEP" =~ ^[0-9]+$ ]]; then
    echo "WANDB_HISTORY_UNTIL_STEP must be a non-negative integer, got: $WANDB_HISTORY_UNTIL_STEP"
    exit 1
  fi
  export WANDB_HISTORY_UNTIL_STEP

  if [[ -n "$GSPO_INIT_MODEL" && -z "$RESUME_CHECKPOINT" ]]; then
    if [[ -n "$WANDB_STEP_OFFSET_INPUT" && "$WANDB_STEP_OFFSET_INPUT" != "$WANDB_HISTORY_UNTIL_STEP" ]]; then
      echo "For a weight-only history branch, GSPO_WANDB_STEP_OFFSET must equal WANDB_HISTORY_UNTIL_STEP"
      exit 1
    fi
    export GSPO_WANDB_STEP_OFFSET="$WANDB_HISTORY_UNTIL_STEP"
  else
    export GSPO_WANDB_STEP_OFFSET="${GSPO_WANDB_STEP_OFFSET:-0}"
  fi

  export WANDB_NAME="${WANDB_NAME:-${RUN_ID}_from${WANDB_HISTORY_UNTIL_STEP}}"

  echo "===== W&B HISTORY BRANCH ====="
  echo "WANDB_ENTITY=$WANDB_ENTITY"
  echo "WANDB_PROJECT=$WANDB_PROJECT"
  echo "WANDB_HISTORY_SOURCE_RUN_ID=$WANDB_HISTORY_SOURCE_RUN_ID"
  echo "WANDB_HISTORY_UNTIL_STEP=$WANDB_HISTORY_UNTIL_STEP"
  echo "GSPO_WANDB_STEP_OFFSET=$GSPO_WANDB_STEP_OFFSET"
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
  export GSPO_WANDB_STEP_OFFSET="${GSPO_WANDB_STEP_OFFSET:-0}"
  export WANDB_NAME="${WANDB_NAME:-$RUN_ID}"
fi

if [[ ! "$GSPO_WANDB_STEP_OFFSET" =~ ^[0-9]+$ ]]; then
  echo "GSPO_WANDB_STEP_OFFSET must be a non-negative integer, got: $GSPO_WANDB_STEP_OFFSET"
  exit 1
fi

mkdir -p "$REASONING_RL_OUTPUT_DIR"
printf '%s\n' "$GSPO_WANDB_STEP_OFFSET" > "$REASONING_RL_OUTPUT_DIR/wandb_step_offset.txt"
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
echo "WANDB_STEP_OFFSET=$GSPO_WANDB_STEP_OFFSET"
echo "GPUS=$GSPO_TRAIN_GPUS"
echo "NPROC=$GSPO_NPROC_PER_NODE"
echo "GENERATIONS=$GSPO_NUM_GENERATIONS"
echo "GENERATION_BATCH=$GSPO_GENERATION_BATCH_SIZE  # must be 1*4*8=32"
echo "NUM_ITERATIONS=$GSPO_NUM_ITERATIONS"
echo "SAVE_EVAL_STEPS=$GSPO_SAVE_STEPS"
echo "LOGGING_STEPS=$GSPO_LOGGING_STEPS"
echo "POLICY=direct_answer image_max_tokens=$IMAGE_MAX_TOKEN_NUM importance_sampling=token loss_type=grpo"
echo "GROUP_WEIGHTS=k0:$GSPO_GROUP_WEIGHT_K0,k1:$GSPO_GROUP_WEIGHT_K1,k2:$GSPO_GROUP_WEIGHT_K2,k3:$GSPO_GROUP_WEIGHT_K3,k4:$GSPO_GROUP_WEIGHT_K4,k5:$GSPO_GROUP_WEIGHT_K5,k6:$GSPO_GROUP_WEIGHT_K6,k7:$GSPO_GROUP_WEIGHT_K7,k8:$GSPO_GROUP_WEIGHT_K8"
echo "GOLD_SFT=max_correct:$GSPO_GOLD_SFT_MAX_CORRECT weights=k0:$GSPO_GOLD_SFT_WEIGHT_K0,k1:$GSPO_GOLD_SFT_WEIGHT_K1,k2:$GSPO_GOLD_SFT_WEIGHT_K2 coef:$GSPO_GOLD_SFT_COEF"
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
