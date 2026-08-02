"""ms-swift 外部插件：统一 SFT 日志、Pass@8 调度与检查点审计。"""

from __future__ import annotations

import os
import json
import math
import subprocess
import time
from contextlib import contextmanager, nullcontext
from pathlib import Path
from typing import Any


def _format_seconds(seconds: float) -> str:
    seconds = max(0, int(seconds))
    return f"{seconds // 3600:02d}:{seconds % 3600 // 60:02d}:{seconds % 60:02d}"


def _gpu_snapshot() -> str:
    try:
        output = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=utilization.gpu,memory.used", "--format=csv,noheader,nounits"],
            text=True,
            timeout=3,
        )
    except (OSError, subprocess.SubprocessError):
        return "unavailable"
    return ";".join(
        f"gpu{index}:util={parts[0].strip()}% mem={parts[1].strip()}MiB"
        for index, line in enumerate(output.splitlines())
        if len(parts := line.split(",")) == 2
    ) or "unavailable"


def format_training_log(
    *,
    step: int,
    max_steps: int,
    epoch: float,
    logs: dict[str, Any],
    elapsed_seconds: float,
    samples_per_step: int,
    memory_gib: float | None,
) -> list[str]:
    steps_per_second = step / elapsed_seconds if elapsed_seconds else 0.0
    samples_per_second = steps_per_second * samples_per_step
    eta = (max_steps - step) / steps_per_second if steps_per_second else 0.0
    loss = float(logs.get("loss", 0.0))
    accuracy = float(logs.get("acc", logs.get("token_accuracy", 0.0)))
    grad_norm = float(logs.get("grad_norm", 0.0))
    lr = float(logs.get("learning_rate", logs.get("lr", 0.0)))
    memory = "" if memory_gib is None else f" memory={memory_gib:.2f}GiB"
    return [
        f"INFO     | >> epoch={epoch:.2f} step={step}/{max_steps}",
        f"             loss={loss:.4f} token_accuracy={accuracy:.4f} grad_norm={grad_norm:.4f}",
        f"             lr={lr:.2e}{memory}",
        f"             speed={steps_per_second:.2f} step/s, {samples_per_second:.2f} samples/s eta={_format_seconds(eta)}",
    ]


def should_run_pass_at_8(step: int, max_steps: int, interval: int) -> bool:
    return step == 0 or step == max_steps or (step > 0 and step % interval == 0)


def find_training_state_files(checkpoint: Path) -> list[str]:
    forbidden = {
        "optimizer.pt",
        "scheduler.pt",
        "scaler.pt",
        "trainer_state.json",
        "rng_state.pth",
    }
    return sorted(
        path.name
        for path in checkpoint.iterdir()
        if path.name in forbidden or path.name.startswith("rng_state_")
    )


def remove_training_state_files(checkpoint: Path) -> list[str]:
    removed = find_training_state_files(checkpoint)
    for name in removed:
        (checkpoint / name).unlink()
    return removed


def current_samples_per_step(trainer) -> int:
    return int(os.environ.get("SFT_GLOBAL_BATCH_SIZE", "1"))


@contextmanager
def suspend_sequence_parallel():
    try:
        from swift.sequence_parallel import sequence_parallel
    except ImportError:
        yield
        return
    original_world_size = sequence_parallel.world_size
    if original_world_size is None or int(original_world_size) <= 1:
        yield
        return
    sequence_parallel.world_size = 1
    try:
        yield
    finally:
        sequence_parallel.world_size = original_world_size


try:
    from swift.callbacks import TrainerCallback, callbacks_map
except ImportError:  # 使纯 Python 单元测试不依赖 DLC 环境。
    class TrainerCallback:  # type: ignore[no-redef]
        def __init__(self, args, trainer):
            self.args = args
            self.trainer = trainer

    callbacks_map: dict[str, type] = {}


class FinarLogCallback(TrainerCallback):
    def __init__(self, args, trainer):
        super().__init__(args, trainer)
        self.started_at = time.monotonic()

    def on_log(self, args, state, control, logs=None, **kwargs):
        if not state.is_world_process_zero or not logs:
            return control
        memory = logs.get("memory(GiB)")
        for line in format_training_log(
            step=state.global_step,
            max_steps=state.max_steps,
            epoch=float(state.epoch or 0.0),
            logs=logs,
            elapsed_seconds=time.monotonic() - self.started_at,
            samples_per_step=current_samples_per_step(self.trainer),
            memory_gib=float(memory) if memory is not None else None,
        ):
            print(line, flush=True)
        print(f"             gpu={_gpu_snapshot()}", flush=True)
        return control


def _global_rank() -> int:
    try:
        import torch.distributed as dist

        if dist.is_available() and dist.is_initialized():
            return int(dist.get_rank())
    except (ImportError, AttributeError):
        pass
    return int(os.environ.get("RANK", "0"))


def _trace_steps() -> set[int]:
    raw = os.environ.get("SFT_TRACE_STEPS", "234,1302,1303")
    return {int(value.strip()) for value in raw.split(",") if value.strip()}


def _batch_metadata(inputs: dict[str, Any]) -> dict[str, Any]:
    import torch

    tensors = {}
    for key, value in inputs.items():
        if torch.is_tensor(value):
            tensors[key] = {"shape": [int(size) for size in value.shape], "dtype": str(value.dtype)}
    labels = inputs.get("labels")
    valid_labels = ignored_labels = None
    if torch.is_tensor(labels):
        valid_labels = int(torch.count_nonzero(labels.ne(-100)).item())
        ignored_labels = int(labels.numel()) - valid_labels
    return {"valid_labels": valid_labels, "ignored_labels": ignored_labels, "tensors": tensors}


def _trace_path(trainer, attempted_step: int) -> Path:
    rank = _global_rank()
    trace_dir = Path(trainer.args.output_dir) / "train_trace" / f"step-{attempted_step:06d}"
    trace_dir.mkdir(parents=True, exist_ok=True)
    return trace_dir / f"rank-{rank:04d}.json"


def _write_numerics_trace(
    trainer,
    inputs: dict[str, Any],
    attempted_step: int,
    loss_value: float | None,
    *,
    metadata: dict[str, Any] | None = None,
    sample_metadata: dict[str, Any] | None = None,
    extra: dict[str, Any] | None = None,
) -> Path:
    path = _trace_path(trainer, attempted_step)
    payload = {}
    if path.exists():
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            payload = {}
    if metadata is None:
        metadata = _batch_metadata(inputs)
    payload.update({"attempted_step": attempted_step, "global_rank": _global_rank(), **metadata})
    if loss_value is not None or "loss" not in payload:
        payload["loss"] = None if loss_value is None else (loss_value if math.isfinite(loss_value) else str(loss_value))
        payload["loss_finite"] = None if loss_value is None else math.isfinite(loss_value)
    if extra:
        payload.update(extra)
    if sample_metadata is None:
        sampler = getattr(trainer, "_finar_token_budget_sampler", None)
        if sampler is not None:
            sample_metadata = {
                "dataset_indices": list(getattr(sampler, "current_indices", [])),
                "batch_size": int(getattr(sampler, "current_batch_size", 0)),
                "max_tokens": int(getattr(sampler, "current_max_tokens", 0)),
            }
    if sample_metadata:
        payload.update(sample_metadata)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def _finite_value(value: Any) -> bool | None:
    if value is None:
        return None
    try:
        import torch

        finite = torch.isfinite(value)
        if hasattr(finite, "all"):
            finite = finite.all()
        if hasattr(finite, "item"):
            finite = finite.item()
        return bool(finite)
    except (ImportError, AttributeError, TypeError, ValueError, RuntimeError):
        try:
            return math.isfinite(float(value))
        except (TypeError, ValueError):
            return None


def _parameters_finite(model, *, gradients: bool) -> bool | None:
    parameters = getattr(model, "parameters", None)
    if not callable(parameters):
        return None
    observed = False
    for parameter in parameters():
        value = getattr(parameter, "grad", None) if gradients else getattr(parameter, "data", parameter)
        if value is None:
            continue
        observed = True
        finite = _finite_value(value)
        if finite is False:
            return False
        if finite is None:
            return None
    return True if observed else None


def _write_rank_status(trainer, *, errors: int = 0) -> Path:
    rank = _global_rank()
    state = getattr(trainer, "state", None)
    planned = int(getattr(state, "max_steps", 0) or 0)
    completed = int(getattr(state, "global_step", 0) or 0)
    sampler = getattr(trainer, "_finar_token_budget_sampler", None)
    current_sample = getattr(trainer, "_finar_current_sample", None)
    if current_sample is None and sampler is not None:
        current_sample = list(getattr(sampler, "current_indices", []))
    path = Path(trainer.args.output_dir) / "train_trace" / f"rank-{rank:04d}.status.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "planned": planned,
                "completed": completed,
                "remaining": max(0, planned - completed),
                "heartbeat": time.time(),
                "errors": errors,
                "current_sample": current_sample,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return path


class FinarNumericsCallback(TrainerCallback):
    def __init__(self, args, trainer):
        super().__init__(args, trainer)
        self._trace_step: int | None = None
        self._trace_metadata: dict[str, Any] | None = None
        self._trace_sample_metadata: dict[str, Any] | None = None
        self._errors = 0
        self._gradient_hook_handles = []
        self._gradient_observed = False
        self._gradient_all_finite = None
        original_compute_loss = trainer.compute_loss

        def remove_gradient_hooks():
            for handle in self._gradient_hook_handles:
                handle.remove()
            self._gradient_hook_handles.clear()

        def register_gradient_hooks(model):
            parameters = getattr(model, "parameters", None)
            if not callable(parameters):
                return
            import torch

            for parameter in parameters():
                if not getattr(parameter, "requires_grad", False):
                    continue
                register_hook = getattr(parameter, "register_hook", None)
                if not callable(register_hook):
                    continue

                def observe_gradient(gradient):
                    finite = torch.isfinite(gradient)
                    if hasattr(finite, "all"):
                        finite = finite.all()
                    self._gradient_observed = True
                    if self._gradient_all_finite is None:
                        self._gradient_all_finite = finite
                    else:
                        self._gradient_all_finite = self._gradient_all_finite & finite
                    return gradient

                self._gradient_hook_handles.append(register_hook(observe_gradient))

        def gradient_finiteness():
            if not self._gradient_observed or self._gradient_all_finite is None:
                return None
            finite = self._gradient_all_finite
            if hasattr(finite, "item"):
                finite = finite.item()
            return bool(finite)

        self._remove_gradient_hooks = remove_gradient_hooks
        self._gradient_finiteness = gradient_finiteness

        def guarded_compute_loss(model, inputs, *compute_args, **compute_kwargs):
            remove_gradient_hooks()
            self._gradient_observed = False
            self._gradient_all_finite = None
            attempted_step = int(trainer.state.global_step) + 1
            should_trace = attempted_step in _trace_steps()
            trace_inputs = dict(inputs)
            metadata = _batch_metadata(trace_inputs)
            sampler = getattr(trainer, "_finar_token_budget_sampler", None)
            sample_metadata = None
            if sampler is not None:
                sample_metadata = {
                    "dataset_indices": list(getattr(sampler, "current_indices", [])),
                    "batch_size": int(getattr(sampler, "current_batch_size", 0)),
                    "max_tokens": int(getattr(sampler, "current_max_tokens", 0)),
                }
            self._trace_step = attempted_step if should_trace else None
            self._trace_metadata = metadata if should_trace else None
            self._trace_sample_metadata = sample_metadata if should_trace else None
            if metadata is not None:
                trainer._finar_current_sample = {
                    "valid_labels": metadata.get("valid_labels"),
                    "ignored_labels": metadata.get("ignored_labels"),
                    "tensors": metadata.get("tensors", {}),
                    **(sample_metadata or {}),
                }
            if should_trace:
                _write_numerics_trace(
                    trainer,
                    inputs,
                    attempted_step,
                    None,
                    metadata=metadata,
                    sample_metadata=sample_metadata,
                    extra={
                        "forward_loss": None,
                        "gradient_finite": None,
                        "parameters_finite_before": None,
                        "parameters_finite_after": None,
                        "optimizer_capture": "pending",
                    },
                )
            result = original_compute_loss(model, inputs, *compute_args, **compute_kwargs)
            loss = result[0] if isinstance(result, tuple) else result
            loss_value = float(loss.item())
            trace_path = None
            if should_trace or not math.isfinite(loss_value):
                if metadata is None:
                    metadata = _batch_metadata(trace_inputs)
                    trainer._finar_current_sample = {
                        "valid_labels": metadata.get("valid_labels"),
                        "ignored_labels": metadata.get("ignored_labels"),
                        "tensors": metadata.get("tensors", {}),
                        **(sample_metadata or {}),
                    }
                trace_path = _write_numerics_trace(
                    trainer,
                    inputs,
                    attempted_step,
                    loss_value,
                    metadata=metadata,
                    sample_metadata=sample_metadata,
                    extra={"forward_loss": loss_value},
                )
            if not math.isfinite(loss_value):
                self._errors += 1
                _write_rank_status(trainer, errors=self._errors)
                raise FloatingPointError(
                    f"non-finite training loss attempted_step={attempted_step} "
                    f"rank={_global_rank()} trace={trace_path}"
                )
            if should_trace:
                register_gradient_hooks(model)
            return result

        trainer.compute_loss = guarded_compute_loss

    def on_train_begin(self, args, state, control, **kwargs):
        _write_rank_status(self.trainer, errors=self._errors)
        return control

    def on_step_begin(self, args, state, control, **kwargs):
        _write_rank_status(self.trainer, errors=self._errors)
        return control

    def on_pre_optimizer_step(self, args, state, control, optimizer=None, **kwargs):
        step = int(getattr(state, "global_step", 0)) + 1
        if self._trace_step != step:
            return control
        model = getattr(self.trainer, "model", None)
        gradients_finite = self._gradient_finiteness()
        parameters_finite = _parameters_finite(model, gradients=False)
        _write_numerics_trace(
            self.trainer,
            {},
            step,
            None,
            metadata=self._trace_metadata or {},
            sample_metadata=self._trace_sample_metadata,
            extra={
                "gradient_finite": gradients_finite,
                "parameters_finite_before": parameters_finite,
                "optimizer_capture": "available" if optimizer is not None else "unavailable",
            },
        )
        self._remove_gradient_hooks()
        if gradients_finite is False:
            self._errors += 1
            _write_rank_status(self.trainer, errors=self._errors)
            raise FloatingPointError(f"non-finite gradient before optimizer attempted_step={step}")
        if parameters_finite is False:
            self._errors += 1
            _write_rank_status(self.trainer, errors=self._errors)
            raise FloatingPointError(f"non-finite parameters before optimizer attempted_step={step}")
        return control

    def on_step_end(self, args, state, control, **kwargs):
        step = int(getattr(state, "global_step", 0))
        if self._trace_step == step:
            model = getattr(self.trainer, "model", None)
            parameters_finite_after = _parameters_finite(model, gradients=False)
            _write_numerics_trace(
                self.trainer,
                {},
                step,
                None,
                metadata=self._trace_metadata or {},
                sample_metadata=self._trace_sample_metadata,
                extra={"parameters_finite_after": parameters_finite_after},
            )
            self._remove_gradient_hooks()
            if parameters_finite_after is False:
                self._errors += 1
                _write_rank_status(self.trainer, errors=self._errors)
                raise FloatingPointError(f"non-finite parameters after optimizer attempted_step={step}")
        _write_rank_status(self.trainer, errors=self._errors)
        return control

    def on_train_end(self, args, state, control, **kwargs):
        _write_rank_status(self.trainer, errors=self._errors)
        return control


class FinarPassAt8Callback(TrainerCallback):
    def __init__(self, args, trainer):
        super().__init__(args, trainer)
        self.last_step: int | None = None
        self.pending_metrics: dict[str, float | int] | None = None

    def _run(self, state, *, defer_log: bool = False) -> None:
        step = int(state.global_step)
        if self.last_step == step:
            return
        interval = int(os.environ.get("SFT_EVAL_STEPS", "500"))
        at_zero = os.environ.get("SFT_EVAL_AT_ZERO", "true").lower() == "true"
        if not should_run_pass_at_8(step, int(state.max_steps), interval) or (step == 0 and not at_zero):
            return
        self.last_step = step
        from scripts.sft.pass_at_8_eval import run_distributed_evaluation

        model = getattr(self.trainer, "model_wrapped", self.trainer.model)
        accelerator = getattr(self.trainer, "accelerator", None)
        template = getattr(self.trainer, "template", None)
        if accelerator is None:
            unwrap_context = nullcontext(model)
        else:
            try:
                from swift.utils import unwrap_model_for_generation
            except ImportError:
                unwrap_context = nullcontext(model)
            else:
                unwrap_context = unwrap_model_for_generation(model, accelerator)
        template_context = template.generate_context() if template is not None else nullcontext()
        with unwrap_context as model_wrapped, template_context, suspend_sequence_parallel():
            metrics = run_distributed_evaluation(
                model=model_wrapped,
                processor=getattr(self.trainer, "processor", None),
                template=template,
                benchmark_path=Path(os.environ["SFT_BENCHMARK"]),
                project_root=Path(os.environ["QWEN3VL_ROOT"]),
                output_dir=Path(args_output_dir(self.args)) / "eval",
                step=step,
                judge_url=os.environ["SFT_JUDGE_URL"],
                max_samples=int(os.environ.get("SFT_EVAL_MAX_SAMPLES", "0")) or None,
            )
        payload = {f"eval_{key}": value for key, value in metrics.items() if isinstance(value, (int, float))}
        if defer_log:
            self.pending_metrics = payload
        else:
            self.trainer.log(payload)

    def _flush_pending_metrics(self) -> None:
        if self.pending_metrics is None:
            return
        payload = self.pending_metrics
        self.pending_metrics = None
        self.trainer.log(payload)

    def on_train_begin(self, args, state, control, **kwargs):
        self._run(state, defer_log=True)
        return control

    def on_step_begin(self, args, state, control, **kwargs):
        self._flush_pending_metrics()
        return control

    def on_step_end(self, args, state, control, **kwargs):
        self._run(state)
        return control

    def on_train_end(self, args, state, control, **kwargs):
        self._run(state)
        return control

    def on_save(self, args, state, control, **kwargs):
        if state.is_world_process_zero:
            checkpoint = Path(args_output_dir(self.args)) / f"checkpoint-{state.global_step}"
            removed = remove_training_state_files(checkpoint)
            if removed:
                print(
                    "INFO     | >> checkpoint_cleanup removed=" + ",".join(removed),
                    flush=True,
                )
            unexpected = find_training_state_files(checkpoint)
            if unexpected:
                raise RuntimeError(f"save_only_model produced training state files: {unexpected}")
        return control


def args_output_dir(args) -> str:
    return str(getattr(args, "output_dir"))


callbacks_map["finar_log"] = FinarLogCallback
callbacks_map["finar_numerics"] = FinarNumericsCallback
callbacks_map["finar_pass_at_8"] = FinarPassAt8Callback
