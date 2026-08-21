#!/usr/bin/env bash

MODE="${MODE:-rule}"
ROOT="${FINAR_ROOT:-/mnt/nas/bihaoran/qwen3vl}"
PYTHON_BIN="${PYTHON_BIN:-/opt/ac2/bin/python}"
PLUGIN="${FINANCE_REWARD_PLUGIN:-$ROOT/scripts/dlc/finance_gspo_reward.py}"

RULE_DATA="${RULE_DATA:-$ROOT/data/train_multi/train_rl_rule.jsonl}"
JUDGE_DATA="${JUDGE_DATA:-$ROOT/data/train_multi/train_rl_judge.jsonl}"

REWARD_MODEL="${REWARD_MODEL:-/mnt/nas/bihaoran/model/qwen235}"
REWARD_SERVE_NAME="${REWARD_SERVE_NAME:-qwen235-reward}"

if [[ "$MODE" == "reward" ]]; then
    CUDA_VISIBLE_DEVICES=0,1,2,3 "$PYTHON_BIN" -m vllm.entrypoints.openai.api_server \
        --model "$REWARD_MODEL" \
        --served-model-name "$REWARD_SERVE_NAME" \
        --host 0.0.0.0 \
        --port 8001 \
        --tensor-parallel-size 4 \
        --dtype auto \
        --max-model-len "${REWARD_MAX_MODEL_LEN:-8192}" \
        --max-num-seqs "${REWARD_MAX_NUM_SEQS:-16}" \
        --gpu-memory-utilization "${REWARD_GPU_MEMORY_UTILIZATION:-0.90}" \
        --trust-remote-code &

    CUDA_VISIBLE_DEVICES=4,5,6,7 "$PYTHON_BIN" -m vllm.entrypoints.openai.api_server \
        --model "$REWARD_MODEL" \
        --served-model-name "$REWARD_SERVE_NAME" \
        --host 0.0.0.0 \
        --port 8002 \
        --tensor-parallel-size 4 \
        --dtype auto \
        --max-model-len "${REWARD_MAX_MODEL_LEN:-8192}" \
        --max-num-seqs "${REWARD_MAX_NUM_SEQS:-16}" \
        --gpu-memory-utilization "${REWARD_GPU_MEMORY_UTILIZATION:-0.90}" \
        --trust-remote-code &

    wait
else
    if [[ "$MODE" == "judge" ]]; then
        DATA="$JUDGE_DATA"
        REWARD_FUNC="finance_judge"
        EPOCHS="${GSPO_NUM_TRAIN_EPOCHS:-2}"
        export REWARD_URLS="${REWARD_URLS:-http://${REWARD_HOST}:8001,http://${REWARD_HOST}:8002}"
        export REWARD_SERVE_NAME
    else
        DATA="$RULE_DATA"
        REWARD_FUNC="finance_rule"
        EPOCHS="${GSPO_NUM_TRAIN_EPOCHS:-1}"
    fi

    export CUDA_VISIBLE_DEVICES="${TRAIN_GPUS:-0,1,2,3,4,5,6,7}"
    export NPROC_PER_NODE="${NPROC_PER_NODE:-8}"
    export WANDB_MODE="${WANDB_MODE:-offline}"

    OUTPUT_DIR="${GSPO_OUTPUT_DIR:-$ROOT/output/finance_gspo_${MODE}}"

    "$PYTHON_BIN" -m swift.cli rlhf \
        --rlhf_type grpo \
        --model "$SFT_MODEL" \
        --dataset "$DATA" \
        --split_dataset_ratio 0 \
        --external_plugins "$PLUGIN" \
        --reward_funcs "$REWARD_FUNC" \
        --importance_sampling_level sequence \
        --tuner_type full \
        --freeze_vit false \
        --freeze_aligner false \
        --freeze_llm false \
        --torch_dtype bfloat16 \
        --per_device_train_batch_size 1 \
        --gradient_accumulation_steps "${GSPO_GRAD_ACC:-1}" \
        --num_train_epochs "$EPOCHS" \
        --num_generations "${GSPO_NUM_GENERATIONS:-8}" \
        --num_iterations "${GSPO_NUM_ITERATIONS:-1}" \
        --steps_per_generation "${GSPO_STEPS_PER_GENERATION:-1}" \
        --generation_batch_size "${GSPO_GENERATION_BATCH_SIZE:-64}" \
        --max_length "${GSPO_MAX_LENGTH:-8192}" \
        --max_completion_length "${GSPO_MAX_COMPLETION_LENGTH:-1024}" \
        --dynamic_sample "${GSPO_DYNAMIC_SAMPLE:-true}" \
        --max_resample_times "${GSPO_MAX_RESAMPLE_TIMES:-3}" \
        --overlong_filter "${GSPO_OVERLONG_FILTER:-true}" \
        --temperature "${GSPO_TEMPERATURE:-1.0}" \
        --learning_rate "${GSPO_LEARNING_RATE:-1e-6}" \
        --beta "${GSPO_BETA:-0}" \
        --epsilon "${GSPO_EPSILON:-3e-4}" \
        --epsilon_high "${GSPO_EPSILON_HIGH:-4e-4}" \
        --max_grad_norm "${GSPO_MAX_GRAD_NORM:-0.5}" \
        --use_vllm true \
        --vllm_mode colocate \
        --vllm_tensor_parallel_size 1 \
        --vllm_max_model_len "${GSPO_VLLM_MAX_MODEL_LEN:-8192}" \
        --vllm_max_num_seqs "${GSPO_VLLM_MAX_NUM_SEQS:-16}" \
        --vllm_gpu_memory_utilization "${GSPO_VLLM_GPU_MEMORY_UTILIZATION:-0.60}" \
        --sleep_level 1 \
        --save_strategy steps \
        --save_steps "${GSPO_SAVE_STEPS:-100}" \
        --save_total_limit "${GSPO_SAVE_TOTAL_LIMIT:-5}" \
        --save_only_model true \
        --output_dir "$OUTPUT_DIR"
fi
