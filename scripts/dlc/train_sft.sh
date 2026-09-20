#!/usr/bin/env bash
set -euo pipefail

# Stage 1: freeze only the vision encoder.
# The aligner and LLM remain trainable.
export SFT_FREEZE_VIT=true
export SFT_FREEZE_ALIGNER=false
export SFT_FREEZE_LLM=false
export SFT_VIT_GRADIENT_CHECKPOINTING=false

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
exec "$SCRIPT_DIR/start_sft.sh" "$@"
