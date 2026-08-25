"""Training diagnostics and checkpoint cleanup for the full GSPO run.

The reward plugin emits training W&B metrics; checkpoints keep model files only.
"""

from __future__ import annotations

import json
import os
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
