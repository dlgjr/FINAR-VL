# FINAR-VL Evaluation

This directory provides a unified public-benchmark launcher following the same high-level pattern used by Innovator-VL: one entry script groups benchmarks and delegates scoring to benchmark-specific evaluation code.

## Entry point

```bash
MODEL_NAME=FINAR-VL-4B \
API_BASE=http://127.0.0.1:8000/v1 \
API_KEY=EMPTY \
bash evaluation/evaluate.sh
```

The launcher covers the 12 benchmarks reported in the FINAR-VL performance figure:

- Financial QA / chart reasoning: FAMMA, FinChart-Bench, FinMME, FinMMR
- Comprehensive financial multimodal evaluation: FinMTM, MME-Finance, VisFinEval, XFinBench
- Long-document / document-level reasoning: CFMME, FinMMDocR, FinDocMRE, FinEval-MM

## Design

`evaluation/run.py` reads `evaluation/benchmarks.json` and runs each benchmark from its official repository or evaluator. Model serving is standardized through `MODEL_NAME`, `API_BASE`, and `API_KEY` so benchmark adapters can target the same OpenAI-compatible FINAR-VL endpoint.

Each benchmark root is supplied through an environment variable, for example:

```bash
FINMMR_ROOT=/path/to/FinMMR
VISFINEVAL_ROOT=/path/to/VisFinEval
XFINBENCH_ROOT=/path/to/XFinBench
```

Benchmarks whose official repositories require benchmark-specific model configuration use a command environment variable. For example:

```bash
FAMMA_ROOT=/path/to/bench-script
FAMMA_EVAL_CMD="python main_scripts/step_2_generate_ans.py --config_dir configs/finar_gen.yaml && python main_scripts/step_3_eval_ans.py --config_dir configs/finar_eval.yaml"
```

This keeps benchmark-specific scoring in the official evaluator instead of reimplementing metrics in FINAR-VL.

## Official evaluators currently registered

| Benchmark | Official source | Launcher mode |
|---|---|---|
| FAMMA | famma-bench/bench-script | command adapter |
| FinChart-Bench | Tizzzzy/FinChart-Bench | command adapter |
| FinMME | luo-junyu/FinMME | command adapter |
| FinMMR | BUPT-Reasoning-Lab/FinMMR | official inference + evaluation scripts |
| FinMTM | HiThink-Research/FinMTM | command adapter |
| MME-Finance | HiThink-Research/MME-Finance | command adapter |
| VisFinEval | SUFE-AIFLM-Lab/VisFinEval | official `run_model.sh` |
| XFinBench | Zhihan72/XFinBench | official `run_evaluate.sh` |
| FinMMDocR | BUPT-Reasoning-Lab/FinMMDocR | command adapter |

CFMME, FinDocMRE, and FinEval-MM remain configurable through external command adapters until their public evaluator entry points are fixed in the registry.
