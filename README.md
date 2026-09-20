<h1 align="center">
  <img src="assets/finar_vl_logo.svg" width="80" align="left" alt="FINAR-VL Logo">
  FINAR-VL
</h1>

[中文](README.md) | [English](README.en.md)

FINAR-VL 是一个基于 Qwen3-VL-4B-Instruct 的金融多模态大模型训练项目，覆盖财务与估值计算、表格与图表推理、OCR 与文档理解、信息抽取与证据检索、跨页多模态推理、金融知识与市场/风险分析，以及结构化问答和开放式金融分析生成。

## 📦 开源内容

| 内容 | 说明 |
|---|---|
| 训练代码 | 开源 SFT、两个独立 RL 和 MOPD 的训练实现与启动脚本 |
| 训练数据 | 开源规范化后的文本、多模态、Reasoning RL 和 Generation RL 数据 |
| 阶段权重 | 开源 SFT、Reasoning RL 和 Generation RL 的阶段模型权重 |
| 最终权重 | MOPD 完成并验证后开源 `FINAR-VL` 模型权重 |



## 📊 性能表现

<div align="center">
  <img src="assets/finar_vl_logo.svg" width="82" alt="FINAR-VL Logo">
  <br>
  <strong>FINAR-VL-4B</strong>
</div>

<br>

<div align="center">
  <img src="assets/finar_vl_performance.svg" width="100%" alt="FINAR-VL Performance Comparison">
  <br>
  <em><strong>图 1：</strong>FINAR-VL-4B 与通用及金融专项多模态模型在 12 个金融基准上的对比。</em>
</div>

### ✨ 结果亮点

🏆 **跨基准表现**：覆盖 FAMMA、FinChart-Bench、FinMME、FinMMR、FinMTM、MME-Finance、VisFinEval、XFinBench、CFMME、FinMMDocR、FinDocMRE 和 FinEval-MM 共 12 项金融多模态基准。

⚡ **参数效率**：以 4B 参数规模覆盖图表、财报、跨页文档与数值推理等金融多模态任务。

📈 **领域特化**：面向金融场景专项训练，并与通用及金融专项多模态模型进行对比。

🧠 **复杂金融推理**：重点评估图表理解、多模态数值计算、跨页证据定位、长文档理解和金融分析推理。

## 🧩 数据构造

<p align="center">
  <img src="docs/assets/data_construction_flow.svg" alt="FINAR-VL Data Construction Pipeline" width="100%">
</p>

SFT、Reasoning RL 和 Generation RL 共用 Finance World 作为证据底座，但三条数据构造流程彼此独立。

- **共享底座**：原始金融数据 → 标准化证据单元 → `Qwen3-VL-32B-Instruct` → Finance World。
- **SFT**：样本构造 → 筛选清洗 → SFT 训练 → Bad Case 分析 → 定向 SFT 补数。
- **Reasoning RL**：金融图谱采样 → 推理路径 / 任务骨架 → 可执行标准答案 → 高难候选样本。
- **Generation RL**：证据包 → 生成任务骨架 → 问题 + 参考答案。
- **构造模型**：`Qwen3-VL-235B-A22B-Instruct` 负责 SFT/RL 样本规划、生成与答案构造。

更详细的数据构造、Bad Case 飞轮、质量筛选与训练数据路由见 [`docs/data_pipeline.md`](docs/data_pipeline.md)。


## 🏗️ 技术路线

<p align="center">
  <img src="assets/finar_vl_training_pipeline.svg" alt="FINAR-VL Training Pipeline" width="100%">
</p>

训练流程由 SFT、两路独立 RL 和 MOPD 组成：

- **SFT**：建立金融文档理解、表格/图表推理、数值计算和答案生成能力。
- **Reasoning RL**：从 SFT 检查点启动，训练数值、复合数值、单/多选、判断和证据页等可程序验证任务。
- **Generation RL**：同样从 SFT 检查点独立启动，训练开放式金融问答与分析生成；两路 RL 不传递模型权重。
- **MOPD**：以 SFT 检查点初始化学生模型，加载两路 RL 模型作为教师，并按样本类型路由教师信号进行 top-128 GKD，最终产出 `FINAR-VL`。

## ⚡ 快速开始

### 1. 克隆仓库

```bash
git clone https://github.com/dlgjr/FINAR-VL.git
cd FINAR-VL
```

### 2. 安装依赖

建议使用 Python 3.12 和支持 BF16的 NVIDIA GPU。当前正式训练脚本默认使用 8 张 GPU。

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install "ms-swift==4.4.2" "transformers==4.57.6" "wandb==0.28.1" "qwen-vl-utils>=0.0.14" deepspeed modelscope accelerate datasets peft vllm
python -m pip install flash-attn --no-build-isolation
```

### 3. 准备模型和数据

将基础模型、裁判模型和训练数据放入仓库，默认目录结构如下：

```text
FINAR-VL/
├── models/qwen4/
├── models/qwen30/
├── models/qwen32/
├── models/qwen235/
├── data/train_multi/train_multi_sft_minhash_dedup.jsonl
├── data/train_text/train_text_sft_minhash_dedup.jsonl
├── data/train_multi/train_rl_reasoning.jsonl
├── data/train_multi/train_rl_generation.jsonl
└── data/benchmark/my_benchmark/all.jsonl
```

初始化本机环境变量：

```bash
export QWEN3VL_ROOT=$(pwd)
export PYTHON_BIN=$(command -v python)
export PYTHONUSERBASE=$QWEN3VL_ROOT/.python-user
export WORLD_SIZE=1
export RANK=0
export MASTER_ADDR=127.0.0.1
export MASTER_PORT=29500
```

### 4. 运行 SFT

```bash
export JUDGE_MODEL=$QWEN3VL_ROOT/models/qwen30
bash scripts/dlc/start_sft_stage1.sh
```

训练结果默认写入 `output/sft/`。从该目录选择需要进入 RL 的 SFT 检查点。

### 5. 运行 Reasoning RL

```bash
GSPO_NNODES=1 \
GSPO_NODE_RANK=0 \
GSPO_MASTER_ADDR=127.0.0.1 \
GSPO_MASTER_PORT=29510 \
REASONING_START_MODEL=/path/to/sft_checkpoint \
REASONING_RL_DATA=$QWEN3VL_ROOT/data/train_multi/train_rl_reasoning.jsonl \
REASONING_RL_OUTPUT_DIR=$QWEN3VL_ROOT/output/gspo_reasoning \
bash scripts/dlc/start_gspo_reasoning.sh
```

### 6. 运行 Generation RL

Generation RL 与 Reasoning RL 独立，使用同一个 SFT 检查点作为起点：

```bash
GSPO_NNODES=1 \
GSPO_NODE_RANK=0 \
GSPO_MASTER_ADDR=127.0.0.1 \
GSPO_MASTER_PORT=29520 \
GSPO_JUDGE_MODEL=$QWEN3VL_ROOT/models/qwen235 \
GENERATION_START_MODEL=/path/to/sft_checkpoint \
GENERATION_RL_DATA=$QWEN3VL_ROOT/data/train_multi/train_rl_generation.jsonl \
GENERATION_RL_OUTPUT_DIR=$QWEN3VL_ROOT/output/gspo_generation \
bash scripts/dlc/start_gspo_generation.sh
```

### 7. 运行 MOPD

当前 MOPD 启动脚本按单机 4 卡设计：GPU 0、1 训练学生模型，GPU 2、3 分别运行 Reasoning 和 Generation teacher。

```bash
MOPD_STUDENT_MODEL=/path/to/sft_checkpoint \
MOPD_REASONING_TEACHER=/path/to/reasoning_rl_checkpoint \
MOPD_GENERATION_TEACHER=/path/to/generation_rl_checkpoint \
MOPD_REASONING_DATA=/path/to/reasoning_train_gspo.jsonl \
MOPD_GENERATION_DATA=/path/to/generation_train_gspo.jsonl \
bash scripts/mopd/run_mopd_dual_expert_4gpu_top128.sh
```

脚本默认使用 top-128 GKD，并每 20 step 保存 checkpoint 和执行阶段评估。

## 📁 目录结构

```text
FINAR-VL/
├── README.md
├── README.en.md
├── data/
│   ├── benchmark/                 # 训练期间评估数据
│   ├── train_multi/               # 多模态 SFT、RL 数据及图片
│   └── train_text/                # 纯文本 SFT 数据
├── models/
│   ├── qwen4/                     # Qwen3-VL-4B-Instruct
│   ├── qwen30/                    # 训练评估模型
│   ├── qwen32/                    # Qwen3-VL-32B-Instruct，证据抽取
│   └── qwen235/                   # Qwen3-VL-235B-A22B-Instruct，数据构造与裁判
├── scripts/
│   ├── data/                      # 数据构建、清洗和格式转换
│   ├── sft/                       # SFT 采样、蒸馏和评估组件
│   ├── rl/                        # RL 数据、奖励、调度和审计组件
│   ├── dlc/                       # 正式训练启动脚本
│   └── mopd/                      # MOPD 训练脚本
├── tests/                         # 单元测试
└── output/                        # 训练日志、权重和评估结果
```

