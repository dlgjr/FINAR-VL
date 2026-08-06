# Token-budget Dynamic Batch Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 DSW SFT 中按真实编码 token 长度使用4/2/1动态 batch，并在模型前向传播前跳过超过49152 token 的样本。

**Architecture:** 新增独立的纯 Python 分桶与批次规划模块，由 ms-swift 外部插件在 DSW 环境变量启用时替换训练 dataloader。规划器先读取 LazyLLMDataset 的真实编码长度，再按桶内 batch 大小构造可复现批次；DLC 默认不启用。

**Tech Stack:** Python 3.12、PyTorch DataLoader、ms-swift 4.4.2、Transformers Trainer、pytest、Bash

---

### Task 1: 实现纯分桶规则与可复现批次规划

**Files:**
- Create: `scripts/sft/token_budget_batch.py`
- Create: `tests/test_token_budget_batch.py`

- [ ] **Step 1: 写分桶规则失败测试**

```python
from scripts.sft.token_budget_batch import batch_size_for_length


def test_batch_size_for_length_uses_confirmed_boundaries():
    assert batch_size_for_length(1) == 4
    assert batch_size_for_length(8192) == 4
    assert batch_size_for_length(8193) == 2
    assert batch_size_for_length(32768) == 2
    assert batch_size_for_length(32769) == 1
    assert batch_size_for_length(49152) == 1
    assert batch_size_for_length(49153) is None
```

- [ ] **Step 2: 运行测试并确认因模块不存在而失败**

Run: `python -m pytest tests/test_token_budget_batch.py::test_batch_size_for_length_uses_confirmed_boundaries -q`

Expected: FAIL，提示 `ModuleNotFoundError`。

- [ ] **Step 3: 实现最小分桶函数**

```python
def batch_size_for_length(length: int) -> int | None:
    if length <= 0:
        raise ValueError("token length must be positive")
    if length <= 8192:
        return 4
    if length <= 32768:
        return 2
    if length <= 49152:
        return 1
    return None
```

- [ ] **Step 4: 写批次规划失败测试**

```python
from scripts.sft.token_budget_batch import TokenBudgetBatchPlan


def test_plan_batches_by_bucket_without_duplicates():
    plan = TokenBudgetBatchPlan.from_lengths(
        [100, 200, 300, 400, 9000, 10000, 40000, 60000], seed=42
    )
    batches = plan.batches_for_epoch(0)
    assert sorted(index for batch in batches for index in batch) == list(range(7))
    assert sorted(len(batch) for batch in batches) == [1, 2, 4]
    assert plan.skipped_indices == [7]


def test_plan_is_reproducible_and_changes_between_epochs():
    plan = TokenBudgetBatchPlan.from_lengths(list(range(1, 33)), seed=42)
    assert plan.batches_for_epoch(0) == plan.batches_for_epoch(0)
    assert plan.batches_for_epoch(0) != plan.batches_for_epoch(1)
```

- [ ] **Step 5: 实现计划对象和 epoch 打乱**

实现 `TokenBudgetBatchPlan`，保存三个有效桶、跳过索引、固定 seed；每个 epoch 使用 `random.Random(seed + epoch)` 分别打乱桶内索引、按对应 batch 切片，再打乱批次列表。最后不足一个完整 batch 的样本也作为较小 batch 保留。

- [ ] **Step 6: 运行单元测试**

Run: `python -m pytest tests/test_token_budget_batch.py -q`

Expected: 全部 PASS。

### Task 2: 扫描 ms-swift 数据集真实编码长度

**Files:**
- Modify: `scripts/sft/token_budget_batch.py`
- Modify: `tests/test_token_budget_batch.py`

- [ ] **Step 1: 写长度提取失败测试**

```python
from scripts.sft.token_budget_batch import encoded_length


def test_encoded_length_accepts_lengths_and_input_ids():
    assert encoded_length({"lengths": [7, 9]}) == 9
    assert encoded_length({"input_ids": [1, 2, 3]}) == 3
```

- [ ] **Step 2: 运行测试确认函数缺失**

Run: `python -m pytest tests/test_token_budget_batch.py::test_encoded_length_accepts_lengths_and_input_ids -q`

Expected: FAIL，提示无法导入 `encoded_length`。

- [ ] **Step 3: 实现长度提取与扫描**

实现：

```python
def encoded_length(item: dict) -> int:
    lengths = item.get("lengths")
    if lengths is not None:
        return max(int(value) for value in lengths)
    return len(item["input_ids"])


def scan_dataset_lengths(dataset) -> list[int]:
    return [encoded_length(dataset[index]) for index in range(len(dataset))]
```

扫描时让数据集沿用 ms-swift 自身 template 编码，确保图片 token 和文本 token 的处理与训练一致。

- [ ] **Step 4: 写并运行假数据集扫描测试**

使用实现 `__len__`、`__getitem__` 的内存假数据集，断言扫描顺序稳定且每个索引只读取一次。

Run: `python -m pytest tests/test_token_budget_batch.py -q`

Expected: 全部 PASS。

### Task 3: 接入 Trainer dataloader

**Files:**
- Modify: `scripts/sft/token_budget_batch.py`
- Modify: `scripts/sft/swift_sft_plugin.py`
- Modify: `tests/test_token_budget_batch.py`
- Modify: `tests/test_sft_plugin.py`

- [ ] **Step 1: 写 BatchSampler 失败测试**

创建 `TokenBudgetBatchSampler`，测试 `set_epoch()`、`__iter__()`、`__len__()`，并断言 epoch 0 的所有索引无重复、跳过索引不出现。

- [ ] **Step 2: 实现 BatchSampler**

`TokenBudgetBatchSampler` 包装 `TokenBudgetBatchPlan`；`__iter__` 返回当前 epoch 的索引列表，`set_epoch` 更新 epoch，`__len__` 返回当前 epoch 批次数。

- [ ] **Step 3: 写插件启用条件失败测试**

```python
def test_dynamic_batch_is_dsw_only(monkeypatch):
    monkeypatch.delenv("SFT_TOKEN_BUDGET_BATCH", raising=False)
    assert token_budget_batch_enabled() is False
    monkeypatch.setenv("SFT_TOKEN_BUDGET_BATCH", "true")
    assert token_budget_batch_enabled() is True
```

- [ ] **Step 4: 实现 DSW 条件接入**

在 `swift_sft_plugin.py` 增加 `FinarTokenBudgetCallback`。callback 初始化时仅在 `SFT_TOKEN_BUDGET_BATCH=true` 时：

1. 扫描 `trainer.train_dataset`；
2. 构建 `TokenBudgetBatchPlan`；
3. 保存统计信息到 callback；
4. 用实例方法替换 `trainer.get_train_dataloader`，使用原 trainer 的 `data_collator`、worker、pin-memory 配置和 `TokenBudgetBatchSampler` 创建 PyTorch DataLoader；
5. 不设置该环境变量时保持原 dataloader 完全不变。

- [ ] **Step 5: 注册 callback 并运行测试**

注册名为 `finar_token_budget_batch`，使用轻量 fake trainer 验证启用和禁用两条路径。

Run: `python -m pytest tests/test_token_budget_batch.py tests/test_sft_plugin.py -q`

Expected: 全部 PASS。

### Task 4: 增加动态 batch 日志

**Files:**
- Modify: `scripts/sft/token_budget_batch.py`
- Modify: `scripts/sft/swift_sft_plugin.py`
- Modify: `tests/test_token_budget_batch.py`

- [ ] **Step 1: 写统计摘要失败测试**

断言长度 `[100, 200, 9000, 40000, 60000]` 输出三个有效桶各自样本数、批次数、跳过数1、有效样本数4。

- [ ] **Step 2: 实现 `summary()`**

返回 JSON 可序列化字典，字段固定为：`short_samples`、`medium_samples`、`long_samples`、`skipped_samples`、`effective_samples`、`total_batches`。

- [ ] **Step 3: 输出启动日志**

callback 初始化后只在 world process zero 打印：

```text
INFO     | >> token_budget_batch short<=8192 batch=4 samples=...
             medium<=32768 batch=2 samples=...
             long<=49152 batch=1 samples=...
             skipped>49152 samples=... effective=... batches=...
```

将同一摘要写入 `<output_dir>/token_budget_batch_summary.json`。

- [ ] **Step 4: 运行日志测试**

Run: `python -m pytest tests/test_token_budget_batch.py tests/test_sft_plugin.py -q`

Expected: 全部 PASS。

### Task 5: 更新 DSW 启动配置

**Files:**
- Modify: `scripts/dsw/run_sft_debug.sh`
- Modify: `tests/test_sft_launchers.py`

- [ ] **Step 1: 写启动配置失败测试**

要求脚本包含：

```text
SFT_TOKEN_BUDGET_BATCH=true
--per_device_train_batch_size 1
--gradient_accumulation_steps 1
--max_length 81920
--callbacks finar_log finar_pass_at_8 finar_token_budget_batch
```

并确认 DLC 脚本不包含 `finar_token_budget_batch`。

- [ ] **Step 2: 运行测试确认失败**

Run: `python -m pytest tests/test_sft_launchers.py -q`

Expected: FAIL，缺少动态 batch 环境变量和 callback。

- [ ] **Step 3: 修改 DSW 脚本**

设置 `SFT_TOKEN_BUDGET_BATCH=true`，梯度累积改回1，保持81920扫描上限，注册动态 callback；启动日志打印三档 batch 和跳过边界。DLC 文件保持固定 batch=1。

- [ ] **Step 4: 运行启动脚本测试**

Run: `python -m pytest tests/test_sft_launchers.py -q`

Expected: 全部 PASS。

### Task 6: 回归验证

**Files:**
- Verify: `scripts/sft/token_budget_batch.py`
- Verify: `scripts/sft/swift_sft_plugin.py`
- Verify: `scripts/dsw/run_sft_debug.sh`

- [ ] **Step 1: 运行全部相关测试**

Run: `python -m pytest tests/test_token_budget_batch.py tests/test_sft_plugin.py tests/test_sft_pass_at_8.py tests/test_sft_launchers.py -q`

Expected: 0 failures。

- [ ] **Step 2: 运行 Python 语法检查**

Run: `python -m py_compile scripts/sft/token_budget_batch.py scripts/sft/swift_sft_plugin.py scripts/sft/pass_at_8_eval.py`

Expected: exit code 0。

- [ ] **Step 3: 检查改动范围**

Run: `git status --short -- scripts/sft/token_budget_batch.py scripts/sft/swift_sft_plugin.py scripts/dsw/run_sft_debug.sh tests/test_token_budget_batch.py tests/test_sft_plugin.py tests/test_sft_launchers.py`

Expected: 只显示计划内文件。

- [ ] **Step 4: DSW 实机验收**

同步脚本后运行 `bash scripts/dsw/run_sft_debug.sh`，确认启动摘要存在、72k样本计入 skipped、5 step 完成且无 OOM，并保存显存峰值和吞吐日志。

