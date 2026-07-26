#!/usr/bin/env bash
set -euo pipefail

ROOT=/mnt/nas/bihaoran/qwen3vl
source "$ROOT/scripts/common/env.sh"
cd "$ROOT"

MODEL_DIR="$ROOT/models/models/Qwen--Qwen3-VL-2B-Instruct/snapshots/master"
DATASET="$ROOT/data/gspo_smoke.jsonl"
REWARD_PLUGIN="$ROOT/scripts/dsw/gspo_smoke_reward.py"
OUTPUT_DIR="$ROOT/output/dsw-gspo-vllm-smoke"
LOG_FILE="$ROOT/logs/gspo_vllm_smoke_$(date +%Y%m%d_%H%M%S).log"

export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}"
export NPROC_PER_NODE="${NPROC_PER_NODE:-1}"
export IMAGE_MAX_TOKEN_NUM="${IMAGE_MAX_TOKEN_NUM:-256}"

echo "===== GSPO VLLM CONFIG ====="
echo "devices: $CUDA_VISIBLE_DEVICES"
echo "nproc: $NPROC_PER_NODE"
echo "model: $MODEL_DIR"
echo "log: $LOG_FILE"

swift rlhf \
  --rlhf_type grpo \
  --model "$MODEL_DIR" \
  --dataset "$DATASET" \
  --split_dataset_ratio 0 \
  --external_plugins "$REWARD_PLUGIN" \
  --reward_funcs gspo_smoke \
  --importance_sampling_level sequence \
  --tuner_type full \
  --freeze_vit false \
  --freeze_aligner false \
  --freeze_llm false \
  --torch_dtype bfloat16 \
  --attn_impl sdpa \
  --use_vllm true \
  --vllm_mode colocate \
  --vllm_gpu_memory_utilization 0.25 \
  --vllm_tensor_parallel_size 1 \
  --vllm_max_model_len 1024 \
  --vllm_max_num_seqs 2 \
  --vllm_enforce_eager true \
  --sleep_level 1 \
  --optim adamw_torch \
  --per_device_train_batch_size 1 \
  --gradient_accumulation_steps 2 \
  --num_generations 2 \
  --num_iterations 2 \
  --max_length 1024 \
  --max_completion_length 32 \
  --temperature 1 \
  --learning_rate 1e-6 \
  --beta 0 \
  --epsilon 3e-4 \
  --epsilon_high 4e-4 \
  --max_grad_norm 0.5 \
  --gradient_checkpointing false \
  --vit_gradient_checkpointing false \
  --max_steps 2 \
  --logging_steps 1 \
  --log_completions true \
  --save_strategy no \
  --eval_strategy no \
  --report_to none \
  --dataset_num_proc 1 \
  --dataloader_num_workers 0 \
  --output_dir "$OUTPUT_DIR" \
  2>&1 | tee "$LOG_FILE"

echo "DSW_GSPO_VLLM_OK"
