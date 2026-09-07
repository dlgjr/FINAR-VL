#!/usr/bin/env bash

ROOT=/mnt/nas/duolg/qwen3vl
cd "$ROOT" || exit 1

export QWEN3VL_ROOT="$ROOT"

# ===== Data / model =====
export REASONING_RL_DATA="$ROOT/data/train_multi/train_rl_reasoning_rule_12835_gold.jsonl"
export REASONING_START_MODEL="$ROOT/output/sft_test_unclean/checkpoint-550"

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
export GSPO_GENERATION_BATCH_SIZE=8
export GSPO_SCHEDULE_BATCH_SIZE=4

# Responses shorter than 20 generated tokens are treated as failed reasoning.
export GSPO_REASONING_SHORT_TOKENS=20
export GSPO_REASONING_SHORT_REWARD=-0.1

# ===== Training =====
export GSPO_NUM_TRAIN_EPOCHS=4
export GSPO_BATCH_SIZE=1
export GSPO_GRAD_ACC=1
export GSPO_DYNAMIC_SAMPLE=true
export GSPO_MAX_RESAMPLE_TIMES=3

export GSPO_LEARNING_RATE=1e-6
export GSPO_BETA=0.01
export GSPO_ENTROPY_COEF=0.001
export GSPO_MAX_GRAD_NORM=1.0
export GSPO_EPSILON=0.03
export GSPO_EPSILON_HIGH=0.05

export GSPO_STEPS_PER_GENERATION=2
export GSPO_NUM_ITERATIONS=2
export GSPO_TEMPERATURE=1.2

# ===== Checkpoint / logging =====
export GSPO_SAVE_TOTAL_LIMIT=30
export GSPO_LOGGING_STEPS=1

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
export GSPO_VLLM_GPU_MEMORY_UTILIZATION=0.35
export GSPO_VLLM_ENFORCE_EAGER=true
export GSPO_VLLM_MM_PROCESSOR_CACHE_GB=0
export GSPO_VLLM_SLEEP_LEVEL=1

# ===== W&B =====
export WANDB_PROJECT=FINAR-VL-GSPO
export WANDB_MODE=offline

RUN_ID="reasoning_pass8_gold_v8_4gpu_$(date +%Y%m%d_%H%M%S)"
export GSPO_RUN_ID="$RUN_ID"
export WANDB_NAME="$RUN_ID"
export REASONING_RL_OUTPUT_DIR="$ROOT/output/gspo/$RUN_ID"

mkdir -p "$REASONING_RL_OUTPUT_DIR"

echo "===== RUN CONFIG ====="
echo "ROOT=$ROOT"
echo "MODEL=$REASONING_START_MODEL"
echo "DATA=$REASONING_RL_DATA"
echo "OUTPUT=$REASONING_RL_OUTPUT_DIR"
echo "GPUS=$GSPO_TRAIN_GPUS"
echo "NPROC=$GSPO_NPROC_PER_NODE"
echo "GENERATIONS=$GSPO_NUM_GENERATIONS"
echo "GENERATION_BATCH=$GSPO_GENERATION_BATCH_SIZE  # must be 1*4*2=8"
echo "SHORT_RESPONSE=<${GSPO_REASONING_SHORT_TOKENS} tokens => reward ${GSPO_REASONING_SHORT_REWARD}"
echo "EVAL_DATA=$GSPO_EVAL_DATA"
echo "EVAL_SEEDS=$GSPO_EVAL_SEEDS"
echo "EVAL_ASSET_ROOT=$GSPO_BENCH_ASSET_ROOT"

if [[ ! -f "$REASONING_START_MODEL/config.json" ]]; then
  echo "MODEL NOT FOUND: $REASONING_START_MODEL/config.json"
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

bash "$ROOT/scripts/dlc/start_gspo_reasoning.sh" \
  2>&1 | tee "$REASONING_RL_OUTPUT_DIR/train.log"

rc=${PIPESTATUS[0]}
echo "training_exit_code=$rc"
exit "$rc"
