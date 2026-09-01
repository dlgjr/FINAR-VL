#!/usr/bin/env bash

ROOT="${QWEN3VL_ROOT:-/mnt/nas/bihaoran/qwen3vl}"
CHECKPOINTS=(
  "/mnt/nas/bihaoran/qwen3vl/output/sft_test_unclean/checkpoint15500_ep2_lr1e5/checkpoint-1372"
  "/mnt/nas/bihaoran/qwen3vl/output/sft_test_unclean/checkpoint15500_ep2_lr1e5/checkpoint-2744"
)
BENCHMARK="/mnt/nas/bihaoran/qwen3vl/data/benchmark/test.jsonl"
IMAGE_DIR="/mnt/nas/bihaoran/qwen3vl/data/benchmark/assets"
EVAL_ROOT="${SFT_TEST_UNCLEAN_EVAL_ROOT:-$ROOT/output/sft_test_unclean/checkpoint15500_ep2_lr1e5/test_eval}"
JUDGE_MODEL="${JUDGE_MODEL:-/mnt/nas/bihaoran/model/qwen30}"
JUDGE_GPU="${SFT_TEST_UNCLEAN_JUDGE_GPU:-7}"
EVAL_GPU="${SFT_TEST_UNCLEAN_EVAL_GPU:-0}"
JUDGE_PORT="${SFT_JUDGE_PORT:-8001}"
NODE_RANK="${RANK:-0}"
NODE_WORLD_SIZE="${WORLD_SIZE:-2}"

source "$ROOT/scripts/dlc/dlc_env.sh"

PYTHON_BIN="${PYTHON_BIN:-/opt/ac2/bin/python}"
export PYTHONPATH="$ROOT:$PYTHON_USER_SITE${PYTHONPATH:+:$PYTHONPATH}"
export IMAGE_MAX_TOKEN_NUM="${IMAGE_MAX_TOKEN_NUM:-512}"
export SFT_PASS_AT_8_TEMPERATURE="${SFT_PASS_AT_8_TEMPERATURE:-1.0}"
export SFT_JUDGE_URL="http://127.0.0.1:$JUDGE_PORT"
export GSPO_JUDGE_SERVE_NAME="qwen30-judge"
export SFT_EVAL_MAX_SAMPLES=0

if [[ "$NODE_WORLD_SIZE" != "2" || ! "$NODE_RANK" =~ ^[01]$ ]]; then
  echo "requires two DLC nodes: WORLD_SIZE=2 and RANK=0/1; got WORLD_SIZE=$NODE_WORLD_SIZE RANK=$NODE_RANK"
else
  mkdir -p "$EVAL_ROOT/logs" "$EVAL_ROOT/sync"
  checkpoint="${CHECKPOINTS[$NODE_RANK]}"
  checkpoint_name="$(basename "$checkpoint")"
  checkpoint_output="$EVAL_ROOT/$checkpoint_name"
  checkpoint_log="$EVAL_ROOT/logs/$checkpoint_name.log"
  PREPARED_DATA="$EVAL_ROOT/test_abs_images_rank${NODE_RANK}.jsonl"
  NODE_STATUS="$EVAL_ROOT/sync/node_${NODE_RANK}.status"

  printf 'running\n' >"$NODE_STATUS"

  "$PYTHON_BIN" - "$BENCHMARK" "$IMAGE_DIR" "$PREPARED_DATA" <<'PY'
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

  JUDGE_LOG="$EVAL_ROOT/logs/qwen30_judge_rank${NODE_RANK}.log"
  (
    export CUDA_VISIBLE_DEVICES="$JUDGE_GPU"
    export WANDB_DISABLED=true
    export WANDB_MODE=disabled
    "$PYTHON_BIN" -m vllm.entrypoints.openai.api_server \
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

  judge_ready=0
  for _ in $(seq 1 1800); do
    if "$PYTHON_BIN" -c "import urllib.request; urllib.request.urlopen('$SFT_JUDGE_URL/health', timeout=2)" >/dev/null 2>&1; then
      judge_ready=1
      break
    fi
    sleep 2
  done

  if (( judge_ready == 1 )); then
    rm -rf "$checkpoint_output/eval"
    mkdir -p "$checkpoint_output/eval"
    echo "checkpoint_start rank=$NODE_RANK checkpoint=$checkpoint_name eval_gpu=$EVAL_GPU judge_gpu=$JUDGE_GPU log=$checkpoint_log"

    (
      export CUDA_VISIBLE_DEVICES="$EVAL_GPU"
      export WANDB_DISABLED=true
      export WANDB_MODE=disabled
      export SFT_BENCHMARK="$PREPARED_DATA"
      export SFT_EVAL_OUTPUT="$checkpoint_output/eval"
      export TMPDIR="/tmp/qwen3vl-test-unclean-eval-$checkpoint_name"
      export TMP="$TMPDIR"
      export TEMP="$TMPDIR"
      mkdir -p "$TMPDIR"
      unset RANK WORLD_SIZE LOCAL_RANK MASTER_ADDR MASTER_PORT
      "$PYTHON_BIN" "$ROOT/scripts/sft/run_eval_only.py" \
        --model "$checkpoint" \
        --model_type qwen3_vl \
        --infer_backend transformers \
        --torch_dtype bfloat16 \
        --attn_impl sdpa \
        --device_map cuda:0
    ) >"$checkpoint_log" 2>&1 &
    EVAL_PID=$!

    STATUS_PATH="$checkpoint_output/eval/step-000000/status/rank_0000.json"
    RUN_CONFIG_PATH="$checkpoint_output/eval/step-000000/run_config.json"
    while kill -0 "$EVAL_PID" 2>/dev/null; do
      if [[ -f "$STATUS_PATH" && -f "$RUN_CONFIG_PATH" ]]; then
        "$PYTHON_BIN" -c "import json; s=json.load(open('$STATUS_PATH')); c=json.load(open('$RUN_CONFIG_PATH')); total=int(c['total']); done=int(s['completed']); errors=int(s['errors']); print(f'checkpoint_progress rank=$NODE_RANK checkpoint=$checkpoint_name completed={done}/{total} errors={errors} progress={(done+errors)/total*100 if total else 0:.2f}% elapsed={float(s[\"elapsed_seconds\"]):.1f}s', flush=True)"
      fi
      sleep 10
    done

    if wait "$EVAL_PID"; then
      "$PYTHON_BIN" -c "import json; s=json.load(open('$STATUS_PATH')); c=json.load(open('$RUN_CONFIG_PATH')); total=int(c['total']); done=int(s['completed']); errors=int(s['errors']); print(f'checkpoint_progress rank=$NODE_RANK checkpoint=$checkpoint_name completed={done}/{total} errors={errors} progress={(done+errors)/total*100 if total else 0:.2f}% elapsed={float(s[\"elapsed_seconds\"]):.1f}s', flush=True)"
      printf 'complete\n' >"$NODE_STATUS"
      echo "checkpoint_finished rank=$NODE_RANK checkpoint=$checkpoint_name"
    else
      printf 'failed\n' >"$NODE_STATUS"
      echo "checkpoint_failed rank=$NODE_RANK checkpoint=$checkpoint_name log=$checkpoint_log"
    fi
  else
    printf 'failed\n' >"$NODE_STATUS"
    echo "judge server not ready on rank=$NODE_RANK; see $JUDGE_LOG"
  fi

  kill "$JUDGE_PID" 2>/dev/null || true

  if [[ "$NODE_RANK" == "0" ]]; then
    echo "waiting_for_rank1 checkpoint=${CHECKPOINTS[1]}"
    while true; do
      rank0_status="$(cat "$EVAL_ROOT/sync/node_0.status" 2>/dev/null || true)"
      rank1_status="$(cat "$EVAL_ROOT/sync/node_1.status" 2>/dev/null || true)"
      if [[ "$rank0_status" == "complete" && "$rank1_status" == "complete" ]]; then
        break
      fi
      if [[ "$rank0_status" == "failed" || "$rank1_status" == "failed" ]]; then
        echo "evaluation_failed rank0_status=$rank0_status rank1_status=$rank1_status"
        break
      fi
      echo "waiting_for_nodes rank0_status=${rank0_status:-missing} rank1_status=${rank1_status:-missing}"
      sleep 10
    done

    if [[ "$(cat "$EVAL_ROOT/sync/node_0.status" 2>/dev/null || true)" == "complete" && "$(cat "$EVAL_ROOT/sync/node_1.status" 2>/dev/null || true)" == "complete" ]]; then
      "$PYTHON_BIN" - "$BENCHMARK" "$EVAL_ROOT" "${CHECKPOINTS[@]}" <<'PY'
import json
import sys
from collections import defaultdict
from pathlib import Path

benchmark = Path(sys.argv[1])
eval_root = Path(sys.argv[2])
checkpoints = [Path(path) for path in sys.argv[3:]]

rows = []
with benchmark.open(encoding="utf-8") as handle:
    for line in handle:
        if line.strip():
            rows.append(json.loads(line))

all_summaries = {}
for checkpoint in checkpoints:
    name = checkpoint.name
    step_dir = eval_root / name / "eval" / "step-000000"
    predictions_path = step_dir / "predictions.jsonl"
    errors_path = step_dir / "errors.jsonl"
    predictions = [json.loads(line) for line in predictions_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    errors = [json.loads(line) for line in errors_path.read_text(encoding="utf-8").splitlines() if line.strip()] if errors_path.is_file() else []

    stats = defaultdict(lambda: {"total": 0, "completed": 0, "errors": 0, "pass_at_1_count": 0, "pass_at_8_count": 0})
    for row in rows:
        source = str(row.get("source") or "unknown")
        stats[source]["total"] += 1

    for prediction in predictions:
        index = int(str(prediction["sample_id"]).rsplit(":", 1)[1])
        source = str(rows[index].get("source") or "unknown")
        stats[source]["completed"] += 1
        stats[source]["pass_at_1_count"] += int(bool(prediction["first_correct"]))
        stats[source]["pass_at_8_count"] += int(int(prediction["correct_count"]) > 0)

    for error in errors:
        index = int(str(error["sample_id"]).rsplit(":", 1)[1])
        source = str(rows[index].get("source") or "unknown")
        stats[source]["errors"] += 1

    source_summary = {}
    for source in sorted(stats):
        item = stats[source]
        total = item["total"]
        source_summary[source] = {
            **item,
            "coverage": item["completed"] / total if total else 0.0,
            "pass_at_1": item["pass_at_1_count"] / total if total else 0.0,
            "pass_at_8": item["pass_at_8_count"] / total if total else 0.0,
        }

    summary_path = step_dir / "source_summary.json"
    summary_path.write_text(json.dumps(source_summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    all_summaries[name] = source_summary

    print(f"\n===== {name} =====")
    print(f"{'source':32s} {'total':>7s} {'done':>7s} {'error':>7s} {'coverage':>10s} {'pass@1':>10s} {'pass@8':>10s}")
    for source, item in source_summary.items():
        print(
            f"{source[:32]:32s} {item['total']:7d} {item['completed']:7d} {item['errors']:7d} "
            f"{item['coverage']:10.4f} {item['pass_at_1']:10.4f} {item['pass_at_8']:10.4f}"
        )

(eval_root / "source_summary.json").write_text(
    json.dumps(all_summaries, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
)
print(f"\nsource_summary={eval_root / 'source_summary.json'}")
PY
    fi
  fi
fi
