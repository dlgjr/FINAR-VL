export PROJECT_ROOT=/mnt/nas/bihaoran/qwen3vl

export HF_HOME=$PROJECT_ROOT/cache/huggingface
export HF_DATASETS_CACHE=$PROJECT_ROOT/cache/huggingface/datasets
export HUGGINGFACE_HUB_CACHE=$PROJECT_ROOT/cache/huggingface/hub

export MODELSCOPE_CACHE=$PROJECT_ROOT/models
export TORCH_HOME=$PROJECT_ROOT/cache/torch
export TORCH_EXTENSIONS_DIR=$PROJECT_ROOT/cache/torch-extensions
export PIP_CACHE_DIR=$PROJECT_ROOT/cache/pip
export PYTHONPYCACHEPREFIX=$PROJECT_ROOT/cache/pycache

export TMPDIR=$PROJECT_ROOT/tmp
export TMP=$PROJECT_ROOT/tmp
export TEMP=$PROJECT_ROOT/tmp

export WANDB_DIR=$PROJECT_ROOT/logs/wandb

mkdir -p \
  "$HF_DATASETS_CACHE" \
  "$HUGGINGFACE_HUB_CACHE" \
  "$MODELSCOPE_CACHE" \
  "$TORCH_HOME" \
  "$TORCH_EXTENSIONS_DIR" \
  "$PIP_CACHE_DIR" \
  "$PYTHONPYCACHEPREFIX" \
  "$TMPDIR" \
  "$WANDB_DIR"

cd "$PROJECT_ROOT"
