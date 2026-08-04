#!/usr/bin/env bash
set -euo pipefail

ROOT="${QWEN3VL_ROOT:-/mnt/nas/bihaoran/qwen3vl}"
export NPROC_PER_NODE=2
export CUDA_VISIBLE_DEVICES=0,1
source "$ROOT/scripts/dlc/dlc_env.sh"

export BASE_MODEL="$ROOT/models/qwen4"
export TRAIN_MULTI="${TRAIN_MULTI:-$ROOT/data/train_multi/train_multi_sft_minhash_dedup.jsonl}"
export TRAIN_TEXT="${TRAIN_TEXT:-$ROOT/data/train_text/train_text_sft_minhash_dedup.jsonl}"
export SFT_BENCHMARK="$ROOT/data/benchmark/my_benchmark/all.jsonl"
export SFT_EVAL_MAX_SAMPLES=1
export SFT_EVAL_STEPS=5
export SFT_EVAL_AT_ZERO=false
export SFT_GLOBAL_BATCH_SIZE=1
export SFT_JUDGE_URL="${SFT_JUDGE_URL:-http://127.0.0.1:8001}"
export WANDB_DISABLED=true
export WANDB_MODE=disabled
export IMAGE_MAX_TOKEN_NUM=256
export PYTORCH_ALLOC_CONF=expandable_segments:True
export SFT_ATTN_IMPL="${SFT_ATTN_IMPL:-sdpa}"
export SFT_CELOSS_PARALLEL_SIZE="${SFT_CELOSS_PARALLEL_SIZE:-4096}"
export SFT_DEBUG_MAX_LENGTH="${SFT_DEBUG_MAX_LENGTH:-81920}"
export CELOSS_PARALLEL_SIZE="$SFT_CELOSS_PARALLEL_SIZE"

PYTHON_BIN="${PYTHON_BIN:-/opt/ac2/bin/python}"
SWIFT_BIN="${SWIFT_BIN:-$PYTHONUSERBASE/bin/swift}"
RUN_ID="${SFT_DSW_RUN_ID:-sft_dsw_$(date +%Y%m%d_%H%M%S)}"
RUN_DIR="${SFT_DSW_OUTPUT_DIR:-$ROOT/output/sft_dsw/$RUN_ID}"
DEBUG_DATA="$RUN_DIR/debug_train.jsonl"

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
"$PYTHON_BIN" - "$ROOT" "$DEBUG_DATA" <<'PY'
import json
import os
import sys
from itertools import zip_longest
from pathlib import Path

from transformers import AutoTokenizer

root = Path(sys.argv[1])
output = Path(sys.argv[2])
sys.path.insert(0, str(root))
from scripts.sft.debug_sample_selection import select_representative_rows

tokenizer = AutoTokenizer.from_pretrained(root / 'models/qwen4', trust_remote_code=True)
paths = [Path(os.environ['TRAIN_MULTI']), Path(os.environ['TRAIN_TEXT'])]


def candidate_rows():
    with paths[0].open(encoding='utf-8') as multi, paths[1].open(encoding='utf-8') as text:
        for pair in zip_longest(multi, text):
            for line in pair:
                if line is None:
                    continue
                row = json.loads(line)
                chars = sum(len(str(message['content'])) for message in row['messages'])
                if chars <= 7000 or 9000 <= chars <= 28000 or 33000 <= chars <= 48000 or chars >= 55000:
                    yield row


def estimated_tokens(row):
    token_ids = tokenizer.apply_chat_template(row['messages'], tokenize=True, add_generation_prompt=False)
    return len(token_ids) + len(row.get('images', [])) * 255


selected = select_representative_rows(candidate_rows(), length_fn=estimated_tokens)
with output.open('w', encoding='utf-8') as handle:
    for row in selected:
        handle.write(json.dumps(row, ensure_ascii=False) + '\n')
PY

echo "===== SFT DSW DEBUG CONFIG ====="
echo "model=$BASE_MODEL debug_data=$DEBUG_DATA benchmark=$SFT_BENCHMARK"
echo "max_steps=5 max_length=$SFT_DEBUG_MAX_LENGTH gpus=0,1 sequence_parallel=2 deepspeed=zero2 fixed_batch=1 eval_samples=1 candidates=8"

exec "$SWIFT_BIN" sft \
  --model "$BASE_MODEL" \
  --model_type qwen3_vl \
  --dataset "$DEBUG_DATA" \
  --split_dataset_ratio 0 \
  --strict false \
  --tuner_type full \
  --freeze_vit false \
  --freeze_aligner false \
  --freeze_llm false \
  --torch_dtype bfloat16 \
  --attn_impl "$SFT_ATTN_IMPL" \
  --per_device_train_batch_size 1 \
  --gradient_accumulation_steps 1 \
  --gradient_checkpointing true \
  --vit_gradient_checkpointing true \
  --deepspeed zero2 \
  --sequence_parallel_size 2 \
  --max_length "$SFT_DEBUG_MAX_LENGTH" \
  --max_steps 5 \
  --learning_rate 1e-6 \
  --lr_scheduler_type cosine \
  --warmup_ratio 0.03 \
  --logging_steps 1 \
  --logging_nan_inf_filter false \
  --eval_strategy no \
  --save_strategy steps \
  --save_steps 5 \
  --save_only_model true \
  --report_to none \
  --external_plugins "$ROOT/scripts/sft/swift_sft_plugin.py" \
  --callbacks finar_log finar_numerics finar_pass_at_8 \
  --output_dir "$RUN_DIR"
