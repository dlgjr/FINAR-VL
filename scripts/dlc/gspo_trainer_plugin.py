"""Evaluation/checkpoint callback for the full GSPO run.

Evaluation artifacts are written to disk and are intentionally not passed to
``trainer.log``; only the reward plugin emits training W&B metrics.
"""

from __future__ import annotations

import json
import os
from contextlib import nullcontext
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

from scripts.rl.gspo_audit import build_audit_records
from scripts.sft.pass_at_8_eval import run_distributed_evaluation


class GSPOGRPOTrainer(GRPOTrainer):
    """Add a static entropy bonus to ms-swift's existing GRPO/GSPO loss."""

    def _prepare_rollout_params(self):
        super()._prepare_rollout_params()
        if not self.args.use_vllm:
            self.request_config.logprobs = True

    def _prepare_vllm(self):
        super()._prepare_vllm()
        if not self.args.use_vllm:
            self.engine.generation_config.use_cache = False

    def _get_per_token_logps_and_entropies(self, *args, **kwargs):
        per_token_logps, entropies = super()._get_per_token_logps_and_entropies(*args, **kwargs)
        self._gspo_entropy_tensor = entropies
        return per_token_logps, entropies

    def _compute_loss_and_metrics(self, model, model_inputs, grpo_batch):
        loss, metrics_data = super()._compute_loss_and_metrics(model, model_inputs, grpo_batch)
        rollout_logps = getattr(grpo_batch, "rollout_per_token_logps", None)
        old_logps = getattr(grpo_batch, "old_per_token_logps", None)
        if rollout_logps is not None and old_logps is not None:
            import torch

            completion_mask = metrics_data["completion_mask"].bool()
            absolute_error = (rollout_logps.float() - old_logps.float()).abs()
            valid_error = absolute_error.masked_select(completion_mask)
            gathered_error = self.accelerator.gather_for_metrics(valid_error.detach())
            metrics_data["logprob_parity"] = {
                "mean": gathered_error.mean().item(),
                "p99": torch.quantile(gathered_error, 0.99).item(),
                "max": gathered_error.max().item(),
            }
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
        parity = metrics_data.get("logprob_parity")
        if parity:
            mode = metrics_data["mode"]
            self._metrics[mode]["logprob_parity/mean_abs_error"].append(parity["mean"])
            self._metrics[mode]["logprob_parity/p99_abs_error"].append(parity["p99"])
            self._metrics[mode]["logprob_parity/max_abs_error"].append(parity["max"])
        regularization = metrics_data.get("entropy_regularization")
        if regularization:
            mode = metrics_data["mode"]
            self._metrics[mode]["entropy/coef"].append(regularization["coef"])
            self._metrics[mode]["entropy/regularized_mean"].append(regularization["mean"])
            self._metrics[mode]["entropy/regularization_loss"].append(regularization["loss"])










    # PASS8_GOLD_V11_BEGIN
    @staticmethod
    def _gather_samples_equal_size(samples):
        # ms-swift already gathers rewards globally in _compute_rewards_per_func().
        # Match its native dynamic-sampling implementation for samples.
        from accelerate.utils import gather_object
        return gather_object(samples)

    @staticmethod
    def _make_gold_sample(sample):
        import copy

        final_answer = str(sample.extra.get("gold_final_answer") or "").strip()
        trajectory = str(
            sample.extra.get("gold_trajectory")
            or sample.extra.get("solution")
            or ""
        ).strip()
        if not final_answer or not trajectory:
            return None

        terminal = f"答案：{final_answer}"
        if trajectory.splitlines()[-1].strip() != terminal:
            trajectory = trajectory.rstrip() + "\n\n" + terminal

        gold = copy.deepcopy(sample)
        if gold.messages and gold.messages[-1].get("role") == "assistant":
            gold.messages[-1] = {"role": "assistant", "content": trajectory}
        else:
            gold.messages.append({"role": "assistant", "content": trajectory})

        gold.response_token_ids = []
        gold.response_loss_mask = []
        gold.rollout_logprobs = []
        gold.finish_reason = "stop"
        gold.add_eos = False
        gold.encoded = None
        gold.routed_experts = None
        gold.rollout_infos = {}
        gold.extra["_gold_injected"] = True
        return gold

    def _weighted_rewards(self, rewards_per_func):
        return (
            rewards_per_func * self.reward_weights.unsqueeze(0)
        ).nansum(dim=1)

    def _initial_rollout_metrics(self, rewards_per_func):
        import torch

        rewards = self._weighted_rewards(rewards_per_func)
        if rewards.numel() % 8:
            raise RuntimeError(
                f"Pass@8 reward tensor must be divisible by 8, got {rewards.numel()}"
            )
        grouped = rewards.view(-1, 8)
        finite_mask = torch.isfinite(grouped).all(dim=1)
        grouped = grouped[finite_mask]
        if grouped.numel() == 0:
            return {
                "rollout/pass8": 0.0,
                "rollout/positive_per_8": 0.0,
                "rollout/all8": 0.0,
            }

        positive = grouped > 0
        positive_count = positive.sum(dim=1).float()

        # Raw policy quality BEFORE Gold injection.
        return {
            "rollout/pass8": float((positive_count > 0).float().mean().item()),
            "rollout/positive_per_8": float(positive_count.mean().item()),
            "rollout/all8": float((grouped >= 1).all(dim=1).float().mean().item()),
        }

    def _record_concise_train_metrics(self, metrics):
        store = getattr(self, "_metrics", None)
        if store is None:
            return
        train_store = store.setdefault("train", {})
        for key, value in metrics.items():
            train_store.setdefault(key, []).append(float(value))

    def _inject_gold_into_all_failed_groups(self, all_samples, rewards_per_func):
        import torch

        if os.environ.get("GSPO_GOLD_INJECT", "true").lower() != "true":
            return list(all_samples), rewards_per_func, 0

        if self.dynamic_num_samples:
            raise RuntimeError("Pass@8 gold injection requires dynamic_num_samples=False")
        if self.num_generations != 8:
            raise RuntimeError(
                f"Pass@8 gold injection requires num_generations=8, got {self.num_generations}"
            )
        if rewards_per_func.ndim != 2 or rewards_per_func.shape[1] != 1:
            raise RuntimeError(
                "Pass@8 gold injection expects exactly one reward function "
                f"(shape={tuple(rewards_per_func.shape)})"
            )
        if len(all_samples) != rewards_per_func.shape[0]:
            raise RuntimeError(
                f"sample/reward mismatch: samples={len(all_samples)} "
                f"rewards={rewards_per_func.shape[0]}"
            )
        if len(all_samples) % 8:
            raise RuntimeError(f"incomplete Pass@8 group: samples={len(all_samples)}")

        full_reward = float(os.environ.get("GSPO_GOLD_REWARD", "1.0"))
        if abs(full_reward - 1.0) > 1e-12:
            raise ValueError(f"GSPO_GOLD_REWARD must be exactly 1.0, got {full_reward}")

        total_rewards = self._weighted_rewards(rewards_per_func)
        samples = list(all_samples)
        rewards = rewards_per_func.clone()
        injected = 0

        for start in range(0, len(samples), 8):
            group_rewards = total_rewards[start:start + 8]
            raw_group = rewards[start:start + 8]

            if not torch.isfinite(raw_group).all() or not torch.isfinite(group_rewards).all():
                continue

            # 0 and -0.1 are failures. Any positive/partial reward blocks injection.
            if not torch.all(group_rewards <= 0):
                continue

            target = start + int(torch.argmin(group_rewards).item())
            gold = self._make_gold_sample(samples[target])
            if gold is None:
                raise RuntimeError(
                    "all-failed Pass@8 group has no valid gold_final_answer/gold_trajectory"
                )
            samples[target] = gold
            rewards[target, 0] = 1.0
            injected += 1

        return samples, rewards, injected

    def _dynamic_sampling(self, samples, rewards_per_func):
        import torch

        target_size = int(self.args.generation_batch_size)
        if target_size % 8:
            raise RuntimeError(
                f"generation_batch_size must be divisible by 8, got {target_size}"
            )

        local_size = len(samples)
        raw_metrics = self._initial_rollout_metrics(rewards_per_func)

        valid_samples = []
        valid_reward_chunks = []
        filler_samples = []
        filler_reward_chunks = []

        current_samples = samples
        current_rewards = rewards_per_func

        for attempt in range(self.max_resample_times + 1):
            all_samples = self._gather_samples_equal_size(current_samples)
            if attempt == self.max_resample_times:
                all_samples, current_rewards, _ = self._inject_gold_into_all_failed_groups(
                    all_samples, current_rewards
                )

            rewards_std = self.compute_std(current_samples, current_rewards)
            valid_mask = rewards_std > 0
            finite_mask = torch.isfinite(current_rewards).all(dim=1)

            valid_samples.extend(
                [sample for sample, valid in zip(all_samples, valid_mask.tolist()) if valid]
            )
            valid_reward_chunks.append(current_rewards[valid_mask])

            filler_mask = (~valid_mask) & finite_mask
            filler_samples.extend(
                [sample for sample, keep in zip(all_samples, filler_mask.tolist()) if keep]
            )
            filler_reward_chunks.append(current_rewards[filler_mask])

            if len(valid_samples) >= target_size or attempt == self.max_resample_times:
                break

            inputs = next(self.dynamic_resample_iterator)
            if self.template.truncation_strategy == "raise":
                inputs = self.resample_encode_failed_inputs(inputs)
            current_samples = self.to_samples(inputs)
            current_samples = self._generate_completions(current_samples)
            current_rewards = self._compute_rewards_per_func(current_samples)

        valid_rewards = (
            torch.cat(valid_reward_chunks, dim=0)
            if valid_reward_chunks
            else rewards_per_func.new_empty((0, rewards_per_func.shape[1]))
        )

        if len(valid_samples) >= target_size:
            selected_samples = valid_samples[:target_size]
            selected_rewards = valid_rewards[:target_size]
        else:
            need = target_size - len(valid_samples)
            filler_rewards = (
                torch.cat(filler_reward_chunks, dim=0)
                if filler_reward_chunks
                else rewards_per_func.new_empty((0, rewards_per_func.shape[1]))
            )
            if len(filler_samples) < need:
                raise RuntimeError(
                    "dynamic sampling could not build a finite generation batch: "
                    f"valid={len(valid_samples)} filler={len(filler_samples)} target={target_size}"
                )
            selected_samples = valid_samples + filler_samples[:need]
            selected_rewards = torch.cat([valid_rewards, filler_rewards[:need]], dim=0)

        selected_groups = target_size // 8
        injected_groups = sum(
            bool(getattr(sample, "extra", {}).get("_gold_injected"))
            for sample in selected_samples
        )

        # Only ONE intervention metric. Everything else belongs in stdout/reward_pool,
        # not the W&B training dashboard.
        raw_metrics["intervention/gold_group_ratio"] = (
            injected_groups / selected_groups if selected_groups else 0.0
        )
        self._record_concise_train_metrics(raw_metrics)

        if self.accelerator.is_main_process:
            import json
            print(
                "[GSPO-TRAIN-CORE] "
                + json.dumps(raw_metrics, ensure_ascii=False, sort_keys=True),
                flush=True,
            )

        process_slice = slice(
            self.accelerator.process_index * local_size,
            (self.accelerator.process_index + 1) * local_size,
        )
        return selected_samples[process_slice], selected_rewards
    def _get_per_token_logps_and_entropies(self, *args, **kwargs):
        per_token_logps, entropies = super()._get_per_token_logps_and_entropies(
            *args, **kwargs
        )
        self._gspo_policy_logps_tensor = per_token_logps
        self._gspo_entropy_tensor = entropies
        return per_token_logps, entropies

    def _compute_loss_and_metrics(self, model, model_inputs, grpo_batch):
        import torch

        loss, metrics_data = super()._compute_loss_and_metrics(
            model, model_inputs, grpo_batch
        )

        current_logps = self.__dict__.pop("_gspo_policy_logps_tensor", None)
        entropies = self.__dict__.pop("_gspo_entropy_tensor", None)

        entropy_coef = float(os.environ.get("GSPO_ENTROPY_COEF", "0.02"))
        if entropy_coef != 0.0 and entropies is not None:
            completion_mask = metrics_data["completion_mask"]
            entropy_mean = (
                entropies.masked_fill(completion_mask == 0, 0.0).sum()
                / metrics_data["completion_token_count"]
            )
            loss = loss - entropy_coef * entropy_mean
            gathered_entropy = self.accelerator.gather_for_metrics(
                entropy_mean.detach()
            )
            metrics_data["concise_entropy_mean"] = gathered_entropy.nanmean().item()

        old_logps = getattr(grpo_batch, "old_per_token_logps", None)
        if (
            current_logps is not None
            and old_logps is not None
            and getattr(self, "importance_sampling_level", None) == "sequence"
        ):
            completion_mask = metrics_data["completion_mask"].to(
                dtype=current_logps.dtype
            )
            token_count = completion_mask.sum(dim=-1).clamp(min=1.0)
            seq_log_weight = (
                ((current_logps - old_logps) * completion_mask).sum(dim=-1)
                / token_count
            )
            seq_weight = torch.exp(
                torch.clamp(seq_log_weight.detach().float(), min=-20.0, max=20.0)
            )
            global_weight = self.accelerator.gather_for_metrics(seq_weight)
            global_weight = global_weight[torch.isfinite(global_weight)]

            if global_weight.numel() > 0:
                sum_w = global_weight.sum()
                sum_w2 = global_weight.square().sum()
                n = float(global_weight.numel())
                ess_ratio = (sum_w * sum_w) / (
                    n * sum_w2.clamp(min=torch.finfo(sum_w2.dtype).tiny)
                )
                metrics_data["sequence_ess_ratio"] = float(
                    ess_ratio.clamp(min=0.0, max=1.0).item()
                )

        return loss, metrics_data

    def _update_metrics(self, metrics_data):
        super()._update_metrics(metrics_data)
        mode = metrics_data["mode"]

        if "concise_entropy_mean" in metrics_data:
            self._metrics[mode]["entropy/mean"].append(
                metrics_data["concise_entropy_mean"]
            )

        if "sequence_ess_ratio" in metrics_data:
            self._metrics[mode]["ess/ratio"].append(
                metrics_data["sequence_ess_ratio"]
            )

    # PASS8_GOLD_V11_END


class GSPOEvalCallback(TrainerCallback):
    def __init__(self, args, trainer):
        super().__init__(args, trainer)
        self.args = args
        self.trainer = trainer
        self.last_eval_step: int | None = None
        self.last_reward_print_step = 0
        self.reward_pool_offsets: dict[str, int] = {}
        self.last_lr_decay_step = 0
        self.best_eval_metric: float | None = None
        self.no_improve_evals = 0

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

    def _run(self, state, control=None, *, force: bool = False) -> None:
        step = int(state.global_step)
        interval = int(os.environ.get("GSPO_EVAL_STEPS", "200"))
        if not force and (step == 0 or step % interval != 0):
            return
        if self.last_eval_step == step:
            return
        self.last_eval_step = step
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
        with unwrap_context as model_wrapped, template_context:
            metrics = run_distributed_evaluation(
                model=model_wrapped,
                processor=getattr(self.trainer, "processor", None),
                template=template,
                benchmark_path=Path(os.environ["GSPO_BENCHMARK"]),
                project_root=Path(os.environ["QWEN3VL_ROOT"]),
                output_dir=Path(self.args.output_dir) / "eval",
                step=step,
                judge_url=os.environ.get("GSPO_JUDGE_URL", "http://127.0.0.1:8001"),
                max_samples=int(os.environ.get("GSPO_EVAL_MAX_SAMPLES", "0")) or None,
            )
        if int(step) > 0 and getattr(state, "is_world_process_zero", True):
            pool_path = Path(os.environ.get("GSPO_REWARD_POOL", str(Path(self.args.output_dir) / "reward_pool.jsonl")))
            pool: list[dict[str, Any]] = []
            for current in self._reward_pool_paths(pool_path):
                pool.extend(json.loads(line) for line in current.read_text(encoding="utf-8").splitlines() if line.strip())
            if pool:
                audit = build_audit_records(
                    pool,
                    seed=int(os.environ.get("GSPO_AUDIT_SEED", "42")),
                    max_completion_length=int(os.environ.get("GSPO_MAX_COMPLETION_LENGTH", "2048")),
                )
                audit_path = Path(self.args.output_dir) / "eval" / f"step-{step:06d}" / "high_reward_audit.json"
                audit_path.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        if control is not None:
            pass  # early-stop bookkeeping removed; eval is observational only
        print(f"[GSPO_EVAL] step={step} metrics={json.dumps(metrics, ensure_ascii=False)}", flush=True)

    def on_train_begin(self, args, state, control, **kwargs):
        if getattr(state, "is_world_process_zero", True):
            pool_path = Path(os.environ.get("GSPO_REWARD_POOL", str(Path(self.args.output_dir) / "reward_pool.jsonl")))
            self.reward_pool_offsets = {
                str(path): path.stat().st_size for path in self._reward_pool_paths(pool_path)
            }
        self._run(state, control, force=True)
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
        self._run(state, control, force=True)
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
        self.last_eval_step = None
        self.last_reward_print_step = 0
        self.reward_pool_offsets = {}
        self._run(state, force=True)
        return control


callbacks_map["gspo_eval"] = GSPOEvalCallback
TrainerFactory.TRAINER_MAPPING["grpo"] = "scripts.dlc.gspo_trainer_plugin.GSPOGRPOTrainer"
