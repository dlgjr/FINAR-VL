#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/dlc_env.sh"

cd "$QWEN3VL_ROOT"

PYTHON_BIN=/opt/ac2/bin/python
SWIFT_BIN="$PYTHONUSERBASE/bin/swift"

RUN_ID="$(date +%Y%m%d_%H%M%S)"
RUN_DIR="$OUTPUT_ROOT/dlc-pipeline/$RUN_ID"
SFT_OUTPUT="$RUN_DIR/sft"
GSPO_OUTPUT="$RUN_DIR/gspo"

mkdir -p "$SFT_OUTPUT" "$GSPO_OUTPUT"

echo "===== DLC CONFIG ====="
echo "host: $(hostname)"
echo "python: $PYTHON_BIN"
echo "python_user_base: $PYTHONUSERBASE"
echo "devices: $CUDA_VISIBLE_DEVICES"
echo "nproc_per_node: $NPROC_PER_NODE"
echo "use_vllm: $USE_VLLM"
echo "run_dir: $RUN_DIR"

for file in \
  "$BASE_MODEL/config.json" \
  "$SFT_DATA" \
  "$GSPO_DATA" \
  "$REWARD_PLUGIN"
do
  test -f "$file" || {
    echo "文件不存在: $file"
    exit 1
  }
done

# 安装到 NAS，不建立虚拟环境，不安装普通 PyPI vLLM。
if ! "$PYTHON_BIN" - <<'PY' >/dev/null 2>&1
import swift
import transformers

assert swift.__version__ == "4.4.2"
assert transformers.__version__ == "4.57.6"
PY
then
  "$PYTHON_BIN" -m pip install \
    --user \
    --no-cache-dir \
    --upgrade-strategy only-if-needed \
    "ms-swift==4.4.2" \
    "transformers==4.57.6" \
    "qwen-vl-utils>=0.0.14" \
    modelscope \
    accelerate \
    datasets \
    peft
fi

test -x "$SWIFT_BIN" || {
  echo "swift 不存在: $SWIFT_BIN"
  exit 1
}

# 验证解释器、PPU 原生库和 vLLM 均来自 /opt/ac2。
"$PYTHON_BIN" - <<'PY'
import importlib.metadata
import os
import sys
import sysconfig

import torch
import swift
import transformers
import vllm

print("sys.executable:", sys.executable)
print("sys.prefix:", sys.prefix)
print("torch:", torch.__version__)
print("swift:", swift.__version__)
print("transformers:", transformers.__version__)
print("vllm:", importlib.metadata.version("vllm"))
print("vllm_path:", vllm.__file__)
print("device_count:", torch.cuda.device_count())

assert sys.executable == "/opt/ac2/bin/python"
assert sys.prefix.startswith("/opt/ac2")
assert torch.cuda.is_available()

required = int(os.environ["NPROC_PER_NODE"])
assert torch.cuda.device_count() >= required

purelib = sysconfig.get_path("purelib")
acext_lib = os.path.join(purelib, "lib", "libacext.so")

print("system_purelib:", purelib)
print("libacext:", acext_lib)
print("libacext_exists:", os.path.exists(acext_lib))

assert purelib.startswith("/opt/ac2")
assert os.path.exists(acext_lib)

import acext

print("acext_path:", acext.__file__)

for index in range(required):
    print(index, torch.cuda.get_device_name(index))

print("DLC_ENV_OK")
PY

echo
echo "===== STAGE 1: FULL SFT ====="

"$SWIFT_BIN" sft \
  --model "$BASE_MODEL" \
  --dataset "$SFT_DATA" \
  --split_dataset_ratio 0 \
  --tuner_type full \
  --freeze_vit false \
  --freeze_aligner false \
  --freeze_llm false \
  --torch_dtype bfloat16 \
  --attn_impl sdpa \
  --optim adamw_torch \
  --per_device_train_batch_size "$SFT_BATCH_SIZE" \
  --gradient_accumulation_steps "$SFT_GRAD_ACC" \
  --max_length "$MAX_LENGTH" \
  --learning_rate 1e-6 \
  --gradient_checkpointing false \
  --max_steps "$SFT_MAX_STEPS" \
  --logging_steps 1 \
  --save_strategy steps \
  --save_steps "$SFT_MAX_STEPS" \
  --save_total_limit 1 \
  --eval_strategy no \
  --report_to none \
  --dataset_num_proc 1 \
  --dataloader_num_workers 0 \
  --output_dir "$SFT_OUTPUT"

SFT_CHECKPOINT="$(
  find "$SFT_OUTPUT" \
    -type d \
    -name 'checkpoint-*' \
    | sort -V \
    | tail -n 1
)"

test -n "$SFT_CHECKPOINT" || {
  echo "没有找到 SFT checkpoint"
  exit 1
}

echo "SFT checkpoint: $SFT_CHECKPOINT"
echo "DLC_SFT_OK"

GSPO_VLLM_ARGS=(
  --use_vllm "$USE_VLLM"
)

if [ "$USE_VLLM" = "true" ]; then
  GSPO_VLLM_ARGS+=(
    --vllm_mode "$VLLM_MODE"
    --vllm_gpu_memory_utilization "$VLLM_GPU_MEMORY_UTILIZATION"
    --vllm_tensor_parallel_size "$VLLM_TENSOR_PARALLEL_SIZE"
    --vllm_max_model_len "$VLLM_MAX_MODEL_LEN"
    --vllm_max_num_seqs "$VLLM_MAX_NUM_SEQS"
    --vllm_enforce_eager "$VLLM_ENFORCE_EAGER"
    --sleep_level "$VLLM_SLEEP_LEVEL"
  )
fi

echo
echo "===== STAGE 2: FULL GSPO ====="

"$SWIFT_BIN" rlhf \
  --rlhf_type grpo \
  --model "$SFT_CHECKPOINT" \
  --dataset "$GSPO_DATA" \
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
  "${GSPO_VLLM_ARGS[@]}" \
  --optim adamw_torch \
  --per_device_train_batch_size "$GSPO_BATCH_SIZE" \
  --gradient_accumulation_steps "$GSPO_GRAD_ACC" \
  --num_generations "$NUM_GENERATIONS" \
  --num_iterations "$NUM_ITERATIONS" \
  --max_length "$MAX_LENGTH" \
  --max_completion_length "$MAX_COMPLETION_LENGTH" \
  --temperature 1 \
  --learning_rate 1e-6 \
  --beta 0 \
  --epsilon 3e-4 \
  --epsilon_high 4e-4 \
  --max_grad_norm 0.5 \
  --gradient_checkpointing false \
  --vit_gradient_checkpointing false \
  --max_steps "$GSPO_MAX_STEPS" \
  --logging_steps 1 \
  --log_completions true \
  --save_strategy no \
  --eval_strategy no \
  --report_to none \
  --dataset_num_proc 1 \
  --dataloader_num_workers 0 \
  --output_dir "$GSPO_OUTPUT"

echo "DLC_GSPO_OK"
echo "DLC_PIPELINE_OK"
echo "output: $RUN_DIR"
