# Finance QA 有效输出目标设计

## 目标

本地调用魔搭 API-Inference，以两个多模态模型轮流处理输入，持续生成 Finance QA 数据，直到同一输出目录中累计得到 1500 条通过现有校验的有效输出。

有效输出数量定义为：

`accepted_multi + accepted_text`

错误、限流失败、格式不合格和质量校验未通过的结果不计入 1500 条目标。

## 命令行与默认行为

- 在 `scripts/generate_finance_qa_kimi.py` 中新增 `--target-accepted` 参数，默认值为 `1500`。
- 保留 `--max-records` 和 `--max-records-per-type`，用于显式限制扫描范围。未提供这两个限制时，程序持续读取后续数据，直到达到有效输出目标或输入耗尽。
- 默认并发数由 `4` 调整为 `1`，用户仍可通过 `--concurrency` 覆盖。
- 两个模型继续按输入顺序轮流分配，同一条输入产生的所有生成请求只调用其中一个模型。

## 输出与断点续跑

所有结果继续写入同一个 `--output-dir`：

- `raw_generations.jsonl`
- `finance_generated_multi.jsonl`
- `finance_generated_text.jsonl`
- `errors.jsonl`
- `summary.json`
- `run_config.json`

启动时读取现有有效输出数量。如果数量不足 1500，则仅处理尚未完成的输入并补足差额；达到 1500 后直接合并并退出。

生成以小批次执行。若一个已提交批次产生的有效结果超过剩余配额，只写入达到目标所需的结果，保证最终有效输出总数为 1500。

## 魔搭接口兼容修复

- 发送给魔搭的 `seed` 映射到 `1` 至 `2147483647`，避免超出服务端接受的 32 位有符号整数范围。
- 对 HTTP 429 限流错误执行有限次数的指数退避重试。
- Token 继续仅从 `MODELSCOPE_SDK_TOKEN` 环境变量读取，不写入配置、日志或输出。

## 错误处理

- 单次请求重试耗尽后写入 `errors.jsonl`，继续处理后续输入。
- 生成结果未通过现有解析或质量校验时不计入目标，继续处理后续输入。
- 输入数据耗尽但有效输出不足 1500 时，程序以非零状态结束，并在汇总中保留实际有效数量和错误数量。

## 测试

在 `tests/test_generate_finance_qa_kimi.py` 中增加以下测试：

- `--target-accepted` 和默认并发参数。
- 超范围 `seed` 被映射到合法范围。
- 429 限流错误经过有限退避后成功或按预期失败。
- 已有有效输出参与断点计数。
- 生成过程达到 1500 条后停止。
- 批次超过剩余配额时最终只保留 1500 条有效输出。
- 输入耗尽但未达到目标时返回失败状态。

运行新增测试、现有 Kimi/魔搭测试以及 `tests/test_generate_finance_qa.py`，确认原 Qwen 流程不受影响。
