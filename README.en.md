<h1 align="center">
  <img src="assets/finar_vl_logo.svg" width="80" align="left" alt="FINAR-VL Logo">
  FINAR-VL
</h1>

[中文](README.md) | [English](README.en.md)

## 🎯 Introduction

**FINAR-VL** is a financial multimodal large language model built on Qwen3-VL-4B-Instruct. It targets financial and valuation calculations, table/chart reasoning, OCR/document understanding, information extraction and evidence retrieval, cross-page multimodal reasoning, financial knowledge and market-risk analysis, and structured/open-ended financial QA.

The project provides an end-to-end pipeline covering financial data construction and cleaning, SFT, Reasoning RL, Generation RL, MOPD, and public-benchmark evaluation, together with the corresponding training code, data, and stage checkpoints.

### Key Highlights

🏦 **Financial Multimodality**: Covers tables, charts, cross-page documents, and numerical tasks in financial reports, announcements, research reports, and related materials.

🧠 **Dual-branch RL**: Reasoning RL strengthens programmatically verifiable financial reasoning, while Generation RL targets open-ended financial analysis and generation.

🔬 **Multi-teacher Distillation**: MOPD uses the two RL models as reasoning and generation teachers and distills them into a unified 4B student with top-128 GKD.

📊 **Public Benchmarks**: FINAR-VL is evaluated on 12 public financial multimodal benchmarks: FAMMA, FinChart-Bench, FinMME, FinMMR, FinMTM, MME-Finance, VisFinEval, XFinBench, CFMME, FinMMDocR, FinDocMRE, and FinEval-MM.

## 📦 Open-source Content

| Item | Description |
|---|---|
| Training code | SFT, two independent RL pipelines, MOPD implementation, and launch scripts |
| Training data | Normalized text, multimodal, Reasoning RL, and Generation RL data |
| Stage checkpoints | SFT, Reasoning RL, and Generation RL checkpoints |
| Final checkpoint | The `FINAR-VL` model checkpoint will be released after MOPD is completed and validated |


## 📊 Performance

<div align="center">
  <img src="assets/finar_vl_logo.svg" width="82" alt="FINAR-VL Logo">
  <br>
  <strong>FINAR-VL-4B</strong>
</div>

<br>

<div align="center">
  <img src="assets/finar_vl_performance.svg" width="100%" alt="FINAR-VL Performance Comparison">
  <br>
  <em><strong>Figure 1:</strong> Comparison of FINAR-VL-4B with general-purpose and finance-specialized multimodal models across 12 financial benchmarks.</em>
</div>

### ✨ Highlights

🏆 **Cross-benchmark performance**: The comparison covers 12 financial multimodal benchmarks: FAMMA, FinChart-Bench, FinMME, FinMMR, FinMTM, MME-Finance, VisFinEval, XFinBench, CFMME, FinMMDocR, FinDocMRE, and FinEval-MM.

⚡ **Parameter efficiency**: The 4B model covers financial multimodal tasks involving charts, reports, cross-page documents, and numerical reasoning.

📈 **Domain specialization**: FINAR-VL is trained specifically for financial scenarios and compared with both general-purpose and finance-specialized multimodal models.

🧠 **Complex financial reasoning**: Evaluation emphasizes chart understanding, multimodal numerical calculation, cross-page evidence localization, long-document understanding, and financial analytical reasoning.

## 🧩 Data Construction

<p align="center">
  <img src="docs/assets/data_construction_flow.svg" alt="FINAR-VL Data Construction Pipeline" width="100%">
</p>

SFT, Reasoning RL, and Generation RL share Finance World as the common evidence foundation, while their data-construction pipelines remain independent.

- **Shared foundation**: raw financial data → standardized evidence units → `Qwen3-VL-32B-Instruct` → Finance World.
- **SFT**: sample construction → filtering and cleaning → SFT training → Bad Case analysis → targeted SFT augmentation.
- **Reasoning RL**: Financial Graph sampling → reasoning path / task skeleton → executable gold → hard candidates.
- **Generation RL**: evidence bundle → generation task skeleton → question + reference answer.
- **Construction model**: `Qwen3-VL-235B-A22B-Instruct` handles SFT/RL sample planning, rendering, and answer construction.

## 🏗️ Training Pipeline

<p align="center">
  <img src="assets/finar_vl_training_pipeline.svg" alt="FINAR-VL Training Pipeline" width="100%">
</p>

The pipeline consists of SFT, two independent RL branches, and MOPD:

- **SFT**: builds financial document understanding, table/chart reasoning, numerical calculation, and answer-generation capabilities.
- **Reasoning RL**: starts from the SFT checkpoint and trains programmatically verifiable numeric, composite-numeric, single/multiple-choice, true/false, and evidence-page tasks.
- **Generation RL**: independently starts from the same SFT checkpoint and trains open-ended financial QA and analytical generation; no model weights are passed between the two RL branches.
- **MOPD**: initializes the student from the SFT checkpoint, loads the two RL models as teachers, routes each sample to its corresponding teacher, and performs top-128 GKD to produce `FINAR-VL`.

## ⚡ Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/dlgjr/FINAR-VL.git
cd FINAR-VL
```

### 2. Install Dependencies

Python 3.12 and NVIDIA GPUs with BF16 support are recommended. The current production training scripts use eight GPUs by default.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install "ms-swift==4.4.2" "transformers==4.57.6" "wandb==0.28.1" "qwen-vl-utils>=0.0.14" deepspeed modelscope accelerate datasets peft vllm
python -m pip install flash-attn --no-build-isolation
```

### 3. Prepare Models and Data

Place the base model, evaluation/judge models, and training data in the repository using the following default layout:

```text
FINAR-VL/
├── models/qwen4/
├── models/qwen30/
├── models/qwen32/
├── models/qwen235/
├── evaluation/                     # Public benchmark evaluation launcher and registry
├── data/train_multi/train_multi_sft_minhash_dedup.jsonl
├── data/train_text/train_text_sft_minhash_dedup.jsonl
├── data/train_multi/train_rl_reasoning.jsonl
├── data/train_multi/train_rl_generation.jsonl
└── data/benchmark/my_benchmark/all.jsonl
```

Initialize the local environment variables:

```bash
export QWEN3VL_ROOT=$(pwd)
export PYTHON_BIN=$(command -v python)
export PYTHONUSERBASE=$QWEN3VL_ROOT/.python-user
export WORLD_SIZE=1
export RANK=0
export MASTER_ADDR=127.0.0.1
export MASTER_PORT=29500
```

### 4. Run SFT

```bash
export JUDGE_MODEL=$QWEN3VL_ROOT/models/qwen30
bash scripts/dlc/train_sft.sh
```

Outputs are written to `output/sft/` by default. Select the SFT checkpoint that should be used as the starting point for RL.

### 5. Run Reasoning RL

```bash
GSPO_NNODES=1 \
GSPO_NODE_RANK=0 \
GSPO_MASTER_ADDR=127.0.0.1 \
GSPO_MASTER_PORT=29510 \
REASONING_START_MODEL=/path/to/sft_checkpoint \
REASONING_RL_DATA=$QWEN3VL_ROOT/data/train_multi/train_rl_reasoning.jsonl \
REASONING_RL_OUTPUT_DIR=$QWEN3VL_ROOT/output/gspo_reasoning \
bash scripts/dlc/train_reasoning_rl.sh
```

### 6. Run Generation RL

Generation RL is independent of Reasoning RL and starts from the same SFT checkpoint:

```bash
GSPO_NNODES=1 \
GSPO_NODE_RANK=0 \
GSPO_MASTER_ADDR=127.0.0.1 \
GSPO_MASTER_PORT=29520 \
GSPO_JUDGE_MODEL=$QWEN3VL_ROOT/models/qwen235 \
GENERATION_START_MODEL=/path/to/sft_checkpoint \
GENERATION_RL_DATA=$QWEN3VL_ROOT/data/train_multi/train_rl_generation.jsonl \
GENERATION_RL_OUTPUT_DIR=$QWEN3VL_ROOT/output/gspo_generation \
bash scripts/dlc/train_generation_rl.sh
```

### 7. Run MOPD

The current MOPD launcher is designed for a single machine with four GPUs: GPUs 0 and 1 train the student model, while GPUs 2 and 3 serve the Reasoning and Generation teachers.

```bash
MOPD_STUDENT_MODEL=/path/to/sft_checkpoint \
MOPD_REASONING_TEACHER=/path/to/reasoning_rl_checkpoint \
MOPD_GENERATION_TEACHER=/path/to/generation_rl_checkpoint \
MOPD_REASONING_DATA=/path/to/reasoning_train_gspo.jsonl \
MOPD_GENERATION_DATA=/path/to/generation_train_gspo.jsonl \
bash scripts/mopd/train_mopd.sh
```

The script uses top-128 GKD by default and saves a checkpoint with stage evaluation every 20 steps.

## 🧪 Public Benchmark Evaluation

FINAR-VL is evaluated on the same 12 public financial multimodal benchmarks shown in the performance figure: FAMMA, FinChart-Bench, FinMME, FinMMR, FinMTM, MME-Finance, VisFinEval, XFinBench, CFMME, FinMMDocR, FinDocMRE, and FinEval-MM.

Together, these benchmarks cover financial chart understanding, financial-document QA, multimodal numerical reasoning, cross-page evidence localization, long-document understanding, and broader financial multimodal reasoning.

A unified launcher follows the same organization pattern as Innovator-VL and delegates each benchmark to its official evaluator:

```bash
MODEL_NAME=FINAR-VL-4B API_BASE=http://127.0.0.1:8000/v1 API_KEY=EMPTY bash evaluation/evaluate.sh
```

See [`evaluation/README.md`](evaluation/README.md) for benchmark-specific configuration.
## 📁 Repository Structure

```text
FINAR-VL/
├── README.md
├── README.en.md
├── data/
│   ├── benchmark/                 # Evaluation data used during training
│   ├── train_multi/               # Multimodal SFT and RL data, including images
│   └── train_text/                # Text-only SFT data
├── models/
│   ├── qwen4/                     # Qwen3-VL-4B-Instruct
│   ├── qwen30/                    # Evaluation model used during training
│   ├── qwen32/                    # Qwen3-VL-32B-Instruct, evidence extraction
│   └── qwen235/                   # Qwen3-VL-235B-A22B-Instruct, data construction and judging
├── scripts/
│   ├── data/                      # Data construction, cleaning, and format conversion
│   ├── sft/                       # SFT sampling, distillation, and evaluation components
│   ├── rl/                        # RL data, reward, scheduling, and audit components
│   ├── dlc/                       # SFT / RL launchers and runtime plugins
│   └── mopd/                      # MOPD training launcher
└── output/                        # Training logs, checkpoints, and evaluation results
```

