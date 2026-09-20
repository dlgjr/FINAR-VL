#!/usr/bin/env bash

export MODEL_NAME="${MODEL_NAME:-FINAR-VL-4B}"
export API_BASE="${API_BASE:-http://127.0.0.1:8000/v1}"
export API_KEY="${API_KEY:-EMPTY}"
export OUTPUT_DIR="${OUTPUT_DIR:-evaluation/results}"

# Financial QA / chart reasoning
python evaluation/run.py --benchmarks FAMMA FinChart-Bench FinMME FinMMR

# Comprehensive financial multimodal evaluation
python evaluation/run.py --benchmarks FinMTM MME-Finance VisFinEval XFinBench

# Long-document / document-level reasoning
python evaluation/run.py --benchmarks CFMME FinMMDocR FinDocMRE FinEval-MM
