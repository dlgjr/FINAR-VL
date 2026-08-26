from pathlib import Path

from scripts.data.augment_reasoning_calculations import build_dataset
from scripts.data.copy_augmented_reasoning_images import collect_image_mapping, copy_images


def row(task: str, question: str, answer: str, source: str = "source") -> dict:
    return {
        "messages": [
            {"role": "user", "content": question},
            {"role": "assistant", "content": answer},
        ],
        "images": ["assets/image.png"],
        "source": source,
        "split": "train",
        "task": task,
    }


def test_build_dataset_reduces_retrieval_and_adds_numeric_calculations() -> None:
    reasoning = [
        row("evidence_retrieval", f"find page {index}", str(index), "finder")
        for index in range(4)
    ] + [row("old_reasoning", "old question", "A")]
    test = [
        row("finmmr", f"Calculate the average for {index} and {index + 1}.", str(index + 0.5), "finmmr")
        for index in range(4)
    ] + [row("finmmr", "What is shown in the image?", "12", "finmmr")]

    output, audit = build_dataset(
        reasoning,
        test,
        retrieval_count=2,
        calculation_count=3,
        seed=7,
    )

    assert audit["retrieval_after"] == 2
    assert audit["added_calculation_rows"] == 3
    assert audit["output_rows"] == 6
    added = [item for item in output if item.get("task_original") == "finmmr"]
    assert len(added) == 3
    assert all(item["task"] == "multi_step_numerical_reasoning" for item in added)
    assert all(item["verifier_type"] == "numeric" for item in added)
    assert all(item["reward_type"] == "rule" for item in added)
    assert all(item["images"][0].startswith("assets_rl/ewai/") for item in added)
    assert all(item["_reward_routing"]["original_images"] == ["assets/image.png"] for item in added)


def test_build_dataset_is_deterministic() -> None:
    reasoning = [row("evidence_retrieval", f"page {index}", str(index)) for index in range(3)]
    test = [
        row("finmmr", f"Compute the ratio using {index} and {index + 1}.", str(index), "finmmr")
        for index in range(5)
    ]

    first, first_audit = build_dataset(reasoning, test, retrieval_count=1, calculation_count=2, seed=11)
    second, second_audit = build_dataset(reasoning, test, retrieval_count=1, calculation_count=2, seed=11)

    assert first == second
    assert first_audit == second_audit


def test_calculation_selection_covers_each_test_task_when_capacity_allows() -> None:
    test = [
        row(task, f"Calculate the {task} ratio using {index} and {index + 1}.", str(index), task)
        for task in ("finmmr", "finmme", "famma")
        for index in range(3)
    ]

    output, audit = build_dataset([], test, retrieval_count=0, calculation_count=6, seed=5)

    assert set(audit["added_original_task_counts"]) == {"finmmr", "finmme", "famma"}
    assert all(count > 0 for count in audit["added_original_task_counts"].values())
    assert len(output) == 6


def test_copy_images_uses_only_augmented_mapping(tmp_path: Path) -> None:
    source_root = tmp_path / "benchmark"
    target_root = tmp_path / "train_multi"
    source = source_root / "assets" / "source.png"
    source.parent.mkdir(parents=True)
    source.write_bytes(b"image")
    dataset = tmp_path / "augmented.jsonl"
    dataset.write_text(
        '{"images":["assets/old.png"],"task":"old"}\n'
        '{"images":["assets_rl/ewai/1.png"],"_reward_routing":'
        '{"version":"reasoning_calculation_augmentation_v1",'
        '"source_line":1,"original_images":["assets/source.png"]}}\n',
        encoding="utf-8",
    )

    assert collect_image_mapping(dataset) == {"assets/source.png": "assets_rl/ewai/1.png"}
    assert copy_images(dataset, source_root, target_root) == 1
    assert (target_root / "assets_rl" / "ewai" / "1.png").read_bytes() == b"image"
