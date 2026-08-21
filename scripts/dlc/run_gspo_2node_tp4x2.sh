#!/usr/bin/env bash

# 2 nodes x 8 GPUs x 96GB
#
# reward node:
#   MODE=reward bash run_gspo_2node_tp4x2.sh
#
# train node:
#   SFT_MODEL=/path/to/sft \
#   RL_DATA=/path/to/train_rl_generation.jsonl \
#   REWARD_HOST=10.x.x.x \
#   bash run_gspo_2node_tp4x2.sh

MODE="${MODE:-train}"
ROOT="${FINAR_ROOT:-/mnt/nas/bihaoran/qwen3vl}"
PYTHON_BIN="${PYTHON_BIN:-/opt/ac2/bin/python}"

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
    RL_DATA="${RL_DATA:-$ROOT/data/train_rl_generation.jsonl}"
    WORK_DIR="${GSPO_WORK_DIR:-$ROOT/output/gspo_235b}"
    PREP_DATA="$WORK_DIR/train_rl_gspo.jsonl"
    REWARD_PLUGIN="$WORK_DIR/gspo_235b_reward.py"
    OUTPUT_DIR="${GSPO_OUTPUT_DIR:-$WORK_DIR/run}"

    mkdir -p "$WORK_DIR" "$OUTPUT_DIR"

    "$PYTHON_BIN" - "$RL_DATA" "$PREP_DATA" <<'PY'
import json
import sys

src, dst = sys.argv[1], sys.argv[2]

with open(src, "r", encoding="utf-8") as fin, open(dst, "w", encoding="utf-8") as fout:
    for line in fin:
        if not line.strip():
            continue
        row = json.loads(line)
        messages = row["messages"]
        fout.write(json.dumps({
            "messages": messages[:-1],
            "question": next(
                (m["content"] for m in reversed(messages[:-1]) if m.get("role") == "user"),
                "",
            ),
            "solution": messages[-1]["content"],
            "task": row.get("task", ""),
            "output_format": row.get("output_format", ""),
            "source": row.get("source", ""),
        }, ensure_ascii=False) + "\n")
PY

    cat > "$REWARD_PLUGIN" <<'PY'
import json
import os
import re
import urllib.request
from concurrent.futures import ThreadPoolExecutor

from swift.rewards import ORM, orms


def _at(value, i, default=""):
    if isinstance(value, (list, tuple)):
        return value[i] if i < len(value) else default
    return default if value is None else value


def _completion_text(value):
    if isinstance(value, str):
        return value
    if isinstance(value, list) and value and isinstance(value[-1], dict):
        return str(value[-1].get("content", ""))
    return str(value)


def _score(item):
    index, question, reference, candidate, output_format = item
    urls = [x.strip() for x in os.environ["REWARD_URLS"].split(",") if x.strip()]
    url = urls[index % len(urls)]

    prompt = f"""你是金融问答强化学习的奖励模型。根据题目和参考答案评价候选答案。

评分：
1.0：结论正确，关键内容完整，符合输出要求。
0.75：核心结论正确，仅有轻微遗漏或冗余。
0.5：部分正确，但存在重要遗漏、含混或局部错误。
0.25：只有少量相关正确内容，核心回答基本错误。
0.0：错误、答非所问、与参考答案关键结论冲突。

允许与参考答案表述不同但事实和结论正确的答案。
单选、多选、判断题优先检查最终选项或判断结论。
只返回 JSON：{{"score": 0.0}}

题目：
{question}

输出类型：
{output_format}

参考答案：
{reference}

候选答案：
{candidate}
"""

    payload = json.dumps({
        "model": os.environ.get("REWARD_SERVE_NAME", "qwen235-reward"),
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.0,
        "max_tokens": 64,
        "response_format": {"type": "json_object"},
        "chat_template_kwargs": {"enable_thinking": False},
    }, ensure_ascii=False).encode("utf-8")

    req = urllib.request.Request(
        url.rstrip("/") + "/v1/chat/completions",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(
            req, timeout=float(os.environ.get("REWARD_TIMEOUT", "300"))
        ) as resp:
            content = json.loads(resp.read().decode("utf-8"))["choices"][0]["message"]["content"]

        try:
            score = float(json.loads(content)["score"])
        except Exception:
            score = float(re.search(r'"?score"?\s*:\s*([0-9.]+)', content).group(1))

        return max(0.0, min(1.0, score))
    except Exception as e:
        print("[REWARD_ERROR]", url, repr(e), flush=True)
        return 0.0


class Qwen235JudgeReward(ORM):
    def __call__(self, completions, **kwargs):
        items = [
            (
                i,
                str(_at(kwargs.get("question"), i)),
                str(_at(kwargs.get("solution"), i)),
                _completion_text(completion),
                str(_at(kwargs.get("output_format"), i)),
            )
            for i, completion in enumerate(completions)
        ]

        with ThreadPoolExecutor(
            max_workers=int(os.environ.get("REWARD_CONCURRENCY", "4"))
        ) as pool:
            rewards = list(pool.map(_score, items))

        print("[GSPO_235B_REWARD]", rewards, flush=True)
        return rewards


orms["qwen235_judge"] = Qwen235JudgeReward
PY

    export CUDA_VISIBLE_DEVICES="${TRAIN_GPUS:-0,1,2,3,4,5,6,7}"
    export NPROC_PER_NODE=8
    export REWARD_SERVE_NAME
    export REWARD_URLS="${REWARD_URLS:-http://${REWARD_HOST}:8001,http://${REWARD_HOST}:8002}"
    export WANDB_MODE="${WANDB_MODE:-offline}"

    "$PYTHON_BIN" -m swift.cli rlhf \
        --rlhf_type grpo \
        --model "$SFT_MODEL" \
        --dataset "$PREP_DATA" \
        --split_dataset_ratio 0 \
        --external_plugins "$REWARD_PLUGIN" \
        --reward_funcs qwen235_judge \
        --importance_sampling_level sequence \
        --tuner_type full \
        --torch_dtype bfloat16 \
        --per_device_train_batch_size 1 \
        --gradient_accumulation_steps "${GSPO_GRAD_ACC:-1}" \
        --num_train_epochs "${GSPO_NUM_TRAIN_EPOCHS:-1}" \
        --num_generations "${GSPO_NUM_GENERATIONS:-8}" \
        --num_iterations "${GSPO_NUM_ITERATIONS:-1}" \
        --steps_per_generation "${GSPO_STEPS_PER_GENERATION:-1}" \
        --generation_batch_size "${GSPO_GENERATION_BATCH_SIZE:-64}" \
        --max_length "${GSPO_MAX_LENGTH:-8192}" \
        --max_completion_length "${GSPO_MAX_COMPLETION_LENGTH:-1024}" \
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
