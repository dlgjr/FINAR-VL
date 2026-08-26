#!/usr/bin/env bash
if [ -z "${BASH_VERSION:-}" ]; then
  exec bash "$0" "$@"
fi
set -euo pipefail

RUNS_ROOT=""
OUTPUT_DIR=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --runs_root)
      RUNS_ROOT="${2:?--runs_root requires a value}"
      shift 2
      ;;
    --output_dir)
      OUTPUT_DIR="${2:?--output_dir requires a value}"
      shift 2
      ;;
    *)
      echo "unknown argument: $1" >&2
      exit 1
      ;;
  esac
done

: "${RUNS_ROOT:?--runs_root is required}"
: "${OUTPUT_DIR:?--output_dir is required}"
: "${MOPD_REASONING_TEACHER:?MOPD_REASONING_TEACHER is required}"
: "${MOPD_GENERATION_TEACHER:?MOPD_GENERATION_TEACHER is required}"

CODE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd -P)"
NAS_ROOT="${QWEN3VL_ROOT:-/mnt/nas/bihaoran/qwen3vl}"
NODE_WORLD_SIZE="${WORLD_SIZE:?DLC must provide WORLD_SIZE}"
NODE_RANK="${RANK:?DLC must provide RANK}"
if [[ "$NODE_WORLD_SIZE" != "2" ]]; then
  echo "MOPD requires WORLD_SIZE=2, got: $NODE_WORLD_SIZE" >&2
  exit 1
fi

STUDENT_MODEL="${MOPD_STUDENT_MODEL:-$NAS_ROOT/output/sft_test_unclean/checkpoint15500_ep2_lr1e5/checkpoint-2744}"
REASONING_SOURCE="$NAS_ROOT/data/train_multi/train_rl_reasoning.jsonl"
GENERATION_SOURCE="$NAS_ROOT/data/train_multi/train_rl_generation.jsonl"
BENCHMARK="$NAS_ROOT/data/benchmark/my_benchmark/all.jsonl"
JUDGE_MODEL="${MOPD_JUDGE_MODEL:-/mnt/nas/bihaoran/model/qwen30}"
MEDIA_ROOT="$NAS_ROOT/data/train_multi"

export QWEN3VL_ROOT="$NAS_ROOT"
source "$CODE_ROOT/scripts/dlc/dlc_env.sh"
export NNODES="$NODE_WORLD_SIZE"
export NODE_RANK="$NODE_RANK"
export NPROC_PER_NODE=5
export CUDA_VISIBLE_DEVICES=0,1,2,3,4
export PYTHONPATH="$CODE_ROOT:$PYTHON_USER_SITE${PYTHONPATH:+:$PYTHONPATH}"
export IMAGE_MAX_TOKEN_NUM=512
export PYTORCH_ALLOC_CONF=expandable_segments:True

PYTHON_BIN="${PYTHON_BIN:-/opt/ac2/bin/python}"
SWIFT_BIN="${SWIFT_BIN:-$PYTHONUSERBASE/bin/swift}"
if [[ -x "$SWIFT_BIN" ]]; then
  SWIFT_CMD=("$SWIFT_BIN")
elif "$PYTHON_BIN" -c 'import swift' >/dev/null 2>&1; then
  SWIFT_CMD=("$PYTHON_BIN" -m swift.cli)
else
  echo "ms-swift is unavailable: $SWIFT_BIN" >&2
  exit 1
fi

for required in \
  "$STUDENT_MODEL/config.json" \
  "$MOPD_REASONING_TEACHER/config.json" \
  "$MOPD_GENERATION_TEACHER/config.json" \
  "$JUDGE_MODEL/config.json" \
  "$REASONING_SOURCE" \
  "$GENERATION_SOURCE" \
  "$BENCHMARK" \
  "$CODE_ROOT/scripts/rl/prepare_gspo_data.py" \
  "$CODE_ROOT/scripts/sft/swift_sft_plugin.py"; do
  test -f "$required" || { echo "missing required file: $required" >&2; exit 1; }
done
test -d "$MEDIA_ROOT/assets_rl" || { echo "missing RL assets: $MEDIA_ROOT/assets_rl" >&2; exit 1; }

export MOPD_LOCAL_TMPDIR="${MOPD_LOCAL_TMPDIR:-/tmp/qwen3vl-mopd-node-${NODE_RANK}}"
export TMPDIR="$MOPD_LOCAL_TMPDIR"
export TMP="$TMPDIR"
export TEMP="$TMPDIR"
export HF_HOME="$TMPDIR/cache/huggingface"
export HF_DATASETS_CACHE="$HF_HOME/datasets"
export HUGGINGFACE_HUB_CACHE="$HF_HOME/hub"
export MODELSCOPE_CACHE="$TMPDIR/cache/modelscope"
export TRITON_CACHE_DIR="$TMPDIR/cache/triton"
export TORCHINDUCTOR_CACHE_DIR="$TMPDIR/cache/torchinductor"
mkdir -p \
  "$RUNS_ROOT" \
  "$OUTPUT_DIR" \
  "$TMPDIR" \
  "$HF_DATASETS_CACHE" \
  "$HUGGINGFACE_HUB_CACHE" \
  "$MODELSCOPE_CACHE" \
  "$TRITON_CACHE_DIR" \
  "$TORCHINDUCTOR_CACHE_DIR"

OUTPUT_PROBE="$OUTPUT_DIR/.output_dir_write_probe.rank_${NODE_RANK}"
printf 'writable\n' >"$OUTPUT_PROBE"
rm -f "$OUTPUT_PROBE"
echo "runs_root=$RUNS_ROOT"
echo "output_dir=$OUTPUT_DIR writable=1 nas_root=$NAS_ROOT"

export WANDB_MODE=offline
export WANDB_PROJECT="${WANDB_PROJECT:-FINAR-VL-MOPD}"
export WANDB_DIR="$OUTPUT_DIR/wandb"
export WANDB_NAME="${MOPD_RUN_NAME:-$(basename "$OUTPUT_DIR")}"
mkdir -p "$WANDB_DIR"
"$PYTHON_BIN" -c 'import wandb; print(f"wandb.enabled=true wandb.mode=offline version={wandb.__version__} path={wandb.__file__}")'

PREPARED_DIR="$OUTPUT_DIR/prepared_data"
REASONING_DATA="$PREPARED_DIR/reasoning.jsonl"
GENERATION_DATA="$PREPARED_DIR/generation.jsonl"
DATA_READY="$PREPARED_DIR/.ready"
mkdir -p "$PREPARED_DIR"
if [[ "$NODE_RANK" == "0" ]]; then
  rm -f "$DATA_READY"
  "$PYTHON_BIN" -m scripts.rl.prepare_gspo_data \
    "$REASONING_SOURCE" \
    "$REASONING_DATA" \
    "$PREPARED_DIR/reasoning.audit.json"
  "$PYTHON_BIN" -m scripts.rl.prepare_gspo_data \
    "$GENERATION_SOURCE" \
    "$GENERATION_DATA" \
    "$PREPARED_DIR/generation.audit.json"
  touch "$DATA_READY"
else
  for attempt in $(seq 1 1800); do
    if [[ -f "$DATA_READY" ]]; then
      break
    fi
    sleep 1
    if (( attempt == 1800 )); then
      echo "timed out waiting for prepared MOPD data: $DATA_READY" >&2
      exit 1
    fi
  done
fi

REASONING_PORT="${MOPD_REASONING_PORT:-8003}"
GENERATION_PORT="${MOPD_GENERATION_PORT:-8004}"
JUDGE_PORT="${MOPD_JUDGE_PORT:-8002}"
REASONING_URL="http://127.0.0.1:$REASONING_PORT"
GENERATION_URL="http://127.0.0.1:$GENERATION_PORT"
export SFT_JUDGE_URL="http://127.0.0.1:$JUDGE_PORT"
export GSPO_JUDGE_SERVE_NAME=qwen30-judge
export SFT_BENCHMARK="$BENCHMARK"
export SFT_EVAL_STEPS=200
export SFT_EVAL_AT_ZERO=false
export SFT_PASS_AT_8_TEMPERATURE=1.0

cd "$MEDIA_ROOT"
REASONING_LOG="$OUTPUT_DIR/reasoning_teacher_node_${NODE_RANK}.log"
GENERATION_LOG="$OUTPUT_DIR/generation_teacher_node_${NODE_RANK}.log"
JUDGE_LOG="$OUTPUT_DIR/judge_node_${NODE_RANK}.log"

(
  export CUDA_VISIBLE_DEVICES=5
  export WANDB_DISABLED=true
  export WANDB_MODE=disabled
  exec "$PYTHON_BIN" -m vllm.entrypoints.openai.api_server \
    --model "$MOPD_REASONING_TEACHER" \
    --served-model-name mopd-reasoning-teacher \
    --host 127.0.0.1 \
    --port "$REASONING_PORT" \
    --dtype bfloat16 \
    --max-model-len 49152 \
    --tensor-parallel-size 1 \
    --gpu-memory-utilization 0.85 \
    --max-num-seqs 8 \
    --max-logprobs 1 \
    --allowed-local-media-path "$NAS_ROOT" \
    --enforce-eager \
    --generation-config vllm
) >"$REASONING_LOG" 2>&1 &
REASONING_PID=$!

(
  export CUDA_VISIBLE_DEVICES=6
  export WANDB_DISABLED=true
  export WANDB_MODE=disabled
  exec "$PYTHON_BIN" -m vllm.entrypoints.openai.api_server \
    --model "$MOPD_GENERATION_TEACHER" \
    --served-model-name mopd-generation-teacher \
    --host 127.0.0.1 \
    --port "$GENERATION_PORT" \
    --dtype bfloat16 \
    --max-model-len 49152 \
    --tensor-parallel-size 1 \
    --gpu-memory-utilization 0.85 \
    --max-num-seqs 8 \
    --max-logprobs 1 \
    --allowed-local-media-path "$NAS_ROOT" \
    --enforce-eager \
    --generation-config vllm
) >"$GENERATION_LOG" 2>&1 &
GENERATION_PID=$!

(
  export CUDA_VISIBLE_DEVICES=7
  export WANDB_DISABLED=true
  export WANDB_MODE=disabled
  exec "$PYTHON_BIN" -m vllm.entrypoints.openai.api_server \
    --model "$JUDGE_MODEL" \
    --served-model-name qwen30-judge \
    --host 127.0.0.1 \
    --port "$JUDGE_PORT" \
    --dtype bfloat16 \
    --max-model-len 8192 \
    --tensor-parallel-size 1 \
    --gpu-memory-utilization 0.70 \
    --max-num-seqs 8 \
    --allowed-local-media-path "$NAS_ROOT" \
    --enforce-eager \
    --generation-config vllm
) >"$JUDGE_LOG" 2>&1 &
JUDGE_PID=$!

cleanup() {
  kill "$JUDGE_PID" "$GENERATION_PID" "$REASONING_PID" 2>/dev/null || true
}
trap cleanup EXIT

wait_for_model() {
  local pid="$1"
  local url="$2"
  local model="$3"
  local log="$4"
  for attempt in $(seq 1 900); do
    if ! kill -0 "$pid" 2>/dev/null; then
      echo "model server exited before becoming healthy: model=$model log=$log" >&2
      exit 1
    fi
    if "$PYTHON_BIN" - "$url" "$model" <<'PY' >/dev/null 2>&1
import json
import sys
import urllib.request

base, wanted = sys.argv[1:]
with urllib.request.urlopen(base.rstrip('/') + '/v1/models', timeout=2) as response:
    payload = json.load(response)
raise SystemExit(0 if any(str(item.get('id', '')) == wanted for item in payload.get('data', [])) else 1)
PY
    then
      return
    fi
    sleep 2
  done
  echo "model server failed to become healthy: model=$model log=$log" >&2
  exit 1
}

wait_for_model "$REASONING_PID" "$REASONING_URL" mopd-reasoning-teacher "$REASONING_LOG"
wait_for_model "$GENERATION_PID" "$GENERATION_URL" mopd-generation-teacher "$GENERATION_LOG"
wait_for_model "$JUDGE_PID" "$SFT_JUDGE_URL" qwen30-judge "$JUDGE_LOG"

TEACHER_SERVERS="$(printf '[{"url":"%s","tags":["%s"]},{"url":"%s","tags":["%s"]}]' \
  "$REASONING_URL" "$REASONING_DATA" "$GENERATION_URL" "$GENERATION_DATA")"

RUNTIME_MODEL_DIR="$TMPDIR/student_model"
mkdir -p "$RUNTIME_MODEL_DIR"
while IFS= read -r -d '' MODEL_ENTRY; do
  MODEL_ENTRY_NAME="${MODEL_ENTRY##*/}"
  if [[ "$MODEL_ENTRY_NAME" != "tokenizer_config.json" ]]; then
    ln -sfn "$MODEL_ENTRY" "$RUNTIME_MODEL_DIR/$MODEL_ENTRY_NAME"
  fi
done < <(find "$STUDENT_MODEL" -mindepth 1 -maxdepth 1 -print0)
cp "$STUDENT_MODEL/tokenizer_config.json" "$RUNTIME_MODEL_DIR/tokenizer_config.json"
"$PYTHON_BIN" -c 'import json, pathlib, sys; path = pathlib.Path(sys.argv[1]); config = json.loads(path.read_text(encoding="utf-8")); config["fix_mistral_regex"] = False; path.write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")' "$RUNTIME_MODEL_DIR/tokenizer_config.json"

if [[ "$NODE_RANK" == "0" ]]; then
  echo "===== MOPD DLC CONFIG ====="
  echo "nodes=$NODE_WORLD_SIZE train_gpus=0,1,2,3,4 reasoning_teacher_gpu=5 generation_teacher_gpu=6 judge_gpu=7"
  echo "student_model=$STUDENT_MODEL runtime_model=$RUNTIME_MODEL_DIR"
  echo "reasoning_teacher=$MOPD_REASONING_TEACHER reasoning_data=$REASONING_DATA"
  echo "generation_teacher=$MOPD_GENERATION_TEACHER generation_data=$GENERATION_DATA"
  echo "teacher_servers=$TEACHER_SERVERS"
  echo "objective=pure_opd_rl teacher_kl_coef=1.0 reference_beta=0.0 rewards=none"
  echo "epochs=1 learning_rate=5e-6 num_generations=1 num_iterations=1"
  echo "max_length=49152 max_completion_length=2048 eval_steps=200 save_steps=200 eval_at_zero=false"
  echo "wandb.enabled=true wandb.mode=$WANDB_MODE wandb_dir=$WANDB_DIR"
  echo "runs_root=$RUNS_ROOT output_dir=$OUTPUT_DIR"
fi

"${SWIFT_CMD[@]}" rlhf \
  --rlhf_type grpo \
  --model "$RUNTIME_MODEL_DIR" \
  --model_type qwen3_vl \
  --teacher_model_server "$TEACHER_SERVERS" \
  --teacher_tag_key dataset \
  --teacher_kl_coef 1.0 \
  --dataset "$REASONING_DATA" "$GENERATION_DATA" \
  --split_dataset_ratio 0 \
  --dataset_shuffle true \
  --train_dataloader_shuffle true \
  --strict false \
  --lazy_tokenize true \
  --tuner_type full \
  --freeze_vit false \
  --freeze_aligner false \
  --freeze_llm false \
  --torch_dtype bfloat16 \
  --attn_impl flash_attn \
  --deepspeed zero2 \
  --per_device_train_batch_size 1 \
  --gradient_accumulation_steps 1 \
  --gradient_checkpointing true \
  --vit_gradient_checkpointing true \
  --ddp_find_unused_parameters true \
  --num_train_epochs 1 \
  --num_generations 1 \
  --num_iterations 1 \
  --steps_per_generation 1 \
  --max_length 49152 \
  --max_completion_length 2048 \
  --truncation_strategy delete \
  --dynamic_sample false \
  --temperature 1.0 \
  --learning_rate 5e-6 \
  --lr_scheduler_type constant \
  --beta 0.0 \
  --max_grad_norm 0.5 \
  --importance_sampling_level token \
  --use_vllm true \
  --vllm_mode colocate \
  --vllm_tensor_parallel_size 1 \
  --vllm_max_model_len 49152 \
  --vllm_max_num_seqs 1 \
  --vllm_gpu_memory_utilization 0.35 \
  --vllm_mm_processor_cache_gb 0 \
  --vllm_enforce_eager true \
  --sleep_level 2 \
  --logging_steps 1 \
  --eval_strategy no \
  --save_strategy steps \
  --save_steps 200 \
  --save_total_limit 100 \
  --save_only_model true \
  --report_to wandb \
  --run_name "$WANDB_NAME" \
  --external_plugins "$CODE_ROOT/scripts/sft/swift_sft_plugin.py" \
  --callbacks finar_pass_at_8 \
  --dataset_num_proc 1 \
  --dataloader_num_workers 1 \
  --add_version false \
  --output_dir "$OUTPUT_DIR"

echo "DLC_MOPD_OK output_dir=$OUTPUT_DIR"
