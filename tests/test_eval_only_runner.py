from types import ModuleType, SimpleNamespace


def test_evaluate_once_uses_swift_generation_contexts(monkeypatch, tmp_path):
    import scripts.sft.run_eval_only as runner

    events = []

    class Context:
        def __init__(self, name, value=None):
            self.name = name
            self.value = value

        def __enter__(self):
            events.append(self.name + ":enter")
            return self.value

        def __exit__(self, *_):
            events.append(self.name + ":exit")

    monkeypatch.setattr(runner, "unwrap_model_for_generation", lambda model, accelerator: Context("unwrap", model))
    monkeypatch.setattr(runner, "suspend_sequence_parallel", lambda: Context("sp"))

    class Template:
        def generate_context(self):
            return Context("template")

    monkeypatch.setattr(runner, "run_distributed_evaluation", lambda **kwargs: events.append("evaluate") or {"coverage": 1.0})
    result = runner.evaluate_once(
        model=object(),
        processor=None,
        template=Template(),
        accelerator=object(),
        benchmark_path=tmp_path / "benchmark.jsonl",
        project_root=tmp_path,
        output_dir=tmp_path / "eval",
        judge_url="http://judge",
        max_samples=1,
    )

    assert result == {"coverage": 1.0}
    assert events == ["unwrap:enter", "template:enter", "sp:enter", "evaluate", "sp:exit", "template:exit", "unwrap:exit"]


def test_dsw_eval_launcher_uses_initial_model_and_reserved_gpu_layout():
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    text = (root / "scripts" / "dsw" / "run_sft_eval_debug.sh").read_text(encoding="utf-8")

    assert 'CUDA_VISIBLE_DEVICES=2,3' in text
    assert '--model "$BASE_MODEL"' in text
    assert 'BASE_MODEL="$ROOT/models/qwen4"' in text
    assert 'CUDA_VISIBLE_DEVICES=0' in text
    assert '--model "$ROOT/models/qwen4-judge"' not in text
    assert '--tensor-parallel-size 2' in text
    assert '--gpu-memory-utilization 0.5' in text
    assert '--max-num-seqs 8' in text
    assert '--max-model-len 8192' in text
    assert '--dtype bfloat16' in text
    assert 'export WANDB_DISABLED=true' in text
    assert 'export TMPDIR=/tmp' in text


def test_eval_runner_parses_model_from_swift_argv(monkeypatch, tmp_path):
    import sys
    import scripts.sft.run_eval_only as runner

    swift = ModuleType("swift")
    swift.__path__ = []
    arguments = ModuleType("swift.arguments")
    arguments.InferArguments = type("InferArguments", (), {})
    utils = ModuleType("swift.utils")
    captured = {}

    def parse_args(cls):
        captured["class"] = cls
        return SimpleNamespace(model="/mnt/nas/bihaoran/qwen3vl/models/qwen4", accelerator=object()), []

    utils.parse_args = parse_args
    pipelines = ModuleType("swift.pipelines")
    pipelines.__path__ = []
    pipelines_utils = ModuleType("swift.pipelines.utils")
    pipelines_utils.prepare_model_template = lambda args: (object(), SimpleNamespace(processor=None, generate_context=lambda: None))
    monkeypatch.setitem(sys.modules, "swift", swift)
    monkeypatch.setitem(sys.modules, "swift.arguments", arguments)
    monkeypatch.setitem(sys.modules, "swift.utils", utils)
    monkeypatch.setitem(sys.modules, "swift.pipelines", pipelines)
    monkeypatch.setitem(sys.modules, "swift.pipelines.utils", pipelines_utils)
    monkeypatch.setattr(runner, "evaluate_once", lambda **kwargs: captured.update(kwargs) or {})
    monkeypatch.setenv("QWEN3VL_ROOT", str(tmp_path))

    runner.main()

    assert captured["class"] is arguments.InferArguments
    assert captured["model"] is not None
