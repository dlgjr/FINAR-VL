"""Training diagnostics and checkpoint cleanup for the full GSPO run.

The reward plugin emits training W&B metrics; checkpoints keep model files only.
"""

from __future__ import annotations

import json
import os
import pickle
from pathlib import Path
from typing import Any

try:
    from swift.callbacks import TrainerCallback, callbacks_map
    from swift.rlhf_trainers import GRPOTrainer
    from swift.trainers.trainer_factory import TrainerFactory
except ImportError:  # pragma: no cover - DLC supplies ms-swift
    class TrainerCallback:  # type: ignore[no-redef]
        def __init__(self, *args, **kwargs):
            pass

    class GRPOTrainer:  # type: ignore[no-redef]
        pass

    class TrainerFactory:  # type: ignore[no-redef]
        TRAINER_MAPPING: dict[str, str] = {}

    callbacks_map: dict[str, type] = {}  # type: ignore[no-redef]

class GSPOGRPOTrainer(GRPOTrainer):
    """Add a static entropy bonus to ms-swift's existing GRPO/GSPO loss."""

    @staticmethod
    def _serialize_samples(samples: list[Any]) -> bytes:
        return pickle.dumps(samples, protocol=pickle.HIGHEST_PROTOCOL)

    @staticmethod
    def _deserialize_samples(payloads: list[bytes]) -> list[Any]:
        samples: list[Any] = []
        for payload in payloads:
            samples.extend(pickle.loads(payload))
        return samples

    def _gather_samples_equal_size(self, samples: list[Any]) -> list[Any]:
        import torch
        import torch.distributed as dist

        if not dist.is_initialized() or dist.get_world_size() == 1:
            return samples

        payload = self._serialize_samples(samples)
        payload_size = len(payload)
        device = self.accelerator.device
        world_size = dist.get_world_size()
        local_size = torch.tensor([payload_size], dtype=torch.int64, device=device)
        gathered_sizes = [torch.empty_like(local_size) for _ in range(world_size)]
        dist.all_gather(gathered_sizes, local_size)
        sizes = [int(size.item()) for size in gathered_sizes]
        padded_size = max(sizes)

        padded_payload = torch.zeros(padded_size, dtype=torch.uint8, device=device)
        local_payload = torch.frombuffer(bytearray(payload), dtype=torch.uint8).to(device)
        padded_payload[:payload_size].copy_(local_payload)
        gathered_payloads = [torch.empty_like(padded_payload) for _ in range(world_size)]
        dist.all_gather(gathered_payloads, padded_payload)
        payloads = [
            tensor[:size].cpu().numpy().tobytes()
            for tensor, size in zip(gathered_payloads, sizes)
        ]
        return self._deserialize_samples(payloads)

    def _dynamic_sampling(self, samples, rewards_per_func):
        import torch

        resample_count = 0
        valid_samples = []
        valid_rewards_per_func = []
        origin_data = (samples, rewards_per_func)

        while resample_count < self.max_resample_times:
            rewards_std = self.compute_std(samples, rewards_per_func)
            valid_mask = rewards_std > 0
            all_samples = self._gather_samples_equal_size(samples)
            valid_samples.extend([sample for sample, valid in zip(all_samples, valid_mask) if valid])
            valid_rewards_per_func.append(rewards_per_func[valid_mask])
            if len(valid_samples) >= self.args.generation_batch_size:
                break

            inputs = next(self.dynamic_resample_iterator)
            if self.template.truncation_strategy == "raise":
                inputs = self.resample_encode_failed_inputs(inputs)
            samples = self.to_samples(inputs)
            samples = self._generate_completions(samples)
            rewards_per_func = self._compute_rewards_per_func(samples)
            resample_count += 1

        if len(valid_samples) >= self.args.generation_batch_size:
            process_slice = slice(
                self.accelerator.process_index * len(samples),
                (self.accelerator.process_index + 1) * len(samples),
            )
            samples = valid_samples[:self.args.generation_batch_size][process_slice]
            rewards_per_func = torch.cat(valid_rewards_per_func)[:self.args.generation_batch_size]
        else:
            if self.accelerator.is_main_process:
                print(
                    f"There are still std=0 groups present after {self.max_resample_times} retries.",
                    flush=True,
                )
            samples, rewards_per_func = origin_data

        return samples, rewards_per_func

    def _get_per_token_logps_and_entropies(self, *args, **kwargs):
        per_token_logps, entropies = super()._get_per_token_logps_and_entropies(*args, **kwargs)
        self._gspo_entropy_tensor = entropies
        return per_token_logps, entropies

    def _compute_loss_and_metrics(self, model, model_inputs, grpo_batch):
        loss, metrics_data = super()._compute_loss_and_metrics(model, model_inputs, grpo_batch)
        entropies = self.__dict__.pop("_gspo_entropy_tensor")
        entropy_coef = float(os.environ.get("GSPO_ENTROPY_COEF", "0.02"))
        if entropy_coef == 0.0:
            return loss, metrics_data
        completion_mask = metrics_data["completion_mask"]
        entropy_mean = (
            entropies.masked_fill(completion_mask == 0, 0.0).sum()
            / metrics_data["completion_token_count"]
        )
        entropy_loss = -entropy_coef * entropy_mean
        loss = loss + entropy_loss
        gathered_entropy_mean = self.accelerator.gather_for_metrics(entropy_mean.detach()).nanmean().item()
        metrics_data["entropy_regularization"] = {
            "coef": entropy_coef,
            "mean": gathered_entropy_mean,
            "loss": -entropy_coef * gathered_entropy_mean,
        }
        return loss, metrics_data

    def _update_metrics(self, metrics_data):
        super()._update_metrics(metrics_data)
        regularization = metrics_data.get("entropy_regularization")
        if regularization:
            mode = metrics_data["mode"]
            self._metrics[mode]["entropy/coef"].append(regularization["coef"])
            self._metrics[mode]["entropy/regularized_mean"].append(regularization["mean"])
            self._metrics[mode]["entropy/regularization_loss"].append(regularization["loss"])


class GSPOEvalCallback(TrainerCallback):
    def __init__(self, args, trainer):
        super().__init__(args, trainer)
        self.args = args
        self.trainer = trainer
        self.last_reward_print_step = 0
        self.reward_pool_offsets: dict[str, int] = {}
        self.last_lr_decay_step = 0

    @staticmethod
    def _cleanup_checkpoint(path: Path) -> None:
        state_names = {
            "optimizer.pt",
            "optimizer.bin",
            "scheduler.pt",
            "scheduler.bin",
            "rng_state.pth",
            "trainer_state.json",
            "training_args.bin",
        }
        for name in state_names:
            target = path / name
            if target.is_file():
                target.unlink()
        remaining = [str(target) for target in path.iterdir() if target.name in state_names] if path.is_dir() else []
        if remaining:
            raise RuntimeError(f"GSPO checkpoint contains trainer state: {remaining}")

    @staticmethod
    def _reward_pool_paths(pool_path: Path) -> list[Path]:
        ranked = sorted(pool_path.parent.glob("reward_pool_rank_*.jsonl"))
        return ranked or ([pool_path] if pool_path.is_file() else [])

    @staticmethod
    def _new_reward_records(paths: list[Path], offsets: dict[str, int]) -> list[dict[str, Any]]:
        records: list[dict[str, Any]] = []
        for path in paths:
            key = str(path)
            with path.open("rb") as source:
                source.seek(offsets.get(key, 0))
                records.extend(json.loads(line.decode("utf-8")) for line in source if line.strip())
                offsets[key] = source.tell()
        return records

    def _print_top_rewards(self, state) -> None:
        if not getattr(state, "is_world_process_zero", True):
            return
        step = int(state.global_step)
        interval = int(os.environ.get("GSPO_TOP_REWARD_STEPS", "20"))
        if step == 0 or step % interval != 0 or self.last_reward_print_step == step:
            return
        pool_path = Path(os.environ.get("GSPO_REWARD_POOL", str(Path(self.args.output_dir) / "reward_pool.jsonl")))
        records = self._new_reward_records(self._reward_pool_paths(pool_path), self.reward_pool_offsets)
        count = int(os.environ.get("GSPO_TOP_REWARD_K", "5"))
        top = sorted(records, key=lambda row: float(row.get("reward", 0.0)), reverse=True)[:count]
        payload = {
            "step": step,
            "window_start_step": self.last_reward_print_step,
            "window_end_step": step,
            "rollout_count": len(records),
            "top": [
                {
                    "rank": index,
                    "reward": float(row.get("reward", 0.0)),
                    "sample_id": str(row.get("sample_id", "")),
                    "source": row.get("source", ""),
                    "reward_type": row.get("reward_type", ""),
                    "verifier_type": row.get("verifier_type", ""),
                    "question": row.get("question", ""),
                    "completion": row.get("completion", ""),
                }
                for index, row in enumerate(top, 1)
            ],
        }
        print(f"[GSPO_TOP_REWARD] {json.dumps(payload, ensure_ascii=False)}", flush=True)
        self.last_reward_print_step = step

    def on_train_begin(self, args, state, control, **kwargs):
        if getattr(state, "is_world_process_zero", True):
            pool_path = Path(os.environ.get("GSPO_REWARD_POOL", str(Path(self.args.output_dir) / "reward_pool.jsonl")))
            self.reward_pool_offsets = {
                str(path): path.stat().st_size for path in self._reward_pool_paths(pool_path)
            }
        return control

    def on_step_end(self, args, state, control, **kwargs):
        self._print_top_rewards(state)
        step = int(state.global_step)
        interval = int(os.environ.get("GSPO_LR_DECAY_STEPS", "1000"))
        if step > 0 and step % interval == 0 and self.last_lr_decay_step != step:
            gamma = float(os.environ.get("GSPO_LR_DECAY_GAMMA", "0.5"))
            for group in self.trainer.optimizer.param_groups:
                group["lr"] *= gamma
            self.last_lr_decay_step = step
            if getattr(state, "is_world_process_zero", True):
                print(f"[GSPO_LR_DECAY] step={step} gamma={gamma} lr={self.trainer.optimizer.param_groups[0]['lr']}", flush=True)
        return control

    def on_save(self, args, state, control, **kwargs):
        if getattr(state, "is_world_process_zero", True):
            checkpoint = Path(args.output_dir) / f"checkpoint-{state.global_step}"
            self._cleanup_checkpoint(checkpoint)
        return control

    def on_epoch_end(self, args, state, control, **kwargs):
        if getattr(state, "is_world_process_zero", True):
            epoch = int(round(float(state.epoch or 0)))
            checkpoint = Path(args.output_dir) / f"checkpoint-epoch-{epoch}"
            self.trainer.save_model(str(checkpoint))
            self._cleanup_checkpoint(checkpoint)
        return control

    def on_train_end(self, args, state, control, **kwargs):
        if getattr(state, "is_world_process_zero", True):
            checkpoint = Path(args.output_dir) / "final"
            self.trainer.save_model(str(checkpoint))
            self._cleanup_checkpoint(checkpoint)
            self._cleanup_checkpoint(Path(args.output_dir))
        self.last_reward_print_step = 0
        self.reward_pool_offsets = {}
        return control


callbacks_map["gspo_eval"] = GSPOEvalCallback
TrainerFactory.TRAINER_MAPPING["grpo"] = "scripts.dlc.gspo_trainer_plugin.GSPOGRPOTrainer"
