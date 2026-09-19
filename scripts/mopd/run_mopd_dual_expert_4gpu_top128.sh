#!/usr/bin/env bash
if [[ -z "${BASH_VERSION:-}" ]]; then
  exec bash "$0" "$@"
fi
set -euo pipefail

ROOT="${QWEN3VL_ROOT:-/mnt/nas/duolg/qwen3vl}"
OUTPUT_DIR="${MOPD_OUTPUT_DIR:-}"
RESUME_FROM_CHECKPOINT="${MOPD_RESUME_FROM_CHECKPOINT:-}"
RUN_NAME="${MOPD_RUN_NAME:-}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --output_dir)
      OUTPUT_DIR="${2:?--output_dir requires a value}"
      shift 2
      ;;
    --resume_from_checkpoint)
      RESUME_FROM_CHECKPOINT="${2:?--resume_from_checkpoint requires a value}"
      shift 2
      ;;
    --run_name)
      RUN_NAME="${2:?--run_name requires a value}"
      shift 2
      ;;
    *)
      echo "unknown argument: $1" >&2
      exit 1
      ;;
  esac
done

STUDENT_MODEL="${MOPD_STUDENT_MODEL:-$ROOT/output/sft/sft_qwen3vl4b_20260821_183115/v0-20260821-185530/checkpoint-15500}"
REASONING_TEACHER="${MOPD_REASONING_TEACHER:-$ROOT/output/gspo/direct_token_grpo_gold_4gpu_20260912_230850/checkpoint-3120}"
REASONING_SOURCE="${MOPD_REASONING_DATA:-$ROOT/output/gspo/direct_token_grpo_gold_4gpu_20260912_230850/train_gspo.jsonl}"
GENERATION_TEACHER="${MOPD_GENERATION_TEACHER:-$ROOT/output/gspo/generation_qwen3vl4b_ckpt700_20260827_retry3_tp4sleep2/v0-20260827-025050/checkpoint-2350}"
GENERATION_SOURCE="${MOPD_GENERATION_DATA:-$ROOT/output/gspo/generation_qwen3vl4b_ckpt700_20260827_retry3_tp4sleep2/train_gspo.jsonl}"
BENCHMARK="${MOPD_BENCHMARK:-$ROOT/data/benchmark/my_benchmark/all.jsonl}"

if [[ -n "$RESUME_FROM_CHECKPOINT" && -z "$OUTPUT_DIR" ]]; then
  OUTPUT_DIR="$(dirname "$RESUME_FROM_CHECKPOINT")"
fi
if [[ -z "$OUTPUT_DIR" ]]; then
  RUN_STAMP="$(date +%Y%m%d_%H%M%S)"
  OUTPUT_DIR="$ROOT/output/mopd/mopd_dual_expert_4gpu_${RUN_STAMP}"
fi
if [[ -z "$RUN_NAME" ]]; then
  RUN_NAME="$(basename "$OUTPUT_DIR")"
fi

export QWEN3VL_ROOT="$ROOT"
export MOPD_STUDENT_MODEL="$STUDENT_MODEL"
source "$ROOT/scripts/dlc/dlc_env.sh"

# Single-node 4x96GB layout:
#   GPU 0-1: student training + colocated rollout vLLM
#   GPU 2:   reasoning teacher
#   GPU 3:   generation teacher + LLM judge
export NNODES=1
export NODE_RANK=0
export NPROC_PER_NODE=2
export MASTER_ADDR="${MASTER_ADDR:-127.0.0.1}"
export MASTER_PORT="${MOPD_MASTER_PORT:-29620}"
export CUDA_VISIBLE_DEVICES=0,1
export PYTHONPATH="$ROOT:$PYTHON_USER_SITE${PYTHONPATH:+:$PYTHONPATH}"
export IMAGE_MAX_TOKEN_NUM="${MOPD_IMAGE_MAX_TOKEN_NUM:-10240}"
export GSPO_TRAIN_ASSET_ROOT="${GSPO_TRAIN_ASSET_ROOT:-$ROOT/data/train_multi/assets_rl}"
export GSPO_BENCH_ASSET_ROOT="${GSPO_BENCH_ASSET_ROOT:-$ROOT/data/benchmark/assets}"
export PYTORCH_ALLOC_CONF="${PYTORCH_ALLOC_CONF:-expandable_segments:True}"

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
  "$STUDENT_MODEL/tokenizer_config.json" \
  "$REASONING_TEACHER/config.json" \
  "$GENERATION_TEACHER/config.json" \
  "$REASONING_SOURCE" \
  "$GENERATION_SOURCE" \
  "$BENCHMARK" \
  "$ROOT/scripts/sft/swift_sft_plugin.py" \
  "$ROOT/scripts/sft/swift_sft_plugin_impl.py" \
  "$ROOT/scripts/sft/pass_at_8_eval.py"; do
  test -f "$required" || { echo "missing required file: $required" >&2; exit 1; }
done

mkdir -p "$OUTPUT_DIR"
OUTPUT_PROBE="$OUTPUT_DIR/.write_probe"
printf 'ok\n' > "$OUTPUT_PROBE"
rm -f "$OUTPUT_PROBE"

export MOPD_LOCAL_TMPDIR="${MOPD_LOCAL_TMPDIR:-/tmp/qwen3vl-mopd-${RUN_NAME}}"
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
  "$TMPDIR" \
  "$HF_DATASETS_CACHE" \
  "$HUGGINGFACE_HUB_CACHE" \
  "$MODELSCOPE_CACHE" \
  "$TRITON_CACHE_DIR" \
  "$TORCHINDUCTOR_CACHE_DIR" \
  "$OUTPUT_DIR/wandb"

# W&B: log every optimizer step directly online.
unset WANDB_DISABLED
export WANDB_MODE=online
export WANDB_PROJECT="${WANDB_PROJECT:-FINAR-VL-MOPD}"
export WANDB_DIR="$OUTPUT_DIR/wandb"
export WANDB_NAME="$RUN_NAME"
if [[ -n "$RESUME_FROM_CHECKPOINT" ]]; then
  : "${WANDB_RUN_ID:?resume requires WANDB_RUN_ID so W&B continues the same run}"
  export WANDB_RESUME="${WANDB_RESUME:-must}"
fi

# -----------------------------------------------------------------------------
# Build a deterministic exactly-balanced MOPD dataset.
# Every consecutive pair contains one reasoning row and one generation row.
# Pair order alternates so a fixed DDP rank does not always see the same expert.
# The larger source is truncated to min(N_reasoning, N_generation).
# -----------------------------------------------------------------------------
PREPARED_DIR="$OUTPUT_DIR/prepared_data"
BALANCED_DATA="$PREPARED_DIR/mopd_balanced.jsonl"
BALANCE_AUDIT="$PREPARED_DIR/mopd_balanced.audit.json"
mkdir -p "$PREPARED_DIR"

if [[ -z "$RESUME_FROM_CHECKPOINT" || ! -s "$BALANCED_DATA" ]]; then
  "$PYTHON_BIN" - "$REASONING_SOURCE" "$GENERATION_SOURCE" "$BALANCED_DATA" "$BALANCE_AUDIT" "${MOPD_DATA_SEED:-42}" <<'PY'
import json
import random
import sys
from pathlib import Path
from scripts.rl.prepare_gspo_data import _resolve_training_image

reasoning_path, generation_path, output_path, audit_path, seed_text = sys.argv[1:]
seed = int(seed_text)

REASONING_SUFFIX = "请只输出最终答案本身，不要输出分析过程或额外解释。"
GENERATION_SUFFIX = "请在回复最后一行按“答案：具体答案”的格式给出最终答案。"
OLD_REASONING_PROMPT = (
    "请先独立分析问题，结合相关文本、表格和图像信息，完成必要的推理、计算和结果核对后再作答。不要直接猜测答案。"
    "\n请在回复最后一行按“答案：具体答案”的格式给出最终答案。"
)
PREVIOUS_REASONING_PROMPT = (
    "请严格按以下顺序作答："
    "\n1. 先仔细读取并理解图像、表格和文本中的相关信息，明确需要使用的数据；"
    "\n2. 再基于读取到的信息进行分析、推理和必要的计算，并核对结果；"
    "\n3. 最后给出答案。"
    "\n不要跳过读图直接猜答案，也不要只输出最终答案。"
    "\n请在回复最后一行按“答案：具体答案”的格式给出最终答案。"
)
LEGACY_REASONING_SYSTEM_PROMPT = """请仔细完成用户给出的计算题，并给出每一步的详细计算步骤，严禁直接输出答案。

1. 先理解题意，明确题目要求计算的目标是什么。

2. 如果题目已经明确描述了计算关系，必须首先严格按照题目原意写出计算公式。
不得自行改变题目给出的运算关系，不得自行增加、删除或替换计算指标。

3. 写出完成这个计算实际需要的数据。
如果题目包含图片、表格或图表，请从中读取与当前计算直接相关的数据；
如果没有图片，则从题干或文本中提取所需数据。

只允许使用前面计算公式中出现的指标。
不要读取、列举或计算题目没有要求的其他指标。
不要用名称相似的指标替代题目明确指定的指标。
如果题目已经直接给出了某个计算所需指标的数值，请直接使用该数值，不要根据其他相关指标重新推导或替代它。

4. 将提取的数据代入前面确定的公式，并展示必要的计算过程。
计算过程中必须保持与题目原始计算关系一致。

5. 在完成前面的数据提取和计算步骤之前，不要直接输出最终答案。

最后一行严格按照以下格式输出：

最终答案：具体答案"""
LEGACY_USER_SENTENCES = (
    "严禁直接给出答案，必须给出计算的相关步骤。",
    "只使用完成用户所问计算直接需要的数据；即使图片中存在其他指标，也不要把它们加入计算过程。",
)

def clean_user_text(text: str) -> str:
    cleaned = text
    for suffix in (OLD_REASONING_PROMPT, PREVIOUS_REASONING_PROMPT, REASONING_SUFFIX, GENERATION_SUFFIX):
        cleaned = cleaned.replace("\n" + suffix, "").replace(suffix, "")
    for sentence in LEGACY_USER_SENTENCES:
        cleaned = cleaned.replace("\n" + sentence, "").replace(sentence, "")
    return cleaned.rstrip()

def strip_reasoning_legacy_system(messages: list) -> None:
    remove = []
    for idx, message in enumerate(messages):
        if not isinstance(message, dict) or message.get("role") != "system":
            continue
        content = message.get("content", "")
        if isinstance(content, str):
            cleaned = content.replace(LEGACY_REASONING_SYSTEM_PROMPT, "").strip()
            if cleaned:
                message["content"] = cleaned
            else:
                remove.append(idx)
        elif isinstance(content, list):
            new_content=[]
            for item in content:
                if isinstance(item, dict) and item.get("type") == "text" and isinstance(item.get("text"), str):
                    cleaned = item["text"].replace(LEGACY_REASONING_SYSTEM_PROMPT, "").strip()
                    if cleaned:
                        copied=dict(item); copied["text"]=cleaned; new_content.append(copied)
                else:
                    new_content.append(item)
            if new_content:
                message["content"] = new_content
            else:
                remove.append(idx)
    for idx in reversed(remove):
        messages.pop(idx)

def patch_last_user_message(row: dict, route: str) -> None:
    messages = row.get("messages")
    if not isinstance(messages, list):
        raise ValueError(f"{route} sample has invalid messages: {type(messages)!r}")
    if route == "reasoning":
        strip_reasoning_legacy_system(messages)
        wanted = REASONING_SUFFIX
    else:
        wanted = GENERATION_SUFFIX
    for message in reversed(messages):
        if not isinstance(message, dict) or message.get("role") != "user":
            continue
        content = message.get("content", "")
        if isinstance(content, str):
            message["content"] = clean_user_text(content) + "\n" + wanted
            return
        if isinstance(content, list):
            for item in reversed(content):
                if isinstance(item, dict) and item.get("type") == "text" and isinstance(item.get("text"), str):
                    item["text"] = clean_user_text(item["text"]) + "\n" + wanted
                    return
            content.append({"type":"text","text":wanted})
            return
        raise ValueError(f"{route} user content has invalid type: {type(content)!r}")
    raise ValueError(f"{route} sample has no user message")

def load(path: str, route: str):
    rows=[]
    with open(path,'r',encoding='utf-8') as handle:
        for line_number,line in enumerate(handle,1):
            if not line.strip():
                continue
            row=json.loads(line)
            patch_last_user_message(row, route)

            # Use the exact image lookup logic from the recent GSPO preparation code.
            # Examples:
            #   assets_rl/ewai/generation_1314.png
            #     -> $GSPO_TRAIN_ASSET_ROOT/ewai/generation_1314.png
            #   assets/foo.png
            #     -> $GSPO_TRAIN_ASSET_ROOT/foo.png
            # Absolute existing paths are preserved. If neither train nor benchmark
            # root contains the file, fail before training rather than silently resample.
            if row.get('images'):
                row['images']=[_resolve_training_image(image) for image in row['images']]

            original_id=row.get('sample_id') or row.get('id') or f'line:{line_number}'
            row['_mopd_original_sample_id']=str(original_id)
            row['sample_id']=f'{route}:{original_id}'
            row['prompt_id']=f'{route}:{original_id}'
            row['mopd_teacher']=route
            rows.append(row)
    return rows

reasoning=load(reasoning_path,'reasoning')
generation=load(generation_path,'generation')
if not reasoning or not generation:
    raise SystemExit(f'empty MOPD source: reasoning={len(reasoning)} generation={len(generation)}')
rng=random.Random(seed); rng.shuffle(reasoning); rng.shuffle(generation)
pairs=min(len(reasoning),len(generation))
reasoning=reasoning[:pairs]; generation=generation[:pairs]
out=Path(output_path); out.parent.mkdir(parents=True,exist_ok=True)
with out.open('w',encoding='utf-8') as handle:
    for i,(r,g) in enumerate(zip(reasoning,generation)):
        pair=(r,g) if i%2==0 else (g,r)
        for row in pair:
            handle.write(json.dumps(row,ensure_ascii=False)+'\n')
with out.open('r',encoding='utf-8') as handle:
    written=[json.loads(line) for line in handle if line.strip()]
for i in range(0,len(written),2):
    routes={written[i]['mopd_teacher'],written[i+1]['mopd_teacher']}
    if routes != {'reasoning','generation'}:
        raise RuntimeError(f'unbalanced pair at rows {i},{i+1}: {routes}')
audit={
    'seed':seed,'reasoning_source':reasoning_path,'generation_source':generation_path,
    'pairs':pairs,'output_rows':len(written),'reasoning_used':pairs,'generation_used':pairs,
    'pair_invariant':'each consecutive pair has exactly one reasoning and one generation sample',
    'reasoning_user_suffix':REASONING_SUFFIX,'generation_user_suffix':GENERATION_SUFFIX,
    'train_asset_root': __import__('os').environ.get('GSPO_TRAIN_ASSET_ROOT'),
    'bench_asset_root': __import__('os').environ.get('GSPO_BENCH_ASSET_ROOT'),
    'image_resolution': 'scripts.rl.prepare_gspo_data._resolve_training_image',
}
Path(audit_path).write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(audit,ensure_ascii=False))
PY
fi

# -----------------------------------------------------------------------------
# Runtime plugin:
# 1) reuse the repository SFT Pass@1/Pass@8 evaluation callback;
# 2) replace its original on_save cleanup (which deletes CURRENT state) with the
#    repository's GSPO latest-state policy: verify current resume state first,
#    then delete resume state from older checkpoints while keeping model weights.
# -----------------------------------------------------------------------------
RUNTIME_PLUGIN="$PREPARED_DIR/mopd_runtime_plugin.py"
cat > "$RUNTIME_PLUGIN" <<'PY'
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import asdict
from pathlib import Path
from typing import Any

from scripts.sft import swift_sft_plugin as _swift_sft_plugin  # noqa: F401
from scripts.sft.swift_sft_plugin_impl import FinarPassAt8Callback
import scripts.sft.pass_at_8_eval as _mopd_eval

# The generic dataset preprocessor may drop unknown JSONL columns before
# GKDSample.from_row sees them.  Therefore `mopd_teacher` in sample.extra is
# not reliable.  Route using formal fields/messages as a fallback.
from swift.rl_core.data import OnPolicySample

_REASONING_ROUTE_SUFFIX = "请只输出最终答案本身，不要输出分析过程或额外解释。"
_GENERATION_ROUTE_SUFFIX = "请在回复最后一行按“答案：具体答案”的格式给出最终答案。"

_original_get_tag = OnPolicySample.get_tag


def _message_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                value = item.get("text")
                if isinstance(value, str):
                    parts.append(value)
        return "\n".join(parts)
    return ""


def _mopd_get_tag(self, tag_key: str = "dataset"):
    # Keep the normal ms-swift behavior whenever the column survived.
    value = _original_get_tag(self, tag_key)
    if value is not None or tag_key != "mopd_teacher":
        return value

    # prompt_id is a formal OnPolicySample field, so prefer it if preserved.
    prompt_id = str(getattr(self, "prompt_id", "") or "")
    if prompt_id.startswith("reasoning:"):
        return "reasoning"
    if prompt_id.startswith("generation:"):
        return "generation"

    # Final fallback: the two RL policies have exact, mutually exclusive
    # suffixes on the last user message. `messages` is a formal sample field.
    for message in reversed(getattr(self, "messages", None) or []):
        if not isinstance(message, dict) or message.get("role") != "user":
            continue
        user_text = _message_text(message.get("content", ""))
        if _REASONING_ROUTE_SUFFIX in user_text:
            return "reasoning"
        if _GENERATION_ROUTE_SUFFIX in user_text:
            return "generation"
        break

    return None


OnPolicySample.get_tag = _mopd_get_tag

_MOPD_TEACHER_TOKENIZER = None
_MOPD_TEACHER_MODEL_CACHE: dict[str, str] = {}
_MOPD_TEACHER_REQUEST_INDEX = 0


def _decode_teacher_content(content: Any) -> Any:
    global _MOPD_TEACHER_TOKENIZER
    token_ids = None
    if isinstance(content, list) and all(isinstance(value, int) for value in content):
        token_ids = content
    elif isinstance(content, dict) and isinstance(content.get("token_ids"), list):
        token_ids = content["token_ids"]
    if token_ids is None:
        return content
    if _MOPD_TEACHER_TOKENIZER is None:
        from transformers import AutoTokenizer
        _MOPD_TEACHER_TOKENIZER = AutoTokenizer.from_pretrained(
            os.environ["MOPD_STUDENT_MODEL"], trust_remote_code=True
        )
    return _MOPD_TEACHER_TOKENIZER.decode(token_ids, skip_special_tokens=False)


def _openai_teacher_messages(request: dict[str, Any]) -> list[dict[str, Any]]:
    images = iter(request.get("images") or [])
    messages: list[dict[str, Any]] = []
    for message in request.get("messages") or []:
        content = _decode_teacher_content(message.get("content", ""))
        if isinstance(content, str) and "<image>" in content:
            rich_content: list[dict[str, Any]] = []
            for index, part in enumerate(content.split("<image>")):
                if index:
                    image = Path(str(next(images))).resolve()
                    rich_content.append({"type": "image_url", "image_url": {"url": image.as_uri()}})
                if part:
                    rich_content.append({"type": "text", "text": part})
            content = rich_content
        messages.append({"role": message["role"], "content": content})
    return messages


def _swift_chat_completion_response(body: dict[str, Any]):
    from swift.infer_engine.protocol import ChatCompletionResponse, ChatCompletionResponseChoice, ChatMessage, UsageInfo
    choices = []
    for raw_choice in body.get("choices") or []:
        raw_message = dict(raw_choice.get("message") or {})
        if "reasoning_content" not in raw_message and "reasoning" in raw_message:
            raw_message["reasoning_content"] = raw_message["reasoning"]
        message = ChatMessage(**{k: v for k, v in raw_message.items() if k in ChatMessage.__dataclass_fields__})
        choice_payload = {
            k: v for k, v in raw_choice.items()
            if k in ChatCompletionResponseChoice.__dataclass_fields__ and k != "message"
        }
        choices.append(ChatCompletionResponseChoice(message=message, **choice_payload))
    usage = UsageInfo(**{
        k: v for k, v in (body.get("usage") or {}).items() if k in UsageInfo.__dataclass_fields__
    })
    response_payload = {
        k: v for k, v in body.items()
        if k in ChatCompletionResponse.__dataclass_fields__ and k not in {"choices", "usage"}
    }
    return ChatCompletionResponse(choices=choices, usage=usage, **response_payload)


def _served_model_for(base_url: str) -> str:
    base_url = base_url.rstrip("/")
    cached = _MOPD_TEACHER_MODEL_CACHE.get(base_url)
    if cached is not None:
        return cached
    with urllib.request.urlopen(base_url + "/v1/models", timeout=10) as response:
        payload = json.load(response)
    models = [str(item.get("id")) for item in payload.get("data", []) if item.get("id")]
    if len(models) != 1:
        raise RuntimeError(f"expected exactly one teacher model at {base_url}, got {models}")
    _MOPD_TEACHER_MODEL_CACHE[base_url] = models[0]
    return models[0]


def _install_openai_teacher_client() -> None:
    from swift.rlhf_trainers.vllm_client import VLLMInferClient
    if getattr(VLLMInferClient, "_mopd_openai_compatible", False):
        return

    def infer(self, infer_requests, request_config=None, metrics=None, **kwargs):
        global _MOPD_TEACHER_REQUEST_INDEX
        del metrics, kwargs
        config = (
            request_config if isinstance(request_config, dict)
            else asdict(request_config) if request_config is not None else {}
        )
        requested_topk = int(config.get("prompt_logprobs", 0))
        base_url = self.base_urls[0].rstrip("/")
        model = _served_model_for(base_url)
        results = []
        for infer_request in infer_requests:
            request_index = _MOPD_TEACHER_REQUEST_INDEX
            _MOPD_TEACHER_REQUEST_INDEX += 1
            request = asdict(infer_request) if not isinstance(infer_request, dict) else infer_request
            payload = {
                "model": model,
                "messages": _openai_teacher_messages(request),
                "temperature": float(config.get("temperature", 0.0)),
                "max_tokens": int(config.get("max_tokens", 1)),
                "prompt_logprobs": requested_topk,
                "echo": True,
                "add_generation_prompt": False,
            }
            chat_template_kwargs = request.get("chat_template_kwargs")
            if isinstance(chat_template_kwargs, dict) and chat_template_kwargs:
                payload["chat_template_kwargs"] = chat_template_kwargs
            print(
                f"[MOPD_TEACHER_REQUEST] index={request_index} model={model} "
                f"prompt_logprobs={requested_topk} images={len(request.get('images') or [])}",
                flush=True,
            )
            req = urllib.request.Request(
                base_url + "/v1/chat/completions",
                data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            try:
                with urllib.request.urlopen(
                    req, timeout=float(os.environ.get("MOPD_TEACHER_REQUEST_TIMEOUT", "600"))
                ) as response:
                    body = json.loads(response.read().decode("utf-8"))
            except urllib.error.HTTPError as error:
                detail = error.read().decode("utf-8", errors="replace")
                raise RuntimeError(
                    f"teacher API HTTP {error.code}: model={model} "
                    f"prompt_logprobs={requested_topk} detail={detail}"
                ) from error
            usage = body.get("usage") or {}
            print(
                f"[MOPD_TEACHER_RESPONSE] index={request_index} model={model} "
                f"prompt_logprobs={requested_topk} "
                f"prompt_tokens={usage.get('prompt_tokens', 'unknown')} "
                f"completion_tokens={usage.get('completion_tokens', 'unknown')}",
                flush=True,
            )
            results.append(_swift_chat_completion_response(body))
        return results

    VLLMInferClient.infer = infer
    VLLMInferClient._mopd_openai_compatible = True


_install_openai_teacher_client()

_REASONING_EVAL_SEED = int(os.environ.get("MOPD_REASONING_EVAL_SEED", "17"))
_GENERATION_EVAL_SEED = int(os.environ.get("MOPD_GENERATION_EVAL_SEED", "42"))
_REASONING_SUFFIX = "请只输出最终答案本身，不要输出分析过程或额外解释。"
_GENERATION_SUFFIX = "请在回复最后一行按“答案：具体答案”的格式给出最终答案。"


def _mopd_eval_route(row):
    reference = str(row["messages"][-1]["content"])
    task = str(row.get("task", ""))
    programmatic = _mopd_eval.programmatic_judge(reference, reference, task=task)
    return "reasoning" if programmatic is not None else "generation"


def _mopd_make_messages(row):
    route = _mopd_eval_route(row)
    suffix = _REASONING_SUFFIX if route == "reasoning" else _GENERATION_SUFFIX
    question = str(row["messages"][0]["content"]).replace("<image>", "").rstrip()
    content = [{"type": "image", "image": str(path)} for path in row["image_paths"]]
    content.append({"type": "text", "text": question + "\n" + suffix})
    return [{"role": "user", "content": content}]


def _mopd_evaluate_row(model, processor, judge_url, row, step):
    del step
    route = _mopd_eval_route(row)
    index = int(row["sample_id"].rsplit(":", 1)[1])
    route_seed = _REASONING_EVAL_SEED if route == "reasoning" else _GENERATION_EVAL_SEED
    base_seed = route_seed + index * 101
    pass_at_1_candidate = _mopd_eval._generate_candidates(
        model, processor, row, seed=base_seed, do_sample=True,
        temperature=_mopd_eval.PASS_AT_1_TEMPERATURE, num_return_sequences=1,
    )[0]
    pass_at_8_candidates = _mopd_eval._generate_candidates(
        model, processor, row, seed=base_seed + 1, do_sample=True,
        temperature=_mopd_eval.PASS_AT_8_TEMPERATURE, num_return_sequences=8,
    )
    reference = str(row["messages"][-1]["content"])
    pass_at_1_generation = _mopd_eval._judge_generation(judge_url, row, reference, pass_at_1_candidate)
    generations = [
        _mopd_eval._judge_generation(judge_url, row, reference, candidate)
        for candidate in pass_at_8_candidates
    ]
    all_generations = [pass_at_1_generation, *generations]
    model_judged_count = sum(item["judge"] == "model" for item in all_generations)
    return {
        "sample_id": row["sample_id"],
        "task": row["task"],
        "reference_answer": _mopd_eval.extract_answer(reference),
        "correct_count": sum(item["correct"] for item in generations),
        "first_correct": bool(pass_at_1_generation["correct"]),
        "pass_at_1_generation": pass_at_1_generation,
        "programmatic_count": len(all_generations) - model_judged_count,
        "model_judged_count": model_judged_count,
        "generations": generations,
        "mopd_eval_route": route,
        "mopd_eval_seed": route_seed,
    }


_mopd_eval._make_messages = _mopd_make_messages
_mopd_eval._evaluate_row = _mopd_evaluate_row

_STATE_PATTERNS = (
    "optimizer.pt", "optimizer.bin", "scheduler.pt", "scheduler.bin", "scaler.pt",
    "trainer_state.json", "training_args.bin", "rng_state*.pth",
)


def _checkpoint_step(path: Path):
    prefix = "checkpoint-"
    if not path.is_dir() or not path.name.startswith(prefix):
        return None
    suffix = path.name[len(prefix):]
    return int(suffix) if suffix.isdigit() else None


def _deepspeed_state_dirs(checkpoint: Path) -> list[Path]:
    return sorted(path for path in checkpoint.glob("global_step*") if path.is_dir())


def _remove_resume_state(checkpoint: Path) -> bool:
    import shutil
    removed = False
    if not checkpoint.is_dir():
        return False
    for pattern in _STATE_PATTERNS:
        for target in checkpoint.glob(pattern):
            if target.is_file():
                target.unlink(); removed = True
    latest = checkpoint / "latest"
    if latest.is_file():
        latest.unlink(); removed = True
    for state_dir in _deepspeed_state_dirs(checkpoint):
        shutil.rmtree(state_dir); removed = True
    return removed


def _has_complete_resume_state(checkpoint: Path) -> bool:
    if not checkpoint.is_dir():
        return False
    has_trainer_state = (checkpoint / "trainer_state.json").is_file()
    world_size = int(os.environ.get("MOPD_TRAIN_WORLD_SIZE", "2"))
    if world_size > 1:
        has_rng_state = all((checkpoint / f"rng_state_{rank}.pth").is_file() for rank in range(world_size))
    else:
        has_rng_state = any(checkpoint.glob("rng_state*.pth"))
    has_optimizer = any((checkpoint / name).is_file() for name in ("optimizer.pt", "optimizer.bin"))
    has_scheduler = any((checkpoint / name).is_file() for name in ("scheduler.pt", "scheduler.bin"))
    standard_complete = has_optimizer and has_scheduler
    deepspeed_complete = False
    for state_dir in _deepspeed_state_dirs(checkpoint):
        if any(state_dir.glob("*_optim_states.pt")) and any(state_dir.glob("*_model_states.pt")):
            deepspeed_complete = True
            break
    return has_trainer_state and has_rng_state and (standard_complete or deepspeed_complete)


def _on_save_keep_latest_state(self, args, state, control, **kwargs):
    if not getattr(state, "is_world_process_zero", True):
        return control
    current_step = int(state.global_step)
    output_dir = Path(args.output_dir)
    current_checkpoint = output_dir / f"checkpoint-{current_step}"
    if not _has_complete_resume_state(current_checkpoint):
        print(
            f"[MOPD_CHECKPOINT_STATE] current={current_checkpoint.name} "
            "state_incomplete=true keep_previous=true", flush=True,
        )
        return control
    removed_from = []
    for checkpoint in output_dir.glob("checkpoint-*"):
        step = _checkpoint_step(checkpoint)
        if step is None or step >= current_step:
            continue
        if _remove_resume_state(checkpoint):
            removed_from.append(checkpoint.name)
    print(
        f"[MOPD_CHECKPOINT_STATE] latest={current_checkpoint.name} state_verified=true "
        f"removed_previous={','.join(sorted(removed_from)) or 'none'}", flush=True,
    )
    return control


FinarPassAt8Callback.on_save = _on_save_keep_latest_state

try:
    from swift.rlhf_trainers.gkd_trainer import GKDTrainer
except ImportError:
    GKDTrainer = None

if GKDTrainer is not None and not getattr(GKDTrainer.__init__, "_mopd_rollout_compatible", False):
    _original_gkd_init = GKDTrainer.__init__
    def _mopd_gkd_init(self, *args, **kwargs):
        self.dynamic_num_samples = False
        self.rollout_pad_count = 0
        _original_gkd_init(self, *args, **kwargs)
    _mopd_gkd_init._mopd_rollout_compatible = True
    GKDTrainer.__init__ = _mopd_gkd_init
PY

# Student runtime model: preserve repository's tokenizer compatibility workaround
# without modifying the immutable base checkpoint.
RUNTIME_MODEL_DIR="$TMPDIR/student_model"
rm -rf "$RUNTIME_MODEL_DIR"
mkdir -p "$RUNTIME_MODEL_DIR"
while IFS= read -r -d '' MODEL_ENTRY; do
  MODEL_ENTRY_NAME="${MODEL_ENTRY##*/}"
  if [[ "$MODEL_ENTRY_NAME" != "tokenizer_config.json" ]]; then
    ln -sfn "$MODEL_ENTRY" "$RUNTIME_MODEL_DIR/$MODEL_ENTRY_NAME"
  fi
done < <(find "$STUDENT_MODEL" -mindepth 1 -maxdepth 1 -print0)
cp "$STUDENT_MODEL/tokenizer_config.json" "$RUNTIME_MODEL_DIR/tokenizer_config.json"
"$PYTHON_BIN" - "$RUNTIME_MODEL_DIR/tokenizer_config.json" <<'PY'
import json
import pathlib
import sys
path = pathlib.Path(sys.argv[1])
config = json.loads(path.read_text(encoding="utf-8"))
config["fix_mistral_regex"] = False
path.write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
PY

REASONING_PORT="${MOPD_REASONING_PORT:-8013}"
GENERATION_PORT="${MOPD_GENERATION_PORT:-8014}"
REASONING_URL="http://127.0.0.1:${REASONING_PORT}"
GENERATION_URL="http://127.0.0.1:${GENERATION_PORT}"
REASONING_SERVED_MODEL="mopd-reasoning-teacher"
GENERATION_SERVED_MODEL="mopd-generation-teacher"

REASONING_LOG="$OUTPUT_DIR/reasoning_teacher.log"
GENERATION_LOG="$OUTPUT_DIR/generation_teacher.log"

(
  export CUDA_VISIBLE_DEVICES=2
  export WANDB_DISABLED=true
  export WANDB_MODE=disabled
  exec "$PYTHON_BIN" -m vllm.entrypoints.openai.api_server \
    --model "$REASONING_TEACHER" \
    --served-model-name "$REASONING_SERVED_MODEL" \
    --host 127.0.0.1 \
    --port "$REASONING_PORT" \
    --dtype bfloat16 \
    --max-model-len "${MOPD_TEACHER_MAX_MODEL_LEN:-49152}" \
    --tensor-parallel-size 1 \
    --gpu-memory-utilization "${MOPD_TEACHER_GPU_MEMORY_UTILIZATION:-0.85}" \
    --max-num-seqs "${MOPD_TEACHER_MAX_NUM_SEQS:-4}" \
    --max-logprobs "${MOPD_GKD_TOPK:-128}" \
    --allowed-local-media-path "$ROOT" \
    --enforce-eager \
    --generation-config vllm
) > "$REASONING_LOG" 2>&1 &
REASONING_PID=$!

(
  export CUDA_VISIBLE_DEVICES=3
  export WANDB_DISABLED=true
  export WANDB_MODE=disabled
  exec "$PYTHON_BIN" -m vllm.entrypoints.openai.api_server \
    --model "$GENERATION_TEACHER" \
    --served-model-name "$GENERATION_SERVED_MODEL" \
    --host 127.0.0.1 \
    --port "$GENERATION_PORT" \
    --dtype bfloat16 \
    --max-model-len "${MOPD_TEACHER_MAX_MODEL_LEN:-49152}" \
    --tensor-parallel-size 1 \
    --gpu-memory-utilization "${MOPD_TEACHER_GPU_MEMORY_UTILIZATION:-0.85}" \
    --max-num-seqs "${MOPD_TEACHER_MAX_NUM_SEQS:-4}" \
    --max-logprobs "${MOPD_GKD_TOPK:-128}" \
    --allowed-local-media-path "$ROOT" \
    --enforce-eager \
    --generation-config vllm
) > "$GENERATION_LOG" 2>&1 &
GENERATION_PID=$!

cleanup() {
  kill "$GENERATION_PID" "$REASONING_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

wait_for_model() {
  local pid="$1"
  local url="$2"
  local model="$3"
  local log="$4"
  local timeout="${MOPD_TEACHER_STARTUP_TIMEOUT:-1800}"
  local deadline=$((SECONDS + timeout))
  while (( SECONDS < deadline )); do
    if ! kill -0 "$pid" 2>/dev/null; then
      echo "model server exited before healthy: model=$model log=$log" >&2
      tail -n 100 "$log" >&2 || true
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
      return 0
    fi
    sleep 2
  done
  echo "model server health timeout: model=$model log=$log" >&2
  tail -n 100 "$log" >&2 || true
  exit 1
}

wait_for_model "$REASONING_PID" "$REASONING_URL" "$REASONING_SERVED_MODEL" "$REASONING_LOG"
wait_for_model "$GENERATION_PID" "$GENERATION_URL" "$GENERATION_SERVED_MODEL" "$GENERATION_LOG"

TEACHER_SERVERS="$(printf '[{"url":"%s","tags":["reasoning"]},{"url":"%s","tags":["generation"]}]' \
  "$REASONING_URL" "$GENERATION_URL")"

# Reuse the SFT benchmark evaluator. Only samples that need model judging call this
# endpoint; they are judged by the generation expert as requested.
MOPD_INTERVAL_STEPS="${MOPD_INTERVAL_STEPS:-20}"
export SFT_BENCHMARK="$BENCHMARK"
export SFT_EVAL_STEPS="$MOPD_INTERVAL_STEPS"
export SFT_EVAL_AT_ZERO=false
export SFT_PASS_AT_8_TEMPERATURE="${MOPD_EVAL_TEMPERATURE:-1.0}"
export MOPD_REASONING_EVAL_SEED="${MOPD_REASONING_EVAL_SEED:-17}"
export MOPD_GENERATION_EVAL_SEED="${MOPD_GENERATION_EVAL_SEED:-42}"
export SFT_JUDGE_URL="$GENERATION_URL"
export GSPO_JUDGE_SERVE_NAME="$GENERATION_SERVED_MODEL"
MOPD_PER_DEVICE_BATCH="${MOPD_PER_DEVICE_BATCH:-2}"
MOPD_GRAD_ACC="${MOPD_GRAD_ACC:-4}"
MOPD_USE_LOGITS_TO_KEEP="${MOPD_USE_LOGITS_TO_KEEP:-true}"
MOPD_GENERATION_BATCH_SIZE="${MOPD_GENERATION_BATCH_SIZE:-$((NPROC_PER_NODE * MOPD_PER_DEVICE_BATCH))}"
MOPD_GLOBAL_BATCH_SIZE=$((NPROC_PER_NODE * MOPD_PER_DEVICE_BATCH * MOPD_GRAD_ACC))
if (( MOPD_GENERATION_BATCH_SIZE % 2 != 0 )); then
  echo "MOPD_GENERATION_BATCH_SIZE must be even to preserve 1:1 expert balance, got $MOPD_GENERATION_BATCH_SIZE" >&2
  exit 1
fi
export SFT_GLOBAL_BATCH_SIZE="$MOPD_GLOBAL_BATCH_SIZE"
export MOPD_TRAIN_WORLD_SIZE="$NPROC_PER_NODE"

if [[ "${MOPD_EVAL_MAX_SAMPLES:-0}" != "0" ]]; then
  export SFT_EVAL_MAX_SAMPLES="$MOPD_EVAL_MAX_SAMPLES"
fi

BALANCED_ROWS="$(wc -l < "$BALANCED_DATA" | tr -d ' ')"
PAIRS=$((BALANCED_ROWS / 2))
MOPD_GKD_TOPK_VALUE="${MOPD_GKD_TOPK:-128}"
if [[ ! "$MOPD_GKD_TOPK_VALUE" =~ ^[1-9][0-9]*$ ]]; then
  echo "MOPD_GKD_TOPK must be a positive integer, got: $MOPD_GKD_TOPK_VALUE" >&2
  exit 1
fi

echo "===== MOPD DUAL-EXPERT 4GPU CONFIG ====="
echo "root=$ROOT"
echo "output_dir=$OUTPUT_DIR run_name=$RUN_NAME resume=${RESUME_FROM_CHECKPOINT:-none}"
echo "student=$STUDENT_MODEL"
echo "reasoning_teacher=$REASONING_TEACHER gpu=2 url=$REASONING_URL"
echo "generation_teacher=$GENERATION_TEACHER gpu=3 url=$GENERATION_URL judge_url=$GENERATION_URL"
echo "reasoning_data=$REASONING_SOURCE"
echo "generation_data=$GENERATION_SOURCE"
echo "balanced_data=$BALANCED_DATA rows=$BALANCED_ROWS pairs=$PAIRS"
echo "train_gpus=0,1 per_device_batch=$MOPD_PER_DEVICE_BATCH generation_batch_size=$MOPD_GENERATION_BATCH_SIZE grad_accum=$MOPD_GRAD_ACC global_optimizer_batch=$MOPD_GLOBAL_BATCH_SIZE"
echo "image_max_token_num=$IMAGE_MAX_TOKEN_NUM epochs=${MOPD_NUM_TRAIN_EPOCHS:-2} save_total_limit=${MOPD_SAVE_TOTAL_LIMIT:-20}"
echo "train_asset_root=$GSPO_TRAIN_ASSET_ROOT bench_asset_root=$GSPO_BENCH_ASSET_ROOT"
echo "image_resolver=scripts.rl.prepare_gspo_data._resolve_training_image"
echo "routing_key=mopd_teacher routing=reasoning->reasoning_teacher,generation->generation_teacher"
echo "routing_fallback=prompt_id_then_exact_user_suffix"
echo "objective=on_policy_gkd topk=$MOPD_GKD_TOPK_VALUE lmbda=${MOPD_GKD_LMBDA:-1.0} gkd_beta=${MOPD_GKD_BETA:-0.5} sft_alpha=${MOPD_SFT_ALPHA:-0.0}"
echo "use_logits_to_keep=$MOPD_USE_LOGITS_TO_KEEP"
echo "reasoning_user_suffix=请只输出最终答案本身，不要输出分析过程或额外解释。"
echo "generation_user_suffix=请在回复最后一行按“答案：具体答案”的格式给出最终答案。"
echo "eval_steps=$SFT_EVAL_STEPS save_steps=$MOPD_INTERVAL_STEPS benchmark=$BENCHMARK reasoning_eval_seed=$MOPD_REASONING_EVAL_SEED generation_eval_seed=$MOPD_GENERATION_EVAL_SEED"
echo "wandb_mode=$WANDB_MODE wandb_project=$WANDB_PROJECT logging_steps=1"
echo "teacher_servers=$TEACHER_SERVERS"

cd "$ROOT"
ARGS=(
  rlhf
  --rlhf_type gkd
  --model "$RUNTIME_MODEL_DIR"
  --model_type qwen3_vl
  --teacher_model_server "$TEACHER_SERVERS"
  --teacher_tag_key mopd_teacher
  --gkd_logits_topk "$MOPD_GKD_TOPK_VALUE"
  --lmbda "${MOPD_GKD_LMBDA:-1.0}"
  --sft_alpha "${MOPD_SFT_ALPHA:-0.0}"
  --dataset "$BALANCED_DATA"
  --split_dataset_ratio 0
  --dataset_shuffle false
  --train_dataloader_shuffle false
  --strict false
  --lazy_tokenize true
  --tuner_type full
  --freeze_vit false
  --freeze_aligner false
  --freeze_llm false
  --torch_dtype bfloat16
  --attn_impl flash_attn
  --deepspeed zero2
  --per_device_train_batch_size "$MOPD_PER_DEVICE_BATCH"
  --gradient_accumulation_steps "$MOPD_GRAD_ACC"
  --gradient_checkpointing true
  --vit_gradient_checkpointing true
  --ddp_find_unused_parameters true
  --num_train_epochs "${MOPD_NUM_TRAIN_EPOCHS:-2}"
  --num_generations 1
  --num_iterations 1
  --steps_per_generation 1
  --generation_batch_size "$MOPD_GENERATION_BATCH_SIZE"
  --max_length "${MOPD_MAX_LENGTH:-49152}"
  --max_completion_length "${MOPD_MAX_COMPLETION_LENGTH:-2048}"
  --truncation_strategy delete
  --dynamic_sample false
  --temperature "${MOPD_TEMPERATURE:-1.0}"
  --learning_rate "${MOPD_LEARNING_RATE:-5e-6}"
  --lr_scheduler_type constant
  --beta "${MOPD_GKD_BETA:-0.5}"
  --max_grad_norm "${MOPD_MAX_GRAD_NORM:-0.5}"
  --importance_sampling_level token
  --use_logits_to_keep "$MOPD_USE_LOGITS_TO_KEEP"
  --use_vllm true
  --vllm_mode colocate
  --vllm_tensor_parallel_size 1
  --vllm_max_model_len "${MOPD_VLLM_MAX_MODEL_LEN:-49152}"
  --vllm_max_num_seqs "${MOPD_VLLM_MAX_NUM_SEQS:-2}"
  --vllm_gpu_memory_utilization "${MOPD_VLLM_GPU_MEMORY_UTILIZATION:-0.30}"
  --vllm_mm_processor_cache_gb 0
  --vllm_enforce_eager true
  --sleep_level 2
  --logging_steps 1
  --eval_strategy no
  --save_strategy steps
  --save_steps "$MOPD_INTERVAL_STEPS"
  --save_total_limit "${MOPD_SAVE_TOTAL_LIMIT:-20}"
  --save_only_model false
  --report_to wandb
  --run_name "$RUN_NAME"
  --external_plugins "$RUNTIME_PLUGIN"
  --callbacks finar_pass_at_8
  --dataset_num_proc 1
  --dataloader_num_workers 1
  --add_version false
  --output_dir "$OUTPUT_DIR"
)

if [[ -n "$RESUME_FROM_CHECKPOINT" ]]; then
  test -d "$RESUME_FROM_CHECKPOINT" || { echo "missing resume checkpoint: $RESUME_FROM_CHECKPOINT" >&2; exit 1; }
  ARGS+=(--resume_from_checkpoint "$RESUME_FROM_CHECKPOINT")
fi

"${SWIFT_CMD[@]}" "${ARGS[@]}"

echo "MOPD_OK output_dir=$OUTPUT_DIR"