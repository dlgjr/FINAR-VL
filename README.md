# FINAR-VL

[中文](README.md) | [English](README.en.md)

FINAR-VL 是一个面向金融领域的多模态大模型训练项目，基于 Qwen3-VL-4B-Instruct 训练 `FINAR-VL`。项目重点处理多表、多图、跨页金融材料中的信息提取、证据定位与数值计算问题。

## 开源内容

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

⚡ **参数效率**：FINAR-VL 以 4B 参数规模面向金融领域进行专项优化，用更小的模型规模覆盖图表、财报、跨页文档与数值推理任务。

📈 **领域特化**：对比同时保留 Qwen3-VL-4B-Instruct 基线、Qwen3-VL-32B 强通用模型，以及 InternVL、MiniCPM、Fin-R1、FinLMM-R1 等代表性模型。

🧠 **复杂金融推理**：重点评估图表理解、多模态数值计算、跨页证据定位、长文档理解和金融分析推理能力。

> 当前图中 FINAR-VL 分数为用于版式与目标展示的暂定值；正式发布时将以完整实测结果替换。

## 数据构造

<p align="center">
  <img src="docs/assets/data_construction_flow.svg" alt="FINAR-VL Data Construction Pipeline" width="100%">
</p>

SFT、Reasoning RL 和 Generation RL 共用 Finance World 作为证据底座，但三条数据构造流程彼此独立。

- **共享底座**：原始金融数据 → 标准化证据单元 → `Qwen3-VL-32B-Instruct` → Finance World。
- **SFT**：样本构造 → 筛选清洗 → SFT 训练 → Bad Case 分析 → 定向 SFT 补数。
- **Reasoning RL**：金融图谱采样 → 推理路径 / 任务骨架 → 可执行标准答案 → 高难候选样本。
- **Generation RL**：证据包 → 生成任务骨架 → 问题 + 参考答案。
- **构造模型**：`Qwen3-VL-235B-A22B-Instruct` 负责 SFT/RL 样本规划、生成与答案构造。


## 技术路线

<p align="center">
  <img src="assets/finar_vl_training_pipeline.svg" alt="FINAR-VL Training Pipeline" width="100%">
</p>

Reasoning RL 和 Generation RL 是两个独立训练阶段，均从同一个 SFT 检查点启动。Reasoning RL 强化可程序验证的金融推理能力；Generation RL 强化开放式金融问答和分析生成能力。两路 RL 之间不传递模型权重。

MOPD 以 SFT 检查点初始化学生模型，同时加载 Reasoning RL 和 Generation RL 的产出作为两个教师模型，根据 reasoning 和 generation 数据分别提供 token级教师信号。当前训练脚本使用 top-128 GKD：每个样本只路由到对应教师，由教师返回 top-128 token 分布进行蒸馏。MOPD 的产出模型命名为 `FINAR-VL`。

## 快速开始

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

当前 MOPD 启动脚本按单机 4 卡设计。默认使用 GPU 0、1 训练学生模型，GPU 2 运行 Reasoning teacher，GPU 3 运行 Generation teacher；需要模型裁判的评估样本也复用 Generation teacher。

```bash
MOPD_STUDENT_MODEL=/path/to/sft_checkpoint \
MOPD_REASONING_TEACHER=/path/to/reasoning_rl_checkpoint \
MOPD_GENERATION_TEACHER=/path/to/generation_rl_checkpoint \
MOPD_REASONING_DATA=/path/to/reasoning_train_gspo.jsonl \
MOPD_GENERATION_DATA=/path/to/generation_train_gspo.jsonl \
bash scripts/mopd/run_mopd_dual_expert_4gpu_top128.sh
```

脚本默认使用 top-128 GKD，图片路径沿用 RL 数据准备阶段的解析逻辑。训练每 20 step 保存一次 checkpoint 并执行阶段评估。Qwen3-VL 的学生前向默认开启 `use_logits_to_keep`，只保留需要计算蒸馏损失的 logits，避免长序列在 LM head 处产生过大的显存峰值。


训练过程中生成的 W&B 日志、模型权重、评估结果、奖励审计和各 rank状态均保存在 `output/`。

## 训练阶段

### 1. SFT

SFT 阶段联合使用金融文本和多模态数据，建立金融文档理解、表格计算、图表推理和答案生成能力。

训练链路包含：

- 按任务类型、模态和实际 token长度生成确定性采样计划；
- 对 OCR、图表、跨模态推理等任务设置最低采样配额；
- 对生成类样本使用基础模型在线蒸馏，降低通用生成能力退化；
- 在训练过程中执行 Pass@1 和 Pass@8 评估；
- 记录 W&B日志、模型权重和评估结果。

### 2. Reasoning RL

Reasoning RL 路线面向具有明确标准答案的金融推理任务，使用程序化可验证奖励训练模型。

主要任务包括：

- 多步数值推理；
- 多表和单表计算；
- 财报证据页检索；
- 图表数值推理；
- 单选、多选和判断任务。

该阶段采用 GSPO，奖励由数值、单位、选项、页码及结构化答案校验器计算，默认不依赖模型裁判。

### 3. Generation RL

Generation RL 路线面向开放式金融问答和分析生成任务，与 Reasoning RL 分别从同一个 SFT 检查点启动。

该阶段使用混合奖励：

- 对选择题、判断题等结构化任务使用规则奖励；
- 对开放式金融分析和生成任务使用多模态模型裁判；
- 对奖励结果、异常输出和各 rank的完成状态进行持续记录。

### 4. MOPD

MOPD 阶段以 SFT 检查点作为学生模型，同时使用 Reasoning RL 和 Generation RL 的产出作为推理教师与生成教师。训练数据保持 reasoning 和 generation 两路等量，样本根据路由只请求对应教师。

当前实现使用 top-128 GKD。教师服务返回每个目标位置的 top-128 token 概率，学生模型据此计算蒸馏损失。Reasoning teacher 使用 Reasoning RL 训练时的回答格式，Generation teacher 使用 Generation RL 的回答格式，避免在蒸馏阶段混用两套策略提示词。

训练脚本同时复用 SFT 阶段的 Pass@1 / Pass@8 评估。能够程序判分的样本直接使用规则判分，确实需要模型裁判的样本交给 Generation teacher。checkpoint 每 20 step 保存一次，最新 checkpoint 保留完整训练状态，旧 checkpoint 只保留模型权重。

## RL 数据与奖励设计

| 数据路线 | 主要任务 | 奖励方式 |
|---|---|---|
| Reasoning | 数值计算、表格推理、证据页检索、结构化问答 | 程序化规则奖励 |
| Generation | 开放式金融分析、知识问答、图表理解、选择和判断任务 | 规则奖励与模型裁判混合 |

RL 数据进入训练前依次执行：

1. 统一数据结构并生成稳定样本标识；
2. 校验问题、图片、答案和奖励路由；
3. 根据图片数量与分辨率、输入长度、生成长度和裁判调用成本估计计算量；
4. 将数据拆分为细粒度任务并进行负载均衡；
5. 训练期间记录计划任务数、完成数、剩余数、心跳和错误状态。

## 目录结构

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

