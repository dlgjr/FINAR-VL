# FINAR-VL 数据与训练开发说明

本文记录 README 中省略的实现细节。代码行为以仓库当前脚本为准。

## 1. 数据构造总览

FINAR-VL 将原始金融材料统一整理为 Finance World，再分别构造 SFT、Reasoning RL 和 Generation RL 数据。

主要入口：

- `scripts/data/build_finance_sailorfog.py`：Finance World 与初始 SFT 数据。
- `scripts/data/build_badcase_flywheel.py`：Bad Case 定向补数。
- `scripts/data/clean_synthetic_data.py`：统一格式检查、task 重标注与质量筛选。
- `scripts/data/build_rl_candidate_bank.py`：Reasoning / Generation RL 候选数据。
- `scripts/data/build_generation_rl_data.py`：Generation RL 的两阶段构造流程。
- `scripts/data/reclassify_rl_routes.py`：RL reward route 重分类。
- `scripts/rl/prepare_gspo_data.py`：转换为 GSPO 训练格式。

## 2. Finance World

### 2.1 Evidence Unit

`build_finance_sailorfog.py` 从 PDF、图片、JSON/JSONL、CSV、Parquet、TXT/Markdown 中抽取证据单元。

PDF 按页保存文本和页面图像；结构化数据优先保留 context/reference/table/OCR 等上下文字段，并排除已有 QA supervision，避免把原答案重新作为证据输入。

### 2.2 Entity 与 Fact

实体和事实抽取由 `Qwen3-VL-32B-Instruct` 完成。

文本数值事实先通过规则扫描生成候选 metric/value，再由模型完成指标、期间、scope、报表类型等归一化。图片事实要求直接依据图像，无法可靠读取的精确数值不进入事实。

Fact 记录的主要字段包括：

- entity / company；
- metric 与 canonical metric；
- value、unit、currency；
- period、scope、statement type；
- text/image 来源；
- image index、visual type；
- evidence quote；
- confidence。

当前置信度逻辑中，高置信事实直接进入 `graph_facts.jsonl`；中间区间再次复核；低置信事实进入 `fact_quarantine.jsonl`。

### 2.3 Relation Graph

`build_graph` 在事实之间建立以下关系：

- `same_company_metric`：同公司、同指标；
- `same_company_period`：同公司、同期间；
- `same_metric_period`：同指标、同期间；
- `same_source`：同一来源；
- `financial_formula:<name>`：同 entity / period / scope / unit 下满足预定义金融公式依赖。

文档实体之间还建立：

- `same_company_cross_period`；
- `same_industry_peer`。

这些关系用于后续多跳、跨期、同业和数值任务的证据采样。

### 2.4 初始 SFT 构造

初始构造覆盖 OCR、文档感知、单表/多表、图表、跨模态、多页检索、数值推理、金融知识、风险/政策、投资与组合等任务。

数值任务先生成可执行表达式，再由 Python 重新执行并校验每一步和最终答案。普通任务由构造模型生成后，再检查 supported、answerable、visual_required 等条件。

难度分为 easy / medium / hard。medium 至少依赖 2 条关键证据；hard 至少依赖 3 条关键证据，数值 hard 样本同时要求至少 3 步依赖计算。

## 3. Bad Case 飞轮

`build_badcase_flywheel.py` 不直接改写原 Bad Case 问题，而是把错误模式转换成新的构造约束，再从 Finance World 重新取证据生成新样本。

### 3.1 分类

每个 Bad Case 被归纳为：

- 一个 task type；
- 一个主要 error type；
- 一组 scenario tags；
- 后续构造重点。

error type 覆盖 OCR、表格、图表、检索、entity/period/scope/metric 混淆、单位币种、金融公式、算术、多步推理、风险、政策、审计、摘要、证据不足等错误。

### 3.2 检索优先级

新证据优先保持金融语义相关性，检索层级依次为：

1. 同文档；
2. 同实体同期间；
3. 同实体相邻期间；
4. 同实体其他期间；
5. 明确允许跨公司的任务中，同业 peer。

视觉任务还会检查图片数量、visual family、页数以及文本/图片组合要求。

### 3.3 定向构造

对于混淆类错误，优先加入真实的相似干扰项；视觉错误必须使用新的原始金融图片；计算类错误构造可程序验证的数值任务；证据边界错误同时覆盖可回答和材料不足样本。

新样本完成后再次检查：

- evidence support；
- 是否确实训练目标错误能力；
- visual policy；
- answerability；
- 与原 Bad Case 的差异。

## 4. 数据质量筛选

`clean_synthetic_data.py` 先执行基础格式和图片检查，再由 `Qwen3-VL-235B-A22B-Instruct` 根据 SFT sampler 的实际 task vocabulary 重新标注 task，并逐项打分。

10 个 rubric 为：

1. `answerability`：材料能否得到明确答案；
2. `answer_correctness`：监督答案是否正确；
3. `evidence_grounding`：关键事实是否被证据支持；
4. `financial_alignment`：主体、期间、指标、scope、币种和单位是否一致；
5. `reasoning_correctness`：计算、比较和推理是否成立；
6. `instruction_following`：答案类型、粒度和格式是否满足要求；
7. `modality_grounding`：视觉/多表/多图任务是否真实依赖对应模态；
8. `no_leakage_or_shortcut`：题面是否泄露答案或存在明显捷径；
9. `training_value`：样本是否自然、有效且具有训练价值；
10. `clarity_and_integrity`：问题、答案和必要推理是否完整一致。

每项只取 0 或 0.5，满分 5.0；默认保留总分不低于 4.0 的样本。

## 5. SFT task 与采样实现

SFT 的 task vocabulary 和 family 映射定义在 `scripts/sft/sample_plan_base.py`，覆盖：

- accounting / valuation；
- table reasoning；
- chart reasoning；
- document perception / OCR；
- information extraction；
- retrieval grounding；
- multipage financial reasoning；
- numerical / statistics；
- financial knowledge；
- market / macro reasoning；
- risk / policy / advice；
- classification / sentiment；
- generation / dialogue；
- general capability。

正式入口 `scripts/sft/sample_plan.py` 在基础 sampler 上增加项目级约束，包括 OCR、OCR transcription、financial summarization、visual description、image caption、insufficient-information detection 和 accounting/audit reasoning 的最低配额。

采样计划按 task、family、模态和序列长度生成确定性 block；正式 SFT launcher 当前设置多模态目标比例为 0.40，并对长输出降低长度惩罚，以避免长文档/长答案监督被过度压低。

## 6. RL 数据与 Reward Route

### 6.1 Reasoning RL

Reasoning 数据优先保留可以直接验证的任务。当前 programmatic verifier 包括：

- `numeric`；
- `numeric_final`；
- `composite_numeric`；
- `single_choice`；
- `multiple_choice`；
- `true_false`；
- `page_numbers`。

`prepare_gspo_data.py` 会重新校验数值 gold、单位、program 执行结果、evidence pages 和结构化答案。存在 program metadata 时会重新执行 add/subtract/multiply/divide 表达式并检查最终展示值。

### 6.2 Generation RL

Generation RL 主要面向开放式金融分析，包括财报分析、指标解释、文档比较/解释、摘要、风险、审计、行业、宏观、合规和组合分析等任务。

`build_generation_rl_data.py` 将流程拆为两阶段：

1. 32B VLM 从原始文本/图片抽取 Generation evidence facts；
2. 235B VLM 基于 evidence graph 规划 task skeleton，再生成问题和 grounded reference answer，并可执行最终构造检查。

### 6.3 Reward Routing

`reclassify_rl_routes.py` 和 `prepare_gspo_data.py` 根据输出形式决定 reward route。

具有明确结构答案的样本走 rule verifier；开放式语义答案走 `model_judge`。Generation 数据中若能恢复为 choice、true/false 或直接数值格式，也会优先进入规则奖励，而不是强制使用模型裁判。

## 7. GSPO 训练行为

Reasoning RL 与 Generation RL 都由各自启动脚本从 SFT checkpoint 独立启动。

当前 GSPO 训练每个 prompt 生成 8 个候选，并根据在线 verifier 的结果进行难度处理。实现位于 `scripts/dlc/gspo_direct_curriculum_plugin.py`、`gspo_reward_std_curriculum_plugin.py` 等插件中。

训练、数据构造和 reward routing 的参数可能继续调整；修改实现时应同步更新本文以及中英文 README 中对应的高层描述。
