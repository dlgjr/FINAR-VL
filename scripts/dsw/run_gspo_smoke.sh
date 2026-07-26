#!/usr/bin/env bash
set -e

cd /mnt/nas/bihaoran/qwen3vl

export HF_HOME=/mnt/nas/bihaoran/qwen3vl/cache/huggingface
export HF_DATASETS_CACHE=/mnt/nas/bihaoran/qwen3vl/cache/huggingface/datasets
export HUGGINGFACE_HUB_CACHE=/mnt/nas/bihaoran/qwen3vl/cache/huggingface/hub
export XDG_CACHE_HOME=/mnt/nas/bihaoran/qwen3vl/cache/xdg
export TORCH_HOME=/mnt/nas/bihaoran/qwen3vl/cache/torch
export TMPDIR=/mnt/nas/bihaoran/qwen3vl/tmp
export TMP="${TMPDIR}"
export TEMP="${TMPDIR}"

MODEL_DIR='/mnt/nas/bihaoran/qwen3vl/models/models/Qwen--Qwen3-VL-2B-Instruct/snapshots/master'

IMAGE_MAX_TOKEN_NUM=256 \
CUDA_VISIBLE_DEVICES=0 \
swift rlhf \
  --rlhf_type grpo \
  --model "${MODEL_DIR}" \
  --dataset /mnt/nas/bihaoran/qwen3vl/data/gspo_smoke.jsonl \
  --split_dataset_ratio 0 \
  --external_plugins /mnt/nas/bihaoran/qwen3vl/scripts/dsw/gspo_smoke_reward.py \
  --reward_funcs gspo_smoke \
  --importance_sampling_level sequence \
  --tuner_type full \
  --freeze_vit false \
  --freeze_aligner false \
  --freeze_llm false \
  --torch_dtype bfloat16 \
  --attn_impl sdpa \
  --use_vllm false \
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
  --output_dir /mnt/nas/bihaoran/qwen3vl/output/qwen3-vl-2b-gspo-smoke
