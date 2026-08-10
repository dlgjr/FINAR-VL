#!/usr/bin/env bash
set -euo pipefail

ROOT="${QWEN3VL_ROOT:-/mnt/nas/bihaoran/qwen3vl}"
export NPROC_PER_NODE=1
export CUDA_VISIBLE_DEVICES=0
source "$ROOT/scripts/dlc/dlc_env.sh"

export BASE_MODEL="$ROOT/models/qwen4"
export TRAIN_MULTI="${TRAIN_MULTI:-$ROOT/data/train_multi/train_multi_sft_minhash_dedup.jsonl}"
export TRAIN_TEXT="${TRAIN_TEXT:-$ROOT/data/train_text/train_text_sft_minhash_dedup.jsonl}"
export SFT_BENCHMARK="$ROOT/data/benchmark/my_benchmark/all.jsonl"
export SFT_EVAL_MAX_SAMPLES=1
export SFT_EVAL_STEPS=5
export SFT_EVAL_AT_ZERO=false
export SFT_GLOBAL_BATCH_SIZE=2
export SFT_JUDGE_URL="${SFT_JUDGE_URL:-http://127.0.0.1:8001}"
export WANDB_DISABLED=true
export WANDB_MODE=disabled
export IMAGE_MAX_TOKEN_NUM=512
export PYTORCH_ALLOC_CONF=expandable_segments:True
export SFT_ATTN_IMPL="${SFT_ATTN_IMPL:-sdpa}"
export SFT_CELOSS_PARALLEL_SIZE="${SFT_CELOSS_PARALLEL_SIZE:-4096}"
export SFT_DEBUG_MAX_LENGTH="${SFT_DEBUG_MAX_LENGTH:-49152}"
export CELOSS_PARALLEL_SIZE="$SFT_CELOSS_PARALLEL_SIZE"

PYTHON_BIN="${PYTHON_BIN:-/opt/ac2/bin/python}"
SWIFT_BIN="${SWIFT_BIN:-$PYTHONUSERBASE/bin/swift}"
RUN_ID="${SFT_DSW_RUN_ID:-sft_dsw_$(date +%Y%m%d_%H%M%S)}"
RUN_DIR="${SFT_DSW_OUTPUT_DIR:-$ROOT/output/sft_dsw/$RUN_ID}"

mkdir -p "$RUN_DIR"
test -f "$BASE_MODEL/config.json" || { echo "模型不存在：$BASE_MODEL" >&2; exit 1; }
if ! "$PYTHON_BIN" - <<'PY' >/dev/null 2>&1
import swift
import transformers
import deepspeed
import wandb

assert swift.__version__ == "4.4.2"
assert transformers.__version__ == "4.57.6"
assert wandb.__version__ == "0.28.1"
PY
then
  "$PYTHON_BIN" -m pip install \
    --user \
    --no-cache-dir \
    --upgrade-strategy only-if-needed \
    "ms-swift==4.4.2" \
    "transformers==4.57.6" \
    "wandb==0.28.1" \
    "qwen-vl-utils>=0.0.14" \
    deepspeed \
    modelscope \
    accelerate \
    datasets \
    peft
fi
test -x "$SWIFT_BIN" || { echo "swift 不存在：$SWIFT_BIN" >&2; exit 1; }

SFT_PLAN_DIR="$RUN_DIR/sample_plans"
export SFT_PLAN_DIR
"$PYTHON_BIN" "$ROOT/scripts/sft/sample_plan.py" \
  --train-multi "$TRAIN_MULTI" \
  --train-text "$TRAIN_TEXT" \
  --output-dir "$SFT_PLAN_DIR" \
  --global-batch-size "$SFT_GLOBAL_BATCH_SIZE" \
  --dp-world-size 1 \
  --per-device-batch 1 \
  --grad-acc 2 \
  --seed "${SFT_PLAN_SEED:-42}" \
  --model "$BASE_MODEL" \
  --model-type qwen3_vl \
  --max-length "$SFT_DEBUG_MAX_LENGTH" \
  --max-steps 5 \
  --scan-num-proc "${SFT_SCAN_NUM_PROC:-1}"

echo "===== SFT DSW DEBUG CONFIG ====="
echo "model=$BASE_MODEL benchmark=$SFT_BENCHMARK"
echo "max_steps=5 max_length=$SFT_DEBUG_MAX_LENGTH gpus=0 sequence_parallel=1 deepspeed=zero2 fixed_batch=1 grad_accum=2 eval_samples=1"
echo "tuner=lora rank=16 alpha=32 dropout=0.05 target_modules=all-linear learning_rate=1e-5 warmup_ratio=0.05 max_grad_norm=1.0"
echo "sample_plan_dir=$SFT_PLAN_DIR"

exec "$SWIFT_BIN" sft \
  --model "$BASE_MODEL" \
  --model_type qwen3_vl \
  --dataset "$TRAIN_MULTI" "$TRAIN_TEXT" \
  --split_dataset_ratio 0 \
  --dataset_shuffle false \
  --train_dataloader_shuffle false \
  --strict false \
  --tuner_type lora \
  --freeze_vit true \
  --freeze_aligner false \
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
  --max_steps 5 \
  --learning_rate 1e-5 \
  --lr_scheduler_type cosine \
  --warmup_ratio 0.05 \
  --max_grad_norm 1.0 \
  --logging_steps 1 \
  --logging_nan_inf_filter false \
  --eval_strategy no \
  --save_strategy steps \
  --save_steps 5 \
  --save_only_model true \
  --report_to none \
  --external_plugins "$ROOT/scripts/sft/swift_sft_plugin.py" \
  --callbacks finar_log finar_numerics finar_pass_at_8 finar_plan \
  --output_dir "$RUN_DIR"
