# FINAR-VL benchmark v2 整理与交接说明

## 1. 目标

整理 `D:\FINAR-VL-main\data\benchmark\my_benchmark\all.jsonl`，生成：

`D:\FINAR-VL-main\data\benchmark\my_benchmark\all_v2.jsonl`

原 `all.jsonl` 必须保持不变。

本次整理以任务能力与题目实际内容的一致性为核心，不依赖原始 `task`、`split` 或来源标签直接判定质量。每条候选数据都必须人工审核问题、标准答案、图片及任务能力是否对应。

## 2. 已确认的用户要求

1. 输出使用 `all_v2.jsonl`，不覆盖 `all.jsonl`。
2. 允许从 `D:\FINAR-VL-main\data\benchmark` 中寻找补充数据。
3. 允许基于可信金融材料自行编写新题和标准答案。
4. 自行编写的数据必须逐条审核，确保答案正确、题意明确、与任务能力一致。
5. 纳入整理范围的每个子任务最终严格保持10条。
6. 数量不足时补充；数量过多时先剔除质量差的数据，仍超过10条再固定随机剔除。
7. 本轮不处理多表、多图跨页计算任务 `long_document_cross_page`。
8. 不允许开启子智能体。

## 3. 现有文件和日志

### 3.1 基准集

- 当前基准集：`D:\FINAR-VL-main\data\benchmark\my_benchmark\all.jsonl`
- 图片根目录：`D:\FINAR-VL-main\data\benchmark\my_benchmark\assets`
- 可选补充来源：`D:\FINAR-VL-main\data\benchmark`

当前 `all.jsonl` 共380条、42类；157条含图片，图片引用591个，现有路由均可访问。

### 3.2 评估日志映射

- step0：`C:\Users\123\.codex\attachments\dd82b54b-4eda-45d6-aa5d-d3366c4329d0\pasted-text.txt`
- step1000：`C:\Users\123\.codex\attachments\2ed54908-4d21-42bb-af40-2b43f21fb822\pasted-text.txt`
- step2000：`C:\Users\123\.codex\attachments\ca511497-378c-41a7-ae62-d03054f760c4\pasted-text.txt`
- step3000：`C:\Users\123\.codex\attachments\f5ee2768-0160-41ba-8b6e-e7a7880631d5\pasted-text.txt`
- step4000：`C:\Users\123\.codex\attachments\bedea18c-4b39-4681-a752-e912c6b31bcc\pasted-text.txt`
- step5000：`C:\Users\123\.codex\attachments\e540a308-0b1a-43e1-98f9-bced65f0ba9b\pasted-text.txt`
- step6500：`C:\Users\123\.codex\attachments\a4eaaf50-92d8-4f2b-b201-d2c56ae413f1\pasted-text.txt`

总体 P1/P8：

`0.3711/0.5000 → 0.3474/0.5000 → 0.3500/0.5132 → 0.3184/0.4947 → 0.2737/0.4974 → 0.2974/0.4895 → 0.2842/0.4842`

日志中存在7处 `P8 < P1`，不符合标准累计 Pass@k 定义。数据整理不能依赖该异常字段判断单条样本质量。

## 4. 最终任务范围

### 4.1 原定26类：全部整理到10条

#### A. 保留并扩充

1. `chart_data_extraction`
2. `cross_modal_multi_hop`
3. `financial_ocr`
4. `merger_acquisition_completeness_classification`
5. `single_table_qa`
6. `statistics_comparison_ranking`
7. `basic_arithmetic_metrics`

处理原则：保留逐条审核后合格的原题；不足10条时补充；超过10条时先剔除问题样本，再固定随机抽减。

#### B. 清洗后保留

1. `entity_extraction_classification`
2. `financial_event_extraction`
3. `financial_audit_fundamentals`
4. `financial_summarization`
5. `monetary_policy_stance_classification`
6. `summary_announcement`
7. `portfolio_allocation_risk_return`

处理原则：逐条复核能力标签、题意、答案和输出格式。可明确修复的样本直接修复；存在歧义、事实错误或能力漂移的样本替换。

#### C. 暂停使用并重建

1. `compliance_safety_suitability`
2. `esg_issue_identification`
3. `financial_causal_event_reasoning`
4. `financial_counterfactual_inference`
5. `financial_data_description`
6. `financial_multi_turn_perception`
7. `financial_numeric_labeling`
8. `financial_semantic_role_labeling`
9. `multi_step_numerical_reasoning`
10. `multi_table_reasoning`
11. `multimodal_financial_knowledge`
12. `risk_sentiment_policy`

处理原则：现有样本只作为问题参考。最终10条必须重新筛选、重新标注或自行编写，确保每条达到本说明第6节的质量门槛。

说明：用户本轮要求“不看多表多图计算那种的”主要用于复查原26类之外是否还有遗漏问题。原26类中已经明确列出的 `multi_step_numerical_reasoning` 与 `multi_table_reasoning` 仍保留在原定范围；如果执行前用户明确要求一并排除，再调整范围。

### 4.2 新增纳入整理的12类

1. `candlestick_time_series`：现有7条；P8由0.714降至0.143；存在相似形态和主观答案。重建或补充到10条。
2. `evidence_retrieval`：现有8条；三次评估各缺失1条，长文档页码输出容易受格式影响。保留经核实的证据页，补到10条。
3. `explanation_anomaly_causality`：现有7条；P1/P8由0.714/1.000降至0.286/0.286；标准答案存在图片外推断。重建为证据约束解释题。
4. `financial_relation_extraction`：现有10条；多关系答案缺少稳定分隔。统一为合法 JSON 数组并复核关系边界。
5. `financial_sentiment_analysis`：现有10条；指令使用“正面/中性/负面”，答案使用“正向/中立/负向”。统一标签并复核歧义新闻。
6. `financial_topic_classification`：现有10条；数据主要为希腊语和英文，与中文金融应用相关性不足。重建为中文或中英平衡的金融主题分类。
7. `image_caption`：现有7条；标准答案过长且含不可见推断。补到10条，答案限制为图中可验证内容。
8. `industry_trend_inference`：现有7条；模型表现稳定，但数量不足。保留合格题并补到10条。
9. `investment_advice_strategy`：现有7条；6500 step 出现 P8<P1，答案主观且存在图片外推断。重建为非个性化、证据约束的策略和风险分析。
10. `relationship_equity_structure`：现有7条；部分题实际考股东回报而非股权结构，精度要求不一致。剔除漂移题，使用单图股权关系题补到10条。
11. `spatial_localization`：现有7条；其中一条实际考油价趋势，不属于空间定位。剔除漂移题并补到10条。
12. `stock_movement_prediction`：现有10条；未来涨跌标签具有随机性，含人工虚构 `$aaa` 样本。替换为时间边界明确、标签来自真实后续收盘数据的样本，并避免把不确定预测写成必然推理。

### 4.3 保持原样的3类

以下任务已有10条，数据与模型表现未发现需要本轮重建的问题：

1. `financial_certification_exam_qa`
2. `financial_entity_extraction`
3. `financial_headline_classification`

这3类从原 `all.jsonl` 原样复制到 `all_v2.jsonl`。

### 4.4 本轮不处理的1类

1. `long_document_cross_page`

该任务属于多图跨页计算，本轮按用户要求不检查、不重建，原8条直接复制。

## 5. 最终数量

- 整理范围：38类 × 10条 = 380条。
- 原样保留：3类 × 10条 = 30条。
- 不处理的 `long_document_cross_page`：8条。
- `all_v2.jsonl` 预期总数：418条。
- 任务总数仍为42类。

原先“420条”的计算有误；420条只有在42类全部统一为10条时才成立。本轮保留 `long_document_cross_page` 的原8条，因此正确总数是418条。

## 6. 单条数据质量门槛

每条候选样本必须逐项审核，任一关键项不合格即修复或替换：

1. **能力一致性**：实际考察能力必须与 `task` 对应，不能只依据来源标签。
2. **问题可答性**：题目提供的信息足以作答；不存在缺页、缺图、未定义术语或隐含外部条件。
3. **答案唯一性**：客观题有唯一正确答案；开放题有清晰评分要点和合理等价表达范围。
4. **事实正确性**：金融概念、事件、公司信息和政策表述准确。
5. **数值正确性**：重新计算公式、单位、百分比、正负号和保留小数位。
6. **格式一致性**：指令要求与标准答案格式一致；结构化答案必须是合法 JSON。
7. **证据约束**：多模态答案只能使用图片或题干可验证的信息，不添加图片外事实。
8. **图片质量**：图片清晰、方向正确、关键文字可读，问题与图片内容直接相关。
9. **语言质量**：表述简洁、无乱码、无逐字符异常空格、无不必要冗长提示。
10. **安全性**：投资相关任务不得给出个性化确定性收益承诺；风险与策略答案明确条件和不确定性。
11. **独立性**：不得存在完全重复题；近重复题不得只替换公司名或数值。
12. **评估可执行性**：答案应便于现有评估器稳定判断，避免依赖无界开放式措辞。

## 7. 各类任务的统一答案规范

1. 分类任务：答案只使用指令中明确列出的规范标签。
2. 选择题：统一要求“仅输出选项字母”，标准答案也只保留字母。
3. 数值题：答案包含数值和必要单位；题干明确保留位数。
4. 实体抽取：输出合法 JSON 数组，明确实体类型和文本跨度含义。
5. 事件抽取：输出合法 JSON 数组；每个事件对象字段固定，缺失字段使用统一规则。
6. 关系抽取：输出合法 JSON 数组，每项使用固定的主体、关系、客体字段。
7. 序列标注：题干给出确定的分词单元，答案长度必须与输入 token 数一致。
8. 摘要和公告分析：答案覆盖关键事实、影响方向、风险和不确定性，不断言必然股价变化。
9. 图像描述：只描述清晰可见的信息；不推测不可见原因、公司历史或未来表现。
10. 风险和投资策略：采用非个性化表述，区分可见事实、合理推断和无法确定内容。

## 8. 数据来源优先级

1. 逐条审核后合格的现有 `all.jsonl` 样本。
2. `D:\FINAR-VL-main\data\benchmark` 中任务能力真正对应的原始数据。
3. 基于可信原始金融材料自行编写的新题。

禁止从训练集 `train_text_sft.jsonl`、`train_multi.jsonl` 或 `train_align.jsonl` 复制样本进入 benchmark，以免训练评估泄漏。

自行编写题目时，事实题必须能从题干或图片直接验证；不依赖模型记忆作为答案依据。

## 9. 图片和路由规则

1. 新增图片统一放在：

   `D:\FINAR-VL-main\data\benchmark\my_benchmark\assets\<task>\`

2. JSONL 中使用相对于仓库根目录的路径，例如：

   `data/benchmark/my_benchmark/assets/chart_data_extraction/0011_01.png`

3. 新增多模态样本的 `<image>` 占位符数量必须与 `images` 数组长度一致。
4. 所有新增图片必须实际存在；不得沿用不存在的外部路径。
5. 已保留原样本可以继续使用现有图片路由。

## 10. 整理流程

1. 读取 `all.jsonl`，按任务建立候选池。
2. 为38个整理任务建立逐条审核记录，标记：保留、修复、替换、补充、剔除及原因。
3. 对“暂停使用并重建”组重新构建10条合格样本，不以凑数为目标。
4. 对数量不足的任务优先检索 `data\benchmark`，确认内容对应后再导入。
5. 对无法找到高质量来源的缺口自行编写，并逐条复核。
6. 对超过10条的任务先按质量排序剔除；全都合格仍超量时使用固定随机种子 `20260810` 抽减。
7. 合并38个整理任务、3个原样任务和 `long_document_cross_page` 原8条，生成 `all_v2.jsonl`。
8. 生成审核报告：

   `D:\FINAR-VL-main\data\benchmark\my_benchmark\all_v2_audit.md`

   报告至少列出每类原数量、保留、修复、新增、剔除、最终数量及主要问题。

## 11. 最终验证标准

1. `all_v2.jsonl` 每行均能独立解析为 JSON。
2. 共42类、418条。
3. 38个整理任务各10条。
4. 3个原样任务各10条，内容与原 `all.jsonl` 一致。
5. `long_document_cross_page` 保持原8条。
6. 所有 `messages` 至少包含 user 和 assistant，角色顺序正确。
7. 所有问题和答案非空。
8. 所有图片路由存在。
9. `<image>` 数量与 `images` 数组长度一致。
10. 无完全重复的问题与答案组合。
11. 无明显近重复、标签漂移、单位错误、非法 JSON 标准答案和图片外幻觉。
12. 原 `all.jsonl` 未发生修改。

## 12. 下一对话可直接执行的指令

将以下内容完整复制到新的 Codex 对话：

```text
请继续整理 FINAR-VL benchmark v2。首先完整阅读：

D:\FINAR-VL-main\docs\superpowers\specs\2026-08-10-benchmark-v2-curation-design.md

项目根目录：D:\FINAR-VL-main

严格按照文档执行，并遵守 D:\FINAR-VL-main\AGENTS.md。禁止开启 subagent 子智能体。

关键要求：
1. 原始文件 D:\FINAR-VL-main\data\benchmark\my_benchmark\all.jsonl 不得修改。
2. 最终生成 D:\FINAR-VL-main\data\benchmark\my_benchmark\all_v2.jsonl。
3. 同时生成 D:\FINAR-VL-main\data\benchmark\my_benchmark\all_v2_audit.md。
4. 文档规定的38个整理任务必须各10条；3个正常任务原样保留；long_document_cross_page 原8条不处理。最终应为42类、418条。
5. 不能只依靠 task、source 或 split 标签筛选。每一条保留、修复或新增数据都必须审核实际题意、标准答案和任务能力是否一致。
6. 允许从 D:\FINAR-VL-main\data\benchmark 寻找补充数据，也允许基于可信金融材料自行编写；自行编写的每条数据必须逐条复核。
7. 多模态新增数据必须有本地图片，放到 my_benchmark\assets\<task> 下，并保证 JSONL 路由存在。
8. 质量审核后仍超过10条时，使用固定随机种子20260810抽减。
9. 不得从训练集复制样本进入 benchmark。
10. 完成后运行文档第11节的全部验证，报告每类原数量、保留、修复、新增、剔除和最终数量。

开始前先只读盘点现有数据源和相关脚本，然后按文档制定实施计划并开始执行。不要重新讨论已经确认的输出文件、数量和来源权限，遇到文档没有覆盖且会实质改变结果的问题时再询问我。
```

## 13. 当前状态

- 已完成：380条原 benchmark 的字段级审阅、7个 checkpoint 的任务级比较、42类任务质量分析、整理范围确认和本设计文档。
- 尚未开始：`all_v2.jsonl` 的实际生成、图片补充、逐条重建和最终验证。
- 下一步：根据本设计编写实施计划，然后执行数据整理。
