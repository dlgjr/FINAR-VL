#!/usr/bin/env bash
set -euo pipefail

ROOT=/mnt/nas/bihaoran/qwen3vl
source "$ROOT/scripts/dlc/dlc_env.sh"

LOG_FILE="$LOG_ROOT/dlc_pipeline_$(date +%Y%m%d_%H%M%S).log"

if [ "${DLC_STAGE:-smoke}" = "gspo" ]; then
  exec bash "$ROOT/scripts/dlc/start_gspo.sh" \
    2>&1 | tee "$LOG_FILE"
fi

exec bash "$ROOT/scripts/dlc/run_sft_gspo_smoke.sh" \
  2>&1 | tee "$LOG_FILE"
