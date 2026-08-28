#!/usr/bin/env bash
if [ -z "${BASH_VERSION:-}" ]; then
  exec bash "$0" "$@"
fi
set -euo pipefail

CODE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd -P)"
export QWEN3VL_ROOT="${QWEN3VL_ROOT:-/mnt/nas/bihaoran/qwen3vl}"
CHECKPOINT_ROOT="${CHECKPOINT_ROOT:-/mnt/nas/bihaoran/qwen3vl/output/gspo/reasoning_qwen3vl4b_ckpt15500_20260826_retry3_tp4sleep2/v0-20260826-072528}"
BENCHMARK="${SFT_BENCHMARK:-/mnt/nas/bihaoran/qwen3vl/data/benchmark/reasoning_calc_val_50.jsonl}"
IMAGE_DIR="${SFT_BENCHMARK_IMAGE_DIR:-/mnt/nas/bihaoran/qwen3vl/data/benchmark/assets}"
JUDGE_MODEL="${JUDGE_MODEL:-/mnt/nas/bihaoran/model/qwen30}"
EVAL_ROOT="${SFT_CHECKPOINT_EVAL_ROOT:-$CHECKPOINT_ROOT/eval_sft_all}"
JUDGE_GPU="${SFT_CHECKPOINT_EVAL_JUDGE_GPU:-7}"
EVAL_GPU_CSV="${SFT_CHECKPOINT_EVAL_GPUS:-0,1,2,3,4,5,6}"
JUDGE_PORT="${SFT_JUDGE_PORT:-8001}"
JUDGE_STARTUP_TIMEOUT="${SFT_JUDGE_STARTUP_TIMEOUT:-3600}"
NODE_WORLD_SIZE="${WORLD_SIZE:?DLC must provide WORLD_SIZE}"
NODE_RANK="${RANK:?DLC must provide RANK}"
if [[ "$NODE_WORLD_SIZE" != "2" || ! "$NODE_RANK" =~ ^[01]$ ]]; then
  echo "checkpoint evaluation requires WORLD_SIZE=2 and RANK=0/1, got WORLD_SIZE=$NODE_WORLD_SIZE RANK=$NODE_RANK" >&2
  exit 1
fi

source "$CODE_ROOT/scripts/dlc/dlc_env.sh"
PYTHON_BIN="${PYTHON_BIN:-/opt/ac2/bin/python}"

test -d "$CHECKPOINT_ROOT" || { echo "missing checkpoint root: $CHECKPOINT_ROOT" >&2; exit 1; }
test -f "$BENCHMARK" || { echo "missing benchmark: $BENCHMARK" >&2; exit 1; }
test -d "$IMAGE_DIR" || { echo "missing benchmark image dir: $IMAGE_DIR" >&2; exit 1; }
test -f "$JUDGE_MODEL/config.json" || { echo "missing judge model: $JUDGE_MODEL/config.json" >&2; exit 1; }
test -f "$CODE_ROOT/scripts/sft/run_eval_only.py" || { echo "missing eval runner" >&2; exit 1; }
test -f "$CODE_ROOT/scripts/sft/checkpoint_eval_wandb.py" || { echo "missing W&B summary module" >&2; exit 1; }

mkdir -p "$EVAL_ROOT/checkpoints" "$EVAL_ROOT/logs"
PREPARED_BENCHMARK="$EVAL_ROOT/reasoning_calc_val_50_abs_images_rank${NODE_RANK}.jsonl"
"$PYTHON_BIN" - "$BENCHMARK" "$IMAGE_DIR" "$PREPARED_BENCHMARK" <<'PY'
import json
import os
import sys

src, image_dir, dst = sys.argv[1:4]

def resolve(path):
    if os.path.isabs(path):
        return path
    if path.startswith("assets/"):
        path = path[len("assets/"):]
    return os.path.join(image_dir, path)

with open(src, "r", encoding="utf-8") as fin, open(dst, "w", encoding="utf-8") as fout:
    for line in fin:
        row = json.loads(line)
        if isinstance(row.get("images"), list):
            row["images"] = [resolve(path) for path in row["images"]]
        if isinstance(row.get("image"), str):
            row["image"] = resolve(row["image"])
        fout.write(json.dumps(row, ensure_ascii=False) + "\n")
PY
BENCHMARK="$PREPARED_BENCHMARK"
EXPECTED_TASK_COUNT="$("$PYTHON_BIN" - "$BENCHMARK" <<'PY'
import json
import sys

tasks = set()
with open(sys.argv[1], encoding="utf-8") as handle:
    for line in handle:
        if line.strip():
            tasks.add(str(json.loads(line)["task"]))
print(len(tasks))
PY
)"

export PYTHONPATH="$CODE_ROOT:$PYTHON_USER_SITE${PYTHONPATH:+:$PYTHONPATH}"
export SFT_BENCHMARK="$BENCHMARK"
export SFT_JUDGE_URL="http://127.0.0.1:$JUDGE_PORT"
export GSPO_JUDGE_SERVE_NAME=qwen30-judge
export SFT_EVAL_MAX_SAMPLES=0
export SFT_PASS_AT_8_TEMPERATURE="${SFT_PASS_AT_8_TEMPERATURE:-1.0}"
export IMAGE_MAX_TOKEN_NUM="${IMAGE_MAX_TOKEN_NUM:-512}"
export WANDB_PROJECT="${WANDB_PROJECT:-FINAR-VL-GSPO-EVAL}"
export WANDB_NAME="${WANDB_NAME:-$(basename "$CHECKPOINT_ROOT")_sft_all}"
export WANDB_MODE=offline
export WANDB_DIR="$EVAL_ROOT/wandb"

FOCUS_ARGS=()

mkdir -p "$WANDB_DIR"
SYNC_DIR="$EVAL_ROOT/sync"
mkdir -p "$SYNC_DIR"
NODE_STATUS="$SYNC_DIR/node_${NODE_RANK}.status"
printf 'running\n' >"$NODE_STATUS"
JUDGE_PID=""
NODE_EVAL_COMPLETE=0
cleanup() {
  [[ -z "$JUDGE_PID" ]] || kill "$JUDGE_PID" 2>/dev/null || true
  if (( NODE_EVAL_COMPLETE == 0 )); then
    printf 'failed\n' >"$NODE_STATUS"
  fi
}
trap cleanup EXIT
OUTPUT_PROBE="$EVAL_ROOT/.output_dir_write_probe.$$"
printf 'writable\n' >"$OUTPUT_PROBE"
rm -f "$OUTPUT_PROBE"
echo "output_dir=$EVAL_ROOT writable=1 nas_root=$QWEN3VL_ROOT"
echo "checkpoint_root=$CHECKPOINT_ROOT"
echo "benchmark=$BENCHMARK image_dir=$IMAGE_DIR judge_model=$JUDGE_MODEL"
echo "node_rank=$NODE_RANK node_world_size=$NODE_WORLD_SIZE eval_gpus=$EVAL_GPU_CSV judge_gpu=$JUDGE_GPU wandb_mode=$WANDB_MODE wandb_dir=$WANDB_DIR"

"$PYTHON_BIN" -m scripts.sft.checkpoint_eval_wandb validate-benchmark \
  --benchmark "$BENCHMARK" \
  --expected-task-count "$EXPECTED_TASK_COUNT" \
  "${FOCUS_ARGS[@]}"

mapfile -t CHECKPOINTS < <(
  for checkpoint in "$CHECKPOINT_ROOT"/checkpoint-*; do
    [[ -d "$checkpoint" ]] || continue
    [[ "$(basename "$checkpoint")" =~ ^checkpoint-[0-9]+$ ]] || continue
    printf '%s\n' "$checkpoint"
  done | sort -V
)
if (( ${#CHECKPOINTS[@]} == 0 )); then
  echo "no checkpoint-<step> directories found in $CHECKPOINT_ROOT" >&2
  exit 1
fi
for checkpoint in "${CHECKPOINTS[@]}"; do
  test -f "$checkpoint/config.json" || { echo "missing checkpoint config: $checkpoint/config.json" >&2; exit 1; }
done

NODE_CHECKPOINTS=()
for index in "${!CHECKPOINTS[@]}"; do
  if (( index % NODE_WORLD_SIZE == NODE_RANK )); then
    NODE_CHECKPOINTS+=("${CHECKPOINTS[$index]}")
  fi
done
echo "node_checkpoint_count=${#NODE_CHECKPOINTS[@]} total_checkpoint_count=${#CHECKPOINTS[@]}"

IFS=',' read -r -a EVAL_GPUS <<<"$EVAL_GPU_CSV"
if (( ${#EVAL_GPUS[@]} != 7 )); then
  echo "SFT_CHECKPOINT_EVAL_GPUS must contain exactly 7 GPU ids" >&2
  exit 1
fi

JUDGE_LOG="$EVAL_ROOT/logs/qwen30_judge_node_${NODE_RANK}.log"
(
  export CUDA_VISIBLE_DEVICES="$JUDGE_GPU"
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
    --enforce-eager \
    --generation-config vllm
) >"$JUDGE_LOG" 2>&1 &
JUDGE_PID=$!

judge_deadline=$((SECONDS + JUDGE_STARTUP_TIMEOUT))
judge_ready=0
while (( SECONDS < judge_deadline )); do
  if ! kill -0 "$JUDGE_PID" 2>/dev/null; then
    echo "qwen30 judge exited before becoming healthy: $JUDGE_LOG" >&2
    exit 1
  fi
  if "$PYTHON_BIN" -c "import urllib.request; urllib.request.urlopen('$SFT_JUDGE_URL/health', timeout=2)" >/dev/null 2>&1; then
    judge_ready=1
    break
  fi
  sleep 2
done
if (( judge_ready == 0 )); then
  echo "qwen30 judge failed to become healthy within ${JUDGE_STARTUP_TIMEOUT}s: $JUDGE_LOG" >&2
  exit 1
fi
echo "judge_ready url=$SFT_JUDGE_URL model=qwen30-judge log=$JUDGE_LOG"

for ((wave_start = 0; wave_start < ${#NODE_CHECKPOINTS[@]}; wave_start += 7)); do
  pids=()
  names=()
  for ((slot = 0; slot < 7 && wave_start + slot < ${#NODE_CHECKPOINTS[@]}; slot++)); do
    checkpoint="${NODE_CHECKPOINTS[$((wave_start + slot))]}"
    checkpoint_name="$(basename "$checkpoint")"
    checkpoint_output="$EVAL_ROOT/checkpoints/$checkpoint_name"
    summary="$checkpoint_output/eval/step-000000/summary.json"
    if "$PYTHON_BIN" -m scripts.sft.checkpoint_eval_wandb check-summary \
      --benchmark "$BENCHMARK" \
      --expected-task-count "$EXPECTED_TASK_COUNT" \
      --summary "$summary"; then
      echo "checkpoint_skip_complete checkpoint=$checkpoint_name summary=$summary"
      continue
    fi
    if [[ -d "$checkpoint_output/eval" ]]; then
      mv "$checkpoint_output/eval" "$checkpoint_output/eval.incomplete.$(date +%Y%m%d_%H%M%S)"
    fi
    mkdir -p "$checkpoint_output/eval"
    checkpoint_log="$EVAL_ROOT/logs/${checkpoint_name}.log"
    eval_gpu="${EVAL_GPUS[$slot]}"
    echo "checkpoint_start checkpoint=$checkpoint_name gpu=$eval_gpu log=$checkpoint_log"
    (
      export CUDA_VISIBLE_DEVICES="$eval_gpu"
      export WANDB_DISABLED=true
      export WANDB_MODE=disabled
      export SFT_EVAL_OUTPUT="$checkpoint_output/eval"
      export TMPDIR="/tmp/qwen3vl-sft-eval-${checkpoint_name}"
      export TMP="$TMPDIR"
      export TEMP="$TMPDIR"
      mkdir -p "$TMPDIR"
      unset RANK WORLD_SIZE LOCAL_RANK MASTER_ADDR MASTER_PORT
      exec "$PYTHON_BIN" "$CODE_ROOT/scripts/sft/run_eval_only.py" \
        --model "$checkpoint" \
        --model_type qwen3_vl \
        --infer_backend transformers \
        --torch_dtype bfloat16 \
        --attn_impl sdpa \
        --device_map cuda:0
    ) >"$checkpoint_log" 2>&1 &
    pids+=("$!")
    names+=("$checkpoint_name")
  done

  wave_failed=0
  for index in "${!pids[@]}"; do
    if wait "${pids[$index]}"; then
      echo "checkpoint_finished checkpoint=${names[$index]}"
    else
      echo "checkpoint_failed checkpoint=${names[$index]} log=$EVAL_ROOT/logs/${names[$index]}.log" >&2
      wave_failed=1
    fi
  done
  if (( wave_failed != 0 )); then
    exit 1
  fi
done

printf 'complete\n' >"$NODE_STATUS"
NODE_EVAL_COMPLETE=1
if (( NODE_RANK != 0 )); then
  echo "GSPO_CHECKPOINT_EVAL_NODE_OK node_rank=$NODE_RANK checkpoints=${#NODE_CHECKPOINTS[@]} output_dir=$EVAL_ROOT"
  exit 0
fi

while true; do
  all_complete=1
  for checkpoint in "${CHECKPOINTS[@]}"; do
    summary="$EVAL_ROOT/checkpoints/$(basename "$checkpoint")/eval/step-000000/summary.json"
    if ! "$PYTHON_BIN" -m scripts.sft.checkpoint_eval_wandb check-summary \
      --benchmark "$BENCHMARK" \
      --expected-task-count "$EXPECTED_TASK_COUNT" \
      --summary "$summary"; then
      all_complete=0
      break
    fi
  done
  (( all_complete == 1 )) && break
  for ((rank = 1; rank < NODE_WORLD_SIZE; rank++)); do
    if [[ "$(cat "$SYNC_DIR/node_${rank}.status" 2>/dev/null || true)" == "failed" ]]; then
      echo "checkpoint evaluation failed on node rank $rank" >&2
      exit 1
    fi
  done
  sleep 10
done

unset WANDB_DISABLED
export WANDB_MODE=offline
"$PYTHON_BIN" -m scripts.sft.checkpoint_eval_wandb log \
  --checkpoint-root "$CHECKPOINT_ROOT" \
  --eval-root "$EVAL_ROOT" \
  --benchmark "$BENCHMARK" \
  --expected-task-count "$EXPECTED_TASK_COUNT" \
  "${FOCUS_ARGS[@]}" \
  --wandb-dir "$WANDB_DIR" \
  --wandb-project "$WANDB_PROJECT" \
  --wandb-name "$WANDB_NAME" \
  --wandb-mode "$WANDB_MODE"

echo "GSPO_CHECKPOINT_EVAL_OK nodes=$NODE_WORLD_SIZE checkpoints=${#CHECKPOINTS[@]} output_dir=$EVAL_ROOT"
