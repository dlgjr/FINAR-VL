import pickle
from collections import defaultdict
from pathlib import Path
from types import SimpleNamespace

from scripts.dlc.gspo_trainer_plugin import GSPOEvalCallback, GSPOGRPOTrainer, GRPOTrainer, TrainerFactory


class Scalar:
    def __init__(self, value):
        self.value = float(value)

    def __add__(self, other):
        return Scalar(self.value + value_of(other))

    __radd__ = __add__

    def __neg__(self):
        return Scalar(-self.value)

    def __truediv__(self, other):
        return Scalar(self.value / value_of(other))

    def __rmul__(self, other):
        return Scalar(value_of(other) * self.value)

    def detach(self):
        return self

    def nanmean(self):
        return self

    def item(self):
        return self.value


def value_of(value):
    return value.value if isinstance(value, Scalar) else float(value)


class Mask:
    def __init__(self, values):
        self.values = values

    def __eq__(self, value):
        return [item == value for item in self.values]


class Tensor:
    def __init__(self, values):
        self.values = values

    def masked_fill(self, mask, value):
        return Tensor([value if masked else item for item, masked in zip(self.values, mask)])

    def sum(self):
        return Scalar(sum(self.values))


def test_reward_pool_paths_aggregate_all_node_files(tmp_path):
    first = tmp_path / "reward_pool_rank_0.jsonl"
    second = tmp_path / "reward_pool_rank_1.jsonl"
    first.write_text("{}\n", encoding="utf-8")
    second.write_text("{}\n", encoding="utf-8")
    assert GSPOEvalCallback._reward_pool_paths(first) == [first, second]


def test_dynamic_sampling_payloads_preserve_rank_order_with_unequal_sizes():
    rank_zero = [{"sample_id": "short"}]
    rank_one = [{"sample_id": "long", "completion": "x" * 10000}]
    payloads = [
        pickle.dumps(rank_zero, protocol=pickle.HIGHEST_PROTOCOL),
        pickle.dumps(rank_one, protocol=pickle.HIGHEST_PROTOCOL),
    ]

    assert len(payloads[0]) != len(payloads[1])
    assert GSPOGRPOTrainer._deserialize_samples(payloads) == rank_zero + rank_one


def test_dynamic_sampling_uses_equal_size_tensor_gather():
    source = (Path(__file__).resolve().parents[1] / "scripts/dlc/gspo_trainer_plugin.py").read_text(
        encoding="utf-8"
    )
    assert "gather_object(samples)" not in source
    assert "padded_size = max(sizes)" in source
    assert "dist.all_gather(gathered_payloads, padded_payload)" in source
    assert "all_samples = self._gather_samples_equal_size(samples)" in source


def test_rl_callback_keeps_checkpoint_and_reward_hooks_without_benchmark_evaluation():
    source = (Path(__file__).resolve().parents[1] / "scripts/dlc/gspo_trainer_plugin.py").read_text(
        encoding="utf-8"
    )
    assert "run_distributed_evaluation" not in source
    assert "[GSPO_EVAL]" not in source
    assert "def _print_top_rewards" in source
    assert "def on_save" in source
    assert "_cleanup_checkpoint(checkpoint)" in source


def test_entropy_bonus_reuses_base_forward_and_registers_custom_trainer(monkeypatch):
    calls = 0

    def get_logps_and_entropies(self, *args, **kwargs):
        nonlocal calls
        calls += 1
        return "logps", Tensor([2.0, 5.0])

    def compute_loss_and_metrics(self, model, model_inputs, grpo_batch):
        self._get_per_token_logps_and_entropies(model, model_inputs, grpo_batch)
        return Scalar(2.0), {
            "mode": "train",
            "completion_mask": Mask([1, 0]),
            "completion_token_count": Scalar(1.0),
        }

    monkeypatch.setattr(GRPOTrainer, "_get_per_token_logps_and_entropies", get_logps_and_entropies, raising=False)
    monkeypatch.setattr(GRPOTrainer, "_compute_loss_and_metrics", compute_loss_and_metrics, raising=False)
    monkeypatch.setattr(GRPOTrainer, "_update_metrics", lambda self, metrics: None, raising=False)
    monkeypatch.setenv("GSPO_ENTROPY_COEF", "0.01")
    trainer = GSPOGRPOTrainer()
    trainer.accelerator = SimpleNamespace(gather_for_metrics=lambda value: value)
    trainer._metrics = defaultdict(lambda: defaultdict(list))

    loss, metrics = trainer._compute_loss_and_metrics(None, {}, None)
    trainer._update_metrics(metrics)

    assert calls == 1
    assert loss.item() == 1.98
    assert metrics["entropy_regularization"] == {"coef": 0.01, "mean": 2.0, "loss": -0.02}
    assert trainer._metrics["train"]["entropy/regularization_loss"] == [-0.02]
    assert TrainerFactory.TRAINER_MAPPING["grpo"] == "scripts.dlc.gspo_trainer_plugin.GSPOGRPOTrainer"
