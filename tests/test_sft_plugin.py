from types import SimpleNamespace


def test_format_training_log_contains_required_fields():
    from scripts.sft.swift_sft_plugin import format_training_log

    lines = format_training_log(
        step=500,
        max_steps=68815,
        epoch=0.04,
        logs={"loss": 0.25, "acc": 0.75, "grad_norm": 1.5, "learning_rate": 1e-6},
        elapsed_seconds=100.0,
        samples_per_step=28,
        memory_gib=42.0,
    )

    rendered = "\n".join(lines)
    assert "epoch=0.04 step=500/68815" in rendered
    assert "loss=0.2500 token_accuracy=0.7500" in rendered
    assert "lr=1.00e-06" in rendered
    assert "speed=" in rendered and "samples/s" in rendered and "eta=" in rendered


def test_gpu_snapshot_falls_back_when_nvidia_smi_is_unavailable(monkeypatch):
    from scripts.sft.swift_sft_plugin import _gpu_snapshot
    import subprocess

    monkeypatch.setattr(subprocess, "check_output", lambda *args, **kwargs: (_ for _ in ()).throw(OSError()))
    assert _gpu_snapshot() == "unavailable"


def test_training_log_does_not_emit_dynamic_batch(monkeypatch, capsys):
    from scripts.sft.swift_sft_plugin import FinarLogCallback

    monkeypatch.setattr("scripts.sft.swift_sft_plugin._gpu_snapshot", lambda: "gpu0:util=0% mem=1MiB")
    callback = FinarLogCallback(SimpleNamespace(), SimpleNamespace())
    state = SimpleNamespace(
        is_world_process_zero=True,
        global_step=1,
        max_steps=5,
        epoch=0.1,
    )
    callback.on_log(
        None,
        state,
        None,
        logs={"loss": 1.0, "learning_rate": 1e-6},
    )

    assert "dynamic_batch" not in capsys.readouterr().out


def test_current_samples_per_step_uses_fixed_global_batch(monkeypatch):
    from scripts.sft.swift_sft_plugin import current_samples_per_step

    monkeypatch.setenv("SFT_GLOBAL_BATCH_SIZE", "12")
    assert current_samples_per_step(SimpleNamespace()) == 12


def test_sequence_parallel_is_suspended_and_restored_for_pass_at_k(monkeypatch):
    from scripts.sft.swift_sft_plugin import suspend_sequence_parallel
    import sys
    from types import ModuleType

    fake_sp = SimpleNamespace(world_size=2)
    fake_swift = ModuleType("swift")
    fake_swift.__path__ = []
    fake_module = ModuleType("swift.sequence_parallel")
    fake_module.sequence_parallel = fake_sp
    monkeypatch.setitem(sys.modules, "swift", fake_swift)
    monkeypatch.setitem(sys.modules, "swift.sequence_parallel", fake_module)

    with suspend_sequence_parallel():
        assert fake_sp.world_size == 1
    assert fake_sp.world_size == 2


def test_evaluation_schedule_runs_at_zero_interval_and_final_step():
    from scripts.sft.swift_sft_plugin import should_run_pass_at_8

    assert should_run_pass_at_8(0, 68815, 500) is True
    assert should_run_pass_at_8(500, 68815, 500) is True
    assert should_run_pass_at_8(501, 68815, 500) is False
    assert should_run_pass_at_8(68815, 68815, 500) is True


def test_step_zero_metrics_are_deferred_until_progress_callback_is_initialized(monkeypatch, tmp_path):
    import scripts.sft.pass_at_8_eval as pass_at_8_eval
    from scripts.sft.swift_sft_plugin import FinarPassAt8Callback

    monkeypatch.setenv("SFT_EVAL_STEPS", "500")
    monkeypatch.setenv("SFT_EVAL_AT_ZERO", "true")
    monkeypatch.setenv("SFT_BENCHMARK", str(tmp_path / "benchmark.jsonl"))
    monkeypatch.setenv("QWEN3VL_ROOT", str(tmp_path))
    monkeypatch.setenv("SFT_JUDGE_URL", "http://judge")
    monkeypatch.setattr(
        pass_at_8_eval,
        "run_distributed_evaluation",
        lambda **kwargs: {"pass_at_1": 0.25, "pass_at_8": 0.5, "coverage": 1.0, "error_count": 0},
    )

    class FakeProgress:
        def on_log(self):
            assert hasattr(self, "start_time"), "ProgressCallbackNew was not initialized"

    progress = FakeProgress()
    logs = []

    def trainer_log(payload):
        progress.on_log()
        logs.append(payload)

    callback = object.__new__(FinarPassAt8Callback)
    callback.args = SimpleNamespace(output_dir=str(tmp_path / "output"))
    callback.trainer = SimpleNamespace(model=object(), processor=None, template=None, log=trainer_log)
    callback.last_step = None
    callback.pending_metrics = None
    state = SimpleNamespace(global_step=0, max_steps=5)

    callback.on_train_begin(None, state, None)
    assert logs == []
    assert callback.pending_metrics == {
        "eval_pass_at_1": 0.25,
        "eval_pass_at_8": 0.5,
        "eval_coverage": 1.0,
        "eval_error_count": 0,
    }

    progress.start_time = 1.0
    callback.on_step_begin(None, state, None)
    callback.on_step_begin(None, state, None)
    assert logs == [{
        "eval_pass_at_1": 0.25,
        "eval_pass_at_8": 0.5,
        "eval_coverage": 1.0,
        "eval_error_count": 0,
    }]
    assert callback.pending_metrics is None


def test_nonzero_step_metrics_are_logged_immediately(monkeypatch, tmp_path):
    import scripts.sft.pass_at_8_eval as pass_at_8_eval
    from scripts.sft.swift_sft_plugin import FinarPassAt8Callback

    monkeypatch.setenv("SFT_EVAL_STEPS", "500")
    monkeypatch.setenv("SFT_EVAL_AT_ZERO", "true")
    monkeypatch.setenv("SFT_BENCHMARK", str(tmp_path / "benchmark.jsonl"))
    monkeypatch.setenv("QWEN3VL_ROOT", str(tmp_path))
    monkeypatch.setenv("SFT_JUDGE_URL", "http://judge")
    monkeypatch.setattr(
        pass_at_8_eval,
        "run_distributed_evaluation",
        lambda **kwargs: {"pass_at_1": 0.75, "pass_at_8": 1.0},
    )
    logs = []
    callback = object.__new__(FinarPassAt8Callback)
    callback.args = SimpleNamespace(output_dir=str(tmp_path / "output"))
    callback.trainer = SimpleNamespace(model=object(), processor=None, template=None, log=logs.append)
    callback.last_step = None
    callback.pending_metrics = None

    callback._run(SimpleNamespace(global_step=500, max_steps=1000), defer_log=False)

    assert logs == [{"eval_pass_at_1": 0.75, "eval_pass_at_8": 1.0}]
    assert callback.pending_metrics is None


def test_pass_at_k_uses_unwrapped_model_and_template_generation_context(monkeypatch, tmp_path):
    import sys
    import types
    import scripts.sft.pass_at_8_eval as pass_at_8_eval
    from scripts.sft.swift_sft_plugin import FinarPassAt8Callback

    monkeypatch.setenv("SFT_EVAL_STEPS", "500")
    monkeypatch.setenv("SFT_EVAL_AT_ZERO", "true")
    monkeypatch.setenv("SFT_BENCHMARK", str(tmp_path / "benchmark.jsonl"))
    monkeypatch.setenv("QWEN3VL_ROOT", str(tmp_path))
    monkeypatch.setenv("SFT_JUDGE_URL", "http://judge")
    events = []

    class Context:
        def __init__(self, value=None):
            self.value = value

        def __enter__(self):
            events.append("enter")
            return self.value

        def __exit__(self, *_):
            events.append("exit")

    fake_utils = types.ModuleType("swift.utils")
    fake_utils.unwrap_model_for_generation = lambda model, accelerator: Context("unwrapped")
    monkeypatch.setitem(sys.modules, "swift.utils", fake_utils)

    class Template:
        def generate_context(self):
            return Context()

    captured = {}

    def evaluate(**kwargs):
        captured.update(kwargs)
        events.append("evaluate")
        return {"pass_at_1": 0.0, "pass_at_8": 0.0}

    monkeypatch.setattr(pass_at_8_eval, "run_distributed_evaluation", evaluate)
    callback = object.__new__(FinarPassAt8Callback)
    callback.args = SimpleNamespace(output_dir=str(tmp_path / "output"))
    callback.trainer = SimpleNamespace(
        model="wrapped",
        model_wrapped="wrapped",
        accelerator=object(),
        processor="processor",
        template=Template(),
        log=lambda payload: None,
    )
    callback.last_step = None
    callback.pending_metrics = None

    callback._run(SimpleNamespace(global_step=500, max_steps=1000), defer_log=True)

    assert captured["model"] == "unwrapped"
    assert events == ["enter", "enter", "evaluate", "exit", "exit"]


def test_pass_at_k_callback_retries_final_evaluation_at_train_end(monkeypatch):
    from scripts.sft.swift_sft_plugin import FinarPassAt8Callback

    callback = object.__new__(FinarPassAt8Callback)
    calls = []
    callback._run = lambda state: calls.append(state.global_step)

    state = SimpleNamespace(global_step=5)
    callback.on_train_end(None, state, None)

    assert calls == [5]


def test_checkpoint_state_file_detector_rejects_training_state(tmp_path):
    from scripts.sft.swift_sft_plugin import find_training_state_files

    (tmp_path / "model.safetensors").write_text("model", encoding="utf-8")
    (tmp_path / "optimizer.pt").write_text("state", encoding="utf-8")

    assert find_training_state_files(tmp_path) == ["optimizer.pt"]


def test_checkpoint_cleanup_removes_training_state_but_preserves_model_files(tmp_path):
    from scripts.sft.swift_sft_plugin import remove_training_state_files

    (tmp_path / "model.safetensors").write_text("model", encoding="utf-8")
    (tmp_path / "trainer_state.json").write_text("state", encoding="utf-8")
    (tmp_path / "rng_state_0.pth").write_text("rng", encoding="utf-8")

    assert remove_training_state_files(tmp_path) == ["rng_state_0.pth", "trainer_state.json"]
    assert (tmp_path / "model.safetensors").is_file()
    assert not (tmp_path / "trainer_state.json").exists()
    assert not (tmp_path / "rng_state_0.pth").exists()
