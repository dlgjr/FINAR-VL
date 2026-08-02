import json
import math
import sys
from types import ModuleType, SimpleNamespace

import pytest


class FakeTensor:
    def __init__(self, values, shape, dtype="int64"):
        self.values, self.shape, self.dtype = list(values), shape, dtype
    def ne(self, value):
        return FakeTensor([item != value for item in self.values], self.shape, "bool")
    def numel(self):
        return len(self.values)


class FakeScalar:
    def __init__(self, value): self.value = value
    def item(self): return self.value
    def __bool__(self): return bool(self.value)
    def __and__(self, other): return FakeScalar(bool(self) and bool(other))


class FakeHookHandle:
    def __init__(self): self.removed = False
    def remove(self): self.removed = True


class FakeParameter:
    def __init__(self, data=1.0):
        self.requires_grad = True
        self.data = FakeScalar(data)
        self.grad = None
        self.hooks = []
        self.handles = []

    def register_hook(self, hook):
        self.hooks.append(hook)
        handle = FakeHookHandle()
        self.handles.append(handle)
        return handle

    def emit(self, grad):
        self.grad = grad
        for hook in self.hooks:
            hook(grad)


def install_fake_torch(monkeypatch):
    module = ModuleType("torch")
    module.is_tensor = lambda value: isinstance(value, (FakeTensor, FakeScalar))
    module.count_nonzero = lambda value: FakeScalar(sum(bool(item) for item in value.values))
    module.isfinite = lambda value: FakeScalar(math.isfinite(value.item()))
    monkeypatch.setitem(sys.modules, "torch", module)


def test_numerics_guard_records_selected_step_tensor_metadata(tmp_path, monkeypatch):
    install_fake_torch(monkeypatch)
    from scripts.sft.swift_sft_plugin import FinarNumericsCallback
    monkeypatch.setenv("SFT_TRACE_STEPS", "234,1303")
    trainer = SimpleNamespace(args=SimpleNamespace(output_dir=str(tmp_path)), state=SimpleNamespace(global_step=233))
    trainer.compute_loss = lambda model, inputs, **kwargs: FakeScalar(1.25)
    FinarNumericsCallback(SimpleNamespace(output_dir=str(tmp_path)), trainer)
    loss = trainer.compute_loss(object(), {"input_ids": FakeTensor([1] * 32, (2, 16)),
                                            "labels": FakeTensor([-100] * 12 + [1] * 4 + [-100] * 8 + [2] * 8, (2, 16))})
    assert loss.item() == pytest.approx(1.25)
    trace = json.loads((tmp_path / "train_trace" / "step-000234" / "rank-0000.json").read_text(encoding="utf-8"))
    assert trace["valid_labels"] == 12 and trace["loss_finite"] is True


def test_numerics_guard_records_and_stops_on_nonfinite_loss(tmp_path, monkeypatch):
    install_fake_torch(monkeypatch)
    from scripts.sft.swift_sft_plugin import FinarNumericsCallback
    monkeypatch.delenv("SFT_TRACE_STEPS", raising=False)
    trainer = SimpleNamespace(args=SimpleNamespace(output_dir=str(tmp_path)), state=SimpleNamespace(global_step=233))
    trainer.compute_loss = lambda model, inputs, **kwargs: FakeScalar(float("nan"))
    FinarNumericsCallback(SimpleNamespace(output_dir=str(tmp_path)), trainer)
    with pytest.raises(FloatingPointError, match="attempted_step=234"):
        trainer.compute_loss(object(), {"labels": FakeTensor([-100, 7], (1, 2))})


def test_numerics_trace_keeps_labels_when_compute_loss_consumes_inputs(tmp_path, monkeypatch):
    install_fake_torch(monkeypatch)
    from scripts.sft.swift_sft_plugin import FinarNumericsCallback

    monkeypatch.setenv("SFT_TRACE_STEPS", "234")
    trainer = SimpleNamespace(args=SimpleNamespace(output_dir=str(tmp_path)), state=SimpleNamespace(global_step=233))

    def compute_loss(model, inputs, **kwargs):
        inputs.pop("labels")
        return FakeScalar(1.0)

    trainer.compute_loss = compute_loss
    FinarNumericsCallback(SimpleNamespace(output_dir=str(tmp_path)), trainer)
    trainer.compute_loss(object(), {"labels": FakeTensor([-100, 7, 8], (1, 3))})
    trace = json.loads((tmp_path / "train_trace" / "step-000234" / "rank-0000.json").read_text(encoding="utf-8"))
    assert trace["valid_labels"] == 2


def test_numerics_trace_records_optimizer_finiteness_fields(tmp_path, monkeypatch):
    install_fake_torch(monkeypatch)
    from scripts.sft.swift_sft_plugin import FinarNumericsCallback

    monkeypatch.setenv("SFT_TRACE_STEPS", "234")
    trainer = SimpleNamespace(
        args=SimpleNamespace(output_dir=str(tmp_path)),
        state=SimpleNamespace(global_step=233, max_steps=10),
        model=SimpleNamespace(parameters=lambda: []),
    )
    trainer.compute_loss = lambda model, inputs, **kwargs: FakeScalar(1.0)
    callback = FinarNumericsCallback(SimpleNamespace(output_dir=str(tmp_path)), trainer)
    inputs = {"labels": FakeTensor([1], (1, 1))}
    trainer.compute_loss(object(), inputs)
    callback.on_pre_optimizer_step(trainer.args, trainer.state, None, optimizer=None)
    trainer.state.global_step = 234
    callback.on_step_end(trainer.args, trainer.state, None)
    trace = json.loads((tmp_path / "train_trace" / "step-000234" / "rank-0000.json").read_text(encoding="utf-8"))
    assert "forward_loss" in trace
    assert "gradient_finite" in trace
    assert "parameters_finite_before" in trace
    assert "parameters_finite_after" in trace


def test_numerics_rank_status_records_progress_fields(tmp_path, monkeypatch):
    install_fake_torch(monkeypatch)
    from scripts.sft.swift_sft_plugin import FinarNumericsCallback

    trainer = SimpleNamespace(
        args=SimpleNamespace(output_dir=str(tmp_path)),
        state=SimpleNamespace(global_step=0, max_steps=3),
    )
    trainer.compute_loss = lambda model, inputs, **kwargs: FakeScalar(1.0)
    callback = FinarNumericsCallback(SimpleNamespace(output_dir=str(tmp_path)), trainer)
    monkeypatch.setenv("SFT_TRACE_STEPS", "1")
    trainer.compute_loss(object(), {"input_ids": FakeTensor([1, 2], (1, 2)), "labels": FakeTensor([1, -100], (1, 2))})
    callback.on_step_begin(trainer.args, trainer.state, None)
    trainer.state.global_step = 1
    callback.on_step_end(trainer.args, trainer.state, None)
    status = json.loads((tmp_path / "train_trace" / "rank-0000.status.json").read_text(encoding="utf-8"))
    assert {"planned", "completed", "remaining", "heartbeat", "errors", "current_sample"} <= status.keys()
    assert status["current_sample"] is not None


def test_rank_status_updates_current_sample_on_nontrace_step(tmp_path, monkeypatch):
    install_fake_torch(monkeypatch)
    from scripts.sft.swift_sft_plugin import FinarNumericsCallback

    monkeypatch.setenv("SFT_TRACE_STEPS", "999")
    trainer = SimpleNamespace(
        args=SimpleNamespace(output_dir=str(tmp_path)),
        state=SimpleNamespace(global_step=0, max_steps=2),
    )
    trainer.compute_loss = lambda model, inputs, **kwargs: FakeScalar(1.0)
    callback = FinarNumericsCallback(SimpleNamespace(output_dir=str(tmp_path)), trainer)
    trainer.compute_loss(object(), {"input_ids": FakeTensor([1, 2], (1, 2)), "labels": FakeTensor([1, -100], (1, 2))})
    callback.on_step_end(trainer.args, trainer.state, None)
    status = json.loads((tmp_path / "train_trace" / "rank-0000.status.json").read_text(encoding="utf-8"))
    assert status["current_sample"]["valid_labels"] == 1


def _hook_trainer(tmp_path, parameter):
    trainer = SimpleNamespace(
        args=SimpleNamespace(output_dir=str(tmp_path)),
        state=SimpleNamespace(global_step=233, max_steps=10),
        model=SimpleNamespace(parameters=lambda: [parameter]),
    )
    trainer.compute_loss = lambda model, inputs, **kwargs: FakeScalar(1.0)
    return trainer


def test_trace_step_hooks_observe_finite_gradients_and_remove_handles(tmp_path, monkeypatch):
    install_fake_torch(monkeypatch)
    from scripts.sft.swift_sft_plugin import FinarNumericsCallback

    monkeypatch.setenv("SFT_TRACE_STEPS", "234")
    parameter = FakeParameter()
    trainer = _hook_trainer(tmp_path, parameter)
    callback = FinarNumericsCallback(trainer.args, trainer)
    trainer.compute_loss(trainer.model, {"labels": FakeTensor([1], (1, 1))})
    assert len(parameter.hooks) == 1
    parameter.emit(FakeScalar(1.0))
    callback.on_pre_optimizer_step(trainer.args, trainer.state, None, optimizer=None)
    trace = json.loads((tmp_path / "train_trace" / "step-000234" / "rank-0000.json").read_text(encoding="utf-8"))
    assert trace["gradient_finite"] is True
    assert parameter.handles[0].removed is True


def test_trace_step_raises_before_optimizer_on_nonfinite_gradient(tmp_path, monkeypatch):
    install_fake_torch(monkeypatch)
    from scripts.sft.swift_sft_plugin import FinarNumericsCallback

    monkeypatch.setenv("SFT_TRACE_STEPS", "234")
    parameter = FakeParameter()
    trainer = _hook_trainer(tmp_path, parameter)
    callback = FinarNumericsCallback(trainer.args, trainer)
    trainer.compute_loss(trainer.model, {"labels": FakeTensor([1], (1, 1))})
    parameter.emit(FakeScalar(float("nan")))
    with pytest.raises(FloatingPointError, match="non-finite gradient"):
        callback.on_pre_optimizer_step(trainer.args, trainer.state, None, optimizer=None)
    trace = json.loads((tmp_path / "train_trace" / "step-000234" / "rank-0000.json").read_text(encoding="utf-8"))
    status = json.loads((tmp_path / "train_trace" / "rank-0000.status.json").read_text(encoding="utf-8"))
    assert trace["gradient_finite"] is False
    assert status["errors"] == 1
    assert parameter.handles[0].removed is True


def test_trace_step_records_null_when_no_gradient_hook_fires(tmp_path, monkeypatch):
    install_fake_torch(monkeypatch)
    from scripts.sft.swift_sft_plugin import FinarNumericsCallback

    monkeypatch.setenv("SFT_TRACE_STEPS", "234")
    parameter = FakeParameter()
    trainer = _hook_trainer(tmp_path, parameter)
    callback = FinarNumericsCallback(trainer.args, trainer)
    trainer.compute_loss(trainer.model, {"labels": FakeTensor([1], (1, 1))})
    callback.on_pre_optimizer_step(trainer.args, trainer.state, None, optimizer=None)
    trace = json.loads((tmp_path / "train_trace" / "step-000234" / "rank-0000.json").read_text(encoding="utf-8"))
    assert trace["gradient_finite"] is None


def test_trace_step_raises_on_nonfinite_parameters_before_optimizer(tmp_path, monkeypatch):
    install_fake_torch(monkeypatch)
    from scripts.sft.swift_sft_plugin import FinarNumericsCallback

    monkeypatch.setenv("SFT_TRACE_STEPS", "234")
    parameter = FakeParameter(data=float("nan"))
    trainer = _hook_trainer(tmp_path, parameter)
    callback = FinarNumericsCallback(trainer.args, trainer)
    trainer.compute_loss(trainer.model, {"labels": FakeTensor([1], (1, 1))})
    with pytest.raises(FloatingPointError, match="non-finite parameters before"):
        callback.on_pre_optimizer_step(trainer.args, trainer.state, None, optimizer=None)


def test_trace_step_raises_on_nonfinite_parameters_after_optimizer(tmp_path, monkeypatch):
    install_fake_torch(monkeypatch)
    from scripts.sft.swift_sft_plugin import FinarNumericsCallback

    monkeypatch.setenv("SFT_TRACE_STEPS", "234")
    parameter = FakeParameter()
    trainer = _hook_trainer(tmp_path, parameter)
    callback = FinarNumericsCallback(trainer.args, trainer)
    trainer.compute_loss(trainer.model, {"labels": FakeTensor([1], (1, 1))})
    parameter.emit(FakeScalar(1.0))
    callback.on_pre_optimizer_step(trainer.args, trainer.state, None, optimizer=None)
    parameter.data = FakeScalar(float("nan"))
    trainer.state.global_step = 234
    with pytest.raises(FloatingPointError, match="non-finite parameters after"):
        callback.on_step_end(trainer.args, trainer.state, None)
    trace = json.loads((tmp_path / "train_trace" / "step-000234" / "rank-0000.json").read_text(encoding="utf-8"))
    assert trace["parameters_finite_after"] is False


def test_nontrace_step_does_not_register_gradient_hooks(tmp_path, monkeypatch):
    install_fake_torch(monkeypatch)
    from scripts.sft.swift_sft_plugin import FinarNumericsCallback

    monkeypatch.setenv("SFT_TRACE_STEPS", "999")
    parameter = FakeParameter()
    trainer = _hook_trainer(tmp_path, parameter)
    FinarNumericsCallback(trainer.args, trainer)
    trainer.compute_loss(trainer.model, {"labels": FakeTensor([1], (1, 1))})
    assert parameter.hooks == []
