#!/usr/bin/env bash
set -euo pipefail

QWEN3VL_ROOT="${QWEN3VL_ROOT:-/mnt/nas/bihaoran/qwen3vl}"
BASE_MODEL="${BASE_MODEL:-$QWEN3VL_ROOT/models/qwen4}"
TRAIN_MULTI="${TRAIN_MULTI:-$QWEN3VL_ROOT/data/train_multi/train_multi_sft_minhash_dedup.jsonl}"
TRAIN_TEXT="${TRAIN_TEXT:-$QWEN3VL_ROOT/data/train_text/train_text_sft_minhash_dedup.jsonl}"
PYTHON_BIN="${PYTHON_BIN:-/opt/ac2/bin/python}"
PYTHONUSERBASE="${PYTHONUSERBASE:-$QWEN3VL_ROOT/python-user}"
export PYTHONUSERBASE
SWIFT_BIN="${SWIFT_BIN:-$PYTHONUSERBASE/bin/swift}"
SFT_ATTN_IMPL="${SFT_ATTN_IMPL:-sdpa}"
SFT_CELOSS_PARALLEL_SIZE="${SFT_CELOSS_PARALLEL_SIZE:-4096}"
SFT_DEBUG_MAX_LENGTH="${SFT_DEBUG_MAX_LENGTH:-81920}"
SFT_DEBUG_STEPS="${SFT_DEBUG_STEPS:-1049,1050}"
SFT_OUTPUT_ROOT="${SFT_OUTPUT_ROOT:-$QWEN3VL_ROOT/output/sft_exact_steps}"

export QWEN3VL_ROOT BASE_MODEL TRAIN_MULTI TRAIN_TEXT
export NPROC_PER_NODE=2 CUDA_VISIBLE_DEVICES=0,1
export CELOSS_PARALLEL_SIZE="$SFT_CELOSS_PARALLEL_SIZE"

if [[ -f "$QWEN3VL_ROOT/scripts/dlc/dlc_env.sh" ]]; then
  # shellcheck disable=SC1091
  source "$QWEN3VL_ROOT/scripts/dlc/dlc_env.sh"
fi

if [[ "$SFT_ATTN_IMPL" == "flash_attn" ]]; then
  echo "预检 flash_attn import"
  "$PYTHON_BIN" -c 'import flash_attn'
fi

IFS=',' read -r -a STEPS <<< "$SFT_DEBUG_STEPS"
SFT_PLAN_MAX_STEPS=0
for STEP in "${STEPS[@]}"; do
  if (( STEP > SFT_PLAN_MAX_STEPS )); then
    SFT_PLAN_MAX_STEPS=$STEP
  fi
done
SFT_PLAN_DIR="$SFT_OUTPUT_ROOT/sample_plans"
"$PYTHON_BIN" "$QWEN3VL_ROOT/scripts/sft/sample_plan.py" \
  --train-multi "$TRAIN_MULTI" \
  --train-text "$TRAIN_TEXT" \
  --output-dir "$SFT_PLAN_DIR" \
  --global-batch-size 28 \
  --dp-world-size 14 \
  --per-device-batch 1 \
  --grad-acc 2 \
  --seed 42 \
  --max-steps "$SFT_PLAN_MAX_STEPS"
OVERALL_EXIT_CODE=0
for STEP in "${STEPS[@]}"; do
  RUN_DIR="$SFT_OUTPUT_ROOT/step_${STEP}"
  DEBUG_DATA="$RUN_DIR/debug_train.jsonl"
  mkdir -p "$RUN_DIR"
  echo "独立任务 step=$STEP：从 BASE_MODEL=$BASE_MODEL 启动，仅执行一次 forward/backward/optimizer update"

  "$PYTHON_BIN" "$QWEN3VL_ROOT/scripts/sft/extract_sequence_parallel_sample.py" \
    --plan-dir "$SFT_PLAN_DIR" \
    --train-multi "$TRAIN_MULTI" \
    --train-text "$TRAIN_TEXT" \
    --step "$STEP" \
    --grad-acc 2 \
    --per-device-batch 1 \
    --output "$DEBUG_DATA"

  export SFT_TRACE_STEPS=1
  set +e
  "$SWIFT_BIN" sft \
    --model "$BASE_MODEL" \
    --model_type qwen3_vl \
    --dataset "$DEBUG_DATA" \
    --split_dataset_ratio 0 \
    --dataset_shuffle false \
    --train_dataloader_shuffle false \
    --strict false \
    --tuner_type lora \
    --freeze_vit true \
    --freeze_aligner true \
    --freeze_llm false \
    --target_modules all-linear \
    --lora_rank 16 \
    --lora_alpha 32 \
    --lora_dropout 0.05 \
    --torch_dtype bfloat16 \
    --attn_impl "$SFT_ATTN_IMPL" \
    --per_device_train_batch_size 1 \
    --gradient_accumulation_steps 2 \
    --gradient_checkpointing true \
    --vit_gradient_checkpointing true \
    --deepspeed zero2 \
    --sequence_parallel_size 1 \
    --max_length "$SFT_DEBUG_MAX_LENGTH" \
    --max_steps 1 \
    --learning_rate 1e-5 \
    --lr_scheduler_type cosine \
    --warmup_ratio 0.05 \
    --max_grad_norm 1.0 \
    --logging_steps 1 \
    --logging_nan_inf_filter false \
    --eval_strategy no \
    --save_strategy no \
    --report_to none \
    --external_plugins "$QWEN3VL_ROOT/scripts/sft/swift_sft_plugin.py" \
    --callbacks finar_log finar_numerics \
    --output_dir "$RUN_DIR" >>"$RUN_DIR/run.log" 2>&1
  STEP_EXIT_CODE=$?
  set -e
  echo "swift_exit_code=$STEP_EXIT_CODE" | tee -a "$RUN_DIR/run.log"
  if [[ "$STEP_EXIT_CODE" -ne 0 ]]; then
    OVERALL_EXIT_CODE=1
    continue
  fi
done
exit "$OVERALL_EXIT_CODE"
