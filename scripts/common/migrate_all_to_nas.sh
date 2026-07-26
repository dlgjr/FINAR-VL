#!/usr/bin/env bash
set -euo pipefail

BASE=/mnt/nas/bihaoran/qwen3vl

mkdir -p \
  "$BASE/cache/root" \
  "$BASE/cache/root-local" \
  "$BASE/cache/root-conda" \
  "$BASE/cache/ppu-rtccache" \
  "$BASE/cache/huggingface/datasets" \
  "$BASE/cache/huggingface/hub" \
  "$BASE/cache/modelscope" \
  "$BASE/cache/xdg" \
  "$BASE/cache/torch" \
  "$BASE/cache/torch-extensions" \
  "$BASE/cache/triton" \
  "$BASE/cache/cuda" \
  "$BASE/cache/pip" \
  "$BASE/cache/pycache" \
  "$BASE/cache/conda/pkgs" \
  "$BASE/cache/matplotlib" \
  "$BASE/tmp" \
  "$BASE/logs" \
  "$BASE/output" \
  "$BASE/workspace"

chmod 1777 "$BASE/tmp"

move_and_link() {
  src="$1"
  dst="$2"

  if [ -L "$src" ]; then
    echo "已是软链接，跳过: $src"
    return
  fi

  mkdir -p "$dst"

  if [ -d "$src" ]; then
    echo "迁移: $src -> $dst"
    cp -a "$src"/. "$dst"/
    rm -rf "$src"
  elif [ -e "$src" ]; then
    echo "不处理非目录: $src"
    return
  fi

  mkdir -p "$(dirname "$src")"
  ln -s "$dst" "$src"
}

move_and_link /root/.cache "$BASE/cache/root"
move_and_link /root/.local "$BASE/cache/root-local"
move_and_link /root/.conda "$BASE/cache/root-conda"

if [ -d /root/.triton ]; then
  move_and_link /root/.triton "$BASE/cache/triton"
fi

if [ -d /root/.nv ]; then
  move_and_link /root/.nv "$BASE/cache/cuda"
fi

if [ -d /usr/local/PPU_SDK/rtccache ]; then
  move_and_link \
    /usr/local/PPU_SDK/rtccache \
    "$BASE/cache/ppu-rtccache"
fi

# /workspace 不是挂载点时才迁移
if [ -d /workspace ] && ! mountpoint -q /workspace; then
  move_and_link /workspace "$BASE/workspace"
fi

cat > "$BASE/env.sh" <<'ENV'
export PROJECT_ROOT=/mnt/nas/bihaoran/qwen3vl

export HF_HOME=$PROJECT_ROOT/cache/huggingface
export HF_DATASETS_CACHE=$PROJECT_ROOT/cache/huggingface/datasets
export HUGGINGFACE_HUB_CACHE=$PROJECT_ROOT/cache/huggingface/hub
export HF_MODULES_CACHE=$PROJECT_ROOT/cache/huggingface/modules

export MODELSCOPE_CACHE=$PROJECT_ROOT/models
export XDG_CACHE_HOME=$PROJECT_ROOT/cache/xdg
export TORCH_HOME=$PROJECT_ROOT/cache/torch
export TORCH_EXTENSIONS_DIR=$PROJECT_ROOT/cache/torch-extensions
export TRITON_CACHE_DIR=$PROJECT_ROOT/cache/triton
export CUDA_CACHE_PATH=$PROJECT_ROOT/cache/cuda

export PIP_CACHE_DIR=$PROJECT_ROOT/cache/pip
export PYTHONPYCACHEPREFIX=$PROJECT_ROOT/cache/pycache
export CONDA_PKGS_DIRS=$PROJECT_ROOT/cache/conda/pkgs
export MPLCONFIGDIR=$PROJECT_ROOT/cache/matplotlib

export TMPDIR=$PROJECT_ROOT/tmp
export TMP=$TMPDIR
export TEMP=$TMPDIR

export WANDB_DIR=$PROJECT_ROOT/logs/wandb

mkdir -p \
  "$HF_DATASETS_CACHE" \
  "$HUGGINGFACE_HUB_CACHE" \
  "$HF_MODULES_CACHE" \
  "$MODELSCOPE_CACHE" \
  "$TORCH_EXTENSIONS_DIR" \
  "$TRITON_CACHE_DIR" \
  "$CUDA_CACHE_PATH" \
  "$PIP_CACHE_DIR" \
  "$PYTHONPYCACHEPREFIX" \
  "$CONDA_PKGS_DIRS" \
  "$MPLCONFIGDIR" \
  "$TMPDIR" \
  "$WANDB_DIR"

cd "$PROJECT_ROOT"
ENV

SOURCE_LINE='source /mnt/nas/bihaoran/qwen3vl/env.sh'

if ! grep -Fqx "$SOURCE_LINE" /root/.bashrc 2>/dev/null; then
  echo "$SOURCE_LINE" >> /root/.bashrc
fi

echo
echo "迁移完成"
echo "执行：source $BASE/env.sh"
