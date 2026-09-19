#!/usr/bin/env python3
"""Clean FINAR-VL synthetic data with minimal format checks and Qwen235 scoring.

Every structurally valid row is sent to Qwen235. The model assigns one task
from the SFT sampler vocabulary and scores ten independent rubric items.
Each rubric item is exactly 0 or 0.5. Python recomputes the total score and
keeps rows with total_score >= 4.0 by default.
"""

from __future__ import annotations

import argparse
import ast
import base64
import io
import json
import os
import re
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_ROOT = PROJECT_ROOT / "data" / "synthetic" / "cleaned"
DEFAULT_MODEL = PROJECT_ROOT / "model" / "qwen235"

# task labels are loaded from the actual SFT sampler so construction/cleaning
# cannot drift from training-time task names.
def load_task_labels() -> tuple[str, ...]:
    tasks: set[str] = set()
    base = PROJECT_ROOT / "scripts" / "sft" / "sample_plan_base.py"
    wrapper = PROJECT_ROOT / "scripts" / "sft" / "sample_plan.py"
    if base.exists():
        tree = ast.parse(base.read_text(encoding="utf-8"))
        for node in tree.body:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == "TASK_TO_FAMILY":
                        value = ast.literal_eval(node.value)
                        if isinstance(value, dict):
                            tasks.update(str(key) for key in value)
    if wrapper.exists():
        text = wrapper.read_text(encoding="utf-8")
        tasks.update(re.findall(r'TASK_TO_FAMILY\\["([^"]+)"\\]\\s*=', text))
    if not tasks:
        raise RuntimeError("failed to load SFT task vocabulary from scripts/sft/sample_plan*.py")
    return tuple(sorted(tasks))


TASK_LABELS = load_task_labels()

RUBRIC_KEYS = (
    "answerability",
    "answer_correctness",
    "evidence_grounding",
    "financial_alignment",
    "reasoning_correctness",
    "instruction_following",
    "modality_grounding",
    "no_leakage_or_shortcut",
    "training_value",
    "clarity_and_integrity",
)

JUDGE_SYSTEM = """你是 FINAR-VL 金融训练数据质量审核器。

输入是一条候选 SFT 或 RL 训练样本，以及其原始图片（如果有）。
你只做两件事：
1. 从 task_labels 中选择一个且仅一个最匹配的 task；
2. 按下面 10 条 rubric 逐项评分。

每项只能给 0 或 0.5，禁止其他分值。各项独立判断。

1. answerability
0.5：给定题面、上下文和图片足以得到唯一、明确的答案。
0：材料不足、多解或问题含糊。

2. answer_correctness
0.5：监督答案或 solution 与材料中的事实、数字和关系一致。
0：存在事实、数值、方向、选项或结论错误。

3. evidence_grounding
0.5：答案中的关键事实和结论都能由给定材料支持。
0：存在材料外事实、幻觉或无依据推断。

4. financial_alignment
0.5：主体、期间、指标、合并/母公司/分部口径、币种、单位、比较基准等均一致。
0：存在混公司、混期间、混指标、混 scope、混单位或币种等问题。

5. reasoning_correctness
0.5：所需计算、比较、多跳推理、解释、归纳或因果关系逻辑成立。
0：公式、比较、推理链、解释或因果存在实质错误。
无需显式推理的任务，只要材料到答案的逻辑成立即可给 0.5。

6. instruction_following
0.5：监督答案真正回答问题，且答案类型、粒度和格式符合要求。
0：答非所问、遗漏关键要求或输出形式错误。

7. modality_grounding
0.5：纯文本任务合理使用文本；视觉任务确实依赖图片；多表、多图或跨模态任务真正使用相应多个证据。
0：图片只是装饰、视觉答案被文本完整泄露、应使用多个视觉证据却实际只依赖一个，或模态与任务不匹配。

8. no_leakage_or_shortcut
0.5：题面和上下文没有直接泄露监督答案，也不存在绕过目标能力的明显捷径。
0：答案、关键中间结果或视觉目标被直接暴露，几乎无需目标能力即可作答。

9. training_value
0.5：样本自然、信息充分、难度合理，并能有效训练所标 task 的能力。
0：机械拼接、无意义复杂化、极低信息量、模板垃圾或与 task 明显不匹配。
简单 OCR 或抽取题只要有效训练对应能力，也应给 0.5。

10. clarity_and_integrity
0.5：问题、上下文、答案或 solution 和必要推理清楚、完整、内部一致。
0：乱码、占位符、模板残留、自相矛盾、明显截断或生成错误。

task 标注规则：
- task 必须逐字来自 task_labels。
- 根据样本实际训练能力标注。
- 输入已有 task 仅作弱参考；若实际任务不同，应重新标注。

严格输出单个 JSON：
{
  "task": "从task_labels选择",
  "task_reason": "一句话理由",
  "rubric": {
    "answerability": {"score": 0.5, "reason": "简短原因"},
    "answer_correctness": {"score": 0.5, "reason": "简短原因"},
    "evidence_grounding": {"score": 0.5, "reason": "简短原因"},
    "financial_alignment": {"score": 0.5, "reason": "简短原因"},
    "reasoning_correctness": {"score": 0.5, "reason": "简短原因"},
    "instruction_following": {"score": 0.5, "reason": "简短原因"},
    "modality_grounding": {"score": 0.5, "reason": "简短原因"},
    "no_leakage_or_shortcut": {"score": 0.5, "reason": "简短原因"},
    "training_value": {"score": 0.5, "reason": "简短原因"},
    "clarity_and_integrity": {"score": 0.5, "reason": "简短原因"}
  }
}
不要输出 total_score 或 decision；由 Python 重算。
只输出 JSON。"""


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input", type=Path, action="append", required=True)
    p.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    p.add_argument("--model", type=Path, default=DEFAULT_MODEL)
    p.add_argument("--backend", choices=("vllm", "openai"), default="vllm")
    p.add_argument("--base-url", default=os.environ.get("FINAR_SYNTH_BASE_URL", "http://127.0.0.1:8000/v1"))
    p.add_argument("--api-key", default=os.environ.get("FINAR_SYNTH_API_KEY", "EMPTY"))
    p.add_argument("--tensor-parallel-size", type=int, default=8)
    p.add_argument("--gpu-memory-utilization", type=float, default=0.90)
    p.add_argument("--max-model-len", type=int, default=32768)
    p.add_argument("--threshold", type=float, default=4.0)
    p.add_argument("--max-samples", type=int, default=0)
    p.add_argument("--max-prompt-chars", type=int, default=30000)
    p.add_argument("--judge-retries", type=int, default=2)
    p.add_argument("--skip-image-existence-check", action="store_true")
    return p.parse_args()


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")


def iter_inputs(paths: list[Path]):
    for item in paths:
        files = sorted(item.rglob("*.jsonl")) if item.is_dir() else [item]
        for path in files:
            with path.open(encoding="utf-8-sig") as f:
                for line_no, raw in enumerate(f, 1):
                    raw = raw.strip()
                    if not raw:
                        continue
                    try:
                        yield path, line_no, json.loads(raw), ""
                    except Exception as exc:
                        yield path, line_no, None, f"json_parse_error:{exc}"


def content_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                parts.append(str(item.get("text") or ""))
            elif isinstance(item, str):
                parts.append(item)
        return "\n".join(parts)
    return str(content or "")


def resolve_image(value: str, source_file: Path) -> Path | None:
    path = Path(value)
    candidates = [path] if path.is_absolute() else [PROJECT_ROOT / path, source_file.parent / path]
    return next((p.resolve() for p in candidates if p.is_file()), None)


def format_check(row: Any, source_file: Path, check_images: bool):
    errors = []
    resolved_images = []
    if not isinstance(row, dict):
        return False, ["row_not_object"], []

    messages = row.get("messages")
    if not isinstance(messages, list) or not messages:
        errors.append("messages_missing_or_invalid")
        messages = []

    users, assistants = [], []
    for message in messages:
        if not isinstance(message, dict):
            errors.append("message_not_object")
            continue
        role = str(message.get("role") or "")
        text = content_text(message.get("content"))
        if role == "user":
            users.append(text)
        elif role == "assistant":
            assistants.append(text)

    if not any(x.strip() for x in users):
        errors.append("user_message_empty")
    if not any(x.strip() for x in assistants) and not str(row.get("solution") or row.get("answer") or "").strip():
        errors.append("supervision_target_empty")

    images = row.get("images", [])
    if images is None:
        images = []
    if not isinstance(images, list) or any(not isinstance(x, str) or not x.strip() for x in images):
        errors.append("images_invalid")
        images = []

    for image in images:
        resolved = resolve_image(image, source_file)
        if resolved is None:
            if check_images:
                errors.append(f"image_missing:{image}")
            continue
        if check_images:
            try:
                with Image.open(resolved) as img:
                    img.verify()
            except Exception:
                errors.append(f"image_unreadable:{image}")
                continue
        resolved_images.append(resolved)

    marker_count = "\n".join(users).count("<image>")
    if marker_count and marker_count != len(images):
        errors.append(f"image_marker_count_mismatch:markers={marker_count},images={len(images)}")
    return not errors, errors, resolved_images


def sample_for_judge(row: dict[str, Any], max_chars: int) -> str:
    payload = {
        "existing_task": row.get("task", ""),
        "messages": row.get("messages", []),
        "solution": row.get("solution", ""),
        "answer": row.get("answer", ""),
        "output_format": row.get("output_format", ""),
        "reward_type": row.get("reward_type", ""),
        "reward_subtype": row.get("reward_subtype", ""),
        "verifier_type": row.get("verifier_type", ""),
        "metadata": row.get("metadata", {}),
    }
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))[:max_chars]


class Runner:
    def __init__(self, args: argparse.Namespace):
        self.backend = args.backend
        self.model_name = str(args.model)
        if args.backend == "openai":
            from openai import OpenAI
            self.client = OpenAI(api_key=args.api_key, base_url=args.base_url)
        else:
            from transformers import AutoProcessor
            from vllm import LLM, SamplingParams
            self.processor = AutoProcessor.from_pretrained(self.model_name, trust_remote_code=True)
            self.llm = LLM(
                model=self.model_name,
                tensor_parallel_size=args.tensor_parallel_size,
                gpu_memory_utilization=args.gpu_memory_utilization,
                max_model_len=args.max_model_len,
                trust_remote_code=True,
                limit_mm_per_prompt={"image": 8},
            )
            self.SamplingParams = SamplingParams

    @staticmethod
    def parse_json(text: str) -> dict[str, Any]:
        fence = chr(96) * 3
        text = text.strip().replace(fence + "json", "").replace(fence, "").strip()
        start, end = text.find("{"), text.rfind("}")
        if start < 0 or end < start:
            raise ValueError("judge output has no JSON object")
        return json.loads(text[start:end + 1])

    def json(self, system: str, user: str, images: list[Path]) -> dict[str, Any]:
        if self.backend == "openai":
            content = [{"type": "text", "text": user}]
            for path in images[:8]:
                with Image.open(path) as img:
                    img = img.convert("RGB")
                    buf = io.BytesIO()
                    img.save(buf, format="JPEG", quality=90)
                data = base64.b64encode(buf.getvalue()).decode("ascii")
                content.append({"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + data}})
            out = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "system", "content": system}, {"role": "user", "content": content}],
                temperature=0.0,
                max_tokens=3000,
            )
            return self.parse_json(out.choices[0].message.content or "")

        from qwen_vl_utils import process_vision_info
        content = [{"type": "text", "text": user}]
        content.extend({"type": "image", "image": str(path)} for path in images[:8])
        messages = [{"role": "system", "content": system}, {"role": "user", "content": content}]
        prompt = self.processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        image_inputs, video_inputs = process_vision_info(messages)
        mm = {}
        if image_inputs:
            mm["image"] = image_inputs
        if video_inputs:
            mm["video"] = video_inputs
        out = self.llm.generate(
            [{"prompt": prompt, "multi_modal_data": mm}],
            self.SamplingParams(temperature=0.0, max_tokens=3000),
            use_tqdm=False,
        )
        return self.parse_json(out[0].outputs[0].text)


def validate_judgment(obj: dict[str, Any]):
    task = str(obj.get("task") or "")
    if task not in TASK_LABELS:
        return False, "invalid_task_label", 0.0
    rubric = obj.get("rubric")
    if not isinstance(rubric, dict) or set(rubric) != set(RUBRIC_KEYS):
        return False, "rubric_keys_invalid", 0.0

    total = 0.0
    for key in RUBRIC_KEYS:
        item = rubric.get(key)
        if not isinstance(item, dict):
            return False, f"rubric_item_invalid:{key}", 0.0
        score = item.get("score")
        if score not in (0, 0.0, 0.5):
            return False, f"rubric_score_invalid:{key}={score}", 0.0
        if not str(item.get("reason") or "").strip():
            return False, f"rubric_reason_empty:{key}", 0.0
        total += float(score)
    return True, "", round(total, 2)


def main() -> None:
    args = parse_args()
    args.output_root.mkdir(parents=True, exist_ok=True)
    runner = Runner(args)

    accepted, rejected, format_rejected, judge_failures = [], [], [], []
    counts = Counter()
    processed = 0
    task_labels_text = json.dumps(TASK_LABELS, ensure_ascii=False)

    for source_file, line_no, row, parse_error in iter_inputs(args.input):
        if args.max_samples and processed >= args.max_samples:
            break
        processed += 1

        if parse_error:
            format_rejected.append({"source_file": str(source_file), "source_line": line_no, "errors": [parse_error]})
            counts["format_rejected"] += 1
            continue

        ok, errors, images = format_check(
            row, source_file, check_images=not args.skip_image_existence_check
        )
        if not ok:
            format_rejected.append({
                "source_file": str(source_file),
                "source_line": line_no,
                "errors": errors,
                "sample": row,
            })
            counts["format_rejected"] += 1
            continue

        prompt = (
            "task_labels:\n" + task_labels_text
            + "\n\n候选训练样本：\n"
            + sample_for_judge(row, args.max_prompt_chars)
        )

        judgment = None
        last_error = ""
        for _ in range(max(1, args.judge_retries + 1)):
            try:
                candidate = runner.json(JUDGE_SYSTEM, prompt, images)
                valid, reason, total = validate_judgment(candidate)
                if valid:
                    judgment = candidate
                    judgment["total_score"] = total
                    judgment["decision"] = "accept" if total >= args.threshold else "reject"
                    break
                last_error = reason
            except Exception as exc:
                last_error = str(exc)

        if judgment is None:
            judge_failures.append({
                "source_file": str(source_file),
                "source_line": line_no,
                "error": last_error,
                "sample": row,
            })
            counts["judge_failure"] += 1
            continue

        row = dict(row)
        original_task = row.get("task")
        row["task"] = judgment["task"]
        metadata = dict(row.get("metadata") or {})
        metadata["quality_filter"] = {
            "version": "qwen235_rubric_v1",
            "score": judgment["total_score"],
            "threshold": args.threshold,
            "decision": judgment["decision"],
            "rubric": judgment["rubric"],
            "task_reason": judgment.get("task_reason", ""),
            "original_task": original_task,
        }
        row["metadata"] = metadata
        row["quality_score"] = judgment["total_score"]

        if judgment["decision"] == "accept":
            accepted.append(row)
            counts["accepted"] += 1
            counts[f"task:{row['task']}"] += 1
            construction_type = str(metadata.get("construction_type") or "")
            if construction_type:
                counts[f"construction_type:{construction_type}"] += 1
            difficulty = metadata.get("difficulty")
            if isinstance(difficulty, dict) and difficulty.get("label"):
                counts[f"difficulty:{difficulty['label']}"] += 1
        else:
            rejected.append({
                "source_file": str(source_file),
                "source_line": line_no,
                "quality_score": judgment["total_score"],
                "task": judgment["task"],
                "rubric": judgment["rubric"],
                "sample": row,
            })
            counts["quality_rejected"] += 1
            for key, item in judgment["rubric"].items():
                if float(item["score"]) == 0.0:
                    counts[f"failed_rubric:{key}"] += 1

    write_jsonl(args.output_root / "accepted.jsonl", accepted)
    write_jsonl(args.output_root / "rejected_low_score.jsonl", rejected)
    write_jsonl(args.output_root / "rejected_format.jsonl", format_rejected)
    write_jsonl(args.output_root / "judge_failures.jsonl", judge_failures)

    report = {
        "method": "minimal_format_plus_qwen235_rubric_v1",
        "threshold": args.threshold,
        "rubric_items": list(RUBRIC_KEYS),
        "rubric_points_per_item": 0.5,
        "max_score": 5.0,
        "task_label_count": len(TASK_LABELS),
        "processed": processed,
        "accepted": len(accepted),
        "quality_rejected": len(rejected),
        "format_rejected": len(format_rejected),
        "judge_failures": len(judge_failures),
        "counts": dict(counts),
    }
    (args.output_root / "report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
