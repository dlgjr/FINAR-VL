#!/usr/bin/env bash
# PASS@8 4-GPU DDP VERSION
#   CUDA_VISIBLE_DEVICES=0,1,2,3 by default
#   nproc_per_node=4
#   evaluation source order is preserved:
#     --dataset_shuffle false
#     --train_dataloader_shuffle false
#
set -euo pipefail

ROOT="/mnt/nas/duolg/qwen3vl"
PY="/opt/ac2/bin/python"
SWIFT="/opt/ac2/bin/swift"

MODEL_CKPT="${MODEL_CKPT:-$ROOT/output/sft_test_unclean/checkpoint700_failed37targeted3930_ep2_eval50_gpu23_ddp_llmonly_lr3e7_mb2_ga2_v34/checkpoint-550}"

DATASETS=(
  "$ROOT/data/train_multi/train_rl_reasoning.jsonl"
  "$ROOT/data/benchmark/test_rlvr.jsonl"
)

ORIG_PLUGIN="$ROOT/tmp/qwen3vl_targeted37similar_rank0.py"
PASS8_IMPL="$ROOT/scripts/sft/pass_at_8_eval.py"
CALLBACK_IMPL="$ROOT/scripts/sft/swift_sft_plugin_impl.py"
DUMMY_TRAIN="$ROOT/data/benchmark/hard_cot.jsonl"

EVAL_GPUS="${EVAL_GPUS:-0,1,2,3}"
PASS8_NPROC_PER_NODE="${PASS8_NPROC_PER_NODE:-4}"
EVAL_SEED="${EVAL_SEED:-17}"
SHARD_SIZE="${SHARD_SIZE:-1000}"

export CUDA_VISIBLE_DEVICES="$EVAL_GPUS"
export OMP_NUM_THREADS=1
export TOKENIZERS_PARALLELISM=false
export PYTHONUNBUFFERED=1
unset RANK LOCAL_RANK WORLD_SIZE LOCAL_WORLD_SIZE MASTER_ADDR MASTER_PORT NPROC_PER_NODE NNODES NODE_RANK

export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"
export XDG_CACHE_HOME="$ROOT/cache/xdg"
export HF_HOME="$ROOT/cache/huggingface"
export HF_DATASETS_CACHE="$ROOT/cache/huggingface/datasets"
export HUGGINGFACE_HUB_CACHE="$ROOT/cache/huggingface/hub"
export TRANSFORMERS_CACHE="$ROOT/cache/huggingface/transformers"
export MODELSCOPE_CACHE="$ROOT/cache/modelscope"
export TORCH_HOME="$ROOT/cache/torch"
export TORCH_EXTENSIONS_DIR="$ROOT/cache/torch_extensions"
export TRITON_CACHE_DIR="$ROOT/cache/triton"
export TMPDIR="$ROOT/tmp"
export TMP="$ROOT/tmp"
export TEMP="$ROOT/tmp"

export QWEN3VL_ROOT="$ROOT"
export SFT_JUDGE_URL="${SFT_JUDGE_URL:-http://127.0.0.1:1/v1/chat/completions}"

cd "$ROOT"
mkdir -p "$TMPDIR"

for p in "$PY" "$SWIFT" "$MODEL_CKPT" "$ORIG_PLUGIN" "$PASS8_IMPL" "$CALLBACK_IMPL" "$DUMMY_TRAIN"; do
  [[ -e "$p" ]] || { echo "FATAL: missing $p" >&2; exit 2; }
done
for p in "${DATASETS[@]}"; do
  [[ -f "$p" ]] || { echo "FATAL: missing dataset $p" >&2; exit 2; }
done
[[ "$SHARD_SIZE" =~ ^[1-9][0-9]*$ ]] || { echo "FATAL: SHARD_SIZE must be positive integer" >&2; exit 2; }

IFS=',' read -r -a _PASS8_GPU_IDS <<< "$EVAL_GPUS"
[[ "${#_PASS8_GPU_IDS[@]}" -eq 4 ]] || {
  echo "FATAL: EVAL_GPUS must contain exactly 4 physical GPU ids, got: $EVAL_GPUS" >&2
  exit 2
}
[[ "$PASS8_NPROC_PER_NODE" == "4" ]] || {
  echo "FATAL: PASS8_NPROC_PER_NODE must be 4, got: $PASS8_NPROC_PER_NODE" >&2
  exit 2
}

echo "[GPU] CUDA_VISIBLE_DEVICES=$CUDA_VISIBLE_DEVICES"
echo "[GPU] nproc_per_node=$PASS8_NPROC_PER_NODE"

# Verify the 4 selected GPUs are actually visible to this process.
"$PY" - <<'PY_GPU_PREFLIGHT'
import os
import torch
n = torch.cuda.device_count()
print(f"[GPU-PREFLIGHT] CUDA_VISIBLE_DEVICES={os.environ.get('CUDA_VISIBLE_DEVICES')} device_count={n}")
if n != 4:
    raise SystemExit(f"FATAL: expected exactly 4 visible CUDA devices, got {n}")
PY_GPU_PREFLIGHT

WRAPPER="$ROOT/tmp/pass8_rl_eval_only_wrapper_v1.py"
cat > "$WRAPPER" <<'PY_WRAPPER'
import importlib.util
import inspect
import os
import pathlib
import random
import sys

seed = int(os.environ.get("PASS8_RUN_SEED", "17"))
os.environ["PYTHONHASHSEED"] = str(seed)
for k in ("SFT_SEED","SFT_EVAL_SEED","PASS_AT_8_SEED","PASS8_SEED","EVAL_SEED","SWIFT_SEED"):
    os.environ[k] = str(seed)

random.seed(seed)
try:
    import numpy as np
    np.random.seed(seed)
except Exception:
    pass
try:
    import torch
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
except Exception:
    pass

orig = pathlib.Path(os.environ["SFT_ORIGINAL_PLUGIN"]).resolve()
spec = importlib.util.spec_from_file_location("_pass8_rl_orig_plugin_v1", orig)
if spec is None or spec.loader is None:
    raise RuntimeError(f"cannot load original plugin: {orig}")
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)

from scripts.sft import swift_sft_plugin_impl as impl
from scripts.sft import pass_at_8_eval as eval_mod

for module in (eval_mod, impl):
    for attr, value in list(vars(module).items()):
        if "SEED" in attr.upper() and isinstance(value, int) and not isinstance(value, bool):
            setattr(module, attr, seed)

candidates = []
for cls_name, obj in vars(impl).items():
    if inspect.isclass(obj) and hasattr(obj, "_run") and callable(getattr(obj, "_run")) and hasattr(obj, "on_train_begin") and callable(getattr(obj, "on_train_begin")):
        candidates.append((cls_name, obj))

if len(candidates) != 1:
    raise RuntimeError(f"expected exactly one FINAR callback, found={[x[0] for x in candidates]}")

cls_name, cls = candidates[0]
orig_on_train_begin = cls.on_train_begin

def _eval_only_on_train_begin(self, args, state, control, **kwargs):
    print(f"[PASS8-EVAL-ONLY] begin seed={seed} benchmark={os.environ.get('SFT_BENCHMARK')}", flush=True)
    result = orig_on_train_begin(self, args, state, control, **kwargs)
    print("[PASS8-EVAL-ONLY] done; exiting before first training step", flush=True)
    raise SystemExit(0)

cls.on_train_begin = _eval_only_on_train_begin
print(f"[PASS8-EVAL-ONLY] wrapper ready callback={cls_name} seed={seed}", flush=True)
PY_WRAPPER

"$PY" -m py_compile "$WRAPPER"
echo "[PREFLIGHT] wrapper syntax=OK"

"$PY" - "$PASS8_IMPL" <<'PY_IMPORT'
import importlib.util, pathlib, sys
p = pathlib.Path(sys.argv[1]).resolve()
spec = importlib.util.spec_from_file_location("_pass8_rl_preflight", p)
if spec is None or spec.loader is None:
    raise SystemExit(f"FATAL cannot import {p}")
m = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = m
spec.loader.exec_module(m)
print(f"[PREFLIGHT] pass_at_8_eval import=OK: {p}")
PY_IMPORT

find_free_port () {
  "$PY" - <<'PY_FREE_PORT'
import socket
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind(("", 0))
    print(s.getsockname()[1])
PY_FREE_PORT
}

process_dataset () {
  local SRC="$1"
  local DIR STEM WORK NORMALIZED MANIFEST FINAL_JSONL FINAL_CSV SUMMARY_JSON META_JSON
  DIR="$(dirname "$SRC")"
  STEM="$(basename "$SRC" .jsonl)"
  WORK="$DIR/${STEM}_pass8_work"
  NORMALIZED="$WORK/${STEM}_normalized.jsonl"
  MANIFEST="$DIR/${STEM}_pass8_source_manifest.jsonl"
  FINAL_JSONL="$DIR/${STEM}_pass8_predictions.jsonl"
  FINAL_CSV="$DIR/${STEM}_pass8_per_sample.csv"
  SUMMARY_JSON="$DIR/${STEM}_pass8_summary.json"
  META_JSON="$DIR/${STEM}_pass8_run_meta.json"

  mkdir -p "$WORK/shards"

  echo
  echo "======================================================================"
  echo "[DATASET] $SRC"
  echo "[OUTPUT]  $DIR/${STEM}_pass8_*"
  echo "======================================================================"

  "$PY" - "$SRC" "$NORMALIZED" "$MANIFEST" "$ROOT" <<'PY_NORMALIZE'
import json, pathlib, sys
from collections import Counter

src = pathlib.Path(sys.argv[1]).resolve()
out = pathlib.Path(sys.argv[2]).resolve()
manifest = pathlib.Path(sys.argv[3]).resolve()
root = pathlib.Path(sys.argv[4]).resolve()
source_dir = src.parent
stem = src.stem

MEDIA_KEYS = {"image","images","image_path","image_paths","video","videos","audio","audios"}
IMG_EXTS = {".png",".jpg",".jpeg",".webp",".bmp",".gif",".tif",".tiff"}

def text_content(x):
    if isinstance(x, str):
        return x
    if isinstance(x, list):
        z=[]
        for y in x:
            if isinstance(y,str):
                z.append(y)
            elif isinstance(y,dict) and isinstance(y.get("text"),str):
                z.append(y["text"])
        return "\n".join(z)
    return ""

def question(row):
    for k in ("question","query","prompt","instruction","problem"):
        v=row.get(k)
        if isinstance(v,str) and v.strip():
            return v.strip()
    for m in reversed(row.get("messages") or []):
        if isinstance(m,dict) and m.get("role") in ("user","human"):
            t=text_content(m.get("content"))
            if t.strip():
                return t.strip()
    return ""

ANSWER_KEYS = (
    "reference_answer","answer","final_answer","correct_answer","gold_answer",
    "ground_truth","groundtruth","gt_answer","gold","target","label",
    "solution","expected_answer","reference","response","result",
)

def _scalar(v):
    if isinstance(v,(str,int,float)) and not isinstance(v,bool):
        t=str(v).strip()
        return t if t else ""
    return ""

def answer(row):
    # 1) The schema you showed:
    #    messages=[user ..., assistant "B"].
    for m in reversed(row.get("messages") or []):
        if isinstance(m,dict) and m.get("role") in ("assistant","gpt"):
            t=text_content(m.get("content"))
            if t.strip():
                return t.strip()

    # 2) Common flat answer fields.
    for k in ANSWER_KEYS:
        if k in row:
            t=_scalar(row.get(k))
            if t:
                return t

    # 3) Common RL/RLVR nested containers.
    for ck in (
        "reward_model","reward","metadata","meta","extra_info",
        "evaluation","eval","annotation","annotations","data",
    ):
        obj=row.get(ck)
        if isinstance(obj,dict):
            for k in ANSWER_KEYS:
                if k in obj:
                    t=_scalar(obj.get(k))
                    if t:
                        return t

    # 4) Recursive search for an explicitly answer-like key anywhere.
    def walk(obj):
        if isinstance(obj,dict):
            for k in ANSWER_KEYS:
                if k in obj:
                    t=_scalar(obj.get(k))
                    if t:
                        return t
            for v in obj.values():
                t=walk(v)
                if t:
                    return t
        elif isinstance(obj,list):
            for v in obj:
                t=walk(v)
                if t:
                    return t
        return ""

    return walk(row)

def category(row):
    for k in ("review_category","category","question_category","question_type","type","task_type","rlvr_type","subtype","data_type"):
        v=row.get(k)
        if isinstance(v,str) and v.strip():
            return v.strip()
    v=row.get("task")
    return str(v) if v is not None else "unknown"

def resolve(v):
    if not isinstance(v,str) or not v.strip():
        return v
    v=v.strip()
    if "://" in v or v.startswith("data:"):
        return v
    p=pathlib.Path(v)
    if p.is_absolute():
        return str(p)
    candidates=[
        (source_dir/p).resolve(),
        (root/"data/benchmark"/p).resolve(),
        (root/p).resolve(),
    ]
    for c in candidates:
        if c.exists():
            return str(c)
    return str(candidates[0])

def norm(obj):
    if isinstance(obj,dict):
        z={}
        for k,v in obj.items():
            kl=str(k).lower()
            if kl in MEDIA_KEYS:
                z[k]=[resolve(x) for x in v] if isinstance(v,list) else resolve(v)
            elif kl in ("path","url") and isinstance(v,str) and "://" not in v and pathlib.Path(v).suffix.lower() in IMG_EXTS:
                z[k]=resolve(v)
            else:
                z[k]=norm(v)
        return z
    if isinstance(obj,list):
        return [norm(x) for x in obj]
    return obj

def collect_images(obj):
    vals=[]
    if isinstance(obj,dict):
        for k,v in obj.items():
            kl=str(k).lower()
            if kl in ("image","images","image_path","image_paths"):
                seq=v if isinstance(v,list) else [v]
                vals += [x for x in seq if isinstance(x,str) and "://" not in x and not x.startswith("data:")]
            elif kl in ("path","url") and isinstance(v,str) and "://" not in v and pathlib.Path(v).suffix.lower() in IMG_EXTS:
                vals.append(v)
            vals += collect_images(v)
    elif isinstance(obj,list):
        for x in obj:
            vals += collect_images(x)
    return vals

rows=[]
with src.open(encoding="utf-8") as f:
    for line_no,line in enumerate(f,1):
        if not line.strip():
            continue
        obj=json.loads(line)
        if not isinstance(obj,dict):
            raise SystemExit(f"FATAL non-object row line={line_no}")
        rows.append((line_no,obj))

normalized=[]
manifest_rows=[]
cats=Counter()
images=[]

for idx,(line_no,raw) in enumerate(rows):
    row=norm(raw)
    q=question(row)
    a=answer(row)
    if not q:
        raise SystemExit(f"FATAL no question source_index={idx} line={line_no}")
    has_reference=bool(a)
    original_id=row.get("sample_id", row.get("id"))
    sid=f"{stem}:{idx:08d}"
    cat=category(row)

    row["_pass8_original_sample_id"]=None if original_id is None else str(original_id)
    row["_pass8_source_index"]=idx
    row["_pass8_source_line"]=line_no
    row["_pass8_source_file"]=str(src)
    row["_pass8_category"]=cat
    row["sample_id"]=sid
    row["id"]=sid
    row.setdefault("question",q)
    row.setdefault("query",q)
    row.setdefault("prompt",q)
    if has_reference:
        row.setdefault("reference_answer",a)
        row.setdefault("answer",a)
    row["_pass8_has_reference"]=has_reference

    row_imgs=[]
    for x in collect_images(row):
        if x not in row_imgs:
            row_imgs.append(x)
        if x not in images:
            images.append(x)
    if row_imgs and not row.get("images"):
        row["images"]=row_imgs

    normalized.append(row)
    cats[cat]+=1
    manifest_rows.append({
        "sample_id":sid,
        "source_index":idx,
        "source_line":line_no,
        "source_file":str(src),
        "original_sample_id":None if original_id is None else str(original_id),
        "category":cat,
        "task":row.get("task"),
        "question":q,
        "reference_answer":a if has_reference else None,
        "has_reference":has_reference,
        "directly_verifiable":row.get("directly_verifiable"),
        "review_category":row.get("review_category"),
        "review_reason":row.get("review_reason"),
        "images":row_imgs,
        "top_level_keys":sorted(row.keys()),
    })

missing=[x for x in images if not pathlib.Path(x).is_file()]
if missing:
    print(f"FATAL missing local images={len(missing)}", file=sys.stderr)
    for x in missing[:50]:
        print("  MISSING",x,file=sys.stderr)
    raise SystemExit(2)

out.parent.mkdir(parents=True,exist_ok=True)
with out.open("w",encoding="utf-8") as f:
    for r in normalized:
        f.write(json.dumps(r,ensure_ascii=False)+"\n")
with manifest.open("w",encoding="utf-8") as f:
    for r in manifest_rows:
        f.write(json.dumps(r,ensure_ascii=False)+"\n")

ref_n=sum(1 for r in manifest_rows if r.get("has_reference"))
no_ref=[r for r in manifest_rows if not r.get("has_reference")]
print(f"[NORMALIZE] rows={len(normalized)} reference_available={ref_n} unjudgeable_no_reference={len(no_ref)} unique_images={len(images)} missing=0")
if no_ref:
    print("[NORMALIZE] first unresolved reference schemas:")
    for r in no_ref[:5]:
        print(f"  source_index={r['source_index']} line={r['source_line']} keys={r['top_level_keys']}")
print("[NORMALIZE] category distribution:")
for k,v in cats.most_common():
    print(f"  {k}: {v}")
PY_NORMALIZE

  local TOTAL NSHARDS
  TOTAL="$("$PY" - "$NORMALIZED" <<'PY_COUNT'
import json,pathlib,sys
n=0
for x in pathlib.Path(sys.argv[1]).open(encoding="utf-8"):
    if x.strip() and json.loads(x).get("_pass8_has_reference"):
        n+=1
print(n)
PY_COUNT
)"
  NSHARDS=$(( (TOTAL + SHARD_SIZE - 1) / SHARD_SIZE ))
  echo "[DATASET] judgeable_total=$TOTAL shard_size=$SHARD_SIZE nshards=$NSHARDS"

  "$PY" - "$NORMALIZED" "$WORK/shards" "$SHARD_SIZE" "$WORK/unjudgeable_no_reference.jsonl" <<'PY_SHARD'
import json,pathlib,sys
src=pathlib.Path(sys.argv[1]); out=pathlib.Path(sys.argv[2]); size=int(sys.argv[3]); unresolved=pathlib.Path(sys.argv[4])
out.mkdir(parents=True,exist_ok=True)
judgeable=[]
unjudgeable=[]
for line in src.open(encoding="utf-8"):
    if not line.strip():
        continue
    row=json.loads(line)
    if row.get("_pass8_has_reference"):
        judgeable.append(json.dumps(row,ensure_ascii=False)+"\n")
    else:
        unjudgeable.append(json.dumps(row,ensure_ascii=False)+"\n")

# Remove stale shards first so resume cannot mix old schema with new schema.
for p in out.glob("shard-*.jsonl"):
    p.unlink()

for i,start in enumerate(range(0,len(judgeable),size)):
    (out/f"shard-{i:05d}.jsonl").write_text("".join(judgeable[start:start+size]),encoding="utf-8")
unresolved.write_text("".join(unjudgeable),encoding="utf-8")

print(f"[SHARD] judgeable={len(judgeable)} unjudgeable={len(unjudgeable)} wrote={(len(judgeable)+size-1)//size}")
PY_SHARD

  local I
  for (( I=0; I<NSHARDS; I++ )); do
    local SHARD EOUT PRED LOG EXPECTED
    printf -v SHARD "%s/shards/shard-%05d.jsonl" "$WORK" "$I"
    printf -v EOUT "%s/eval-shard-%05d" "$WORK" "$I"
    PRED="$EOUT/eval/step-000000/predictions.jsonl"
    LOG="$EOUT/pass8.log"
    EXPECTED="$("$PY" - "$SHARD" <<'PY_SC'
import pathlib,sys
print(sum(1 for x in pathlib.Path(sys.argv[1]).open(encoding="utf-8") if x.strip()))
PY_SC
)"

    if "$PY" - "$PRED" "$EXPECTED" <<'PY_CHECK' >/dev/null 2>&1
import json,pathlib,sys
p=pathlib.Path(sys.argv[1]); n=int(sys.argv[2])
if not p.is_file(): raise SystemExit(2)
rows=[json.loads(x) for x in p.open(encoding="utf-8") if x.strip()]
if len(rows)!=n: raise SystemExit(3)
ids=[str(r.get("sample_id","")) for r in rows]
if len(set(ids))!=n or any(not x for x in ids): raise SystemExit(4)
if any("correct_count" not in r for r in rows): raise SystemExit(5)
PY_CHECK
    then
      echo "[SKIP] $STEM shard=$I rows=$EXPECTED"
      continue
    fi

    rm -rf "$EOUT"
    mkdir -p "$EOUT"
    export SFT_BENCHMARK="$SHARD"
    export SFT_ORIGINAL_PLUGIN="$ORIG_PLUGIN"
    export PASS8_RUN_SEED="$EVAL_SEED"

    echo "----------------------------------------------------------------------"
    echo "[EVAL] $STEM shard=$I/$((NSHARDS-1)) rows=$EXPECTED"
    echo "----------------------------------------------------------------------"

    MASTER_PORT="$(find_free_port)"
    echo "[DDP] nproc_per_node=$PASS8_NPROC_PER_NODE master_port=$MASTER_PORT"

    "$PY" -m torch.distributed.run \
      --nproc_per_node="$PASS8_NPROC_PER_NODE" \
      --master_port="$MASTER_PORT" \
      "$SWIFT" sft \
      --model "$MODEL_CKPT" \
      --load_args false \
      --model_type qwen3_vl \
      --dataset "$DUMMY_TRAIN" \
      --split_dataset_ratio 0 \
      --dataset_shuffle false \
      --train_dataloader_shuffle false \
      --strict false \
      --lazy_tokenize true \
      --dataset_num_proc 1 \
      --dataloader_num_workers 0 \
      --dataloader_pin_memory false \
      --tuner_type full \
      --freeze_llm false \
      --freeze_vit true \
      --freeze_aligner true \
      --torch_dtype bfloat16 \
      --attn_impl sdpa \
      --num_train_epochs 1 \
      --per_device_train_batch_size 1 \
      --gradient_accumulation_steps 1 \
      --gradient_checkpointing true \
      --ddp_find_unused_parameters false \
      --max_length 4096 \
      --truncation_strategy delete \
      --learning_rate 1e-7 \
      --logging_steps 1 \
      --eval_strategy no \
      --save_strategy no \
      --report_to none \
      --seed "$EVAL_SEED" \
      --external_plugins "$WRAPPER" \
      --callbacks finar_pass_at_8 \
      --add_version false \
      --output_dir "$EOUT" \
      2>&1 | tee "$LOG"

    "$PY" - "$PRED" "$EXPECTED" <<'PY_VALIDATE'
import json,pathlib,sys
p=pathlib.Path(sys.argv[1]); n=int(sys.argv[2])
if not p.is_file(): raise SystemExit(f"FATAL missing predictions {p}")
rows=[json.loads(x) for x in p.open(encoding="utf-8") if x.strip()]
if len(rows)!=n: raise SystemExit(f"FATAL rows={len(rows)} expected={n}")
ids=[str(r.get("sample_id","")) for r in rows]
if len(set(ids))!=n or any(not x for x in ids): raise SystemExit("FATAL bad sample_id")
if any("correct_count" not in r for r in rows): raise SystemExit("FATAL missing correct_count")
print(f"[VALIDATE] shard OK rows={n}")
PY_VALIDATE
  done

  "$PY" - "$SRC" "$MANIFEST" "$WORK" "$NSHARDS" "$FINAL_JSONL" "$FINAL_CSV" "$SUMMARY_JSON" "$META_JSON" "$MODEL_CKPT" "$EVAL_SEED" "$SHARD_SIZE" "$PASS8_IMPL" <<'PY_ASSEMBLE'
import csv,datetime as dt,json,pathlib,sys
from collections import Counter,defaultdict

src=pathlib.Path(sys.argv[1]).resolve()
manifest_path=pathlib.Path(sys.argv[2]).resolve()
work=pathlib.Path(sys.argv[3]).resolve()
nshards=int(sys.argv[4])
final_jsonl=pathlib.Path(sys.argv[5]).resolve()
final_csv=pathlib.Path(sys.argv[6]).resolve()
summary_json=pathlib.Path(sys.argv[7]).resolve()
meta_json=pathlib.Path(sys.argv[8]).resolve()
model=sys.argv[9]; seed=int(sys.argv[10]); shard_size=int(sys.argv[11]); evaluator=sys.argv[12]

def read_jsonl(p):
    return [json.loads(x) for x in p.open(encoding="utf-8") if x.strip()]

manifest_rows=read_jsonl(manifest_path)
manifest={str(r["sample_id"]):r for r in manifest_rows}
if len(manifest)!=len(manifest_rows): raise SystemExit("FATAL duplicate manifest ids")

pred={}
raw_files=[]
for i in range(nshards):
    p=work/f"eval-shard-{i:05d}"/"eval"/"step-000000"/"predictions.jsonl"
    if not p.is_file(): raise SystemExit(f"FATAL missing {p}")
    raw_files.append(str(p))
    for r in read_jsonl(p):
        sid=str(r.get("sample_id",""))
        if not sid or sid in pred: raise SystemExit(f"FATAL bad/duplicate sid {sid}")
        pred[sid]=r

missing=set(manifest)-set(pred); extra=set(pred)-set(manifest)
if extra:
    raise SystemExit(f"FATAL extra prediction ids={list(extra)[:5]}")
bad_missing=[sid for sid in missing if manifest[sid].get("has_reference")]
if bad_missing:
    raise SystemExit(f"FATAL missing judgeable prediction ids={bad_missing[:5]}")

def bucket(cc):
    if cc<=0: return "pass0_all_wrong"
    if cc<=6: return "pass1_6_rl_priority"
    if cc==7: return "pass7_near_solved"
    return "pass8_solved"

records=[]
catstats=defaultdict(lambda:{"samples":0,"pass8_hits":0,"sum_correct_count":0,"programmatic_count":0,"model_judged_count":0})
buckets=Counter()

for sid,m in sorted(manifest.items(),key=lambda kv:int(kv[1]["source_index"])):
    p=pred.get(sid)
    if p is None:
        cc=None
        gens=[]
        prog=0
        judged=0
        cat=str(m.get("category") or m.get("task") or "unknown")
        b="unjudgeable_no_reference"
        buckets[b]+=1
    else:
        cc=int(p.get("correct_count",0) or 0)
        gens=p.get("generations") if isinstance(p.get("generations"),list) else []
        prog=int(p.get("programmatic_count",0) or 0)
        judged=int(p.get("model_judged_count",0) or 0)
        cat=str(m.get("category") or p.get("task") or "unknown")
        b=bucket(cc)
        buckets[b]+=1
    rec={
        "sample_id":sid,
        "source_index":int(m["source_index"]),
        "source_line":int(m["source_line"]),
        "source_file":m["source_file"],
        "original_sample_id":m.get("original_sample_id"),
        "category":cat,
        "task":p.get("task",m.get("task")) if p else m.get("task"),
        "question":m.get("question"),
        "reference_answer":p.get("reference_answer",m.get("reference_answer")) if p else m.get("reference_answer"),
        "directly_verifiable":m.get("directly_verifiable"),
        "review_category":m.get("review_category"),
        "review_reason":m.get("review_reason"),
        "images":m.get("images",[]),
        "correct_count":cc,
        "num_generations":len(gens),
        "pass_at_8":None if cc is None else bool(cc>0),
        "success_fraction":None if cc is None else cc/8.0,
        "difficulty_bucket":b,
        "programmatic_count":prog,
        "model_judged_count":judged,
        "generations":gens,
    }
    records.append(rec)
    s=catstats[cat]
    s["samples"]+=1
    if cc is None:
        s["unjudgeable_no_reference"]=s.get("unjudgeable_no_reference",0)+1
    else:
        s["judgeable_samples"]=s.get("judgeable_samples",0)+1
        s["pass8_hits"]+=int(cc>0)
        s["sum_correct_count"]+=cc
    s["programmatic_count"]+=prog
    s["model_judged_count"]+=judged

with final_jsonl.open("w",encoding="utf-8") as f:
    for r in records: f.write(json.dumps(r,ensure_ascii=False)+"\n")

fields=["source_index","source_line","sample_id","original_sample_id","category","review_category","directly_verifiable","task","reference_answer","correct_count","num_generations","pass_at_8","success_fraction","difficulty_bucket","programmatic_count","model_judged_count","question","review_reason"]
with final_csv.open("w",encoding="utf-8",newline="") as f:
    w=csv.DictWriter(f,fieldnames=fields); w.writeheader()
    for r in records: w.writerow({k:r.get(k) for k in fields})

n=len(records)
judgeable=[r for r in records if r["correct_count"] is not None]
jn=len(judgeable)
hits=sum(int(r["pass_at_8"]) for r in judgeable)
sumcc=sum(r["correct_count"] for r in judgeable)
cats={}
for k,s in sorted(catstats.items(),key=lambda kv:(-kv[1]["samples"],kv[0])):
    j=int(s.get("judgeable_samples",0))
    cats[k]={**s,
        "judgeable_samples":j,
        "unjudgeable_no_reference":int(s.get("unjudgeable_no_reference",0)),
        "pass8_rate":s["pass8_hits"]/j if j else None,
        "mean_correct_count":s["sum_correct_count"]/j if j else None,
        "mean_success_fraction":s["sum_correct_count"]/(8*j) if j else None}

summary={
    "source_file":str(src),
    "model_checkpoint":model,
    "eval_seed":seed,
    "num_samples":n,
    "expected_generations":n*8,
    "pass8_hits":hits,
    "judgeable_samples":jn,
    "unjudgeable_no_reference":n-jn,
    "pass8_rate":hits/jn if jn else None,
    "mean_correct_count":sumcc/jn if jn else None,
    "mean_success_fraction":sumcc/(8*jn) if jn else None,
    "difficulty_bucket_counts":dict(buckets),
    "rl_priority_1_to_6_count":buckets["pass1_6_rl_priority"],
    "categories":cats,
}
summary_json.write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding="utf-8")

meta={
    "created_at":dt.datetime.now().astimezone().isoformat(),
    "source_file":str(src),
    "source_manifest":str(manifest_path),
    "model_checkpoint":model,
    "evaluator":evaluator,
    "eval_seed":seed,
    "pass_k":8,
    "shard_size":shard_size,
    "num_shards":nshards,
    "num_samples":n,
    "raw_shard_prediction_files":raw_files,
    "final_predictions":str(final_jsonl),
    "per_sample_csv":str(final_csv),
    "summary_json":str(summary_json),
    "traceability":"source_index/source_line locate original JSONL row; canonical sample_id is stable for this source file.",
}
meta_json.write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding="utf-8")

print("======================================================================")
print(f"[DONE] {src.name}: total={n} judgeable={jn} unjudgeable={n-jn}")
print(f"[DONE] pass8={hits}/{jn}={(hits/jn if jn else float('nan')):.6f}")
print(f"[DONE] mean_correct_count={(sumcc/jn if jn else float('nan')):.4f}/8")
print(f"[DONE] rl_priority_1_6={buckets['pass1_6_rl_priority']}")
print(f"[DONE] predictions={final_jsonl}")
print(f"[DONE] csv={final_csv}")
print(f"[DONE] summary={summary_json}")
print(f"[DONE] meta={meta_json}")
print("[DONE] categories:")
for k,s in cats.items():
    rate=s["pass8_rate"]
    meancc=s["mean_correct_count"]
    print(
        f"  {k}: total={s['samples']} judgeable={s['judgeable_samples']} "
        f"unjudgeable={s['unjudgeable_no_reference']} "
        f"pass8={s['pass8_hits']}/{s['judgeable_samples']}="
        f"{(rate if rate is not None else float('nan')):.4f} "
        f"mean_cc={(meancc if meancc is not None else float('nan')):.3f}/8"
    )
print("======================================================================")
PY_ASSEMBLE
}

for ds in "${DATASETS[@]}"; do
  process_dataset "$ds"
done

echo
echo "ALL PASS@8 DATASET SAMPLING DONE"
