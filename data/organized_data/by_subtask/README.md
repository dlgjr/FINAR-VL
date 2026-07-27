# 按统一子任务组织的 Benchmark 数据

该目录由 `classify_benchmark_subtasks.py` 从原有模态清单派生。媒体路径仍相对于 `organized_data/`，原数据及模态目录未改变。

每个子任务目录的 `manifest.jsonl` 是互斥主分类；`tagged.jsonl` 还包括将该子任务作为辅助能力标签的样本。

分类定义、映射边界和全量统计见 `../reports/subtask_classification.md`。
