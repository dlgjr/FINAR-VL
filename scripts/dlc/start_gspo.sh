#!/usr/bin/env bash
set -euo pipefail

ROOT="${QWEN3VL_ROOT:-/mnt/nas/bihaoran/qwen3vl}"
source "$ROOT/scripts/dlc/dlc_env.sh"
source "$ROOT/scripts/dlc/gspo_env.sh"

export QWEN3VL_ROOT="$ROOT"
export CUDA_VISIBLE_DEVICES="$GSPO_TRAIN_GPUS"
export NNODES="$GSPO_NNODES"
export NODE_RANK="$GSPO_NODE_RANK"
export NPROC_PER_NODE="$GSPO_NPROC_PER_NODE"
export MASTER_ADDR="$GSPO_MASTER_ADDR"
export MASTER_PORT="$GSPO_MASTER_PORT"
export WANDB_MODE=offline
export WANDB_PROJECT="${WANDB_PROJECT:-FINAR-VL-GSPO}"
export WANDB_DIR="${WANDB_DIR:-$ROOT/output/gspo/wandb}"
export GSPO_OUTPUT_DIR="${GSPO_OUTPUT_DIR:-$ROOT/output/gspo/${GSPO_RUN_ID:-$(date +%Y%m%d_%H%M%S)}}"
export GSPO_REWARD_POOL="${GSPO_REWARD_POOL:-$GSPO_OUTPUT_DIR/reward_pool_rank_${NODE_RANK}.jsonl}"
export GSPO_REWARD_ERRORS="${GSPO_REWARD_ERRORS:-$GSPO_OUTPUT_DIR/reward_errors_rank_${NODE_RANK}.jsonl}"
export GSPO_STATUS_DIR="${GSPO_STATUS_DIR:-$GSPO_OUTPUT_DIR/rank_status}"
export REWARD_PLUGIN="${REWARD_PLUGIN:-$ROOT/scripts/dlc/gspo_plugins.py}"
export TRAINER_PLUGIN="${TRAINER_PLUGIN:-$ROOT/scripts/dlc/gspo_plugins.py}"
export GSPO_BENCHMARK_ALLOWLIST
export GSPO_MODEL="${GSPO_MODEL:-${SFT_MODEL:-}}"

: "${GSPO_JUDGE_MODEL:?GSPO_JUDGE_MODEL must point to Qwen3-VL-30B-A3B-Thinking weights}"
: "${GSPO_MODEL:?GSPO_MODEL must be the merged full SFT model (LoRA adapter is not accepted)}"
test -f "$GSPO_MODEL/config.json" || { echo "missing merged model config: $GSPO_MODEL/config.json" >&2; exit 1; }
test -f "$ROOT/scripts/dlc/gspo_plugins.py" || { echo "missing GSPO plugin" >&2; exit 1; }

PYTHON_BIN="${PYTHON_BIN:-/opt/ac2/bin/python}"
SWIFT_BIN="${SWIFT_BIN:-$PYTHONUSERBASE/bin/swift}"
if [[ ! -x "$SWIFT_BIN" ]]; then SWIFT_BIN=("$PYTHON_BIN" -m swift.cli); else SWIFT_BIN=("$SWIFT_BIN"); fi
RUN_DIR="$GSPO_OUTPUT_DIR"
mkdir -p "$RUN_DIR" "$WANDB_DIR"
if [[ -n "$GSPO_SOURCE_DATA" ]]; then
  test -f "$GSPO_SOURCE_DATA" || { echo "missing RL source data: $GSPO_SOURCE_DATA" >&2; exit 1; }
  export GSPO_DATA="${GSPO_PREPARED_DATA:-$RUN_DIR/train_gspo.jsonl}"
  DATA_READY="$RUN_DIR/data_preparation.ready"
  if [[ "$NODE_RANK" == "0" ]]; then
    rm -f "$DATA_READY"
    UNSCHEDULED_DATA="$GSPO_DATA.unscheduled"
    "$PYTHON_BIN" -m scripts.rl.prepare_gspo_data "$GSPO_SOURCE_DATA" "$UNSCHEDULED_DATA" "$RUN_DIR/data_preparation.audit.json"
    "$PYTHON_BIN" -m scripts.rl.schedule_gspo_data "$UNSCHEDULED_DATA" "$GSPO_DATA" \
      --workers "$((GSPO_NNODES * GSPO_NPROC_PER_NODE))" --batch-size "$GSPO_SCHEDULE_BATCH_SIZE"
    rm -f "$UNSCHEDULED_DATA" "$UNSCHEDULED_DATA.schedule.json"
    touch "$DATA_READY"
  else
    for attempt in $(seq 1 1800); do
      if [[ -f "$DATA_READY" ]]; then break; fi
      sleep 1
      if (( attempt % 30 == 0 )); then echo "waiting_for_prepared_data seconds=$attempt node_rank=$NODE_RANK"; fi
      if (( attempt == 1800 )); then echo "timed out waiting for prepared GSPO data: $DATA_READY" >&2; exit 1; fi
    done
  fi
fi
test -f "$GSPO_DATA" || { echo "missing derived GSPO data: $GSPO_DATA" >&2; exit 1; }
if [[ -z "${GSPO_EXPECTED_COUNT:-}" ]]; then
  export GSPO_EXPECTED_COUNT="$(wc -l < "$GSPO_DATA" | tr -d ' ')"
fi
export GSPO_PLANNED_ROLLOUTS="${GSPO_PLANNED_ROLLOUTS:-$(( GSPO_EXPECTED_COUNT * GSPO_NUM_TRAIN_EPOCHS * GSPO_NUM_GENERATIONS / (GSPO_NNODES * GSPO_NPROC_PER_NODE) ))}"
if [[ "$NODE_RANK" == "0" ]]; then
  VALIDATION_READY="$RUN_DIR/data_validation.ready"
  rm -f "$VALIDATION_READY"
  VALIDATE_ARGS=("$GSPO_DATA" --expected-count "$GSPO_EXPECTED_COUNT" --root "$ROOT" --route-mode "$GSPO_ROUTE_MODE" --report "$RUN_DIR/data_validation.report.json")
  if [[ "$GSPO_ALLOW_UNVERIFIED_GOLD" != "true" ]]; then
    VALIDATE_ARGS+=(--fail-on-unverified)
  fi
  "$PYTHON_BIN" -m scripts.rl.validate_gspo_data "${VALIDATE_ARGS[@]}" || exit 1
  touch "$VALIDATION_READY"
else
  VALIDATION_READY="$RUN_DIR/data_validation.ready"
  for attempt in $(seq 1 1800); do
    if [[ -f "$VALIDATION_READY" ]]; then break; fi
    sleep 1
    if (( attempt % 30 == 0 )); then echo "waiting_for_data_validation seconds=$attempt node_rank=$NODE_RANK"; fi
    if (( attempt == 1800 )); then echo "timed out waiting for GSPO data validation: $VALIDATION_READY" >&2; exit 1; fi
  done
fi

JUDGE_LOG="$RUN_DIR/judge_node_${NODE_RANK}.log"
(
  export CUDA_VISIBLE_DEVICES="$GSPO_JUDGE_GPU"
  export WANDB_MODE=disabled
  exec "$ROOT/scripts/dlc/start_gspo_judge.sh"
) >"$JUDGE_LOG" 2>&1 &
JUDGE_PID=$!
cleanup() { kill "$JUDGE_PID" 2>/dev/null || true; }
trap cleanup EXIT
for attempt in $(seq 1 180); do
  if "$PYTHON_BIN" -c "import urllib.request; urllib.request.urlopen('$GSPO_JUDGE_URL/health', timeout=2)" >/dev/null 2>&1; then break; fi
  sleep 2
  if (( attempt == 180 )); then echo "judge server failed to become healthy: $JUDGE_LOG" >&2; exit 1; fi
done

if [[ "$NODE_RANK" == "0" ]]; then
  GSPO_EXPECTED_COUNT_VALUE="$GSPO_EXPECTED_COUNT"
  GSPO_GLOBAL_STEPS=$(( (GSPO_EXPECTED_COUNT_VALUE + GSPO_GENERATION_BATCH_SIZE - 1) / GSPO_GENERATION_BATCH_SIZE * GSPO_NUM_TRAIN_EPOCHS ))
  GSPO_CHECKPOINT_COUNT=$(( (GSPO_GLOBAL_STEPS + GSPO_SAVE_STEPS - 1) / GSPO_SAVE_STEPS + GSPO_NUM_TRAIN_EPOCHS + 1 ))
  GSPO_BENCHMARK_GENERATIONS=$(( 94 * 9 * (GSPO_CHECKPOINT_COUNT + 2) ))
  echo "===== FULL GSPO DLC CONFIG ====="
  echo "nodes=$GSPO_NNODES train_ranks=$((GSPO_NNODES * GSPO_NPROC_PER_NODE)) train_gpus=$GSPO_TRAIN_GPUS judge_gpu=$GSPO_JUDGE_GPU"
  echo "model=$GSPO_MODEL judge_model=$GSPO_JUDGE_MODEL data=$GSPO_DATA"
  echo "epochs=$GSPO_NUM_TRAIN_EPOCHS generations=$GSPO_NUM_GENERATIONS iterations=$GSPO_NUM_ITERATIONS steps_per_generation=$GSPO_STEPS_PER_GENERATION generation_batch=$GSPO_GENERATION_BATCH_SIZE"
  echo "max_length=$GSPO_MAX_LENGTH max_completion_length=$GSPO_MAX_COMPLETION_LENGTH save_steps=$GSPO_SAVE_STEPS eval_steps=$GSPO_EVAL_STEPS"
  echo "vllm_mode=$GSPO_VLLM_MODE vllm_max_model_len=$GSPO_VLLM_MAX_MODEL_LEN vllm_max_num_seqs=$GSPO_VLLM_MAX_NUM_SEQS"
  echo "benchmark_allowlist=$GSPO_BENCHMARK_ALLOWLIST allow_unverified_gold=$GSPO_ALLOW_UNVERIFIED_GOLD"
  echo "expected_global_steps=$GSPO_GLOBAL_STEPS expected_checkpoints=$GSPO_CHECKPOINT_COUNT expected_reward_evaluations=$((GSPO_EXPECTED_COUNT_VALUE * GSPO_NUM_TRAIN_EPOCHS * GSPO_NUM_GENERATIONS)) benchmark_generation_count=$GSPO_BENCHMARK_GENERATIONS"
fi

ARGS=(
  rlhf
  --rlhf_type grpo
  --model "$GSPO_MODEL"
  --dataset "$GSPO_DATA"
  --split_dataset_ratio 0
  --external_plugins "$TRAINER_PLUGIN"
  --reward_funcs gspo_mixed
  --importance_sampling_level sequence
  --tuner_type full
  --freeze_vit false
  --freeze_aligner false
  --freeze_llm false
  --torch_dtype bfloat16
  --per_device_train_batch_size "$GSPO_BATCH_SIZE"
  --gradient_accumulation_steps "$GSPO_GRAD_ACC"
  --num_train_epochs "$GSPO_NUM_TRAIN_EPOCHS"
  --num_generations "$GSPO_NUM_GENERATIONS"
  --num_iterations "$GSPO_NUM_ITERATIONS"
  --steps_per_generation "$GSPO_STEPS_PER_GENERATION"
  --generation_batch_size "$GSPO_GENERATION_BATCH_SIZE"
  --max_length "$GSPO_MAX_LENGTH"
  --max_completion_length "$GSPO_MAX_COMPLETION_LENGTH"
  --dynamic_sample "$GSPO_DYNAMIC_SAMPLE"
  --max_resample_times "$GSPO_MAX_RESAMPLE_TIMES"
  --overlong_filter "$GSPO_OVERLONG_FILTER"
  --temperature "$GSPO_TEMPERATURE"
  --learning_rate "$GSPO_LEARNING_RATE"
  --beta "$GSPO_BETA"
  --epsilon "$GSPO_EPSILON"
  --epsilon_high "$GSPO_EPSILON_HIGH"
  --max_grad_norm "$GSPO_MAX_GRAD_NORM"
  --use_vllm "$GSPO_USE_VLLM"
  --vllm_mode "$GSPO_VLLM_MODE"
  --vllm_tensor_parallel_size "$GSPO_VLLM_TENSOR_PARALLEL_SIZE"
  --vllm_max_model_len "$GSPO_VLLM_MAX_MODEL_LEN"
  --vllm_max_num_seqs "$GSPO_VLLM_MAX_NUM_SEQS"
  --vllm_gpu_memory_utilization "$GSPO_VLLM_GPU_MEMORY_UTILIZATION"
  --vllm_enforce_eager "$GSPO_VLLM_ENFORCE_EAGER"
  --sleep_level "$GSPO_VLLM_SLEEP_LEVEL"
  --save_strategy steps
  --save_steps "$GSPO_SAVE_STEPS"
  --save_total_limit "$GSPO_SAVE_TOTAL_LIMIT"
  --save_only_model true
  --eval_strategy no
  --report_to wandb
  --callbacks gspo_eval
  --output_dir "$RUN_DIR"
)
"${SWIFT_BIN[@]}" "${ARGS[@]}"

test -d "$RUN_DIR" || { echo "GSPO output directory missing" >&2; exit 1; }
echo "DLC_FULL_GSPO_OK output=$RUN_DIR"
