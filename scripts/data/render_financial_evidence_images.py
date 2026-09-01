"""Render financial evidence text into document images for genuine multimodal SFT rows."""

from __future__ import annotations

import argparse
import copy
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

import orjson
from PIL import Image, ImageDraw, ImageFont

from scripts.data.select_benchmark_aligned_tasks import (
    _benchmark_hashes,
    _content_hash,
    assess_row,
    review_alignment,
)


FONT_CANDIDATES = (
    Path("C:/Windows/Fonts/msyh.ttc"),
    Path("C:/Windows/Fonts/simhei.ttf"),
    Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"),
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
)

MAX_RENDER_CHARS = 12000


def _with_image_prompt(instruction: str) -> str:
    instruction = instruction.strip()
    instruction = re.sub(r"^(?:<image>\s*)+", "", instruction)
    return f"<image>\n{instruction}"


def split_prompt_evidence(question: str, capability: str) -> tuple[str, str] | None:
    """Separate task instruction from evidence that can be moved into an image."""
    question = question.strip()

    if capability == "financial_event_extraction":
        match = re.search(r"(?:资讯|金融资讯|抽取金融事件及其字段)\s*[:：]", question)
        if match:
            evidence = re.split(r"抽取结果\s*[:：]", question[match.end() :], maxsplit=1)[0].strip()
            instruction = question[: match.start()].strip()
            if "抽取金融事件及其字段" in match.group(0):
                instruction = f"{instruction}抽取金融事件及其字段"
            if evidence:
                return _with_image_prompt(instruction), evidence

    if capability == "entity_extraction_classification":
        marker = re.search(r"请给出正确选项[。.]", question)
        options = re.search(r"\bA\s*[.、:：].*\bB\s*[.、:：].*\bC\s*[.、:：].*$", question, re.DOTALL | re.IGNORECASE)
        if marker and options and marker.end() <= options.start():
            evidence = question[marker.end() : options.start()].strip()
            instruction = f"{question[:marker.end()].strip()} 请阅读图片中的材料。{question[options.start():].strip()}"
            if evidence:
                return _with_image_prompt(instruction), evidence

    if capability == "summary_announcement":
        if "\n\n" in question:
            instruction, evidence = question.split("\n\n", 1)
            if "分析" in instruction and any(
                role in instruction for role in ("个股研究员", "行业研究员")
            ) and evidence.strip():
                return _with_image_prompt(instruction), evidence.strip()
        request = re.search(
            r"^.*?(?:对公司经营及股价的影响|对公司股价的影响|对其股价的影响|impact on (?:the )?(?:company's )?(?:operations|share price)).*?[。.]",
            question,
            re.DOTALL | re.IGNORECASE,
        )
        if request:
            evidence = question[request.end() :].strip()
            if evidence:
                return _with_image_prompt(question[: request.end()]), evidence

    if capability == "compliance_safety_suitability":
        option_block = re.search(r"(?:选项\s*[:：]|\bA\s*[.、:：]).*\bB\s*[.、:：]", question, re.DOTALL | re.IGNORECASE)
        regulatory = any(
            term in question.casefold()
            for term in ("合规", "监管", "法规", "办法", "规定", "gips", "compliance", "regulatory")
        )
        if option_block and regulatory:
            instruction = "请依据图片中的金融监管规则或情境，判断是否合规或选择符合监管要求的选项。"
            return _with_image_prompt(instruction), question

    table_capabilities = {
        "portfolio_allocation_risk_return",
        "financial_audit_fundamentals",
        "basic_arithmetic_metrics",
    }
    if capability in table_capabilities:
        table_start = question.find("|")
        if table_start >= 0:
            prefix = question[:table_start].strip()
            table_and_tail = question[table_start:].strip()
            lines = table_and_tail.splitlines()
            table_lines: list[str] = []
            tail_lines: list[str] = []
            in_table = True
            for line in lines:
                if in_table and line.strip().startswith("|"):
                    table_lines.append(line.strip())
                else:
                    in_table = False
                    tail_lines.append(line)
            evidence = "\n".join(table_lines).strip()
            instruction = "\n".join(part for part in (prefix, "\n".join(tail_lines).strip()) if part).strip()
            if evidence and instruction:
                return _with_image_prompt(instruction), evidence

    if capability == "financial_audit_fundamentals":
        basis = re.search(r"(?:保留意见的基础为|审计意见的基础为)\s*[:：]", question)
        analysis = re.search(r"分析一下|请分析|请判断", question[basis.end() :] if basis else "")
        if basis and analysis:
            analysis_start = basis.end() + analysis.start()
            evidence = question[basis.end() : analysis_start].strip()
            instruction = f"{question[:basis.start()].strip()} {question[analysis_start:].strip()}"
            if evidence:
                return _with_image_prompt(instruction), evidence

    return None


def _font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for path in FONT_CANDIDATES:
        if path.exists():
            return ImageFont.truetype(str(path), size=size)
    return ImageFont.load_default()


def _wrap_line(text: str, font: ImageFont.ImageFont, max_width: int) -> list[str]:
    if not text:
        return [""]
    wrapped: list[str] = []
    current = ""
    for character in text:
        candidate = current + character
        if current and font.getlength(candidate) > max_width:
            wrapped.append(current)
            current = character
        else:
            current = candidate
    if current:
        wrapped.append(current)
    return wrapped


def render_text_pages(
    evidence: str,
    output_dir: Path,
    stem: str,
    *,
    width: int = 1400,
    height: int = 1800,
    font_size: int = 30,
    max_pages: int | None = None,
) -> list[Path]:
    """Render evidence into one or more PNG document pages."""
    output_dir.mkdir(parents=True, exist_ok=True)
    font = _font(font_size)
    margin = 70
    line_height = font_size + 14
    lines: list[str] = []
    for source_line in evidence.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        lines.extend(_wrap_line(source_line, font, width - 2 * margin))
    lines_per_page = max(1, (height - 2 * margin) // line_height)
    if max_pages is not None and len(lines) > lines_per_page * max_pages:
        return []
    paths: list[Path] = []
    for page_index, start in enumerate(range(0, len(lines), lines_per_page), 1):
        page_lines = lines[start : start + lines_per_page]
        image = Image.new("RGB", (width, height), "white")
        draw = ImageDraw.Draw(image)
        y = margin
        for line in page_lines:
            draw.text((margin, y), line, fill="black", font=font)
            y += line_height
        path = output_dir / f"{stem}_p{page_index:02d}.png"
        image.save(path, format="PNG")
        paths.append(path)
    return paths


def make_multimodal_row(
    row: dict[str, Any],
    capability: str,
    input_name: str,
    line_number: int,
    output_dir: Path,
    *,
    image_path_prefix: str,
) -> dict[str, Any] | None:
    """Move separable evidence into rendered images while preserving the target answer."""
    converted = copy.deepcopy(row)
    user_messages = [message for message in converted.get("messages", []) if message.get("role") == "user"]
    if len(user_messages) != 1:
        return None
    question = str(user_messages[0].get("content", ""))
    separated = split_prompt_evidence(question, capability)
    if separated is None:
        return None
    instruction, evidence = separated
    if len(evidence) > MAX_RENDER_CHARS:
        return None
    safe_name = re.sub(r"[^a-zA-Z0-9_-]+", "_", input_name).strip("_") or "input"
    paths = render_text_pages(
        evidence,
        output_dir,
        f"{safe_name}_{line_number:09d}",
        max_pages=4,
    )
    if not paths:
        return None
    image_tokens = "\n".join("<image>" for _ in paths)
    instruction_without_token = re.sub(r"^(?:<image>\s*)+", "", instruction).strip()
    user_messages[0]["content"] = f"{image_tokens}\n{instruction_without_token}"
    prefix = image_path_prefix.rstrip("/")
    converted["images"] = [f"{prefix}/{path.name}" for path in paths]
    converted["rendered_from"] = {
        "input_name": input_name,
        "line_number": line_number,
        "original_source": str(row.get("source", "")),
        "capability": capability,
        "evidence_rendered": True,
    }
    converted["source"] = f"rendered_evidence:{row.get('source', input_name)}"
    return converted


def generate_rendered_candidates(
    input_path: Path,
    output_path: Path,
    image_dir: Path,
    capabilities: tuple[str, ...],
    per_capability: int,
    *,
    input_name: str,
    image_path_prefix: str,
    excluded_content_hashes: set[str] | None = None,
) -> Counter[str]:
    """Incrementally write content-reviewed rendered candidates."""
    counts: Counter[str] = Counter()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with input_path.open("r", encoding="utf-8") as source_handle, output_path.open(
        "w", encoding="utf-8", buffering=1
    ) as output_handle:
        for line_number, line in enumerate(source_handle, 1):
            if not line.strip():
                continue
            row = orjson.loads(line)
            if excluded_content_hashes and _content_hash(row) in excluded_content_hashes:
                continue
            for capability in capabilities:
                if counts[capability] >= per_capability:
                    continue
                decision = assess_row(row, capability)
                reviewed, _ = review_alignment(row, capability, decision)
                if not decision.accepted or not reviewed:
                    continue
                converted = make_multimodal_row(
                    row,
                    capability,
                    input_name,
                    line_number,
                    image_dir,
                    image_path_prefix=image_path_prefix,
                )
                if converted is None:
                    continue
                converted_decision = assess_row(converted, capability)
                converted_reviewed, _ = review_alignment(converted, capability, converted_decision)
                if not converted_decision.accepted or not converted_reviewed:
                    continue
                converted["target_capability"] = capability
                output_handle.write(json.dumps(converted, ensure_ascii=False) + "\n")
                counts[capability] += 1
            if all(counts[capability] >= per_capability for capability in capabilities):
                break
    return counts


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=Path("data/train_text_sft.jsonl"))
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/benchmark_aligned_declining_tasks/rendered_local_candidates.jsonl"),
    )
    parser.add_argument(
        "--image-dir",
        type=Path,
        default=Path("data/benchmark_aligned_declining_tasks/rendered_images"),
    )
    parser.add_argument(
        "--capability",
        action="append",
        dest="capabilities",
        default=[],
    )
    parser.add_argument("--per-capability", type=int, default=1500)
    parser.add_argument("--input-name", default="train_text")
    parser.add_argument(
        "--benchmark",
        type=Path,
        default=Path("data/benchmark/my_benchmark/all.jsonl"),
    )
    parser.add_argument(
        "--image-path-prefix",
        default="data/benchmark_aligned_declining_tasks/rendered_images",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    capabilities = tuple(args.capabilities) or (
        "financial_event_extraction",
        "portfolio_allocation_risk_return",
        "summary_announcement",
        "financial_audit_fundamentals",
        "entity_extraction_classification",
    )
    counts = generate_rendered_candidates(
        args.input,
        args.output,
        args.image_dir,
        capabilities,
        args.per_capability,
        input_name=args.input_name,
        image_path_prefix=args.image_path_prefix,
        excluded_content_hashes=_benchmark_hashes(args.benchmark),
    )
    print(json.dumps(dict(counts), ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()
