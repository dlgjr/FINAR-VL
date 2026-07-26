#!/usr/bin/env bash
set -euo pipefail

ROOT=/mnt/nas/bihaoran/qwen3vl
source "$ROOT/scripts/dlc/dlc_env.sh"

LOG_FILE="$LOG_ROOT/dlc_pipeline_$(date +%Y%m%d_%H%M%S).log"

exec bash "$ROOT/scripts/dlc/run_sft_gspo_smoke.sh" \
  2>&1 | tee "$LOG_FILE"
