"""ms-swift 外部插件：统一 SFT 日志、Pass@8 调度与检查点审计。"""

from __future__ import annotations

import os
import json
import hashlib
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


def _kl_tasks() -> frozenset[str]:
    """返回需要走 KL retention 的精确 task 名；默认只启用 task == generation。"""
    raw = os.environ.get("SFT_KL_TASKS", "generation")
    return frozenset(value.strip() for value in raw.split(",") if value.strip())


def use_kl_for_task(task: Any) -> bool:
    """KL 路由只按 task 精确匹配，不按 family 或模糊 generation 类别扩展。"""
    return str(task or "") in _kl_tasks()


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
            metadata["task"] = getattr(trainer, "_finar_current_task", None)
            metadata["use_kl"] = bool(getattr(trainer, "_finar_use_kl", False))
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
                    "task": metadata.get("task"),
                    "use_kl": metadata.get("use_kl"),
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


try:
    import torch

    _SAMPLER_BASE = torch.utils.data.Sampler
except ImportError:  # 纯 Python 单元测试不依赖 torch
    _SAMPLER_BASE = object  # type: ignore[assignment,misc]


class PlanSampler(_SAMPLER_BASE):
    """按全局采样计划确定性分片，不引入任何随机性。

    计划条目按微步组织，每微步 dp_world_size 个位置；rank r 只消费
    position_in_micro_step == r 的条目。索引映射：multi -> 原索引，
    text -> N_multi + 索引（对应 ms-swift concat 后的 dataset 顺序）。
    """

    def __init__(self, *, plan_dir: Path, rank: int, dataset_len: int) -> None:
        self.plan_dir = Path(plan_dir)
        self.rank = rank
        self.dataset_len = dataset_len
        meta_path = self.plan_dir / "meta.json"
        if not meta_path.is_file():
            raise RuntimeError(f"sample plan meta not found: {meta_path}")
        self.meta = json.loads(meta_path.read_text(encoding="utf-8"))
        self.n_multi = int(self.meta["N_multi"])
        self.total_blocks = int(self.meta["total_blocks"])
        self.per_device_batch = int(self.meta.get("per_device_batch", 1))
        self.grad_acc = int(self.meta["grad_acc"])
        if self.per_device_batch != 1:
            raise AssertionError("sample plan actual accounting requires per_device_batch=1")

    def _length(self) -> int:
        return (
            sum(int(block["steps"]) * self.grad_acc for block in self.meta["blocks"])
            * self.per_device_batch
        )

    def _dataset_index(self, modality: str, index: int) -> int:
        dataset_index = index if modality == "multi" else self.n_multi + index
        if dataset_index >= self.dataset_len:
            raise IndexError(
                f"plan index {dataset_index} (modality={modality}, index={index}) "
                f"out of range for dataset length {self.dataset_len}"
            )
        return dataset_index

    def __iter__(self):
        for block_id in range(self.total_blocks):
            block_path = self.plan_dir / f"block_{block_id:04d}.jsonl"
            with block_path.open(encoding="utf-8") as handle:
                for line in handle:
                    if not line.strip():
                        continue
                    entry = json.loads(line)
                    position = int(entry["position_in_micro_step"])
                    if not (
                        self.rank * self.per_device_batch
                        <= position
                        < (self.rank + 1) * self.per_device_batch
                    ):
                        continue
                    yield self._dataset_index(str(entry["modality"]), int(entry["index"]))

    def __len__(self) -> int:
        return self._length()


_RUNTIME_ROUTE_KEY = "_finar_runtime_route"


class RuntimeReplacementDataset:
    def __init__(
        self,
        dataset,
        template,
        *,
        plan_dir: Path,
        n_multi: int,
        seed: int,
        rejection_dir: Path,
    ) -> None:
        self.dataset = dataset
        self.template = template
        self.n_multi = int(n_multi)
        self.seed = int(seed)
        self.rejection_dir = Path(rejection_dir)
        pool_path = Path(plan_dir) / "replacement_pools.json"
        if pool_path.is_file():
            self.pools = json.loads(pool_path.read_text(encoding="utf-8"))
        else:
            self.pools = {
                "multi": {"__all__": list(range(self.n_multi))},
                "text": {"__all__": list(range(max(0, len(dataset) - self.n_multi)))},
            }
        self._rejection_path = self.rejection_dir / (
            f"runtime_rejected.rank_{_global_rank():04d}.pid_{os.getpid()}.jsonl"
        )

    def __len__(self) -> int:
        return len(self.dataset)

    def _split_index(self, index: int) -> tuple[str, int]:
        if index < self.n_multi:
            return "multi", int(index)
        return "text", int(index - self.n_multi)

    def _dataset_index(self, modality: str, raw_index: int) -> int:
        return int(raw_index) if modality == "multi" else self.n_multi + int(raw_index)

    def _candidate_indices(self, modality: str, task: str, raw_index: int) -> list[int]:
        modality_pools = self.pools.get(modality, {})
        same_task = [int(value) for value in modality_pools.get(task, [])]
        all_candidates = [int(value) for value in modality_pools.get("__all__", [])]
        ordered: list[int] = [raw_index]
        digest = hashlib.sha256(
            f"{self.seed}:{modality}:{task}:{raw_index}".encode("utf-8")
        ).digest()
        remainder = [value for value in same_task if value != raw_index]
        if remainder:
            offset = int.from_bytes(digest[:8], "big") % len(remainder)
            ordered.extend(remainder[offset:] + remainder[:offset])
        fallback = [value for value in all_candidates if value not in ordered]
        if fallback:
            offset = int.from_bytes(digest[8:16], "big") % len(fallback)
            fallback = fallback[offset:] + fallback[:offset]
        ordered.extend(fallback)
        return ordered

    def _write_rejection(
        self,
        *,
        modality: str,
        task: str,
        raw_index: int,
        candidate_raw_index: int,
        reason: str,
        error: Exception,
    ) -> None:
        self.rejection_dir.mkdir(parents=True, exist_ok=True)
        payload = {
            "modality": modality,
            "task": task,
            "raw_index": int(raw_index),
            "candidate_raw_index": int(candidate_raw_index),
            "resolved_raw_index": int(candidate_raw_index),
            "reason": reason,
            "error": f"{type(error).__name__}: {error}",
        }
        with self._rejection_path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False) + "\n")

    @staticmethod
    def _failure_reason(error: Exception) -> str:
        if "MaxLengthError" in type(error).__name__:
            return "max_length"
        return "encode_failed"

    def __getitem__(self, index: int) -> dict[str, Any]:
        if isinstance(index, str):
            return self.dataset[index]
        modality, raw_index = self._split_index(int(index))
        original_row = self.dataset[int(index)]
        task = str(original_row.get("task") or "__unknown__")
        candidates = self._candidate_indices(modality, task, raw_index)
        last_error: Exception | None = None
        replacement_reason = "original"
        for candidate_raw_index in candidates:
            candidate_index = self._dataset_index(modality, candidate_raw_index)
            row = original_row if candidate_index == int(index) else self.dataset[candidate_index]
            candidate_task = str(row.get("task") or "__unknown__")
            try:
                encoded = self.template.encode(row, return_length=True)
                if isinstance(encoded, list):
                    raise ValueError("runtime encode produced multiple rows")
                try:
                    from scripts.sft.sample_plan import family_for_task
                except ImportError:
                    family = candidate_task
                else:
                    family = family_for_task(candidate_task)
                encoded[_RUNTIME_ROUTE_KEY] = {
                    "task": candidate_task,
                    "family": family,
                    "modality": modality,
                    "index": int(candidate_raw_index),
                    "raw_index": int(candidate_raw_index),
                    "planned_raw_index": int(raw_index),
                    "replaced": bool(candidate_raw_index != raw_index),
                    "replacement_reason": replacement_reason,
                }
                return encoded
            except Exception as error:
                last_error = error
                if candidate_raw_index == raw_index:
                    replacement_reason = self._failure_reason(error)
                self._write_rejection(
                    modality=modality,
                    task=task,
                    raw_index=raw_index,
                    candidate_raw_index=candidate_raw_index,
                    reason=self._failure_reason(error),
                    error=error,
                )
        if last_error is None:
            raise ValueError(
                f"no runtime replacement candidate for modality={modality} task={task} raw_index={raw_index}"
            )
        raise ValueError(
            f"runtime replacement exhausted for modality={modality} task={task} raw_index={raw_index}"
        ) from last_error


def _dp_rank() -> tuple[int, int]:
    try:
        from swift.sequence_parallel import sequence_parallel

        if getattr(sequence_parallel, "dp_world_size", None):
            return int(sequence_parallel.dp_rank), int(sequence_parallel.dp_world_size)
    except (ImportError, AttributeError):
        pass
    try:
        import torch.distributed as dist

        if dist.is_available() and dist.is_initialized():
            return int(dist.get_rank()), int(dist.get_world_size())
    except (ImportError, AttributeError):
        pass
    return 0, 1


def _sp_rank_world() -> tuple[int, int]:
    try:
        from swift.sequence_parallel import sequence_parallel

        sp_world = int(getattr(sequence_parallel, "sp_world_size", 1) or 1)
        sp_rank = int(getattr(sequence_parallel, "sp_rank", 0) or 0)
        return sp_rank, sp_world
    except (ImportError, AttributeError):
        return 0, 1


def _distributed_barrier() -> None:
    try:
        import torch.distributed as dist

        if dist.is_available() and dist.is_initialized():
            dist.barrier()
    except (ImportError, AttributeError):
        return


def _empty_distribution() -> dict[str, Any]:
    return {
        "samples": 0,
        "assistant_tokens": 0,
        "sample_ratio": 0.0,
        "token_ratio": 0.0,
        "tasks": {},
        "families": {},
    }


def _add_distribution(target: dict[str, Any], entry: dict[str, Any], token_count: int) -> None:
    task = str(entry["task"])
    family = str(entry.get("family", task))
    target["samples"] += 1
    target["assistant_tokens"] += int(token_count)
    for group, name in (("tasks", task), ("families", family)):
        values = target[group].setdefault(name, {"samples": 0, "assistant_tokens": 0})
        values["samples"] += 1
        values["assistant_tokens"] += int(token_count)


def _finalize_distribution(distribution: dict[str, Any]) -> dict[str, Any]:
    total_samples = int(distribution["samples"])
    total_tokens = int(distribution["assistant_tokens"])
    distribution["sample_ratio"] = 1.0 if total_samples else 0.0
    distribution["token_ratio"] = 1.0 if total_tokens else 0.0
    for grouped in (distribution["tasks"], distribution["families"]):
        for values in grouped.values():
            values["sample_ratio"] = values["samples"] / total_samples if total_samples else 0.0
            values["token_ratio"] = values["assistant_tokens"] / total_tokens if total_tokens else 0.0
    return distribution


def _distribution_difference(planned: dict[str, Any], actual: dict[str, Any]) -> dict[str, Any]:
    difference = _empty_distribution()
    for key in ("samples", "assistant_tokens"):
        difference[key] = int(actual[key]) - int(planned[key])
    for group in ("tasks", "families"):
        names = set(planned[group]) | set(actual[group])
        for name in sorted(names):
            planned_values = planned[group].get(name, {})
            actual_values = actual[group].get(name, {})
            difference[group][name] = {
                "samples": int(actual_values.get("samples", 0)) - int(planned_values.get("samples", 0)),
                "assistant_tokens": int(actual_values.get("assistant_tokens", 0)) - int(planned_values.get("assistant_tokens", 0)),
            }
    return difference


class _PlanRuntimeTracker:
    def __init__(self, plan_dir: str, output_dir: Path) -> None:
        self.plan_dir = Path(plan_dir)
        self.output_dir = Path(output_dir) / "sample_distribution"
        self.rank = _global_rank()
        self.dp_rank, self.dp_world = _dp_rank()
        self.sp_rank, self.sp_world = _sp_rank_world()
        self.meta = json.loads((self.plan_dir / "meta.json").read_text(encoding="utf-8"))
        self.entries: list[dict[str, Any]] = []
        self.planned: dict[int, dict[str, Any]] = {}
        self.actual: dict[int, dict[str, Any]] = {}
        self.cursor = 0
        self.flushed: set[int] = set()
        per_device_batch = int(self.meta.get("per_device_batch", 1))
        if per_device_batch != 1:
            raise AssertionError("sample plan actual accounting requires per_device_batch=1")
        for block_id in range(int(self.meta["total_blocks"])):
            path = self.plan_dir / f"block_{block_id:04d}.jsonl"
            planned = _empty_distribution()
            with path.open(encoding="utf-8") as handle:
                for line in handle:
                    if not line.strip():
                        continue
                    entry = json.loads(line)
                    position = int(entry["position_in_micro_step"])
                    if self.dp_rank <= position < self.dp_rank + 1:
                        self.entries.append(entry)
                        _add_distribution(planned, entry, int(entry.get("assistant_token_count", 0)))
            self.planned[block_id] = planned
            self.actual[block_id] = _empty_distribution()

    def set_skip_batches(self, skip_batches: int) -> None:
        self.cursor = int(skip_batches)

    def current_entry(self) -> dict[str, Any]:
        if self.cursor >= len(self.entries):
            raise AssertionError("rank-local plan cursor exhausted before training ended")
        return self.entries[self.cursor]

    def consume(
        self,
        labels,
        *,
        token_count: int | None = None,
        runtime_route: dict[str, Any] | None = None,
    ) -> None:
        if labels is None:
            raise AssertionError("planned SFT batch must contain labels")
        if getattr(labels, "ndim", None) != 2 or int(labels.shape[0]) != 1:
            raise AssertionError("sample plan actual accounting requires batch dimension 1")
        entry = self.current_entry()
        if token_count is None:
            token_count = int(labels.ne(-100).sum().item())
        actual_entry = dict(entry)
        if runtime_route:
            actual_entry.update(
                {
                    "task": str(runtime_route.get("task") or entry["task"]),
                    "family": str(runtime_route.get("family") or entry["family"]),
                    "modality": str(runtime_route.get("modality") or entry["modality"]),
                    "index": int(runtime_route.get("index", entry["index"])),
                    "raw_index": int(runtime_route.get("raw_index", entry.get("raw_index", entry["index"]))),
                }
            )
        _add_distribution(self.actual[int(entry["block"])], actual_entry, int(token_count))
        self.cursor += 1

    def write_rank_block(self, block_id: int) -> None:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        planned = _finalize_distribution(self.planned[block_id])
        actual = _finalize_distribution(self.actual[block_id])
        payload = {
            "block_id": block_id,
            "rank": self.rank,
            "dp_rank": self.dp_rank,
            "sp_rank": self.sp_rank,
            "sp_world": self.sp_world,
            "planned": planned,
            "actual": actual,
            "difference": _distribution_difference(planned, actual),
        }
        path = self.output_dir / f"block_{block_id:04d}.rank_{self.rank:04d}.json"
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    @staticmethod
    def _merge_full_distribution(target: dict[str, Any], source: dict[str, Any]) -> None:
        target["samples"] += int(source["samples"])
        target["assistant_tokens"] += int(source["assistant_tokens"])
        for group in ("tasks", "families"):
            for name, values in source[group].items():
                target[group].setdefault(name, {"samples": 0, "assistant_tokens": 0})
                target[group][name]["samples"] += int(values["samples"])
                target[group][name]["assistant_tokens"] += int(values["assistant_tokens"])

    @staticmethod
    def _merge_actual_sp_group(target: dict[str, Any], members: list[dict[str, Any]]) -> None:
        representative = min(members, key=lambda payload: int(payload.get("sp_rank", 0)))
        source = representative["actual"]
        target["samples"] += int(source["samples"])
        for group in ("tasks", "families"):
            for name, values in source[group].items():
                target[group].setdefault(name, {"samples": 0, "assistant_tokens": 0})
                target[group][name]["samples"] += int(values["samples"])
        for payload in members:
            source = payload["actual"]
            target["assistant_tokens"] += int(source["assistant_tokens"])
            for group in ("tasks", "families"):
                for name, values in source[group].items():
                    target[group].setdefault(name, {"samples": 0, "assistant_tokens": 0})
                    target[group][name]["assistant_tokens"] += int(values["assistant_tokens"])

    def merge_block(self, block_id: int) -> None:
        merged = {"block_id": block_id, "planned": _empty_distribution(), "actual": _empty_distribution()}
        rank_paths = sorted(self.output_dir.glob(f"block_{block_id:04d}.rank_*.json"))
        groups: dict[int, list[dict[str, Any]]] = {}
        for path in rank_paths:
            payload = json.loads(path.read_text(encoding="utf-8"))
            groups.setdefault(int(payload.get("dp_rank", payload["rank"])), []).append(payload)
        if set(groups) != set(range(self.dp_world)):
            raise RuntimeError(
                f"sample-distribution rank files do not cover all DP ranks: "
                f"expected={list(range(self.dp_world))} actual={sorted(groups)}"
            )
        for dp_rank in range(self.dp_world):
            members = groups[dp_rank]
            expected_sp_world = max(int(payload.get("sp_world", 1)) for payload in members)
            sp_ranks = {int(payload.get("sp_rank", 0)) for payload in members}
            if len(members) != expected_sp_world or sp_ranks != set(range(expected_sp_world)):
                raise RuntimeError(
                    f"sample-distribution SP files incomplete for dp_rank={dp_rank}: "
                    f"expected_sp_world={expected_sp_world} sp_ranks={sorted(sp_ranks)}"
                )
            representative = min(members, key=lambda payload: int(payload.get("sp_rank", 0)))
            self._merge_full_distribution(merged["planned"], representative["planned"])
            self._merge_actual_sp_group(merged["actual"], members)
        merged["planned"] = _finalize_distribution(merged["planned"])
        merged["actual"] = _finalize_distribution(merged["actual"])
        merged["difference"] = _distribution_difference(merged["planned"], merged["actual"])
        path = self.output_dir / f"block_{block_id:04d}.json"
        path.write_text(json.dumps(merged, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _install_plan_dataloader(trainer) -> bool:
    plan_dir = os.environ.get("SFT_PLAN_DIR", "")
    if not plan_dir or not (Path(plan_dir) / "meta.json").is_file():
        return False
    try:
        from swift.dataloader import DataLoaderShard
    except ImportError:
        return False

    import types

    def planned_get_train_dataloader(self, skip_batches=0):
        rank, _ = _dp_rank()
        if int(getattr(self.args, "per_device_train_batch_size", 1)) != 1:
            raise AssertionError("sample plan actual accounting requires per_device_train_batch_size=1")
        dataset = self.train_dataset
        sampler = PlanSampler(
            plan_dir=Path(plan_dir),
            rank=rank,
            dataset_len=len(dataset),
        )
        dataloader_params = {
            "batch_size": self._train_batch_size,
            "collate_fn": self.data_collator,
            "num_workers": self.args.dataloader_num_workers,
            "pin_memory": self.args.dataloader_pin_memory,
            "persistent_workers": self.args.dataloader_persistent_workers,
            "sampler": sampler,
            "drop_last": self.args.dataloader_drop_last,
        }
        if skip_batches > 0:
            from accelerate.data_loader import SkipBatchSampler

            sampler = SkipBatchSampler(sampler, skip_batches=skip_batches * self._train_batch_size)
            dataloader_params["sampler"] = sampler
        tracker = getattr(self, "_finar_plan_tracker", None)
        if tracker is not None:
            tracker.set_skip_batches(int(skip_batches))
        return DataLoaderShard(dataset, device=self.accelerator.device, **dataloader_params)

    trainer.get_train_dataloader = types.MethodType(planned_get_train_dataloader, trainer)
    return True


def _install_runtime_replacement(trainer, plan_dir: Path, tracker: _PlanRuntimeTracker) -> None:
    dataset = trainer.train_dataset
    base_dataset = getattr(dataset, "dataset", dataset)
    trainer.train_dataset = RuntimeReplacementDataset(
        base_dataset,
        trainer.template,
        plan_dir=plan_dir,
        n_multi=int(tracker.meta["N_multi"]),
        seed=int(tracker.meta.get("seed", 42)),
        rejection_dir=Path(args_output_dir(trainer.args)) / "runtime_rejected",
    )
    original_collator = trainer.data_collator

    def runtime_collator(batch):
        routes = [item.pop(_RUNTIME_ROUTE_KEY, None) for item in batch]
        result = original_collator(batch)
        if len(routes) == 1 and routes[0] is not None:
            result[_RUNTIME_ROUTE_KEY] = routes[0]
        return result

    trainer.data_collator = runtime_collator


class FinarPlanCallback(TrainerCallback):
    """启用全局采样计划：替换训练 dataloader 并在 block 边界打印配额统计。"""

    def __init__(self, args, trainer):
        super().__init__(args, trainer)
        plan_dir = os.environ.get("SFT_PLAN_DIR", "")
        self.enabled = bool(plan_dir) and (Path(plan_dir) / "meta.json").is_file()
        self.last_logged_block: int | None = None
        self._blocks: list[dict[str, Any]] = []
        self._steps_per_block = 200
        if self.enabled:
            meta = json.loads((Path(plan_dir) / "meta.json").read_text(encoding="utf-8"))
            if int(getattr(args, "per_device_train_batch_size", 1)) != 1:
                raise AssertionError("sample plan actual accounting requires per_device_train_batch_size=1")
            if int(meta.get("per_device_batch", 1)) != 1:
                raise AssertionError("sample plan actual accounting requires per_device_batch=1")
            self._blocks = meta.get("blocks", [])
            self._steps_per_block = int(meta.get("steps_per_block", 200))
            self._tracker = _PlanRuntimeTracker(plan_dir, args_output_dir(args))
            trainer._finar_plan_tracker = self._tracker
            _install_runtime_replacement(trainer, Path(plan_dir), self._tracker)
            _install_plan_dataloader(trainer)
            original_compute_loss = trainer.compute_loss

            def tracked_compute_loss(model, inputs, *compute_args, **compute_kwargs):
                runtime_route = inputs.pop(_RUNTIME_ROUTE_KEY, None)
                trainer._finar_runtime_route = runtime_route if isinstance(runtime_route, dict) else None
                labels = inputs.get("labels")
                entry = self._tracker.current_entry()
                route = trainer._finar_runtime_route or entry
                task = str(route.get("task") or "")
                trainer._finar_current_task = task
                trainer._finar_use_kl = use_kl_for_task(task)
                trainer._finar_kl_route = {
                    "task": task,
                    "use_kl": trainer._finar_use_kl,
                    "modality": str(route.get("modality") or ""),
                    "index": int(route.get("index", -1)),
                    "raw_index": int(route.get("raw_index", route.get("index", -1))),
                }
                result = original_compute_loss(model, inputs, *compute_args, **compute_kwargs)
                loss = result[0] if isinstance(result, tuple) else result
                if not math.isfinite(float(loss.item())):
                    return result
                actual_token_count = None
                if trainer._finar_use_kl:
                    kl_info = getattr(trainer, "_finar_last_kl", None)
                    if isinstance(kl_info, dict) and str(kl_info.get("task") or "") == task:
                        actual_token_count = int(kl_info.get("local_tokens", 0))
                self._tracker.consume(
                    labels,
                    token_count=actual_token_count,
                    runtime_route=trainer._finar_runtime_route,
                )
                return result

            trainer.compute_loss = tracked_compute_loss

    def on_step_begin(self, args, state, control, **kwargs):
        if not self.enabled or not state.is_world_process_zero:
            return control
        step = int(state.global_step)
        block_id = step // self._steps_per_block
        if block_id >= len(self._blocks) or block_id == self.last_logged_block:
            return control
        self.last_logged_block = block_id
        block = self._blocks[block_id]
        print(
            "INFO     | >> sample_plan "
            f"block={block['block_id']} start_step={block['start_step']} "
            f"steps={block['steps']} alpha={block['alpha']:.2f}",
            flush=True,
        )
        for modality, quotas in block["quotas"].items():
            top = sorted(quotas.items(), key=lambda item: (-int(item[1]), item[0]))[:8]
            summary = " ".join(f"{task}={count}" for task, count in top)
            print(
                f"             {modality} quota={sum(int(q) for q in quotas.values())} "
                f"top_tasks={summary}",
                flush=True,
            )
        return control

    def _flush_block(self, block_id: int) -> None:
        if block_id in self._tracker.flushed:
            return
        self._tracker.write_rank_block(block_id)
        _distributed_barrier()
        if _global_rank() == 0:
            self._tracker.merge_block(block_id)
        self._tracker.flushed.add(block_id)

    def on_step_end(self, args, state, control, **kwargs):
        if not self.enabled:
            return control
        step = int(getattr(state, "global_step", 0))
        if step > 0 and step % self._steps_per_block == 0:
            self._flush_block(step // self._steps_per_block - 1)
        return control

    def on_train_end(self, args, state, control, **kwargs):
        if not self.enabled:
            return control
        final_step = int(getattr(state, "global_step", 0))
        if final_step > 0:
            self._flush_block(min(len(self._blocks) - 1, (final_step - 1) // self._steps_per_block))
        return control


def args_output_dir(args) -> str:
    return str(getattr(args, "output_dir"))


callbacks_map["finar_log"] = FinarLogCallback
callbacks_map["finar_numerics"] = FinarNumericsCallback
callbacks_map["finar_pass_at_8"] = FinarPassAt8Callback
callbacks_map["finar_plan"] = FinarPlanCallback
