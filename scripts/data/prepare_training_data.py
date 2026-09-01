#!/usr/bin/env python3
"""将本地金融数据集整理为 ms-swift 可直接读取的 JSONL。"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import shutil
import sys
import tarfile
import zipfile
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable
from xml.etree import ElementTree


def normalize_split(split: str | None) -> str:
    value = (split or "").strip().lower()
    return "train" if value in {"train", "training"} else "eval"


def build_record(
    user: str,
    assistant: str,
    *,
    source: str,
    source_split: str,
    images: list[str] | None = None,
    task: str | None = None,
) -> dict[str, Any]:
    record: dict[str, Any] = {
        "messages": [
            {"role": "user", "content": str(user).strip()},
            {"role": "assistant", "content": str(assistant).strip()},
        ],
        "source": source,
        "split": source_split,
    }
    if images:
        record["images"] = images
    if task:
        record["task"] = task
    return record


def _record_key(record: dict[str, Any]) -> str:
    payload = {
        "messages": record["messages"],
        "images": record.get("images"),
    }
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


class RecordWriter:
    def __init__(self, path: Path):
        self.path = path
        self._seen: set[str] = set()
        self._file = None
        self.written = 0
        self.duplicates = 0

    def __enter__(self) -> "RecordWriter":
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._file = self.path.open("w", encoding="utf-8", newline="\n")
        return self

    def write(self, record: dict[str, Any]) -> bool:
        key = _record_key(record)
        if key in self._seen:
            self.duplicates += 1
            return False
        self._seen.add(key)
        self._file.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")
        self.written += 1
        return True

    def __exit__(self, exc_type, exc, traceback) -> None:
        if self._file is not None:
            self._file.close()


def _safe_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("._") or "image"


def table_to_markdown(table: list[list[Any]]) -> str:
    if not table:
        return ""
    width = max(len(row) for row in table)
    rows = [[str(cell).replace("|", "\\|").replace("\n", " ") for cell in row] for row in table]
    rows = [row + [""] * (width - len(row)) for row in rows]
    lines = ["| " + " | ".join(rows[0]) + " |", "| " + " | ".join(["---"] * width) + " |"]
    lines.extend("| " + " | ".join(row) + " |" for row in rows[1:])
    return "\n".join(lines)


def chartqa_multimodal_record(
    row: dict[str, Any],
    *,
    asset_root: Path,
    manifest_image_root: str,
) -> dict[str, Any]:
    chart_id = _safe_name(str(row["chart_id"]))
    image = row["image_path"]
    image_bytes = image["bytes"]
    suffix = Path(image.get("path") or "").suffix or ".png"
    image_name = chart_id + suffix.lower()
    asset_root.mkdir(parents=True, exist_ok=True)
    (asset_root / image_name).write_bytes(image_bytes)
    explanation = str(row.get("Explanation") or "").strip()
    answer = str(row["Answer"]).strip()
    response = f"{explanation}\n\n答案：{answer}" if explanation else answer
    return build_record(
        f"<image>{str(row['Question']).strip()}",
        response,
        source="chart_qa",
        source_split="train",
        images=[f"{manifest_image_root.rstrip('/')}/{image_name}"],
        task="chart_qa",
    )


def convert_chartqa_parquets(
    source_dir: Path,
    *,
    text_writer: RecordWriter,
    multi_writer: RecordWriter,
    asset_root: Path,
) -> dict[str, int]:
    import pyarrow.parquet as pq

    counts = {"text": 0, "multi": 0, "skipped_text": 0}
    for parquet_path in sorted(source_dir.glob("*.parquet")):
        parquet = pq.ParquetFile(parquet_path)
        columns = set(parquet.schema_arrow.names)
        for batch in parquet.iter_batches(batch_size=256):
            for row in batch.to_pylist():
                if "image_path" in columns:
                    record = chartqa_multimodal_record(
                        row,
                        asset_root=asset_root,
                        manifest_image_root="data/train_multi/assets/chart_qa",
                    )
                    if multi_writer.write(record):
                        counts["multi"] += 1
                else:
                    if row.get("answer") in (None, ""):
                        counts["skipped_text"] += 1
                        continue
                    references = "\n\n".join(str(x) for x in row.get("references") or [])
                    prompt = f"参考资料：\n{references}\n\n问题：{row['text']}"
                    record = build_record(
                        prompt,
                        row["answer"],
                        source="chart_qa_text",
                        source_split="train",
                        task=str(row.get("type") or "financial_qa"),
                    )
                    if text_writer.write(record):
                        counts["text"] += 1
    return counts


def _json_text(value: Any) -> str:
    if isinstance(value, str):
        return value.strip()
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def _content_text(content: Any) -> str:
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        return "\n".join(
            str(item.get("text") or "") if isinstance(item, dict) else str(item)
            for item in content
        ).strip()
    return str(content or "").strip()


def _normalize_bizfin_record(row: dict[str, Any]) -> list[dict[str, str]] | None:
    messages = []
    for message in row.get("messages") or []:
        content = _content_text(message.get("content"))
        if content:
            messages.append({"role": message["role"], "content": content})
    answer = ""
    for choice in row.get("choices") or []:
        answer = _content_text((choice.get("message") or {}).get("content"))
        if answer:
            break
    if not answer or not any(message["role"] == "user" for message in messages):
        return None
    messages.append({"role": "assistant", "content": answer})
    return messages


def _qa_response(answer: Any, reasoning: Any = None) -> str:
    answer_text = _json_text(answer)
    reasoning_text = _json_text(reasoning) if reasoning not in (None, "", [], {}) else ""
    return f"{reasoning_text}\n\n答案：{answer_text}" if reasoning_text else answer_text


def _load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8-sig") as file:
        return json.load(file)


def _loads_json(text: str) -> Any:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        try:
            from json_repair import repair_json
        except ImportError:
            project_root = Path(__file__).resolve().parents[2]
            for directory in (
                project_root / "python-user" / "lib" / "python3.12" / "site-packages",
                project_root / "venv-dlc" / "lib" / "python3.12" / "site-packages",
            ):
                if directory.is_dir():
                    sys.path.insert(0, str(directory))
            from json_repair import repair_json
        return repair_json(text, return_objects=True)


def _iter_jsonl(path: Path):
    text = path.read_text(encoding="utf-8-sig")
    buffer: list[str] = []
    depth = 0
    started = False
    in_string = False
    escaped = False
    for char in text:
        if not started:
            if char.isspace():
                continue
            started = True
        if char == "\r":
            continue
        if char == "\n" and in_string:
            buffer.append("\\n")
            escaped = False
            continue
        buffer.append(char)
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char in "[{":
            depth += 1
        elif char in "]}":
            depth -= 1
            if depth == 0:
                yield _loads_json("".join(buffer))
                buffer = []
                started = False
    if buffer and "".join(buffer).strip():
        yield _loads_json("".join(buffer))


def _iter_parquet_rows(path: Path):
    import pyarrow.parquet as pq

    parquet = pq.ParquetFile(path)
    for batch in parquet.iter_batches(batch_size=256):
        yield from batch.to_pylist()


def _context_from_financial_item(item: dict[str, Any]) -> str:
    parts = []
    pre_text = item.get("pre_text") or []
    post_text = item.get("post_text") or []
    if pre_text:
        parts.append("\n".join(map(str, pre_text)))
    table = item.get("table_ori") or item.get("table") or []
    if table:
        parts.append(table_to_markdown(table))
    if post_text:
        parts.append("\n".join(map(str, post_text)))
    return "\n\n".join(parts)


def multihiertt_record(row: dict[str, Any], *, split: str) -> dict[str, Any]:
    qa = row.get("qa") or row
    tables = [str(table) for table in row.get("tables") or []]
    parts = []
    used_tables: set[int] = set()
    for paragraph in row.get("paragraphs") or []:
        text = str(paragraph)
        match = re.fullmatch(r"\s*##\s*Table\s+(\d+)\s*(?:##)?\s*", text)
        if match and int(match.group(1)) < len(tables):
            index = int(match.group(1))
            used_tables.add(index)
            parts.append(tables[index])
        else:
            parts.append(text)
    parts.extend(table for index, table in enumerate(tables) if index not in used_tables)
    context = "\n\n".join(part for part in parts if part.strip())
    prompt = f"参考资料：\n{context}\n\n问题：{str(qa['question']).strip()}"
    return build_record(
        prompt,
        _qa_response(qa["answer"], qa.get("program")),
        source="multihiertt",
        source_split=split,
        task="multi_hierarchical_table_qa",
    )


def finer139_record(
    row: dict[str, Any],
    *,
    label_names: list[str],
    split: str,
) -> dict[str, Any]:
    tokens = [str(token) for token in row["tokens"]]
    labels = [
        {
            "token": token,
            "label": label if isinstance(label, str) else label_names[int(label)],
        }
        for token, label in zip(tokens, row["ner_tags"])
    ]
    return build_record(
        "为以下金融文本的每个 token 标注 XBRL 实体标签：\n" + " ".join(tokens),
        _json_text(labels),
        source="finer139",
        source_split=split,
        task="financial_ner",
    )


def pixiu_record(
    row: dict[str, Any],
    *,
    source_name: str,
    split: str,
) -> dict[str, Any]:
    source_name = source_name.removesuffix("-instruct")
    return build_record(
        str(row["query"]).strip(),
        _json_text(row["answer"]),
        source="pixiu_" + source_name.replace("-", "_"),
        source_split=split,
        task=source_name,
    )


def finmme_record(
    row: dict[str, Any],
    *,
    asset_root: Path,
    manifest_image_root: str,
) -> dict[str, Any]:
    image = row["image"]
    suffix = Path(str(image.get("path") or "")).suffix.lower() or ".jpg"
    image_name = f"{row['id']}{suffix}"
    asset_root.mkdir(parents=True, exist_ok=True)
    (asset_root / image_name).write_bytes(image["bytes"])
    context = "\n".join(
        part
        for part in (
            str(row.get("verified_caption") or "").strip(),
            str(row.get("related_sentences") or "").strip(),
        )
        if part
    )
    question = str(row["question_text"]).strip()
    options = str(row.get("options") or "").strip()
    prompt_parts = [part for part in (context, question, options) if part]
    return build_record(
        "<image>" + "\n\n".join(prompt_parts),
        row["answer"],
        source="finmme",
        source_split="train",
        images=[f"{manifest_image_root.rstrip('/')}/{image_name}"],
        task=str(row.get("question_type") or "financial_multimodal_qa"),
    )


def tatdqa_records(
    item: dict[str, Any],
    *,
    split: str,
    image_path: str,
) -> list[dict[str, Any]]:
    records = []
    for question in item.get("questions") or []:
        if question.get("answer") in (None, ""):
            continue
        response = _qa_response(question["answer"], question.get("derivation"))
        scale = str(question.get("scale") or "").strip()
        if scale:
            response += f"\n\n单位：{scale}"
        records.append(
            build_record(
                "<image>" + str(question["question"]).strip(),
                response,
                source="tatdqa",
                source_split=split,
                images=[image_path],
                task=str(question.get("answer_type") or "document_qa"),
            )
        )
    return records


def _copy_image(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)


def _finchart_image_name(annotation_name: str) -> str:
    return re.sub(r"_q\d+(?=\.[^.]+$)", "", annotation_name)


def _fintabnet_objects(xml_bytes: bytes) -> list[dict[str, Any]]:
    root = ElementTree.fromstring(xml_bytes)
    objects = []
    for item in root.findall("object"):
        box = item.find("bndbox")
        if box is None:
            continue
        objects.append(
            {
                "label": item.findtext("name", default=""),
                "bbox": [
                    round(float(box.findtext(name, default="0")), 2)
                    for name in ("xmin", "ymin", "xmax", "ymax")
                ],
            }
        )
    return objects


def convert_fintabnet_tar(
    archive_path: Path,
    *,
    train_writer: RecordWriter,
    eval_writer: RecordWriter,
    asset_dir: Path,
    manifest_image_root: str = "data/train_multi/assets/fintabnet",
) -> dict[str, int]:
    annotations: dict[str, tuple[str, list[dict[str, Any]]]] = {}
    image_members: dict[str, tarfile.TarInfo] = {}
    counts = {"train": 0, "eval": 0}
    asset_dir.mkdir(parents=True, exist_ok=True)
    with tarfile.open(archive_path, "r:") as archive:
        for member in archive:
            if not member.isfile():
                continue
            parts = member.name.split("/")
            suffix = Path(member.name).suffix.lower()
            if len(parts) == 3 and parts[1] in {"train", "val", "test"} and suffix == ".xml":
                binary = archive.extractfile(member)
                if binary:
                    annotations[Path(member.name).stem] = (
                        parts[1],
                        _fintabnet_objects(binary.read()),
                    )
            elif len(parts) == 3 and parts[1] == "images" and suffix == ".jpg":
                image_members[Path(member.name).stem] = member
        for stem, (split, objects) in annotations.items():
            member = image_members.get(stem)
            if member is None:
                continue
            binary = archive.extractfile(member)
            if binary is None:
                continue
            image_name = Path(member.name).name
            (asset_dir / image_name).write_bytes(binary.read())
            target_rel = f"{manifest_image_root.rstrip('/')}/{image_name}"
            record = build_record(
                "<image>识别图像中的表格结构，输出每个结构元素的类别及边界框坐标。",
                _json_text(objects),
                source="fintabnet",
                source_split=split,
                images=[target_rel],
                task="table_structure_detection",
            )
            writer = train_writer if normalize_split(split) == "train" else eval_writer
            key = "train" if normalize_split(split) == "train" else "eval"
            if writer.write(record):
                counts[key] += 1
    return counts


def prepare_all(source_root: Path, project_root: Path, *, include_fintabnet: bool = True) -> dict[str, Any]:
    text_root = project_root / "data" / "train_text"
    multi_root = project_root / "data" / "train_multi"
    paths = {
        "text_train": text_root / "train.jsonl",
        "text_eval": text_root / "eval.jsonl",
        "multi_train": multi_root / "train.jsonl",
        "multi_eval": multi_root / "eval.jsonl",
    }
    source_counts: dict[str, int] = defaultdict(int)
    skipped_records: dict[str, int] = defaultdict(int)
    skipped = ["Fin-R1-main"]
    excluded_by_user = ["FinRAGBench-V-main"]
    downloaded_but_not_direct_sft: dict[str, str] = {}

    with (
        RecordWriter(paths["text_train"]) as text_train,
        RecordWriter(paths["text_eval"]) as text_eval,
        RecordWriter(paths["multi_train"]) as multi_train,
        RecordWriter(paths["multi_eval"]) as multi_eval,
    ):
        def emit_text(record: dict[str, Any], split: str) -> None:
            writer = text_train if normalize_split(split) == "train" else text_eval
            if writer.write(record):
                source_counts[record["source"]] += 1

        def emit_multi(record: dict[str, Any], split: str) -> None:
            writer = multi_train if normalize_split(split) == "train" else multi_eval
            if writer.write(record):
                source_counts[record["source"]] += 1

        # 顶层 FinanceBench：官方基准评测数据。
        financebench = source_root / "financebench_open_source.jsonl"
        if financebench.is_file():
            for row in _iter_jsonl(financebench):
                evidence = "\n".join(
                    str(item.get("evidence_text") or item.get("text") or item)
                    for item in row.get("evidence") or []
                )
                prompt = f"参考资料：\n{evidence}\n\n问题：{row['question']}" if evidence else row["question"]
                emit_text(
                    build_record(
                        prompt,
                        _qa_response(row["answer"], row.get("justification")),
                        source="financebench",
                        source_split="test",
                        task=str(row.get("question_type") or "financial_qa"),
                    ),
                    "test",
                )

        # 顶层 train.json：FinQA 训练数据。
        finqa_top = source_root / "train.json"
        if finqa_top.is_file():
            for row in _load_json(finqa_top):
                qa = row["qa"]
                emit_text(
                    build_record(
                        f"参考资料：\n{_context_from_financial_item(row)}\n\n问题：{qa['question']}",
                        _qa_response(qa["answer"], qa.get("explanation") or qa.get("program")),
                        source="finqa",
                        source_split="train",
                        task="financial_reasoning",
                    ),
                    "train",
                )

        # AlphaFin 本地仅含 testdata。
        alpha = source_root / "AlphaFin-main" / "AlphaFin-main" / "src" / "data" / "stage1_testdata.json"
        if alpha.is_file():
            for row in _load_json(alpha):
                user = "\n".join(str(row.get(k) or "").strip() for k in ("instruction", "input")).strip()
                emit_text(
                    build_record(
                        user,
                        row["output"],
                        source="alphafin",
                        source_split="test",
                        task="stock_trend_prediction",
                    ),
                    "test",
                )

        # BizFinBench 无 train split，作为评测集。
        biz_dir = source_root / "BizFinBench-main" / "BizFinBench-main" / "datasets"
        if biz_dir.is_dir():
            for path in sorted(biz_dir.glob("*.jsonl")):
                for row in _iter_jsonl(path):
                    messages = _normalize_bizfin_record(row)
                    if not messages:
                        skipped_records["bizfinbench_missing_answer"] += 1
                        continue
                    record = {
                        "messages": messages,
                        "source": "bizfinbench",
                        "split": "test",
                        "task": path.stem,
                    }
                    emit_text(record, "test")

        biz_v2_dir = (
            source_root
            / "BizFinBench.v2-main"
            / "BizFinBench.v2-main"
            / "datasets"
        )
        if biz_v2_dir.is_dir():
            for path in sorted(biz_v2_dir.rglob("*.jsonl")):
                for row in _iter_jsonl(path):
                    messages = _normalize_bizfin_record(row)
                    if not messages:
                        skipped_records["bizfinbench_v2_missing_answer"] += 1
                        continue
                    emit_text(
                        {
                            "messages": messages,
                            "source": "bizfinbench_v2",
                            "split": "test",
                            "task": path.stem,
                        },
                        "test",
                    )

        # CFinBench 仅有 dev/val/test。
        cfin = source_root / "CFinBench_W_Answer" / "CFinBench_W_Answer"
        if cfin.is_dir():
            for split_dir in ("dev", "val", "test"):
                for path in sorted((cfin / split_dir).rglob("*.jsonl")):
                    for row in _iter_jsonl(path):
                        if row.get("Answer") in (None, ""):
                            skipped_records["cfinbench_missing_answer"] += 1
                            continue
                        options = "\n".join(
                            f"{chr(65 + i)}. {value}" for i, value in enumerate(row.get("OptionList") or [])
                        )
                        prompt = str(row["text"])
                        if options:
                            prompt += "\n\n选项：\n" + options
                        emit_text(
                            build_record(
                                prompt,
                                row["Answer"],
                                source="cfinbench",
                                source_split=split_dir,
                                task=path.parent.name,
                            ),
                            split_dir,
                        )

        # CFLUE 本地 instruction 数据，无显式 split，作为训练集。
        cflue = source_root / "cflue-master" / "cflue-master" / "data"
        if cflue.is_dir():
            for path in sorted(cflue.rglob("*.json")):
                for row in _load_json(path):
                    if "output" in row:
                        user = "\n".join(
                            str(row.get(k) or "").strip() for k in ("instruction", "input")
                        ).strip()
                        response = row["output"]
                    else:
                        user = str(row["question"]).strip()
                        if row.get("choices"):
                            user += "\n\n选项：" + _json_text(row["choices"])
                        response = _qa_response(row["answer"], row.get("analysis"))
                    emit_text(
                        build_record(
                            user,
                            response,
                            source="cflue",
                            source_split="train",
                            task=str(row.get("sub_task") or row.get("task") or "finance"),
                        ),
                        "train",
                    )

        # ChartQA：文本 parquet 与含二进制图片 parquet。
        chartqa = source_root / "chart-qa"
        if chartqa.is_dir():
            counts = convert_chartqa_parquets(
                chartqa,
                text_writer=text_train,
                multi_writer=multi_train,
                asset_root=multi_root / "assets" / "chart_qa",
            )
            source_counts["chart_qa_text"] += counts["text"]
            source_counts["chart_qa"] += counts["multi"]
            skipped_records["chart_qa_text_missing_answer"] += counts["skipped_text"]

        # ConvFinQA 原始 train/dev/test；使用非 turn 版本避免同源重复。
        conv_zip = source_root / "ConvFinQA-main" / "ConvFinQA-main" / "data.zip"
        if conv_zip.is_file():
            with zipfile.ZipFile(conv_zip) as archive:
                for split, member in (("train", "data/train.json"), ("dev", "data/dev.json"), ("test", "data/test_private.json")):
                    rows = json.loads(archive.read(member))
                    for row in rows:
                        qa_keys = sorted(key for key in row if key == "qa" or key.startswith("qa_"))
                        if not qa_keys:
                            skipped_records["convfinqa_missing_answer"] += 1
                            continue
                        for key in qa_keys:
                            qa = row[key]
                            emit_text(
                                build_record(
                                    f"参考资料：\n{_context_from_financial_item(row)}\n\n问题：{qa['question']}",
                                    _qa_response(
                                        qa["answer"],
                                        qa.get("explanation") or qa.get("program"),
                                    ),
                                    source="convfinqa",
                                    source_split=split,
                                    task="conversational_financial_qa",
                                ),
                                split,
                            )

        # dian-r1；dian-ocr-r1 与其逐文件相同，不重复导入。
        dian = source_root / "dian-r1-data"
        if dian.is_dir():
            for path in sorted(dian.glob("*.json")):
                for row in _load_json(path):
                    emit_text(
                        build_record(
                            row["instruction"],
                            row["output"],
                            source="dian_r1",
                            source_split="train",
                            task=path.stem,
                        ),
                        "train",
                    )

        # DISC-FinLLM。
        disc = source_root / "DISC-FinLLM-main" / "DISC-FinLLM-main"
        if disc.is_dir():
            for split, directory in (("train", disc / "data"), ("test", disc / "eval")):
                if not directory.is_dir():
                    continue
                for path in sorted(directory.glob("*.json")):
                    for row in _load_json(path):
                        if row.get("output") in (None, ""):
                            skipped_records["disc_finllm_missing_answer"] += 1
                            continue
                        user = "\n".join(str(row.get(k) or "").strip() for k in ("instruction", "input")).strip()
                        emit_text(
                            build_record(
                                user,
                                row["output"],
                                source="disc_finllm",
                                source_split=split,
                                task=path.stem,
                            ),
                            split,
                        )

        # DocFEE。
        docfee = source_root / "DocFEE-main" / "DocFEE-main" / "data" / "DFREE_dataset.zip"
        if docfee.is_file():
            with zipfile.ZipFile(docfee) as archive:
                for split, member in (("train", "train.jsonl"), ("test", "test.jsonl")):
                    with archive.open(member) as binary:
                        text = io.TextIOWrapper(binary, encoding="utf-8-sig")
                        for line in text:
                            if not line.strip():
                                continue
                            row = json.loads(line)
                            emit_text(
                                build_record(
                                    f"从以下公告中抽取金融事件及其字段：\n{row['content']}",
                                    _json_text(row["events"]),
                                    source="docfee",
                                    source_split=split,
                                    task="financial_event_extraction",
                                ),
                                split,
                            )

        # FinanceReasoning 为 benchmark test。
        reasoning_dir = (
            source_root
            / "FinanceReasoning-master"
            / "FinanceReasoning-master"
            / "data"
            / "FinanceReasoning"
        )
        if reasoning_dir.is_dir():
            for path in sorted(reasoning_dir.glob("*.json")):
                for row in _load_json(path):
                    prompt = f"参考资料：\n{row['context']}\n\n问题：{row['question']}"
                    emit_text(
                        build_record(
                            prompt,
                            _qa_response(row["ground_truth"], row.get("python_solution")),
                            source="finance_reasoning",
                            source_split="test",
                            task=str(row.get("level") or path.stem),
                        ),
                        "test",
                    )

        # FinAR-Bench 本地仅有 dev。
        finar = source_root / "FinAR-Bench-main" / "FinAR-Bench-main" / "data" / "dev.txt"
        if finar.is_file():
            for row in _iter_jsonl(finar):
                for instance in row.get("instances") or []:
                    emit_text(
                        build_record(
                            f"财务报表：\n{row['table']}\n\n任务：{instance['task']}",
                            instance["ground_truth"],
                            source="finar_bench",
                            source_split="dev",
                            task=str(instance.get("task_type") or "financial_report_qa"),
                        ),
                        "dev",
                    )

        # FinChart-Bench：图像文件 + 三类 JSON 标注，作为评测集。
        finchart = source_root / "FinChart-Bench-main" / "FinChart-Bench-main"
        if finchart.is_dir():
            for prefix in ("MC", "QA", "TF"):
                data_path = finchart / f"{prefix}_data.json"
                image_dir = finchart / f"{prefix}_images"
                if not data_path.is_file():
                    continue
                for row in _load_json(data_path):
                    image_name = _finchart_image_name(row["image"])
                    source_image = image_dir / image_name
                    target_rel = f"data/train_multi/assets/finchart_bench/{prefix.lower()}/{image_name}"
                    target_image = project_root / target_rel
                    _copy_image(source_image, target_image)
                    answer = row.get("answer")
                    reasoning = row.get("reasoning") or row.get("explanation")
                    emit_multi(
                        build_record(
                            f"<image>{row['question']}",
                            _qa_response(answer, reasoning),
                            source="finchart_bench",
                            source_split="test",
                            images=[target_rel.replace("\\", "/")],
                            task=prefix.lower(),
                        ),
                        "test",
                    )

        # FinChina-SA。
        finchina = source_root / "FinChina-SA-main" / "FinChina-SA-main" / "FinChina SA.zip"
        if finchina.is_file():
            with zipfile.ZipFile(finchina) as archive:
                for split, member in (("train", "FinChina SA/train.json"), ("test", "FinChina SA/test.json")):
                    for row in json.loads(archive.read(member)):
                        prompt = f"标题：{row['title']}\n正文：{row['text']}\n\n识别涉及机构及其情感标签。"
                        emit_text(
                            build_record(
                                prompt,
                                _json_text(row["institution"]),
                                source="finchina_sa",
                                source_split=split,
                                task="financial_sentiment",
                            ),
                            split,
                        )

        # FiNER-ORD：按句子聚合 token 标注。
        finer = source_root / "FiNER-ORD-main" / "FiNER-ORD-main" / "data"
        for split, path in (("train", finer / "train" / "train.csv"), ("test", finer / "test" / "test.csv")):
            if not path.is_file():
                continue
            sentences: dict[tuple[str, str], list[tuple[str, str]]] = defaultdict(list)
            with path.open("r", encoding="utf-8-sig", newline="") as file:
                for row in csv.DictReader(file):
                    sentences[(row["doc_idx"], row["sent_idx"])].append((row["gold_token"], row["gold_label"]))
            for tokens in sentences.values():
                prompt = "为以下金融文本中的每个 token 标注实体标签：\n" + " ".join(token for token, _ in tokens)
                emit_text(
                    build_record(
                        prompt,
                        _json_text([{"token": token, "label": label} for token, label in tokens]),
                        source="finer_ord",
                        source_split=split,
                        task="financial_ner",
                    ),
                    split,
                )

        # FINESSE 中与已纳入训练数据同源的 finqa/convfinqa/tatqa 不重复写入评测池。
        finesse = source_root / "FINESSE-Bench-main" / "FINESSE-Bench-main" / "data"
        if finesse.is_dir():
            for path in sorted(finesse.glob("*/question.jsonl")):
                if path.parent.name.lower() in {"finqa", "convfinqa", "tatqa"}:
                    continue
                for row in _iter_jsonl(path):
                    emit_text(
                        build_record(
                            row["prompt"],
                            row["answer"],
                            source="finesse_bench",
                            source_split="test",
                            task=path.parent.name,
                        ),
                        "test",
                    )

        # FinEval。
        fineval = source_root / "FinEval"
        if fineval.is_dir():
            for split_dir in ("dev", "val", "test"):
                for path in sorted((fineval / split_dir).glob("*.csv")):
                    with path.open("r", encoding="utf-8-sig", newline="") as file:
                        for row in csv.DictReader(file):
                            if row.get("answer") in (None, ""):
                                skipped_records["fineval_missing_answer"] += 1
                                continue
                            options = "\n".join(f"{key}. {row[key]}" for key in ("A", "B", "C", "D"))
                            emit_text(
                                build_record(
                                    f"{row['question']}\n\n选项：\n{options}",
                                    _qa_response(row["answer"], row.get("explanation")),
                                    source="fineval",
                                    source_split=split_dir,
                                    task=path.stem.rsplit("_", 1)[0],
                                ),
                                split_dir,
                            )

        # FinTruthQA。
        fintruth = (
            source_root
            / "FinTruthQA-main"
            / "FinTruthQA-main"
            / "dataset"
            / "FinTruthQA.csv"
        )
        if fintruth.is_file():
            with fintruth.open("r", encoding="utf-8-sig", newline="") as file:
                for row in csv.DictReader(file):
                    emit_text(
                        build_record(
                            row["QUES"],
                            row["ANS"],
                            source="fintruthqa",
                            source_split="test",
                            task="financial_qa_truthfulness",
                        ),
                        "test",
                    )

        # HiTab：表格为结构化文本，属于纯文本训练。
        hitab = source_root / "HiTab-main" / "HiTab-main" / "data"
        tables_zip = hitab / "tables.zip"
        if tables_zip.is_file():
            with zipfile.ZipFile(tables_zip) as archive:
                for split, filename in (
                    ("train", "train_samples.jsonl"),
                    ("dev", "dev_samples.jsonl"),
                    ("test", "test_samples.jsonl"),
                ):
                    sample_path = hitab / filename
                    if not sample_path.is_file():
                        continue
                    for row in _iter_jsonl(sample_path):
                        table_name = f"tables/hmt/{row['table_id']}.json"
                        if table_name not in archive.namelist():
                            continue
                        table = json.loads(archive.read(table_name))
                        prompt = f"表格：\n{_json_text(table)}\n\n问题：{row['question']}"
                        emit_text(
                            build_record(
                                prompt,
                                _json_text(row["answer"]),
                                source="hitab",
                                source_split=split,
                                task="hierarchical_table_qa",
                            ),
                            split,
                        )

        # PACIFIC 与 TAT-QA：按 question 展平。
        grouped_sets = [
            (
                "pacific",
                source_root / "PACIFIC-main" / "PACIFIC-main" / "data" / "pacific",
                {"train": "train.json", "dev": "validation.json", "test": "test.json"},
            ),
            (
                "tatqa",
                source_root / "TAT-QA-master" / "TAT-QA-master" / "dataset_raw",
                {
                    "train": "tatqa_dataset_train.json",
                    "dev": "tatqa_dataset_dev.json",
                    "test": "tatqa_dataset_test_gold.json",
                },
            ),
        ]
        for source_name, directory, split_files in grouped_sets:
            for split, filename in split_files.items():
                path = directory / filename
                if not path.is_file():
                    continue
                for item in _load_json(path):
                    table = item.get("table", {}).get("table") or []
                    paragraphs = "\n".join(
                        str(p.get("text") or p) for p in item.get("paragraphs") or []
                    )
                    context = f"表格：\n{table_to_markdown(table)}\n\n段落：\n{paragraphs}"
                    for question in item.get("questions") or []:
                        emit_text(
                            build_record(
                                f"{context}\n\n问题：{question['question']}",
                                _qa_response(question.get("answer"), question.get("derivation")),
                                source=source_name,
                                source_split=split,
                                task="table_text_qa",
                            ),
                            split,
                        )

        # PromptPG/TabMWP：对应 PNG 表格图，作为多模态数据。
        finer139 = (
            source_root
            / "finer-main"
            / "finer-main"
            / "data"
            / "hf_finer139"
        )
        finer139_zip = finer139 / "finer139.zip"
        finer139_info = finer139 / "dataset_infos.json"
        if finer139_zip.is_file() and finer139_info.is_file():
            info = _load_json(finer139_info)["finer-139"]
            label_names = info["features"]["ner_tags"]["feature"]["names"]
            with zipfile.ZipFile(finer139_zip) as archive:
                for split in ("train", "validation", "test"):
                    member = f"{split}.jsonl"
                    if member not in archive.namelist():
                        continue
                    with archive.open(member) as binary:
                        text = io.TextIOWrapper(binary, encoding="utf-8")
                        for line in text:
                            if line.strip():
                                emit_text(
                                    finer139_record(
                                        json.loads(line),
                                        label_names=label_names,
                                        split=split,
                                    ),
                                    split,
                                )

        finmme = source_root / "FinMME-main" / "FinMME-main" / "data"
        if finmme.is_dir():
            for path in sorted(finmme.rglob("*.parquet")):
                for row in _iter_parquet_rows(path):
                    if row.get("answer") in (None, ""):
                        skipped_records["finmme_missing_answer"] += 1
                        continue
                    emit_multi(
                        finmme_record(
                            row,
                            asset_root=multi_root / "assets" / "finmme",
                            manifest_image_root="data/train_multi/assets/finmme",
                        ),
                        "train",
                    )

        pixiu = source_root / "PIXIU-main" / "PIXIU-main" / "data" / "hf"
        if pixiu.is_dir():
            for dataset_dir in sorted(path for path in pixiu.iterdir() if path.is_dir()):
                if (pixiu / f"{dataset_dir.name}-instruct").is_dir():
                    continue
                for path in sorted(dataset_dir.rglob("*.parquet")):
                    filename = path.name.lower()
                    split = (
                        "train"
                        if "train" in filename
                        else "validation"
                        if "valid" in filename
                        else "test"
                    )
                    for row in _iter_parquet_rows(path):
                        if row.get("query") in (None, "") or row.get("answer") in (None, ""):
                            skipped_records["pixiu_missing_supervision"] += 1
                            continue
                        emit_text(
                            pixiu_record(
                                row,
                                source_name=dataset_dir.name,
                                split=split,
                            ),
                            split,
                        )

        tatdqa = source_root / "TAT-DQA-master" / "TAT-DQA-master" / "dataset"
        if tatdqa.is_dir():
            tatdqa_splits = (
                ("train", "tatdqa_dataset_train.json", "tatdqa_docs_train.zip"),
                ("dev", "tatdqa_dataset_dev.json", "tatdqa_docs_dev.zip"),
                ("test", "tatdqa_dataset_test_gold.json", "tatdqa_docs_test.zip"),
            )
            for split, data_name, archive_name in tatdqa_splits:
                data_path = tatdqa / data_name
                archive_path = tatdqa / archive_name
                if not data_path.is_file() or not archive_path.is_file():
                    continue
                with zipfile.ZipFile(archive_path) as archive:
                    for item in _load_json(data_path):
                        doc = item["doc"]
                        image_name = f"{doc['uid']}_{doc['page']}.png"
                        member = f"{split}/{image_name}"
                        if member not in archive.namelist():
                            skipped_records["tatdqa_missing_image"] += len(
                                item.get("questions") or []
                            )
                            continue
                        target_rel = (
                            f"data/train_multi/assets/tatdqa/{split}/{image_name}"
                        )
                        target = project_root / target_rel
                        target.parent.mkdir(parents=True, exist_ok=True)
                        target.write_bytes(archive.read(member))
                        for record in tatdqa_records(
                            item,
                            split=split,
                            image_path=target_rel,
                        ):
                            emit_multi(record, split)

        multihiertt = (
            source_root
            / "MultiHiertt-main"
            / "MultiHiertt-main"
            / "dataset"
            / "multihiertt_data"
        )
        if multihiertt.is_dir():
            for split in ("train", "dev", "test"):
                path = multihiertt / f"{split}.json"
                if not path.is_file():
                    continue
                for row in _load_json(path):
                    qa = row.get("qa") or {}
                    if qa.get("answer") in (None, ""):
                        skipped_records["multihiertt_missing_answer"] += 1
                        continue
                    emit_text(multihiertt_record(row, split=split), split)

        finchain_root = source_root / "finchain-main" / "finchain-main" / "data"
        finchain_paths = []
        if finchain_root.is_dir():
            finchain_paths.extend(sorted((finchain_root / "testset").rglob("*.jsonl")))
            finchain_paths.extend(
                sorted((finchain_root / "templates").rglob("*_problems.jsonl"))
            )
        for path in finchain_paths:
            for row in _iter_jsonl(path):
                if row.get("question") in (None, "") or row.get("solution") in (None, ""):
                    skipped_records["finchain_missing_supervision"] += 1
                    continue
                emit_text(
                    build_record(
                        row["question"],
                        row["solution"],
                        source="finchain",
                        source_split="test",
                        task=path.stem,
                    ),
                    "test",
                )

        finch_manifest = (
            source_root
            / "Finch-main"
            / "Finch-main"
            / "dataset"
            / "finch_workflows_test.jsonl"
        )
        if finch_manifest.is_file():
            workflow_count = sum(1 for _ in _iter_jsonl(finch_manifest))
            downloaded_but_not_direct_sft["Finch-main"] = (
                f"{workflow_count} workflows require binary spreadsheet or document outputs"
            )

        promptpg = source_root / "PromptPG-main" / "PromptPG-main" / "data" / "tabmwp"
        if promptpg.is_dir():
            for split, filename in (
                ("train", "problems_train.json"),
                ("dev", "problems_dev.json"),
                ("test", "problems_test.json"),
            ):
                path = promptpg / filename
                if not path.is_file():
                    continue
                for item_id, row in _load_json(path).items():
                    source_image = promptpg / "tables" / f"{item_id}.png"
                    if not source_image.is_file():
                        continue
                    target_rel = f"data/train_multi/assets/tabmwp/{item_id}.png"
                    _copy_image(source_image, project_root / target_rel)
                    choices = row.get("choices")
                    prompt = f"<image>{row['question']}"
                    if choices:
                        prompt += "\n\n选项：" + _json_text(choices)
                    emit_multi(
                        build_record(
                            prompt,
                            _qa_response(row["answer"], row.get("solution")),
                            source="tabmwp",
                            source_split=split,
                            images=[target_rel],
                            task="table_math_qa",
                        ),
                        split,
                    )

        # 中文金融事件数据集。
        cn_root = source_root / "数据集"
        if cn_root.is_dir():
            nested = next((path for path in cn_root.iterdir() if path.is_dir()), None)
            if nested:
                for split in ("train", "dev", "test"):
                    path = nested / f"{split}.json"
                    if not path.is_file():
                        continue
                    for _, row in _load_json(path):
                        emit_text(
                            build_record(
                                "从以下公告中抽取金融事件及其字段：\n" + "\n".join(row["sentences"]),
                                _json_text(row["recguid_eventname_eventdict_list"]),
                                source="chinese_financial_event",
                                source_split=split,
                                task="financial_event_extraction",
                            ),
                            split,
                        )

        # FinTabNet：从 TAR 中读取 split XML 与对应 JPG。
        fintab_tar = (
            source_root
            / "fintabnet"
            / "FinTabNet.c-Structure"
            / "FinTabNet.c-Structure.tar"
        )
        if include_fintabnet and fintab_tar.is_file():
            counts = convert_fintabnet_tar(
                fintab_tar,
                train_writer=multi_train,
                eval_writer=multi_eval,
                asset_dir=multi_root / "assets" / "fintabnet",
            )
            source_counts["fintabnet"] += counts["train"] + counts["eval"]

        output_counts = {
            "text_train": text_train.written,
            "text_eval": text_eval.written,
            "multi_train": multi_train.written,
            "multi_eval": multi_eval.written,
        }
        duplicates = {
            "text_train": text_train.duplicates,
            "text_eval": text_eval.duplicates,
            "multi_train": multi_train.duplicates,
            "multi_eval": multi_eval.duplicates,
        }

    report = {
        "source_root": str(source_root),
        "outputs": output_counts,
        "duplicates_removed": duplicates,
        "records_by_source": dict(sorted(source_counts.items())),
        "skipped_records": dict(sorted(skipped_records.items())),
        "skipped_no_local_supervised_data": skipped,
        "excluded_by_user": excluded_by_user,
        "downloaded_but_not_direct_sft": downloaded_but_not_direct_sft,
    }
    report_path = project_root / "data" / "dataset_conversion_report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--skip-fintabnet", action="store_true")
    args = parser.parse_args(argv)
    if not args.source.is_dir():
        parser.error(f"源目录不存在：{args.source}")
    if not args.project_root.is_dir():
        parser.error(f"项目目录不存在：{args.project_root}")
    report = prepare_all(
        args.source.resolve(),
        args.project_root.resolve(),
        include_fintabnet=not args.skip_fintabnet,
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
