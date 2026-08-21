#!/usr/bin/env bash
set -euo pipefail

ROOT="${QWEN3VL_ROOT:-/mnt/nas/bihaoran/qwen3vl}"
PYTHON_BIN="${PYTHON_BIN:-/opt/ac2/bin/python}"

SOURCE_BENCHMARK="${SFT_SOURCE_BENCHMARK:-$ROOT/data/benchmark/my_benchmark/all.jsonl}"
DERIVED_BENCHMARK="${SFT_REASONING_BENCHMARK:-$ROOT/data/benchmark/my_benchmark/all_reasoning_v2.jsonl}"

"$PYTHON_BIN" "$ROOT/scripts/data/build_reasoning_benchmark.py" \
  --input "$SOURCE_BENCHMARK" \
  --output "$DERIVED_BENCHMARK"

export SFT_BENCHMARK="$DERIVED_BENCHMARK"

# Keep pure generation distillation at the selected beta.
export SFT_GENERATION_KL_BETA="${SFT_GENERATION_KL_BETA:-0.7}"
export SFT_MIXED_KL_BETA="${SFT_MIXED_KL_BETA:-1.0}"

# The benchmark no longer rewards open-ended visual captions. Do not spend
# retention KL or suppress CE on the visual-description family.
export SFT_MIXED_KL_PROB_FAMILY_VISUAL_DESCRIPTION="${SFT_MIXED_KL_PROB_FAMILY_VISUAL_DESCRIPTION:-0.0}"
export SFT_MIXED_KL_WEIGHT_FAMILY_VISUAL_DESCRIPTION="${SFT_MIXED_KL_WEIGHT_FAMILY_VISUAL_DESCRIPTION:-0.0}"
export SFT_MIXED_CE_SCALE_FAMILY_VISUAL_DESCRIPTION="${SFT_MIXED_CE_SCALE_FAMILY_VISUAL_DESCRIPTION:-1.0}"

# OCR looked worse than it was because format-only answers were previously sent
# to the model judge. Keep a light anchor, but restore full supervised CE.
export SFT_MIXED_KL_PROB_FAMILY_OCR="${SFT_MIXED_KL_PROB_FAMILY_OCR:-0.15}"
export SFT_MIXED_KL_WEIGHT_FAMILY_OCR="${SFT_MIXED_KL_WEIGHT_FAMILY_OCR:-0.20}"
export SFT_MIXED_CE_SCALE_FAMILY_OCR="${SFT_MIXED_CE_SCALE_FAMILY_OCR:-1.0}"

# The replacement visual task is deterministic read-chart/read-table reasoning.
# Give chart-like training tasks a small stability anchor without reducing CE.
export SFT_MIXED_KL_PROB_FAMILY_CHART="${SFT_MIXED_KL_PROB_FAMILY_CHART:-0.08}"
export SFT_MIXED_KL_WEIGHT_FAMILY_CHART="${SFT_MIXED_KL_WEIGHT_FAMILY_CHART:-0.15}"
export SFT_MIXED_CE_SCALE_FAMILY_CHART="${SFT_MIXED_CE_SCALE_FAMILY_CHART:-1.0}"

exec bash "$ROOT/scripts/dlc/start_sft.sh" "$@"
