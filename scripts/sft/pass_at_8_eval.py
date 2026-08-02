"""SFT 期间运行的多图 Pass@8 评估基础组件。"""

from __future__ import annotations

import json
import math
import os
import re
import time
import unicodedata
import urllib.request
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any


_ANSWER_RE = re.compile(r"(?:答案|answer)\s*[:：]\s*", re.IGNORECASE)
_CHOICE_RE = re.compile(r"^\s*([A-H])(?:\s*[.、:：)]|\s|$)", re.IGNORECASE)
_NUMBER_RE = re.compile(r"^\s*[-+]?\d+(?:,\d{3})*(?:\.\d+)?%?\s*$")
_DATE_RE = re.compile(r"^(\d{4})[-/.年](\d{1,2})[-/.月](\d{1,2})日?$")
_PAGE_RE = re.compile(r"第\s*(\d+)\s*页|page\s*(\d+)", re.IGNORECASE)


def extract_answer(value: Any) -> str:
    text = str(value).strip()
    matches = list(_ANSWER_RE.finditer(text))
    return text[matches[-1].end():].strip() if matches else text


def _normalize_text(value: str) -> str:
    value = unicodedata.normalize("NFKC", value).casefold()
    value = re.sub(r"\s+", " ", value)
    return value.strip(" \t\r\n.,;:!?，。；：！？()[]{}<>")


def _number(value: str) -> tuple[Decimal, bool] | None:
    if not _NUMBER_RE.fullmatch(value):
        return None
    normalized = value.strip().replace(",", "")
    percent = normalized.endswith("%")
    if percent:
        normalized = normalized[:-1]
    try:
        return Decimal(normalized), percent
    except InvalidOperation:
        return None


def _number_equal(reference: tuple[Decimal, bool], candidate: tuple[Decimal, bool]) -> bool:
    if reference[1] != candidate[1]:
        return False
    expected, actual = reference[0], candidate[0]
    if expected == 0:
        return actual == 0
    return abs(actual - expected) <= abs(expected) * Decimal("0.01")


def _date(value: str) -> tuple[int, int, int] | None:
    match = _DATE_RE.fullmatch(value.strip())
    if match is None:
        return None
    return tuple(int(part) for part in match.groups())


def _pages(value: str) -> set[int] | None:
    pages = {int(first or second) for first, second in _PAGE_RE.findall(value)}
    return pages or None


def _json_value(value: str) -> Any | None:
    if not value.lstrip().startswith(("{", "[")):
        return None
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return None


def programmatic_judge(reference: Any, candidate: Any) -> bool | None:
    """返回程序判分结论；开放式答案返回 ``None`` 交由模型裁判。"""
    expected = extract_answer(reference)
    actual = extract_answer(candidate)
    expected_choice = _CHOICE_RE.match(expected)
    if expected_choice is not None:
        actual_choice = _CHOICE_RE.match(actual)
        return actual_choice is not None and expected_choice.group(1).casefold() == actual_choice.group(1).casefold()

    expected_number = _number(expected)
    actual_number = _number(actual)
    if expected_number is not None:
        return actual_number is not None and _number_equal(expected_number, actual_number)

    expected_date = _date(expected)
    if expected_date is not None:
        return _date(actual) == expected_date

    expected_pages = _pages(expected)
    if expected_pages is not None:
        return _pages(actual) == expected_pages

    expected_json = _json_value(expected)
    if expected_json is not None:
        return _json_value(actual) == expected_json

    if len(expected) <= 32 and re.fullmatch(r"[A-Za-z0-9_\s,./\-]+", expected):
        return _normalize_text(expected) == _normalize_text(actual)
    return None


def estimate_cost(row: dict[str, Any]) -> float:
    pixels = sum(int(value) for value in row.get("image_pixels", []))
    prompt = len(str(row["messages"][0]["content"]))
    answer = len(str(row["messages"][-1]["content"]))
    return float(len(row.get("images", [])) * 256 + pixels / 1_000_000 + prompt / 4 + answer / 4)


def load_benchmark(path: Path, root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for index, line in enumerate(handle):
            if not line.strip():
                continue
            row = json.loads(line)
            image_paths = []
            for image in row.get("images", []):
                image_path = Path(image)
                image_paths.append(image_path if image_path.is_absolute() else root / image_path)
            row["sample_id"] = f"my_benchmark:{index:06d}"
            row["image_paths"] = image_paths
            row["image_pixels"] = _image_pixels(image_paths)
            rows.append(row)
    return rows


def _image_pixels(paths: list[Path]) -> list[int]:
    if not paths:
        return []
    from PIL import Image

    pixels = []
    for path in paths:
        if not path.is_file():
            pixels.append(0)
            continue
        with Image.open(path) as image:
            pixels.append(image.width * image.height)
    return pixels


@dataclass
class EvaluationQueue:
    root: Path
    tasks: list[dict[str, Any]]

    def initialize(self) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        for task in sorted(self.tasks, key=lambda item: (-float(item["cost"]), item["sample_id"])):
            path = self.root / f"{task['sample_id'].replace(':', '_')}.json"
            if not path.exists():
                path.write_text(json.dumps(task, ensure_ascii=False) + "\n", encoding="utf-8")

    def claim(self, worker: str) -> dict[str, Any] | None:
        for task_path in sorted(self.root.glob("*.json")):
            claim_path = task_path.with_suffix(f".claimed.{worker}")
            try:
                os.replace(task_path, claim_path)
            except FileNotFoundError:
                continue
            return json.loads(claim_path.read_text(encoding="utf-8"))
        return None


def summarize_results(
    results: list[dict[str, Any]],
    *,
    total: int,
    errors: list[dict[str, Any]],
) -> dict[str, Any]:
    task_totals: dict[str, int] = {}
    task_passed: dict[str, int] = {}
    task_first_passed: dict[str, int] = {}
    passed = 0
    first_passed = 0
    for result in results:
        task = str(result["task"])
        correct = int(result["correct_count"]) > 0
        first_correct = bool(result["first_correct"])
        task_totals[task] = task_totals.get(task, 0) + 1
        task_passed[task] = task_passed.get(task, 0) + int(correct)
        task_first_passed[task] = task_first_passed.get(task, 0) + int(first_correct)
        passed += int(correct)
        first_passed += int(first_correct)
    task_summary = {
        task: {
            "completed": task_totals[task],
            "pass_at_1": task_first_passed[task] / task_totals[task],
            "pass_at_8": task_passed[task] / task_totals[task],
        }
        for task in sorted(task_totals)
    }
    return {
        "total": total,
        "completed": len(results),
        "error_count": len(errors),
        "coverage": len(results) / total if total else 0.0,
        "pass_at_1": first_passed / total if total else 0.0,
        "pass_at_8": passed / total if total else 0.0,
        "tasks": task_summary,
    }


def _dist_state() -> tuple[int, int, Any]:
    try:
        import torch.distributed as dist

        if dist.is_available() and dist.is_initialized():
            return dist.get_rank(), dist.get_world_size(), dist
    except ImportError:
        pass
    return 0, 1, None


def _barrier(dist: Any) -> None:
    if dist is not None:
        dist.barrier()


def _broadcast_metrics(metrics: dict[str, Any] | None, dist: Any) -> dict[str, Any]:
    if dist is None:
        return metrics or {}
    payload = [metrics]
    dist.broadcast_object_list(payload, src=0)
    return payload[0] or {}


def _write_jsonl(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def _make_messages(row: dict[str, Any]) -> list[dict[str, Any]]:
    question = str(row["messages"][0]["content"])
    content: list[dict[str, Any]] = [{"type": "image", "image": str(path)} for path in row["image_paths"]]
    content.append({"type": "text", "text": question.replace("<image>", "")})
    return [{"role": "user", "content": content}]


def _generate_candidates(model: Any, processor: Any, row: dict[str, Any], seed: int) -> list[str]:
    import torch

    try:
        from qwen_vl_utils import process_vision_info
    except ImportError as error:
        raise RuntimeError("qwen-vl-utils is required for Pass@8 evaluation") from error

    messages = _make_messages(row)
    prompt = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    image_inputs, video_inputs = process_vision_info(messages)
    inputs = processor(
        text=[prompt],
        images=image_inputs,
        videos=video_inputs,
        padding=True,
        return_tensors="pt",
    )
    device = getattr(model, "device", None)
    if device is None:
        device = next(model.parameters()).device
    inputs = {key: value.to(device) if hasattr(value, "to") else value for key, value in inputs.items()}
    prompt_length = int(inputs["input_ids"].shape[1])
    torch.manual_seed(seed)
    generated = model.generate(
        **inputs,
        do_sample=True,
        temperature=1.0,
        top_p=1.0,
        num_return_sequences=8,
        max_new_tokens=2048,
        use_cache=True,
    )
    return processor.batch_decode(generated[:, prompt_length:], skip_special_tokens=True)


def _judge_with_server(judge_url: str, row: dict[str, Any], reference: str, candidate: str) -> bool:
    question = str(row["messages"][0]["content"]).replace("<image>", "")
    content = (
        "判断候选答案与标准答案在原问题下是否等价。只输出 CORRECT 或 INCORRECT。\n"
        f"问题：{question}\n标准答案：{reference}\n候选答案：{candidate}"
    )
    payload = json.dumps(
        {
            "model": "qwen4-judge",
            "messages": [{"role": "user", "content": content}],
            "temperature": 0.0,
            "max_tokens": 8,
        },
        ensure_ascii=False,
    ).encode("utf-8")
    request = urllib.request.Request(
        judge_url.rstrip("/") + "/v1/chat/completions",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=180) as response:
        body = json.loads(response.read().decode("utf-8"))
    verdict = str(body["choices"][0]["message"]["content"]).strip().upper()
    if verdict == "CORRECT":
        return True
    if verdict == "INCORRECT":
        return False
    raise ValueError(f"invalid judge verdict: {verdict!r}")


def _evaluate_row(model: Any, processor: Any, judge_url: str, row: dict[str, Any], step: int) -> dict[str, Any]:
    index = int(row["sample_id"].rsplit(":", 1)[1])
    candidates = _generate_candidates(model, processor, row, 42 + step * 1_000_003 + index * 101)
    reference = str(row["messages"][-1]["content"])
    judged_by_model = 0
    generations = []
    for candidate in candidates:
        correct = programmatic_judge(reference, candidate)
        route = "programmatic"
        if correct is None:
            route = "model"
            judged_by_model += 1
            correct = _judge_with_server(judge_url, row, reference, candidate)
        generations.append(
            {
                "text": candidate,
                "extracted_answer": extract_answer(candidate),
                "correct": bool(correct),
                "judge": route,
            }
        )
    return {
        "sample_id": row["sample_id"],
        "task": row["task"],
        "reference_answer": extract_answer(reference),
        "correct_count": sum(item["correct"] for item in generations),
        "first_correct": bool(generations[0]["correct"]),
        "programmatic_count": 8 - judged_by_model,
        "model_judged_count": judged_by_model,
        "generations": generations,
    }


def _status(
    path: Path,
    *,
    claimed: int,
    completed: int,
    errors: int,
    global_remaining: int,
    started_at: float,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "planned": claimed,
                "completed": completed,
                "remaining": max(0, claimed - completed - errors),
                "global_remaining": global_remaining,
                "errors": errors,
                "heartbeat": time.time(),
                "elapsed_seconds": round(time.monotonic() - started_at, 3),
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def run_distributed_evaluation(
    *,
    model: Any,
    processor: Any,
    template: Any,
    benchmark_path: Path,
    project_root: Path,
    output_dir: Path,
    step: int,
    judge_url: str,
    max_samples: int | None,
) -> dict[str, Any]:
    """在当前训练权重上评估；每个 rank 动态领取细粒度任务。"""
    rank, _, dist = _dist_state()
    step_dir = output_dir / f"step-{step:06d}"
    queue_dir = step_dir / "queue"
    status_path = step_dir / "status" / f"rank_{rank:04d}.json"
    if rank == 0:
        rows = load_benchmark(benchmark_path, project_root)
        if max_samples is not None:
            rows = sorted(rows, key=lambda item: (-len(item["image_paths"]), item["sample_id"]))[:max_samples]
        tasks = [{"sample_id": row["sample_id"], "cost": estimate_cost(row)} for row in rows]
        EvaluationQueue(queue_dir, tasks).initialize()
        (step_dir / "run_config.json").parent.mkdir(parents=True, exist_ok=True)
        (step_dir / "run_config.json").write_text(
            json.dumps({"step": step, "total": len(rows), "max_samples": max_samples}, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    _barrier(dist)
    rows = load_benchmark(benchmark_path, project_root)
    if max_samples is not None:
        rows = sorted(rows, key=lambda item: (-len(item["image_paths"]), item["sample_id"]))[:max_samples]
    rows_by_id = {row["sample_id"]: row for row in rows}
    queue = EvaluationQueue(queue_dir, [])
    result_path = step_dir / "predictions" / f"rank_{rank:04d}.jsonl"
    error_path = step_dir / "errors" / f"rank_{rank:04d}.jsonl"
    active_processor = processor or getattr(template, "processor", None)
    if active_processor is None:
        raise RuntimeError("ms-swift trainer does not expose a processor")
    was_training = bool(model.training)
    model.eval()
    started_at = time.monotonic()
    claimed = completed = errors = 0
    _status(
        status_path,
        claimed=claimed,
        completed=completed,
        errors=errors,
        global_remaining=len(list(queue_dir.glob("*.json"))),
        started_at=started_at,
    )
    try:
        while (task := queue.claim(f"rank_{rank:04d}")) is not None:
            claimed += 1
            try:
                result = _evaluate_row(model, active_processor, judge_url, rows_by_id[task["sample_id"]], step)
                _write_jsonl(result_path, result)
                completed += 1
            except Exception as error:
                _write_jsonl(
                    error_path,
                    {"sample_id": task["sample_id"], "error_type": type(error).__name__, "error": str(error)},
                )
                errors += 1
            _status(
                status_path,
                claimed=claimed,
                completed=completed,
                errors=errors,
                global_remaining=len(list(queue_dir.glob("*.json"))),
                started_at=started_at,
            )
    finally:
        if was_training:
            model.train()
    _barrier(dist)
    metrics: dict[str, Any] | None = None
    if rank == 0:
        results = []
        errors_list = []
        for path in sorted((step_dir / "predictions").glob("rank_*.jsonl")):
            results.extend(json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip())
        for path in sorted((step_dir / "errors").glob("rank_*.jsonl")):
            errors_list.extend(json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip())
        (step_dir / "predictions.jsonl").write_text(
            "".join(json.dumps(item, ensure_ascii=False) + "\n" for item in results), encoding="utf-8"
        )
        (step_dir / "errors.jsonl").write_text(
            "".join(json.dumps(item, ensure_ascii=False) + "\n" for item in errors_list), encoding="utf-8"
        )
        summary = summarize_results(results, total=len(rows), errors=errors_list)
        summary["programmatic_count"] = sum(int(item["programmatic_count"]) for item in results)
        summary["model_judged_count"] = sum(int(item["model_judged_count"]) for item in results)
        summary["elapsed_seconds"] = round(time.monotonic() - started_at, 3)
        (step_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        metrics = {key: summary[key] for key in ("pass_at_1", "pass_at_8", "coverage", "error_count", "programmatic_count", "model_judged_count", "elapsed_seconds")}
        print(
            "INFO     | >> eval "
            f"step={step} pass_at_1={summary['pass_at_1']:.4f} pass_at_8={summary['pass_at_8']:.4f} coverage={summary['coverage']:.4f} "
            f"errors={summary['error_count']} programmatic={summary['programmatic_count']} "
            f"model_judged={summary['model_judged_count']} elapsed={summary['elapsed_seconds']:.1f}s",
            flush=True,
        )
        for task, task_metrics in summary["tasks"].items():
            print(
                "             "
                f"task={task} pass_at_1={task_metrics['pass_at_1']:.4f} pass_at_8={task_metrics['pass_at_8']:.4f} "
                f"completed={task_metrics['completed']}",
                flush=True,
            )
        for path in sorted((step_dir / "status").glob("rank_*.json")):
            status = json.loads(path.read_text(encoding="utf-8"))
            print(
                "             "
                f"{path.stem} planned={status['planned']} completed={status['completed']} "
                f"remaining={status['remaining']} global_remaining={status['global_remaining']} "
                f"errors={status['errors']} elapsed={status['elapsed_seconds']:.1f}s",
                flush=True,
            )
    _barrier(dist)
    return _broadcast_metrics(metrics, dist)
