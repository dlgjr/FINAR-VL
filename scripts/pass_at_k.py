#!/usr/bin/env python3

import argparse
import hashlib
import importlib.metadata
import json
import math
import os
import re
import sys
import time
import traceback
import unicodedata
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Callable, Iterator, Sequence


DEFAULT_ROOT = "/mnt/nas/bihaoran/qwen3vl"
DEFAULT_MODEL = f"{DEFAULT_ROOT}/models/qwen4"
DEFAULT_MULTI_DATA = f"{DEFAULT_ROOT}/data/train_multi/all.jsonl"
DEFAULT_TEXT_DATA = f"{DEFAULT_ROOT}/data/train_text/all.jsonl"
DEFAULT_OUTPUT = f"{DEFAULT_ROOT}/output/pass_at_k/qwen4_k8"


_ANSWER_MARKER_RE = re.compile(r"(?:答案|answer)\s*[:：]\s*", re.IGNORECASE)
_ANSWER_TAG_RE = re.compile(r"<answer>\s*(.*?)\s*</answer>", re.IGNORECASE | re.DOTALL)
_NUMBER_RE = re.compile(r"^[\$￥¥€£]?\s*[-+]?(?:\d+(?:,\d{3})*|\d+)(?:\.\d+)?%?\s*$")
_CHOICE_RE = re.compile(r"^\s*([A-H])(?:\s*[.、:：)]|\s+|$)", re.IGNORECASE)
_EDGE_PUNCTUATION = " \t\r\n.,;:!?，。；：！？、\"'“”‘’`()[]{}<>《》"


def _last_boxed(text: str) -> str | None:
    marker = r"\boxed{"
    start = text.rfind(marker)
    if start < 0:
        return None
    index = start + len(marker)
    depth = 1
    for cursor in range(index, len(text)):
        char = text[cursor]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[index:cursor].strip()
    return None


def extract_answer(text: Any) -> str:
    value = str(text).strip()
    boxed = _last_boxed(value)
    if boxed is not None:
        return boxed
    tags = list(_ANSWER_TAG_RE.finditer(value))
    if tags:
        return tags[-1].group(1).strip()
    markers = list(_ANSWER_MARKER_RE.finditer(value))
    if markers:
        return value[markers[-1].end() :].strip()
    return value


def _normalize_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).casefold()
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized.strip(_EDGE_PUNCTUATION)


def _parse_json(value: str) -> Any | None:
    if not value.lstrip().startswith(("{", "[")):
        return None
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return None


def _parse_number(value: str) -> tuple[Decimal, bool] | None:
    if not _NUMBER_RE.fullmatch(value):
        return None
    cleaned = value.strip().lstrip("$￥¥€£").replace(",", "")
    is_percent = cleaned.endswith("%")
    if is_percent:
        cleaned = cleaned[:-1]
    try:
        return Decimal(cleaned), is_percent
    except InvalidOperation:
        return None


def _json_equal(expected: Any, actual: Any) -> bool:
    if isinstance(expected, bool) or isinstance(actual, bool):
        return type(expected) is type(actual) and expected == actual
    if isinstance(expected, (int, float)) and isinstance(actual, (int, float)):
        return Decimal(str(expected)) == Decimal(str(actual))
    if type(expected) is not type(actual):
        return False
    if isinstance(expected, dict):
        return expected.keys() == actual.keys() and all(
            _json_equal(expected[key], actual[key]) for key in expected
        )
    if isinstance(expected, list):
        return len(expected) == len(actual) and all(
            _json_equal(left, right) for left, right in zip(expected, actual)
        )
    return expected == actual


def answers_equal(reference: Any, candidate: Any) -> bool:
    expected = extract_answer(reference)
    actual = extract_answer(candidate)

    expected_json = _parse_json(expected)
    actual_json = _parse_json(actual)
    if expected_json is not None or actual_json is not None:
        return (
            expected_json is not None
            and actual_json is not None
            and _json_equal(expected_json, actual_json)
        )

    expected_choice = _CHOICE_RE.fullmatch(expected)
    actual_choice = _CHOICE_RE.match(actual)
    if expected_choice:
        return actual_choice is not None and (
            expected_choice.group(1).casefold() == actual_choice.group(1).casefold()
        )

    expected_number = _parse_number(expected)
    actual_number = _parse_number(actual)
    if expected_number is not None or actual_number is not None:
        return (
            expected_number is not None
            and actual_number is not None
            and expected_number == actual_number
        )

    return _normalize_text(expected) == _normalize_text(actual)


def requires_model_judge(reference: Any) -> bool:
    expected = extract_answer(reference)
    return _CHOICE_RE.fullmatch(expected) is None and _parse_number(expected) is None


def parse_judge_verdict(text: Any) -> bool:
    verdict = str(text).strip()
    if verdict == "正确":
        return True
    if verdict == "错误":
        return False
    raise ValueError(f"invalid judge verdict: {verdict!r}")


def stable_seed(base_seed: int, dataset: str, byte_offset: int) -> int:
    payload = f"{base_seed}\0{dataset}\0{byte_offset}".encode("utf-8")
    return int.from_bytes(hashlib.sha256(payload).digest()[:4], "big")


class JsonlRecordError(ValueError):
    pass


def iter_jsonl_shard(
    path: Path,
    rank: int,
    world_size: int,
    completed_offsets: set[int] | None = None,
    max_records: int | None = None,
) -> Iterator[tuple[int, dict[str, Any]]]:
    if world_size < 1 or not 0 <= rank < world_size:
        raise ValueError(f"invalid rank/world_size: {rank}/{world_size}")

    completed = completed_offsets or set()
    file_size = path.stat().st_size
    start = file_size * rank // world_size
    end = file_size * (rank + 1) // world_size
    emitted = 0

    with path.open("rb") as handle:
        if start:
            handle.seek(start - 1)
            if handle.read(1) != b"\n":
                handle.readline()
        else:
            handle.seek(0)

        while True:
            offset = handle.tell()
            if offset >= end and rank != world_size - 1:
                break
            line = handle.readline()
            if not line:
                break
            if not line.strip() or offset in completed:
                continue
            try:
                row = json.loads(line.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as error:
                row = JsonlRecordError(str(error))
            yield offset, row
            emitted += 1
            if max_records is not None and emitted >= max_records:
                break


def _prompt_messages(row: dict[str, Any]) -> list[dict[str, Any]]:
    messages = [
        {"role": message["role"], "content": message["content"]}
        for message in row["messages"]
    ]
    if not messages or messages[-1]["role"] != "assistant":
        raise ValueError("record must end with an assistant reference")
    messages.pop()
    return messages


def _normalize_image_content(messages: list[dict[str, Any]]) -> int:
    """Convert image markers to chat-template image items and count image slots."""
    image_slot_count = 0
    for message in messages:
        content = message["content"]
        if isinstance(content, str):
            marker_count = content.count("<image>")
            if marker_count == 0:
                continue
            if message["role"] != "user":
                raise ValueError("<image> markers are only supported in user messages")
            rich_content: list[dict[str, str]] = []
            for index, text in enumerate(content.split("<image>")):
                if index:
                    rich_content.append({"type": "image"})
                if text:
                    rich_content.append({"type": "text", "text": text})
            message["content"] = rich_content
            image_slot_count += marker_count
            continue
        if isinstance(content, list):
            message_image_count = sum(
                1
                for item in content
                if isinstance(item, dict) and item.get("type") == "image"
            )
            if message_image_count and message["role"] != "user":
                raise ValueError("image content is only supported in user messages")
            image_slot_count += message_image_count
    return image_slot_count


def _message_text(content: Any) -> str:
    if isinstance(content, str):
        return content.replace("<image>", "")
    if isinstance(content, list):
        return "".join(
            str(item.get("text", ""))
            for item in content
            if isinstance(item, dict) and item.get("type") == "text"
        )
    return str(content)


def _judge_question(row: dict[str, Any]) -> str:
    parts = [
        _message_text(message["content"]).strip()
        for message in row["messages"][:-1]
        if message.get("role") == "user"
    ]
    question = "\n\n".join(part for part in parts if part)
    if not question:
        raise ValueError("record must contain a non-empty user question")
    return question


def build_prompt_input(
    row: dict[str, Any],
    processor: Any,
    root: Path,
) -> dict[str, Any]:
    messages = _prompt_messages(row)
    raw_images = row.get("images")
    if raw_images is None:
        images = []
    elif isinstance(raw_images, (str, bytes)):
        raise TypeError("images must be a sequence of paths, not a string")
    else:
        images = list(raw_images)

    image_slot_count = _normalize_image_content(messages)
    if image_slot_count != len(images):
        raise ValueError(
            "image count/marker count mismatch: "
            f"{len(images)} image paths, {image_slot_count} image slots"
        )

    image_data = []
    if images:
        from PIL import Image

        for image_value in images:
            image_path = Path(image_value)
            if not image_path.is_absolute():
                image_path = root / image_path
            with Image.open(image_path) as image:
                image_data.append(image.convert("RGB").copy())
    prompt = processor.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
    )
    result: dict[str, Any] = {"prompt": prompt}
    if image_data:
        result["multi_modal_data"] = {"image": image_data}
    return result


def build_judge_input(
    row: dict[str, Any],
    reference: str,
    candidate: str,
    processor: Any,
    prompt_input: dict[str, Any],
) -> dict[str, Any]:
    question = _judge_question(row)
    images = prompt_input.get("multi_modal_data", {}).get("image", [])
    judge_text = (
        "请结合原问题，判断模型答案与标准答案的结论是否一致。"
        "允许表述不同，但不能遗漏关键条件、数值或单位。"
        "只输出“正确”或“错误”。\n\n"
        f"原问题：\n{question}\n\n"
        f"标准答案：\n{reference}\n\n"
        f"模型答案：\n{candidate}"
    )
    content: Any = judge_text
    if images:
        content = [
            *({"type": "image"} for _ in images),
            {"type": "text", "text": judge_text},
        ]
    messages = [
        {
            "role": "system",
            "content": "你是答案正确性裁判，只负责判断答案是否正确。",
        },
        {"role": "user", "content": content},
    ]
    result = {
        "prompt": processor.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
        )
    }
    if images:
        result["multi_modal_data"] = prompt_input["multi_modal_data"]
    return result


def _json_line(value: dict[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":")) + "\n"


def repair_jsonl_tail(path: Path) -> None:
    if not path.exists() or path.stat().st_size == 0:
        return
    with path.open("r+b") as handle:
        handle.seek(-1, os.SEEK_END)
        if handle.read(1) == b"\n":
            return

        end = handle.tell()
        search_end = end
        tail_start = 0
        while search_end > 0:
            search_start = max(0, search_end - 8192)
            handle.seek(search_start)
            chunk = handle.read(search_end - search_start)
            newline = chunk.rfind(b"\n")
            if newline >= 0:
                tail_start = search_start + newline + 1
                break
            search_end = search_start

        handle.seek(tail_start)
        tail = handle.read()
        try:
            json.loads(tail.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            handle.truncate(tail_start)
        else:
            handle.seek(0, os.SEEK_END)
            handle.write(b"\n")
        handle.flush()
        os.fsync(handle.fileno())


def _read_completed_offsets(
    result_path: Path,
    error_path: Path,
    dataset: str,
) -> set[int]:
    completed: set[int] = set()
    for path in (result_path, error_path):
        repair_jsonl_tail(path)
        if not path.exists():
            continue
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                record = json.loads(line)
                if record.get("dataset") == dataset:
                    completed.add(int(record["byte_offset"]))
    return completed


def _write_checkpoint(
    output_dir: Path,
    dataset: str,
    rank: int,
    byte_offset: int,
    completed_count: int,
) -> None:
    path = output_dir / "checkpoints" / dataset / f"rank_{rank:04d}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(f".tmp.{os.getpid()}")
    temporary.write_text(
        json.dumps(
            {
                "dataset": dataset,
                "rank": rank,
                "byte_offset": byte_offset,
                "completed_count": completed_count,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def process_dataset(
    *,
    dataset: str,
    input_path: Path,
    root: Path,
    output_dir: Path,
    rank: int,
    world_size: int,
    processor: Any,
    generate_batch: Callable[
        [Sequence[dict[str, Any]], Sequence[int]], Sequence[Sequence[str]]
    ],
    judge_batch: Callable[[Sequence[dict[str, Any]]], Sequence[bool]],
    k: int,
    base_seed: int,
    batch_size: int,
    max_records: int | None = None,
    heartbeat_callback: Callable[[], None] | None = None,
) -> dict[str, int]:
    if k < 2:
        raise ValueError("k must be at least 2")
    if batch_size < 1:
        raise ValueError("batch_size must be at least 1")

    result_path = output_dir / dataset / "results" / f"rank_{rank:04d}.jsonl"
    error_path = output_dir / "errors" / f"rank_{rank:04d}.jsonl"
    result_path.parent.mkdir(parents=True, exist_ok=True)
    error_path.parent.mkdir(parents=True, exist_ok=True)
    for correct_count in range(k - 1):
        repair_jsonl_tail(
            output_dir
            / ".parts"
            / dataset
            / f"correct_{correct_count}"
            / f"rank_{rank:04d}.jsonl"
        )
    completed_offsets = _read_completed_offsets(result_path, error_path, dataset)
    counters = {"completed": 0, "errors": 0, "skipped": len(completed_offsets)}
    batch: list[tuple[int, dict[str, Any], dict[str, Any], str, int]] = []

    with (
        result_path.open("a", encoding="utf-8") as result_handle,
        error_path.open("a", encoding="utf-8") as error_handle,
    ):

        def write_error(offset: int, error: Exception) -> None:
            error_handle.write(
                _json_line(
                    {
                        "dataset": dataset,
                        "byte_offset": offset,
                        "result_index": f"{dataset}:{offset}",
                        "error_type": type(error).__name__,
                        "error": str(error),
                    }
                )
            )
            error_handle.flush()
            counters["errors"] += 1
            if heartbeat_callback is not None:
                heartbeat_callback()
            _write_checkpoint(
                output_dir,
                dataset,
                rank,
                offset,
                counters["completed"] + counters["errors"],
            )

        def run_batch() -> None:
            if not batch:
                return
            try:
                generated = generate_batch(
                    [item[2] for item in batch],
                    [item[4] for item in batch],
                )
                if len(generated) != len(batch):
                    raise ValueError(
                        f"generator returned {len(generated)} rows for {len(batch)} inputs"
                    )
                judgment_ranges: dict[int, tuple[int, int]] = {}
                judgments: dict[int, Sequence[bool]] = {}
                judge_inputs = []
                for item_index, (item, candidates) in enumerate(zip(batch, generated)):
                    if len(candidates) != k:
                        raise ValueError(
                            f"generator returned {len(candidates)} candidates; expected {k}"
                        )
                    _, row, prompt_input, reference, _ = item
                    if not requires_model_judge(reference):
                        continue
                    start = len(judge_inputs)
                    judge_inputs.extend(
                        build_judge_input(
                            row,
                            reference,
                            str(candidate),
                            processor,
                            prompt_input,
                        )
                        for candidate in candidates
                    )
                    judgment_ranges[item_index] = (start, len(judge_inputs))
                if judge_inputs:
                    judge_results = list(judge_batch(judge_inputs))
                    if len(judge_results) != len(judge_inputs):
                        raise ValueError(
                            "judge returned "
                            f"{len(judge_results)} results for {len(judge_inputs)} inputs"
                        )
                    judgments = {
                        item_index: judge_results[start:end]
                        for item_index, (start, end) in judgment_ranges.items()
                    }
            except Exception as error:
                failed_batch = list(batch)
                batch.clear()
                if len(failed_batch) > 1:
                    for item in failed_batch:
                        batch.append(item)
                        run_batch()
                else:
                    write_error(failed_batch[0][0], error)
                return

            for item_index, (item, candidates) in enumerate(zip(batch, generated)):
                offset, row, _, reference, _ = item
                try:
                    correct_values = judgments.get(item_index)
                    if correct_values is None:
                        correct_values = [
                            answers_equal(reference, candidate)
                            for candidate in candidates
                        ]
                    generations = [
                        {
                            "text": str(candidate),
                            "extracted_answer": extract_answer(candidate),
                            "correct": correct,
                        }
                        for candidate, correct in zip(candidates, correct_values)
                    ]
                    correct_count = sum(
                        generation["correct"] for generation in generations
                    )
                    result_index = f"{dataset}:{offset}"
                    result = {
                        "dataset": dataset,
                        "byte_offset": offset,
                        "result_index": result_index,
                        "reference_answer": extract_answer(reference),
                        "correct_count": correct_count,
                        "generations": generations,
                    }
                    if correct_count <= k - 2:
                        bucket_path = (
                            output_dir
                            / ".parts"
                            / dataset
                            / f"correct_{correct_count}"
                            / f"rank_{rank:04d}.jsonl"
                        )
                        bucket_path.parent.mkdir(parents=True, exist_ok=True)
                        bucket_record = dict(row)
                        bucket_record["_pass_at_k"] = {
                            "k": k,
                            "correct_count": correct_count,
                            "dataset": dataset,
                            "result_index": result_index,
                        }
                        with bucket_path.open("a", encoding="utf-8") as bucket_handle:
                            bucket_handle.write(_json_line(bucket_record))
                            bucket_handle.flush()
                    result_handle.write(_json_line(result))
                    result_handle.flush()
                    counters["completed"] += 1
                except Exception as error:
                    write_error(offset, error)
                    continue
                if heartbeat_callback is not None:
                    heartbeat_callback()
                _write_checkpoint(
                    output_dir,
                    dataset,
                    rank,
                    offset,
                    counters["completed"] + counters["errors"],
                )
            batch.clear()

        for offset, row in iter_jsonl_shard(
            input_path,
            rank=rank,
            world_size=world_size,
            completed_offsets=completed_offsets,
            max_records=max_records,
        ):
            if isinstance(row, JsonlRecordError):
                write_error(offset, row)
                continue
            try:
                prompt_input = build_prompt_input(row, processor, root)
                reference = str(row["messages"][-1]["content"])
                batch.append(
                    (
                        offset,
                        row,
                        prompt_input,
                        reference,
                        stable_seed(base_seed, dataset, offset),
                    )
                )
            except Exception as error:
                write_error(offset, error)
                continue
            if len(batch) >= batch_size:
                run_batch()
        run_batch()
    return counters


def ensure_run_config(output_dir: Path, config: dict[str, Any]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "run_config.json"
    encoded = json.dumps(config, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    try:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL)
    except FileExistsError:
        current = None
        for _ in range(100):
            try:
                current = json.loads(path.read_text(encoding="utf-8"))
                break
            except json.JSONDecodeError:
                time.sleep(0.05)
        if current is None:
            raise RuntimeError(f"run configuration is incomplete: {path}")
        if current != config:
            raise ValueError(
                "existing run configuration does not match the requested configuration"
            )
    else:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())


def pass_at_k_estimate(correct_count: int, sample_count: int, k: int) -> float:
    if correct_count <= 0:
        return 0.0
    if sample_count - correct_count < k:
        return 1.0
    return 1.0 - (
        math.comb(sample_count - correct_count, k) / math.comb(sample_count, k)
    )


def _merge_bucket(
    output_dir: Path,
    dataset: str,
    correct_count: int,
    allowed_result_indices: set[str],
) -> int:
    destination = output_dir / dataset / f"correct_{correct_count}.jsonl"
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(f".tmp.{os.getpid()}")
    seen: set[str] = set()
    with temporary.open("w", encoding="utf-8") as output:
        part_dir = output_dir / ".parts" / dataset / f"correct_{correct_count}"
        for part in sorted(part_dir.glob("rank_*.jsonl")) if part_dir.exists() else ():
            repair_jsonl_tail(part)
            with part.open(encoding="utf-8") as handle:
                for line in handle:
                    if not line.strip():
                        continue
                    record = json.loads(line)
                    result_index = str(record["_pass_at_k"]["result_index"])
                    if (
                        result_index not in allowed_result_indices
                        or result_index in seen
                    ):
                        continue
                    seen.add(result_index)
                    output.write(_json_line(record))
    temporary.replace(destination)
    return len(seen)


def merge_outputs(
    *,
    output_dir: Path,
    datasets: Sequence[str],
    k: int,
) -> dict[str, Any]:
    summary: dict[str, Any] = {"k": k, "datasets": {}}
    all_errors: dict[str, set[str]] = {dataset: set() for dataset in datasets}
    error_dir = output_dir / "errors"
    if error_dir.exists():
        for error_path in sorted(error_dir.glob("rank_*.jsonl")):
            repair_jsonl_tail(error_path)
            with error_path.open(encoding="utf-8") as handle:
                for line in handle:
                    if not line.strip():
                        continue
                    record = json.loads(line)
                    dataset = record.get("dataset")
                    if dataset in all_errors:
                        all_errors[dataset].add(str(record["result_index"]))

    for dataset in datasets:
        count_by_correct = {str(value): 0 for value in range(k + 1)}
        result_correct_counts: dict[str, int] = {}
        result_dir = output_dir / dataset / "results"
        if result_dir.exists():
            for result_path in sorted(result_dir.glob("rank_*.jsonl")):
                repair_jsonl_tail(result_path)
                with result_path.open(encoding="utf-8") as handle:
                    for line in handle:
                        if not line.strip():
                            continue
                        record = json.loads(line)
                        result_index = str(record["result_index"])
                        if result_index in result_correct_counts:
                            continue
                        correct_count = int(record["correct_count"])
                        result_correct_counts[result_index] = correct_count
                        count_by_correct[str(correct_count)] += 1

        for correct_count in range(k - 1):
            _merge_bucket(
                output_dir,
                dataset,
                correct_count,
                {
                    result_index
                    for result_index, value in result_correct_counts.items()
                    if value == correct_count
                },
            )

        completed = len(result_correct_counts)
        remaining_errors = all_errors[dataset] - result_correct_counts.keys()
        pass_values = {}
        for pass_k in range(1, k + 1):
            total = sum(
                count
                * pass_at_k_estimate(
                    int(correct_count),
                    k,
                    pass_k,
                )
                for correct_count, count in count_by_correct.items()
            )
            pass_values[str(pass_k)] = total / completed if completed else 0.0

        summary["datasets"][dataset] = {
            "completed": completed,
            "errors": len(remaining_errors),
            "total": completed + len(remaining_errors),
            "correct_counts": count_by_correct,
            "pass_at_k": pass_values,
        }

    summary_path = output_dir / "summary.json"
    temporary = summary_path.with_suffix(f".tmp.{os.getpid()}")
    temporary.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(summary_path)
    return summary


def validate_summary_totals(
    summary: dict[str, Any],
    input_paths: dict[str, Path],
) -> None:
    for dataset, path in input_paths.items():
        with path.open("rb") as handle:
            expected = sum(1 for line in handle if line.strip())
        actual = int(summary["datasets"][dataset]["total"])
        if actual != expected:
            raise RuntimeError(
                f"{dataset} result count mismatch: expected {expected}, got {actual}"
            )


def wait_for_workers(
    output_dir: Path,
    *,
    world_size: int,
    timeout_seconds: float = 0,
    poll_seconds: float = 10,
    startup_timeout_seconds: float = 600,
    stale_timeout_seconds: float = 7200,
) -> None:
    status_dir = output_dir / "_status"
    deadline = time.monotonic() + timeout_seconds if timeout_seconds > 0 else None
    wait_started = time.time()
    while True:
        failures = sorted(status_dir.glob("rank_*.failed.json"))
        if failures:
            failure = json.loads(failures[0].read_text(encoding="utf-8"))
            failed_rank = failure.get("rank")
            if failed_rank is None:
                failed_rank = int(failures[0].name.split("_", 1)[1].split(".", 1)[0])
            raise RuntimeError(
                f"rank {failed_rank} failed: {failure.get('error', 'unknown error')}"
            )
        missing = [
            rank
            for rank in range(world_size)
            if not (status_dir / f"rank_{rank:04d}.success").exists()
        ]
        if not missing:
            return
        now = time.time()
        for rank in missing:
            heartbeat = status_dir / f"rank_{rank:04d}.heartbeat"
            if heartbeat.exists():
                if now - heartbeat.stat().st_mtime > stale_timeout_seconds:
                    raise RuntimeError(f"rank {rank} heartbeat is stale")
            elif now - wait_started > startup_timeout_seconds:
                raise RuntimeError(f"rank {rank} did not start")
        if deadline is not None and time.monotonic() >= deadline:
            raise TimeoutError(f"timed out waiting for ranks: {missing}")
        time.sleep(poll_seconds)


def _version_tuple(version: str) -> tuple[int, ...]:
    match = re.match(r"(\d+)\.(\d+)\.(\d+)", version)
    if match is None:
        raise RuntimeError(f"cannot parse vLLM version: {version}")
    return tuple(int(value) for value in match.groups())


def validate_runtime_dependencies(
    version_getter: Callable[[str], str] | None = None,
) -> dict[str, str]:
    get_version = version_getter or importlib.metadata.version
    versions = {}
    for distribution in (
        "vllm",
        "qwen-vl-utils",
        "transformers",
        "Pillow",
    ):
        try:
            versions[distribution] = get_version(distribution)
        except importlib.metadata.PackageNotFoundError as error:
            raise RuntimeError(
                f"required package is not installed: {distribution}"
            ) from error
    if _version_tuple(versions["vllm"]) < (0, 11, 0):
        raise RuntimeError(f"vLLM >= 0.11.0 is required, found {versions['vllm']}")
    return versions


def configure_vllm_multiprocessing() -> None:
    os.environ["VLLM_WORKER_MULTIPROC_METHOD"] = "spawn"


class VLLMGenerator:
    def __init__(
        self,
        *,
        model: Path,
        k: int,
        temperature: float,
        top_p: float,
        max_tokens: int,
        max_model_len: int,
        max_num_seqs: int,
        gpu_memory_utilization: float,
        max_images_per_prompt: int = 8,
    ) -> None:
        if max_images_per_prompt < 1:
            raise ValueError("max_images_per_prompt must be at least 1")
        configure_vllm_multiprocessing()
        validate_runtime_dependencies()

        from transformers import AutoProcessor
        from vllm import LLM, SamplingParams

        self._sampling_params_class = SamplingParams
        self._k = k
        self._temperature = temperature
        self._top_p = top_p
        self._max_tokens = max_tokens
        self.processor = AutoProcessor.from_pretrained(str(model))
        self._llm = LLM(
            model=str(model),
            tensor_parallel_size=1,
            dtype="bfloat16",
            max_model_len=max_model_len,
            max_num_seqs=max_num_seqs,
            gpu_memory_utilization=gpu_memory_utilization,
            limit_mm_per_prompt={"image": max_images_per_prompt, "video": 0},
            mm_processor_cache_gb=0,
            generation_config="vllm",
        )

    def generate_batch(
        self,
        inputs: Sequence[dict[str, Any]],
        seeds: Sequence[int],
    ) -> list[list[str]]:
        sampling_params = [
            self._sampling_params_class(
                n=self._k,
                temperature=self._temperature,
                top_p=self._top_p,
                max_tokens=self._max_tokens,
                seed=seed,
            )
            for seed in seeds
        ]
        outputs = self._llm.generate(
            list(inputs),
            sampling_params=sampling_params,
            use_tqdm=False,
        )
        return [[candidate.text for candidate in output.outputs] for output in outputs]

    def judge_batch(
        self,
        inputs: Sequence[dict[str, Any]],
    ) -> list[bool]:
        sampling_params = self._sampling_params_class(
            n=1,
            temperature=0.0,
            max_tokens=4,
        )
        outputs = self._llm.generate(
            list(inputs),
            sampling_params=sampling_params,
            use_tqdm=False,
        )
        return [parse_judge_verdict(output.outputs[0].text) for output in outputs]


def _shared_config(args: argparse.Namespace) -> dict[str, Any]:
    return {
        "model": str(Path(args.model)),
        "datasets": list(args.datasets),
        "train_multi": str(Path(args.train_multi)),
        "train_text": str(Path(args.train_text)),
        "world_size": args.world_size,
        "k": args.k,
        "temperature": args.temperature,
        "top_p": args.top_p,
        "max_tokens": args.max_tokens,
        "seed": args.seed,
        "max_model_len": args.max_model_len,
        "max_num_seqs": args.max_num_seqs,
        "max_images_per_prompt": args.max_images_per_prompt,
        "gpu_memory_utilization": args.gpu_memory_utilization,
        "batch_size_multi": args.batch_size_multi,
        "batch_size_text": args.batch_size_text,
        "max_records_per_rank": args.max_records_per_rank,
    }


def _validate_worker_paths(
    root: Path,
    model: Path,
    input_paths: dict[str, Path],
    datasets: Sequence[str],
) -> None:
    if not root.is_dir():
        raise FileNotFoundError(f"project root does not exist: {root}")
    if not model.is_dir():
        raise FileNotFoundError(f"model directory does not exist: {model}")
    for dataset in datasets:
        path = input_paths[dataset]
        if not path.is_file():
            raise FileNotFoundError(f"input dataset does not exist: {path}")


def run_worker(args: argparse.Namespace) -> dict[str, dict[str, int]]:
    root = Path(args.root)
    model = Path(args.model)
    output_dir = Path(args.output_dir)
    input_paths = {
        "train_multi": Path(args.train_multi),
        "train_text": Path(args.train_text),
    }

    status_dir = output_dir / "_status"
    status_dir.mkdir(parents=True, exist_ok=True)
    success_path = status_dir / f"rank_{args.rank:04d}.success"
    failure_path = status_dir / f"rank_{args.rank:04d}.failed.json"
    heartbeat_path = status_dir / f"rank_{args.rank:04d}.heartbeat"
    success_path.unlink(missing_ok=True)
    failure_path.unlink(missing_ok=True)
    heartbeat_path.touch()

    try:
        _validate_worker_paths(root, model, input_paths, args.datasets)
        config = _shared_config(args)
        ensure_run_config(output_dir, config)
        generator = VLLMGenerator(
            model=model,
            k=args.k,
            temperature=args.temperature,
            top_p=args.top_p,
            max_tokens=args.max_tokens,
            max_model_len=args.max_model_len,
            max_num_seqs=args.max_num_seqs,
            gpu_memory_utilization=args.gpu_memory_utilization,
            max_images_per_prompt=args.max_images_per_prompt,
        )
        counters: dict[str, dict[str, int]] = {}
        for dataset in args.datasets:
            counters[dataset] = process_dataset(
                dataset=dataset,
                input_path=input_paths[dataset],
                root=root,
                output_dir=output_dir,
                rank=args.rank,
                world_size=args.world_size,
                processor=generator.processor,
                generate_batch=generator.generate_batch,
                judge_batch=generator.judge_batch,
                k=args.k,
                base_seed=args.seed,
                batch_size=(
                    args.batch_size_multi
                    if dataset == "train_multi"
                    else args.batch_size_text
                ),
                max_records=args.max_records_per_rank,
                heartbeat_callback=heartbeat_path.touch,
            )
        success_path.write_text(
            json.dumps(counters, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        return counters
    except Exception as error:
        failure_path.write_text(
            json.dumps(
                {
                    "rank": args.rank,
                    "error_type": type(error).__name__,
                    "error": str(error),
                    "traceback": traceback.format_exc(),
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        raise


def run_merge(args: argparse.Namespace) -> dict[str, Any]:
    output_dir = Path(args.output_dir)
    wait_for_workers(
        output_dir,
        world_size=args.world_size,
        timeout_seconds=args.wait_timeout,
        poll_seconds=args.poll_seconds,
        startup_timeout_seconds=args.startup_timeout,
        stale_timeout_seconds=args.stale_timeout,
    )
    config_path = output_dir / "run_config.json"
    if not config_path.is_file():
        raise FileNotFoundError(f"run configuration does not exist: {config_path}")
    config = json.loads(config_path.read_text(encoding="utf-8"))
    if config["world_size"] != args.world_size or config["k"] != args.k:
        raise ValueError("merge arguments do not match the run configuration")
    if config["datasets"] != list(args.datasets):
        raise ValueError("merge datasets do not match the run configuration")
    summary = merge_outputs(
        output_dir=output_dir,
        datasets=args.datasets,
        k=args.k,
    )
    if config["max_records_per_rank"] is None:
        validate_summary_totals(
            summary,
            {dataset: Path(config[dataset]) for dataset in args.datasets},
        )
    return summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Qwen3-VL Pass@k sampler")
    subparsers = parser.add_subparsers(dest="command", required=True)

    worker = subparsers.add_parser("worker")
    worker.add_argument("--root", default=DEFAULT_ROOT)
    worker.add_argument("--model", default=DEFAULT_MODEL)
    worker.add_argument("--train-multi", default=DEFAULT_MULTI_DATA)
    worker.add_argument("--train-text", default=DEFAULT_TEXT_DATA)
    worker.add_argument("--output-dir", default=DEFAULT_OUTPUT)
    worker.add_argument(
        "--datasets",
        nargs="+",
        choices=("train_multi", "train_text"),
        default=["train_multi", "train_text"],
    )
    worker.add_argument("--rank", type=int, required=True)
    worker.add_argument("--world-size", type=int, required=True)
    worker.add_argument("--k", type=int, default=8)
    worker.add_argument("--temperature", type=float, default=1.0)
    worker.add_argument("--top-p", type=float, default=1.0)
    worker.add_argument("--max-tokens", type=int, default=2048)
    worker.add_argument("--seed", type=int, default=42)
    worker.add_argument("--max-model-len", type=int, default=131072)
    worker.add_argument("--max-num-seqs", type=int, default=64)
    worker.add_argument("--max-images-per-prompt", type=int, default=8)
    worker.add_argument("--gpu-memory-utilization", type=float, default=0.90)
    worker.add_argument("--batch-size-multi", type=int, default=4)
    worker.add_argument("--batch-size-text", type=int, default=8)
    worker.add_argument("--max-records-per-rank", type=int)

    merge = subparsers.add_parser("merge")
    merge.add_argument("--root", default=DEFAULT_ROOT)
    merge.add_argument("--output-dir", default=DEFAULT_OUTPUT)
    merge.add_argument(
        "--datasets",
        nargs="+",
        choices=("train_multi", "train_text"),
        default=["train_multi", "train_text"],
    )
    merge.add_argument("--world-size", type=int, required=True)
    merge.add_argument("--k", type=int, default=8)
    merge.add_argument("--wait-timeout", type=float, default=0)
    merge.add_argument("--poll-seconds", type=float, default=10)
    merge.add_argument("--startup-timeout", type=float, default=600)
    merge.add_argument("--stale-timeout", type=float, default=7200)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "worker":
        run_worker(args)
    elif args.command == "merge":
        run_merge(args)
    else:
        raise ValueError(f"unsupported command: {args.command}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
