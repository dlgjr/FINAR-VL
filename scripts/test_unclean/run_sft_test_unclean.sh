#!/usr/bin/env bash

ROOT="${QWEN3VL_ROOT:-/mnt/nas/bihaoran/qwen3vl}"
CHECKPOINT="/mnt/nas/bihaoran/qwen3vl/output/sft/sft_qwen3vl4b_20260821_183115/v0-20260821-185530/checkpoint-15500"
TRAIN_DATA="/mnt/nas/bihaoran/qwen3vl/data/benchmark/test.jsonl"
IMAGE_DIR="/mnt/nas/bihaoran/qwen3vl/data/benchmark/assets"

export NPROC_PER_NODE="${NPROC_PER_NODE:-2}"
source "$ROOT/scripts/dlc/dlc_env.sh"

export IMAGE_MAX_TOKEN_NUM="${IMAGE_MAX_TOKEN_NUM:-512}"
export PYTORCH_ALLOC_CONF="${PYTORCH_ALLOC_CONF:-expandable_segments:True}"

PYTHON_BIN="${PYTHON_BIN:-/opt/ac2/bin/python}"
SWIFT_BIN="${SWIFT_BIN:-$PYTHONUSERBASE/bin/swift}"
SFT_ATTN_IMPL="${SFT_ATTN_IMPL:-sdpa}"
SFT_MAX_LENGTH="${SFT_MAX_LENGTH:-49152}"
RUN_ID="${SFT_RUN_ID:-sft_test_unclean_$(date +%Y%m%d_%H%M%S)}"
RUN_DIR="${SFT_OUTPUT_DIR:-$ROOT/output/sft_test_unclean/$RUN_ID}"
PREPARED_DATA="$RUN_DIR/test_abs_images.jsonl"

mkdir -p "$RUN_DIR"

"$PYTHON_BIN" - "$TRAIN_DATA" "$IMAGE_DIR" "$PREPARED_DATA" <<'PY'
import json
import os
import sys

src, image_dir, dst = sys.argv[1:4]

def resolve(path):
    return path if os.path.isabs(path) else os.path.join(image_dir, path)

with open(src, "r", encoding="utf-8") as fin, open(dst, "w", encoding="utf-8") as fout:
    for line in fin:
        row = json.loads(line)
        if isinstance(row.get("images"), list):
            row["images"] = [resolve(path) for path in row["images"]]
        if isinstance(row.get("image"), str):
            row["image"] = resolve(row["image"])
        fout.write(json.dumps(row, ensure_ascii=False) + "\n")
PY

"$SWIFT_BIN" sft \
  --model "$CHECKPOINT" \
  --model_type qwen3_vl \
  --dataset "$PREPARED_DATA" \
  --split_dataset_ratio 0 \
  --dataset_shuffle false \
  --train_dataloader_shuffle false \
  --strict false \
  --lazy_tokenize true \
  --tuner_type full \
  --freeze_vit false \
  --freeze_aligner false \
  --freeze_llm false \
  --torch_dtype bfloat16 \
  --attn_impl "$SFT_ATTN_IMPL" \
  --num_train_epochs 1 \
  --per_device_train_batch_size 1 \
  --gradient_accumulation_steps 2 \
  --gradient_checkpointing true \
  --vit_gradient_checkpointing true \
  --deepspeed zero2 \
  --sequence_parallel_size 1 \
  --max_length "$SFT_MAX_LENGTH" \
  --truncation_strategy delete \
  --learning_rate 1e-5 \
  --lr_scheduler_type cosine \
  --warmup_ratio 0.05 \
  --max_grad_norm 1.0 \
  --logging_steps 1 \
  --logging_nan_inf_filter false \
  --eval_strategy no \
  --save_strategy epoch \
  --save_only_model true \
  --report_to none \
  --output_dir "$RUN_DIR"
