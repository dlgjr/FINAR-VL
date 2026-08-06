#!/usr/bin/env bash
if [ -z "${BASH_VERSION:-}" ]; then
  exec bash "$0" "$@"
fi
set -euo pipefail

ROOT="${QWEN3VL_ROOT:-/mnt/nas/bihaoran/qwen3vl}"
NODE_WORLD_SIZE="${WORLD_SIZE:?DLC must provide WORLD_SIZE}"
NODE_RANK="${RANK:?DLC must provide RANK}"
source "$ROOT/scripts/dlc/dlc_env.sh"

export BASE_MODEL="$ROOT/models/qwen4"
export TRAIN_MULTI="${TRAIN_MULTI:-$ROOT/data/train_multi/train_multi_sft_minhash_dedup.jsonl}"
export TRAIN_TEXT="${TRAIN_TEXT:-$ROOT/data/train_text/train_text_sft_minhash_dedup.jsonl}"
export SFT_BENCHMARK="${SFT_BENCHMARK:-$ROOT/data/benchmark/my_benchmark/all.jsonl}"
export NPROC_PER_NODE=7
export CUDA_VISIBLE_DEVICES=0,1,2,3,4,5,6
export SFT_JUDGE_GPUS=7
export NNODES="$NODE_WORLD_SIZE"
export NODE_RANK="$NODE_RANK"
export SFT_EVAL_STEPS=500
export SFT_EVAL_AT_ZERO=true
export SFT_SAVE_STEPS="${SFT_SAVE_STEPS:-500}"
export SFT_PASS_AT_8_TEMPERATURE="${SFT_PASS_AT_8_TEMPERATURE:-1.0}"
export SFT_TRACE_STEPS="${SFT_TRACE_STEPS:-1049,1050,1051}"
export SFT_FREEZE_VIT="${SFT_FREEZE_VIT:-true}"
export SFT_FREEZE_ALIGNER="${SFT_FREEZE_ALIGNER:-true}"
export SFT_FREEZE_LLM="${SFT_FREEZE_LLM:-false}"
export SFT_VIT_GRADIENT_CHECKPOINTING="${SFT_VIT_GRADIENT_CHECKPOINTING:-false}"
export SFT_GRAD_ACC="${SFT_GRAD_ACC:-2}"
export SFT_DP_WORLD_SIZE=$((NPROC_PER_NODE * NODE_WORLD_SIZE))
export SFT_GLOBAL_BATCH_SIZE=$((SFT_DP_WORLD_SIZE * 1 * SFT_GRAD_ACC))
export SFT_PLAN_SEED="${SFT_PLAN_SEED:-42}"
export SFT_MULTI_RATIO="${SFT_MULTI_RATIO:-0.45}"
export SFT_EPOCHS="${SFT_EPOCHS:-1}"
export WANDB_PROJECT="${WANDB_PROJECT:-FINAR-VL-SFT}"
export WANDB_VERSION="0.28.1"
export WANDB_MODE=offline
export PYTORCH_ALLOC_CONF=expandable_segments:True
export CELOSS_PARALLEL_SIZE=4096

PYTHON_BIN="${PYTHON_BIN:-/opt/ac2/bin/python}"
SWIFT_BIN="${SWIFT_BIN:-$PYTHONUSERBASE/bin/swift}"
RUN_SYNC_DIR="$ROOT/output/sft/.launch"
RUN_ID_FILE="$RUN_SYNC_DIR/${MASTER_PORT:-29500}_${NODE_WORLD_SIZE}.run_id"
if [[ -n "${SFT_RUN_ID:-}" ]]; then
  RUN_ID="$SFT_RUN_ID"
elif (( NODE_RANK == 0 )); then
  mkdir -p "$RUN_SYNC_DIR"
  rm -f "$RUN_ID_FILE"
  RUN_ID="sft_qwen3vl4b_$(date +%Y%m%d_%H%M%S)"
  printf '%s\n' "$RUN_ID" >"$RUN_ID_FILE"
else
  for attempt in $(seq 1 120); do
    if [[ -s "$RUN_ID_FILE" ]]; then
      RUN_ID="$(<"$RUN_ID_FILE")"
      break
    fi
    sleep 1
  done
  : "${RUN_ID:?rank $NODE_RANK did not receive a shared run id}"
fi
RUN_DIR="${SFT_OUTPUT_DIR:-$ROOT/output/sft/$RUN_ID}"
LOG_DIR="$ROOT/logs/sft/$RUN_ID"
JUDGE_LOG="$LOG_DIR/judge_node_${NODE_RANK}.log"
WANDB_READY_FILE="$RUN_SYNC_DIR/${RUN_ID}.wandb_ready"
WANDB_ERROR_FILE="$RUN_SYNC_DIR/${RUN_ID}.wandb_error"
export TMPDIR="/tmp/qwen3vl-sft-${RUN_ID}-node-${NODE_RANK}"
export TMP="$TMPDIR"
export TEMP="$TMPDIR"
export LOCAL_CACHE_ROOT="$TMPDIR/cache"
export HF_HOME="$LOCAL_CACHE_ROOT/huggingface"
export HF_DATASETS_CACHE="$HF_HOME/datasets"
export HUGGINGFACE_HUB_CACHE="$HF_HOME/hub"
export MODELSCOPE_CACHE="$LOCAL_CACHE_ROOT/modelscope"
export TRITON_CACHE_DIR="$LOCAL_CACHE_ROOT/triton"

for required in "$BASE_MODEL/config.json" "$TRAIN_MULTI" "$TRAIN_TEXT" "$SFT_BENCHMARK" "$ROOT/scripts/sft/swift_sft_plugin.py"; do
  test -f "$required" || { echo "missing required file: $required" >&2; exit 1; }
done
if [[ -x "$SWIFT_BIN" ]]; then
  SWIFT_CMD=("$SWIFT_BIN")
elif "$PYTHON_BIN" -c 'import swift' >/dev/null 2>&1; then
  SWIFT_CMD=("$PYTHON_BIN" -m swift.cli)
else
  echo "ms-swift 未安装或不在 PATH：$SWIFT_BIN" >&2
  exit 1
fi

"$PYTHON_BIN" -c 'import flash_attn' >/dev/null 2>&1 || {
  echo "flash_attn is required for DLC SFT; install it in the image before launch" >&2
  exit 1
}

mkdir -p \
  "$RUN_DIR" \
  "$LOG_DIR" \
  "$TMPDIR" \
  "$HF_DATASETS_CACHE" \
  "$HUGGINGFACE_HUB_CACHE" \
  "$MODELSCOPE_CACHE" \
  "$TRITON_CACHE_DIR"

"$PYTHON_BIN" - "$MODELSCOPE_CACHE" <<'PY'
import os
import sys
import tempfile

cache_dir = sys.argv[1]
fd, path = tempfile.mkstemp(prefix=".lock_probe.", dir=cache_dir)
try:
    os.fchmod(fd, 0o600)
finally:
    os.close(fd)
    os.unlink(path)
PY

wandb_check() {
  "$PYTHON_BIN" - "$WANDB_VERSION" <<'PY'
import importlib.metadata
import sys

try:
    version = importlib.metadata.version("wandb")
except importlib.metadata.PackageNotFoundError:
    raise SystemExit(1)
raise SystemExit(0 if version == sys.argv[1] else 1)
PY
}

if (( NODE_RANK == 0 )); then
  rm -f "$WANDB_READY_FILE" "$WANDB_ERROR_FILE"
  if ! wandb_check; then
    if ! "$PYTHON_BIN" -m pip install \
      --user \
      --no-cache-dir \
      --no-input \
      --upgrade-strategy only-if-needed \
      "wandb==$WANDB_VERSION"; then
      printf 'wandb installation failed on node rank %s\n' "$NODE_RANK" >"$WANDB_ERROR_FILE"
      exit 1
    fi
  fi
  if ! wandb_check; then
    printf 'wandb version check failed after installation\n' >"$WANDB_ERROR_FILE"
    exit 1
  fi
  printf '%s\n' "$WANDB_VERSION" >"$WANDB_READY_FILE"
else
  for attempt in $(seq 1 120); do
    if [[ -f "$WANDB_ERROR_FILE" ]]; then
      cat "$WANDB_ERROR_FILE" >&2
      exit 1
    fi
    if [[ -f "$WANDB_READY_FILE" ]]; then
      break
    fi
    sleep 5
  done
  [[ -f "$WANDB_READY_FILE" ]] || {
    echo "wandb installation did not become ready within 600 seconds" >&2
    exit 1
  }
  wandb_check || {
    echo "wandb $WANDB_VERSION is not importable on node rank $NODE_RANK" >&2
    exit 1
  }
fi

WANDB_INFO="$($PYTHON_BIN - <<'PY'
import wandb
print(f"version={wandb.__version__} path={wandb.__file__}")
PY
)"

if (( NODE_RANK == 0 )); then
  echo "===== SFT DLC CONFIG ====="
  echo "model=$BASE_MODEL"
  echo "train_multi=$TRAIN_MULTI"
  echo "train_text=$TRAIN_TEXT"
  echo "benchmark=$SFT_BENCHMARK"
  echo "max_steps=from_sample_plan max_length=49152 global_batch=$SFT_GLOBAL_BATCH_SIZE per_device_batch=1 grad_accum=$SFT_GRAD_ACC"
  echo "tuner=lora rank=16 alpha=32 dropout=0.05 target_modules=all-linear"
  echo "learning_rate=1e-5 scheduler=cosine warmup_ratio=0.05 max_grad_norm=1.0"
  echo "eval_step0=true eval_steps=500 save_steps=$SFT_SAVE_STEPS"
  echo "pass_at_1=greedy pass_at_8_temperature=$SFT_PASS_AT_8_TEMPERATURE"
  echo "training_gpus_per_node=7 judge_gpus_per_node=1 nodes=$NODE_WORLD_SIZE"
  echo "training_topology=sequence_parallel:1,data_parallel:$SFT_DP_WORLD_SIZE deepspeed=zero2"
  echo "freeze_vit=$SFT_FREEZE_VIT freeze_aligner=$SFT_FREEZE_ALIGNER freeze_llm=$SFT_FREEZE_LLM vit_gradient_checkpointing=$SFT_VIT_GRADIENT_CHECKPOINTING"
  echo "wandb_project=$WANDB_PROJECT run_dir=$RUN_DIR"
  echo "local_cache_root=$LOCAL_CACHE_ROOT"
  echo "hf_home=$HF_HOME"
  echo "hf_datasets_cache=$HF_DATASETS_CACHE"
  echo "modelscope_cache=$MODELSCOPE_CACHE"
  echo "triton_cache_dir=$TRITON_CACHE_DIR"
  echo "cache_probe=fchmod_ok"
  echo "wandb_mode=$WANDB_MODE $WANDB_INFO"
fi

(
  export CUDA_VISIBLE_DEVICES="$SFT_JUDGE_GPUS"
  export WANDB_DISABLED=true
  export WANDB_MODE=disabled
  exec "$PYTHON_BIN" -m vllm.entrypoints.openai.api_server \
    --model "$BASE_MODEL" \
    --served-model-name qwen4-judge \
    --host 127.0.0.1 \
    --port 8001 \
    --dtype bfloat16 \
    --max-model-len 8192 \
    --tensor-parallel-size 1 \
    --gpu-memory-utilization 0.5 \
    --max-num-seqs 8
) >"$JUDGE_LOG" 2>&1 &
JUDGE_PID=$!
cleanup() { kill "$JUDGE_PID" 2>/dev/null || true; }
trap cleanup EXIT

for attempt in $(seq 1 120); do
  if "$PYTHON_BIN" -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8001/health', timeout=2)" >/dev/null 2>&1; then
    break
  fi
  sleep 2
  if (( attempt == 120 )); then
    echo "judge server failed to become healthy: $JUDGE_LOG" >&2
    exit 1
  fi
done

export SFT_JUDGE_URL=http://127.0.0.1:8001
export WANDB_DIR="$LOG_ROOT/wandb"
export WANDB_NAME="$RUN_ID"
export IMAGE_MAX_TOKEN_NUM=512

SFT_PLAN_DIR="$RUN_DIR/sample_plans"
export SFT_PLAN_DIR
if (( NODE_RANK == 0 )); then
  "$PYTHON_BIN" "$ROOT/scripts/sft/sample_plan.py" \
    --train-multi "$TRAIN_MULTI" \
    --train-text "$TRAIN_TEXT" \
    --output-dir "$SFT_PLAN_DIR" \
    --global-batch-size "$SFT_GLOBAL_BATCH_SIZE" \
    --dp-world-size "$SFT_DP_WORLD_SIZE" \
    --per-device-batch 1 \
    --grad-acc "$SFT_GRAD_ACC" \
    --seed "$SFT_PLAN_SEED" \
    --multi-ratio "$SFT_MULTI_RATIO" \
    --epochs "$SFT_EPOCHS"
else
  for attempt in $(seq 1 900); do
    if [[ -f "$SFT_PLAN_DIR/meta.json" ]]; then
      break
    fi
    sleep 2
  done
  test -f "$SFT_PLAN_DIR/meta.json" || {
    echo "sample plan did not become ready within 1800 seconds" >&2
    exit 1
  }
fi
SFT_MAX_STEPS="$("$PYTHON_BIN" -c 'import json,sys; print(json.load(open(sys.argv[1], encoding="utf-8"))["max_steps"])' "$SFT_PLAN_DIR/meta.json")"
echo "sample_plan_dir=$SFT_PLAN_DIR epochs=$SFT_EPOCHS max_steps=$SFT_MAX_STEPS"


"${SWIFT_CMD[@]}" sft \
  --model "$BASE_MODEL" \
  --model_type qwen3_vl \
  --dataset "$TRAIN_MULTI" "$TRAIN_TEXT" \
  --split_dataset_ratio 0 \
  --dataset_shuffle false \
  --train_dataloader_shuffle false \
  --strict false \
  --tuner_type lora \
  --freeze_vit "$SFT_FREEZE_VIT" \
  --freeze_aligner "$SFT_FREEZE_ALIGNER" \
  --freeze_llm "$SFT_FREEZE_LLM" \
  --target_modules all-linear \
  --lora_rank 16 \
  --lora_alpha 32 \
  --lora_dropout 0.05 \
  --torch_dtype bfloat16 \
  --attn_impl flash_attn \
  --deepspeed zero2 \
  --per_device_train_batch_size 1 \
  --gradient_accumulation_steps "$SFT_GRAD_ACC" \
  --gradient_checkpointing true \
  --vit_gradient_checkpointing "$SFT_VIT_GRADIENT_CHECKPOINTING" \
  --sequence_parallel_size 1 \
  --use_logits_to_keep true \
  --ddp_timeout 86400 \
  --max_length 49152 \
  --truncation_strategy delete \
  --max_steps "$SFT_MAX_STEPS" \
  --learning_rate 1e-5 \
  --lr_scheduler_type cosine \
  --warmup_ratio 0.05 \
  --max_grad_norm 1.0 \
  --logging_steps 1 \
  --eval_strategy no \
  --save_strategy steps \
  --save_steps "$SFT_SAVE_STEPS" \
  --save_total_limit 100 \
  --save_only_model true \
  --report_to wandb \
  --run_name "$RUN_ID" \
  --external_plugins "$ROOT/scripts/sft/swift_sft_plugin.py" \
  --callbacks finar_log finar_numerics finar_pass_at_8 finar_plan \
  --dataset_num_proc 1 \
  --dataloader_num_workers 1 \
  --output_dir "$RUN_DIR"
