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

# Open-ended visual description is no longer a benchmark target, but it remains
# a useful base capability. Keep the explicitly selected moderate protection.
export SFT_MIXED_KL_PROB_FAMILY_VISUAL_DESCRIPTION="${SFT_MIXED_KL_PROB_FAMILY_VISUAL_DESCRIPTION:-0.50}"
export SFT_MIXED_KL_WEIGHT_FAMILY_VISUAL_DESCRIPTION="${SFT_MIXED_KL_WEIGHT_FAMILY_VISUAL_DESCRIPTION:-0.50}"
export SFT_MIXED_CE_SCALE_FAMILY_VISUAL_DESCRIPTION="${SFT_MIXED_CE_SCALE_FAMILY_VISUAL_DESCRIPTION:-1.0}"

# financial_data_description is the closest direct training proxy for the new
# visual-data benchmark. Override the family-level 0.5 policy for this task only.
export SFT_MIXED_KL_PROB_FINANCIAL_DATA_DESCRIPTION="${SFT_MIXED_KL_PROB_FINANCIAL_DATA_DESCRIPTION:-0.80}"
export SFT_MIXED_KL_WEIGHT_FINANCIAL_DATA_DESCRIPTION="${SFT_MIXED_KL_WEIGHT_FINANCIAL_DATA_DESCRIPTION:-0.80}"
export SFT_MIXED_CE_SCALE_FINANCIAL_DATA_DESCRIPTION="${SFT_MIXED_CE_SCALE_FINANCIAL_DATA_DESCRIPTION:-1.0}"

# OCR shows genuine retention loss after fixing format-only judge failures.
# Strongly anchor both OCR tasks while keeping the full supervised CE signal.
export SFT_MIXED_KL_PROB_FAMILY_OCR="${SFT_MIXED_KL_PROB_FAMILY_OCR:-0.80}"
export SFT_MIXED_KL_WEIGHT_FAMILY_OCR="${SFT_MIXED_KL_WEIGHT_FAMILY_OCR:-0.80}"
export SFT_MIXED_CE_SCALE_FAMILY_OCR="${SFT_MIXED_CE_SCALE_FAMILY_OCR:-1.0}"

# Market-chart confidence and deterministic visual-data reasoning both lose a
# large amount of probability mass during SFT. Protect the chart family strongly.
export SFT_MIXED_KL_PROB_FAMILY_CHART="${SFT_MIXED_KL_PROB_FAMILY_CHART:-0.80}"
export SFT_MIXED_KL_WEIGHT_FAMILY_CHART="${SFT_MIXED_KL_WEIGHT_FAMILY_CHART:-0.80}"
export SFT_MIXED_CE_SCALE_FAMILY_CHART="${SFT_MIXED_CE_SCALE_FAMILY_CHART:-1.0}"

printf '%s\n' \
  "[finar-retention] generation_beta=$SFT_GENERATION_KL_BETA mixed_beta=$SFT_MIXED_KL_BETA" \
  "[finar-retention] visual_description: p=$SFT_MIXED_KL_PROB_FAMILY_VISUAL_DESCRIPTION lambda=$SFT_MIXED_KL_WEIGHT_FAMILY_VISUAL_DESCRIPTION ce=$SFT_MIXED_CE_SCALE_FAMILY_VISUAL_DESCRIPTION" \
  "[finar-retention] financial_data_description: p=$SFT_MIXED_KL_PROB_FINANCIAL_DATA_DESCRIPTION lambda=$SFT_MIXED_KL_WEIGHT_FINANCIAL_DATA_DESCRIPTION ce=$SFT_MIXED_CE_SCALE_FINANCIAL_DATA_DESCRIPTION" \
  "[finar-retention] ocr: p=$SFT_MIXED_KL_PROB_FAMILY_OCR lambda=$SFT_MIXED_KL_WEIGHT_FAMILY_OCR ce=$SFT_MIXED_CE_SCALE_FAMILY_OCR" \
  "[finar-retention] chart: p=$SFT_MIXED_KL_PROB_FAMILY_CHART lambda=$SFT_MIXED_KL_WEIGHT_FAMILY_CHART ce=$SFT_MIXED_CE_SCALE_FAMILY_CHART"

exec bash "$ROOT/scripts/dlc/start_sft.sh" "$@"
