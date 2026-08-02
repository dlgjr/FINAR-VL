#!/usr/bin/env python3
"""将处理后的财报整理为可整体上传的问答生成输入包。"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
from collections import Counter
from pathlib import Path
from typing import Any, Iterable


PACKAGE_TYPES = (
    "page_qa",
    "table_qa",
    "figure_qa",
    "cross_page_qa",
    "long_document_qa",
)

SAMPLE_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "Financial multimodal generated sample",
    "type": "object",
    "required": [
        "record_id",
        "source_dataset",
        "source_id",
        "modality",
        "question",
        "answer",
        "cot",
        "task_type",
        "media",
        "is_complete",
        "missing_assets",
        "metadata",
    ],
    "properties": {
        "record_id": {"type": "string", "minLength": 1},
        "source_dataset": {"type": "string", "minLength": 1},
        "source_file": {"type": "string"},
        "source_id": {"type": "string", "minLength": 1},
        "modality": {"enum": ["multimodal", "text"]},
        "question": {"type": "string", "minLength": 1},
        "answer": {"type": ["string", "null"]},
        "cot": {
            "type": "string",
            "pattern": "^<think>[\\s\\S]+</think>$",
        },
        "choices": {"type": "object"},
        "task_type": {"type": "string", "minLength": 1},
        "media": {"type": "array", "items": {"type": "string"}, "maxItems": 5},
        "context_files": {"type": "array", "items": {"type": "string"}},
        "is_complete": {"type": "boolean"},
        "missing_assets": {"type": "array", "items": {"type": "string"}},
        "metadata": {
            "type": "object",
            "required": [
                "generation_prompt_id",
                "difficulty",
                "generation_status",
                "evidence",
                "solution_trace",
            ],
            "properties": {
                "generation_prompt_id": {"type": "string", "minLength": 1},
                "difficulty": {"type": "string"},
                "generation_status": {"enum": ["accepted", "rejected"]},
                "evidence": {
                    "type": "array",
                    "minItems": 2,
                    "items": {
                        "type": "object",
                        "required": ["source_ref"],
                        "properties": {
                            "source_ref": {"type": "string"},
                            "page": {"type": ["integer", "null"]},
                            "bbox": {
                                "type": ["array", "null"],
                                "items": {"type": "number", "minimum": 0, "maximum": 1},
                                "minItems": 4,
                                "maxItems": 4,
                            },
                            "table_cell": {"type": ["object", "null"]},
                        },
                        "additionalProperties": True,
                    },
                },
                "solution_trace": {
                    "type": "object",
                    "required": [
                        "retrieved_metrics",
                        "chart_text_alignment",
                        "formula_selection_reason",
                        "steps",
                        "calculations",
                        "unit_and_rounding",
                        "evidence_conclusion",
                    ],
                    "properties": {
                        "retrieved_metrics": {
                            "type": "array",
                            "minItems": 3,
                        },
                        "chart_text_alignment": {
                            "type": "array",
                            "minItems": 1,
                        },
                        "formula_selection_reason": {
                            "type": "string",
                            "minLength": 1,
                        },
                        "steps": {"type": "array", "minItems": 2},
                        "calculations": {
                            "type": "array",
                            "minItems": 2,
                            "items": {
                                "type": "object",
                                "required": [
                                    "expression",
                                    "claimed_result",
                                    "unit",
                                    "rounding_digits",
                                    "evidence_indices",
                                ],
                                "properties": {
                                    "expression": {
                                        "type": "string",
                                        "minLength": 1,
                                    },
                                    "claimed_result": {"type": "number"},
                                    "unit": {"type": "string"},
                                    "rounding_digits": {
                                        "type": "integer",
                                        "minimum": 0,
                                        "maximum": 8,
                                    },
                                    "evidence_indices": {
                                        "type": "array",
                                        "minItems": 1,
                                        "items": {
                                            "type": "integer",
                                            "minimum": 0,
                                        },
                                    },
                                },
                            },
                        },
                        "unit_and_rounding": {
                            "type": "string",
                            "minLength": 1,
                        },
                        "evidence_conclusion": {
                            "type": "string",
                            "minLength": 1,
                        },
                    },
                    "additionalProperties": True,
                },
                "verification": {"type": "object"},
                "programmatic_validation": {
                    "type": "object",
                    "properties": {
                        "metrics_passed": {"type": "boolean"},
                        "evidence_grounding_passed": {"type": "boolean"},
                        "arithmetic_passed": {"type": "boolean"},
                        "calculation_results": {"type": "array"},
                        "failures": {"type": "array"},
                    },
                },
            },
            "additionalProperties": True,
        },
    },
    "additionalProperties": True,
}

QUESTION_CANDIDATE_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "Financial hard question candidate",
    "type": "object",
    "required": [
        "candidate_id",
        "bundle_id",
        "generation_prompt_id",
        "question",
        "task_type",
        "media_paths",
        "evidence",
        "expected_steps",
        "metric_refs",
        "chart_text_alignment",
        "formula_selection_reason",
        "hardness",
        "finance_checks",
    ],
    "not": {"required": ["answer"]},
    "properties": {
        "candidate_id": {"type": "string", "minLength": 1},
        "bundle_id": {"type": "string", "minLength": 1},
        "generation_prompt_id": {"type": "string", "pattern": "^FM-H[A-Z]{2}-\\d{2}$"},
        "question": {"type": "string", "minLength": 1, "maxLength": 1200},
        "task_type": {"type": "string", "minLength": 1},
        "media_paths": {
            "type": "array",
            "minItems": 1,
            "maxItems": 5,
            "items": {"type": "string", "maxLength": 512},
        },
        "evidence": {
            "type": "array",
            "minItems": 3,
            "maxItems": 8,
            "items": {
                "type": "object",
                "required": [
                    "source_ref",
                    "page",
                    "media_index",
                    "bbox",
                    "table_cell",
                    "text_quote",
                ],
                "properties": {
                    "source_ref": {"type": "string", "maxLength": 512},
                    "page": {
                        "type": ["integer", "null"],
                        "minimum": 1,
                    },
                    "media_index": {
                        "type": ["integer", "null"],
                        "minimum": 0,
                    },
                    "bbox": {
                        "type": ["array", "null"],
                        "minItems": 4,
                        "maxItems": 4,
                        "items": {"type": "number"},
                    },
                    "table_cell": {
                        "type": ["object", "string", "null"],
                    },
                    "text_quote": {"type": "string", "maxLength": 600},
                },
            },
        },
        "expected_steps": {
            "type": "array",
            "minItems": 2,
            "maxItems": 6,
            "items": {"type": "string", "maxLength": 500},
        },
        "metric_refs": {
            "type": "array",
            "minItems": 3,
            "maxItems": 8,
            "items": {
                "type": "object",
                "required": [
                    "name",
                    "page",
                    "value",
                    "unit",
                    "evidence_index",
                ],
                "properties": {
                    "name": {"type": "string", "maxLength": 200},
                    "page": {
                        "type": ["integer", "null"],
                        "minimum": 1,
                    },
                    "value": {"type": "string", "maxLength": 120},
                    "unit": {"type": "string", "maxLength": 50},
                    "evidence_index": {
                        "type": "integer",
                        "minimum": 0,
                    },
                },
            },
        },
        "chart_text_alignment": {
            "type": "array",
            "minItems": 1,
            "maxItems": 4,
            "items": {
                "type": "object",
                "properties": {
                    "visual_ref": {"type": "string", "maxLength": 512},
                    "text_ref": {"type": "string", "maxLength": 512},
                    "relationship": {"type": "string", "maxLength": 600},
                },
            },
        },
        "formula_selection_reason": {
            "type": "string",
            "minLength": 1,
            "maxLength": 1200,
        },
        "hardness": {
            "type": "object",
            "required": [
                "independent_evidence_count",
                "page_count",
                "modality_count",
                "calculation_step_count",
            ],
            "properties": {
                "independent_evidence_count": {
                    "type": "integer",
                    "minimum": 3,
                },
                "page_count": {"type": "integer", "minimum": 2},
                "modality_count": {"type": "integer", "minimum": 2},
                "calculation_step_count": {
                    "type": "integer",
                    "minimum": 2,
                },
            },
        },
        "finance_checks": {"type": "object"},
    },
    "additionalProperties": True,
}


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _copy_file(source: Path, target: Path) -> None:
    if source.resolve() == target.resolve():
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)


def _project_path(path: Path, project_root: Path) -> str:
    try:
        relative = path.resolve().relative_to(project_root.resolve())
    except ValueError as error:
        raise ValueError(
            f"package path must be inside project root: {path}"
        ) from error
    return relative.as_posix()


def _normalized_bbox(
    bbox: Iterable[float] | None,
    width: float,
    height: float,
) -> list[float] | None:
    if bbox is None:
        return None
    values = [float(value) for value in bbox]
    if len(values) != 4 or width <= 0 or height <= 0:
        return None
    x1, y1, x2, y2 = values
    return [
        round(max(0.0, min(1.0, x1 / width)), 6),
        round(max(0.0, min(1.0, y1 / height)), 6),
        round(max(0.0, min(1.0, x2 / width)), 6),
        round(max(0.0, min(1.0, y2 / height)), 6),
    ]


def _page_layout(ocr: dict[str, Any], ocr_path: str) -> dict[str, Any]:
    width = float(ocr.get("width") or 0)
    height = float(ocr.get("height") or 0)
    regions = []
    for block in ocr.get("blocks") or []:
        regions.append(
            {
                "text": str(block.get("text") or ""),
                "bbox": _normalized_bbox(block.get("bbox"), width, height),
                "confidence": block.get("confidence"),
            }
        )
    return {
        "page_number": int(ocr["page_number"]),
        "width": int(width),
        "height": int(height),
        "ocr": ocr_path,
        "regions": regions,
    }


def _table_layout(
    table: dict[str, Any],
    width: float,
    height: float,
) -> dict[str, Any]:
    return {
        "table_id": table["table_id"],
        "page_number": int(table["page_number"]),
        "bbox": _normalized_bbox(table.get("bbox"), width, height),
        "title": table.get("title") or "",
        "unit": table.get("unit") or "",
        "cells": [
            {
                "text": str(cell.get("text") or ""),
                "bbox": _normalized_bbox(cell.get("bbox"), width, height),
                "confidence": cell.get("confidence"),
            }
            for cell in table.get("cells") or []
        ],
    }


def _figure_layout(
    figure: dict[str, Any],
    width: float,
    height: float,
) -> dict[str, Any]:
    return {
        "figure_id": figure["figure_id"],
        "page_number": int(figure["page_number"]),
        "bbox": _normalized_bbox(figure.get("bbox"), width, height),
        "crop_bbox": _normalized_bbox(figure.get("crop_bbox"), width, height),
        "figure_type": figure.get("figure_type") or figure.get("layout_label") or "",
        "confidence": figure.get("confidence"),
    }


def _copy_page_files(
    processed: Path,
    page: dict[str, Any],
    target: Path,
    project_root: Path,
) -> tuple[list[str], dict[str, list[str]], dict[str, Any]]:
    image_target = target / "page.png"
    text_target = target / "page.txt"
    ocr_target = target / "ocr.json"
    _copy_file(processed / page["image"], image_target)
    _copy_file(processed / page["text"], text_target)
    _copy_file(processed / page["ocr"], ocr_target)

    image_path = _project_path(image_target, project_root)
    text_path = _project_path(text_target, project_root)
    ocr_path = _project_path(ocr_target, project_root)
    ocr = _read_json(processed / page["ocr"])
    return (
        [image_path],
        {
            "pdf_text": [text_path],
            "ocr": [ocr_path],
            "tables": [],
            "figures": [],
        },
        _page_layout(ocr, ocr_path),
    )


def _copy_metadata(
    metadata_path: Path,
    category_document_root: Path,
) -> dict[str, Any]:
    target = category_document_root / "metadata.json"
    if not target.exists():
        _copy_file(metadata_path, target)
    return _read_json(metadata_path)


def _write_bundle(target: Path, row: dict[str, Any]) -> None:
    _write_json(target, row)


def _text_ngrams(text: str) -> set[str]:
    normalized = re.sub(r"\s+", "", text)
    normalized = re.sub(r"[^\u4e00-\u9fffA-Za-z0-9%]", "", normalized)
    return {
        normalized[index : index + 2]
        for index in range(max(0, len(normalized) - 1))
    }


def _cross_page_groups(
    processed: Path,
    pages: list[dict[str, Any]],
    limit: int,
) -> list[list[dict[str, Any]]]:
    candidates: list[tuple[float, int, list[dict[str, Any]]]] = []
    page_texts = [
        (processed / page["text"]).read_text(encoding="utf-8", errors="replace")
        for page in pages
    ]
    ngrams = [_text_ngrams(text) for text in page_texts]
    for index in range(len(pages) - 1):
        left = ngrams[index]
        right = ngrams[index + 1]
        union = left | right
        overlap = len(left & right) / len(union) if union else 0.0
        asset_bonus = 0.01 * (
            len(pages[index].get("tables") or [])
            + len(pages[index + 1].get("tables") or [])
            + len(pages[index].get("figures") or [])
            + len(pages[index + 1].get("figures") or [])
        )
        candidates.append((overlap + asset_bonus, index, pages[index : index + 2]))
    candidates.sort(key=lambda item: (-item[0], item[1]))
    return [group for _, _, group in candidates[:limit]]


def _copy_related_assets(
    processed: Path,
    page: dict[str, Any],
    target: Path,
    project_root: Path,
    contexts: dict[str, list[str]],
    page_layout: dict[str, Any],
) -> None:
    width = float(page_layout["width"])
    height = float(page_layout["height"])
    for table_id in page.get("tables") or []:
        source_dir = processed / "tables" / table_id
        target_dir = target / "tables" / table_id
        for name in ("image.png", "table.md", "table.json"):
            _copy_file(source_dir / name, target_dir / name)
        contexts["tables"].extend(
            [
                _project_path(target_dir / "table.json", project_root),
                _project_path(target_dir / "table.md", project_root),
            ]
        )
        table = _read_json(source_dir / "table.json")
        page_layout.setdefault("tables", []).append(
            _table_layout(table, width, height)
        )

    for figure_id in page.get("figures") or []:
        image_source = processed / "figures" / f"{figure_id}.png"
        json_source = processed / "figures" / f"{figure_id}.json"
        target_dir = target / "figures"
        _copy_file(image_source, target_dir / f"{figure_id}.png")
        _copy_file(json_source, target_dir / f"{figure_id}.json")
        contexts["figures"].append(
            _project_path(target_dir / f"{figure_id}.json", project_root)
        )
        figure = _read_json(json_source)
        page_layout.setdefault("figures", []).append(
            _figure_layout(figure, width, height)
        )


def _base_row(
    *,
    bundle_id: str,
    package_type: str,
    document_id: str,
    page_numbers: list[int],
    media_paths: list[str],
    context_files: dict[str, list[str]],
    page_region_map: dict[str, Any],
    metadata: dict[str, Any],
    samples_per_bundle: int,
) -> dict[str, Any]:
    return {
        "bundle_id": bundle_id,
        "dataset_stage": "generation_input",
        "package_type": package_type,
        "document_id": document_id,
        "source_metadata": metadata,
        "page_numbers": page_numbers,
        "media_paths": media_paths,
        "context_files": context_files,
        "page_region_map": page_region_map,
        "samples_requested": samples_per_bundle,
    }


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _package_manifest(
    output_root: Path,
    bundle_counts: Counter[str],
    source_documents: list[dict[str, Any]],
    excluded_documents: list[dict[str, Any]],
    permission_overrides: list[dict[str, Any]],
) -> dict[str, Any]:
    files = []
    for path in sorted(output_root.rglob("*")):
        if not path.is_file() or path.name == "package_manifest.json":
            continue
        files.append(
            {
                "path": path.relative_to(output_root).as_posix(),
                "size": path.stat().st_size,
                "sha256": _sha256(path),
            }
        )
    return {
        "format": "finance_qa_generation_input_v1",
        "valid_documents": len(source_documents),
        "source_documents": source_documents,
        "excluded_documents": excluded_documents,
        "training_permission_overrides": permission_overrides,
        "bundle_counts": dict(bundle_counts),
        "bundle_count": sum(bundle_counts.values()),
        "file_count": len(files),
        "total_bytes": sum(item["size"] for item in files),
        "files": files,
    }


def prepare_package(
    *,
    source_root: Path,
    output_root: Path,
    project_root: Path,
    prompt_library: Path,
    max_cross_page_groups: int = 20,
    samples_per_bundle: int = 2,
    refresh_control_files: bool = False,
) -> dict[str, Any]:
    source_root = source_root.resolve()
    output_root = output_root.resolve()
    project_root = project_root.resolve()
    prompt_library = prompt_library.resolve()
    if output_root.exists() and any(output_root.iterdir()) and not refresh_control_files:
        raise FileExistsError(f"output directory is not empty: {output_root}")
    output_root.mkdir(parents=True, exist_ok=True)
    if samples_per_bundle < 1:
        raise ValueError("samples_per_bundle must be positive")
    if max_cross_page_groups < 0:
        raise ValueError("max_cross_page_groups cannot be negative")

    prompt_target = output_root / "prompts" / prompt_library.name
    _copy_file(prompt_library, prompt_target)
    _write_json(
        output_root / "schemas" / "financial_multimodal_sample.schema.json",
        SAMPLE_SCHEMA,
    )
    _write_json(
        output_root / "schemas" / "financial_question_candidate.schema.json",
        QUESTION_CANDIDATE_SCHEMA,
    )
    if refresh_control_files:
        all_path = output_root / "all.jsonl"
        counts: Counter[str] = Counter()
        if all_path.is_file():
            with all_path.open(encoding="utf-8") as handle:
                for line in handle:
                    if line.strip():
                        row = json.loads(line)
                        counts[str(row.get("package_type") or "unknown")] += 1
        previous_manifest = (
            _read_json(output_root / "package_manifest.json")
            if (output_root / "package_manifest.json").is_file()
            else {}
        )
        manifest = _package_manifest(
            output_root,
            counts,
            list(previous_manifest.get("source_documents") or []),
            list(previous_manifest.get("excluded_documents") or []),
            list(previous_manifest.get("training_permission_overrides") or []),
        )
        manifest["refresh_control_files"] = True
        _write_json(output_root / "package_manifest.json", manifest)
        return manifest

    rows: list[dict[str, Any]] = []
    counts: Counter[str] = Counter()
    source_documents: list[dict[str, Any]] = []
    excluded_documents: list[dict[str, Any]] = []
    permission_overrides: list[dict[str, Any]] = []

    raw_root = source_root / "raw"
    processed_root = source_root / "processed"
    processed_ids = {
        path.name for path in processed_root.iterdir() if path.is_dir()
    }

    for raw_dir in sorted(path for path in raw_root.iterdir() if path.is_dir()):
        metadata_path = raw_dir / "metadata.json"
        if not metadata_path.is_file():
            continue
        metadata = _read_json(metadata_path)
        document_id = str(metadata.get("document_id") or raw_dir.name)
        if metadata.get("mime_type") != "application/pdf" or document_id not in processed_ids:
            excluded_documents.append(
                {
                    "document_id": document_id,
                    "mime_type": metadata.get("mime_type"),
                    "reason": "not_a_processed_pdf",
                }
            )
            continue

        processed = processed_root / document_id
        document = _read_json(processed / "document.json")
        pages = list(document.get("pages") or [])
        source_documents.append(metadata)
        if metadata.get("allowed_for_training") is not True:
            permission_overrides.append(
                {
                    "document_id": document_id,
                    "original_allowed_for_training": metadata.get(
                        "allowed_for_training"
                    ),
                    "action": "included_by_user_instruction",
                }
            )

        page_by_number = {
            int(page["page_number"]): page for page in pages
        }

        for page in pages:
            page_number = int(page["page_number"])
            target = (
                output_root
                / "assets"
                / "page_qa"
                / document_id
                / f"page_{page_number:04d}"
            )
            category_root = target.parent
            source_metadata = _copy_metadata(metadata_path, category_root)
            media, contexts, layout = _copy_page_files(
                processed, page, target, project_root
            )
            row = _base_row(
                bundle_id=f"page_qa:{document_id}:page_{page_number:04d}",
                package_type="page_qa",
                document_id=document_id,
                page_numbers=[page_number],
                media_paths=media,
                context_files=contexts,
                page_region_map={"pages": [layout]},
                metadata=source_metadata,
                samples_per_bundle=samples_per_bundle,
            )
            _write_bundle(target / "bundle.json", row)
            rows.append(row)
            counts["page_qa"] += 1

        table_pages = {
            int(page["page_number"])
            for page in pages
            if page.get("tables")
        }
        for page_number in sorted(table_pages):
            page = page_by_number[page_number]
            target = (
                output_root
                / "assets"
                / "table_qa"
                / document_id
                / f"page_{page_number:04d}"
            )
            source_metadata = _copy_metadata(metadata_path, target.parent)
            base_media, base_contexts, page_layout = _copy_page_files(
                processed, page, target, project_root
            )
            width = float(page_layout["width"])
            height = float(page_layout["height"])
            for table_id in page.get("tables") or []:
                source_dir = processed / "tables" / table_id
                table_target = target / "tables" / table_id
                for name in ("image.png", "table.md", "table.json"):
                    _copy_file(source_dir / name, table_target / name)
                table_image = _project_path(
                    table_target / "image.png", project_root
                )
                table_json = _project_path(
                    table_target / "table.json", project_root
                )
                table_md = _project_path(
                    table_target / "table.md", project_root
                )
                table = _read_json(source_dir / "table.json")
                contexts = {
                    key: list(value) for key, value in base_contexts.items()
                }
                contexts["tables"] = [table_json, table_md]
                row = _base_row(
                    bundle_id=f"table_qa:{document_id}:{table_id}",
                    package_type="table_qa",
                    document_id=document_id,
                    page_numbers=[page_number],
                    media_paths=[base_media[0], table_image],
                    context_files=contexts,
                    page_region_map={
                        "pages": [page_layout],
                        "tables": [_table_layout(table, width, height)],
                    },
                    metadata=source_metadata,
                    samples_per_bundle=samples_per_bundle,
                )
                _write_bundle(table_target / "bundle.json", row)
                rows.append(row)
                counts["table_qa"] += 1

        figure_pages = {
            int(page["page_number"])
            for page in pages
            if page.get("figures")
        }
        for page_number in sorted(figure_pages):
            page = page_by_number[page_number]
            target = (
                output_root
                / "assets"
                / "figure_qa"
                / document_id
                / f"page_{page_number:04d}"
            )
            source_metadata = _copy_metadata(metadata_path, target.parent)
            base_media, base_contexts, page_layout = _copy_page_files(
                processed, page, target, project_root
            )
            width = float(page_layout["width"])
            height = float(page_layout["height"])
            for figure_id in page.get("figures") or []:
                image_source = processed / "figures" / f"{figure_id}.png"
                json_source = processed / "figures" / f"{figure_id}.json"
                figure_target = target / "figures"
                _copy_file(image_source, figure_target / f"{figure_id}.png")
                _copy_file(json_source, figure_target / f"{figure_id}.json")
                image_path = _project_path(
                    figure_target / f"{figure_id}.png", project_root
                )
                json_path = _project_path(
                    figure_target / f"{figure_id}.json", project_root
                )
                figure = _read_json(json_source)
                contexts = {
                    key: list(value) for key, value in base_contexts.items()
                }
                contexts["figures"] = [json_path]
                row = _base_row(
                    bundle_id=f"figure_qa:{document_id}:{figure_id}",
                    package_type="figure_qa",
                    document_id=document_id,
                    page_numbers=[page_number],
                    media_paths=[base_media[0], image_path],
                    context_files=contexts,
                    page_region_map={
                        "pages": [page_layout],
                        "figures": [
                            _figure_layout(figure, width, height)
                        ],
                    },
                    metadata=source_metadata,
                    samples_per_bundle=samples_per_bundle,
                )
                _write_bundle(
                    figure_target / f"{figure_id}.bundle.json", row
                )
                rows.append(row)
                counts["figure_qa"] += 1

        groups = _cross_page_groups(
            processed, pages, max_cross_page_groups
        )
        for group_index, group in enumerate(groups, start=1):
            target = (
                output_root
                / "assets"
                / "cross_page_qa"
                / document_id
                / f"group_{group_index:04d}"
            )
            source_metadata = _copy_metadata(metadata_path, target.parent)
            media_paths: list[str] = []
            contexts = {
                "pdf_text": [],
                "ocr": [],
                "tables": [],
                "figures": [],
            }
            layouts = []
            page_numbers = []
            for page in group:
                page_number = int(page["page_number"])
                page_target = target / f"page_{page_number:04d}"
                media, page_contexts, layout = _copy_page_files(
                    processed, page, page_target, project_root
                )
                media_paths.extend(media)
                for key in contexts:
                    contexts[key].extend(page_contexts[key])
                _copy_related_assets(
                    processed,
                    page,
                    page_target,
                    project_root,
                    contexts,
                    layout,
                )
                layouts.append(layout)
                page_numbers.append(page_number)
            row = _base_row(
                bundle_id=f"cross_page_qa:{document_id}:group_{group_index:04d}",
                package_type="cross_page_qa",
                document_id=document_id,
                page_numbers=page_numbers,
                media_paths=media_paths,
                context_files=contexts,
                page_region_map={"pages": layouts},
                metadata=source_metadata,
                samples_per_bundle=samples_per_bundle,
            )
            _write_bundle(target / "bundle.json", row)
            rows.append(row)
            counts["cross_page_qa"] += 1

        long_target = (
            output_root / "assets" / "long_document_qa" / document_id
        )
        shutil.copytree(processed, long_target, dirs_exist_ok=True)
        source_metadata = _copy_metadata(metadata_path, long_target)
        page_index = []
        for page in pages:
            page_number = int(page["page_number"])
            page_index.append(
                {
                    "page_number": page_number,
                    "image": _project_path(
                        long_target / page["image"], project_root
                    ),
                    "text": _project_path(
                        long_target / page["text"], project_root
                    ),
                    "ocr": _project_path(
                        long_target / page["ocr"], project_root
                    ),
                    "tables": list(page.get("tables") or []),
                    "figures": list(page.get("figures") or []),
                }
            )
        document_json_path = _project_path(
            long_target / "document.json", project_root
        )
        row = _base_row(
            bundle_id=f"long_document_qa:{document_id}",
            package_type="long_document_qa",
            document_id=document_id,
            page_numbers=[int(page["page_number"]) for page in pages],
            media_paths=[],
            context_files={
                "pdf_text": [],
                "ocr": [],
                "tables": [],
                "figures": [],
                "documents": [document_json_path],
            },
            page_region_map={"page_index": page_index},
            metadata=source_metadata,
            samples_per_bundle=samples_per_bundle,
        )
        _write_bundle(long_target / "bundle.json", row)
        rows.append(row)
        counts["long_document_qa"] += 1

    all_path = output_root / "all.jsonl"
    with all_path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(
                json.dumps(
                    row, ensure_ascii=False, separators=(",", ":")
                )
                + "\n"
            )

    manifest = _package_manifest(
        output_root,
        counts,
        source_documents,
        excluded_documents,
        permission_overrides,
    )
    _write_json(output_root / "package_manifest.json", manifest)
    return manifest


def build_parser() -> argparse.ArgumentParser:
    project_root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(
        description="Prepare portable finance QA generation input package"
    )
    parser.add_argument(
        "--source-root",
        type=Path,
        default=Path(r"D:\qwen3_vl_data\爬虫数据\finance_data"),
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=project_root / "data" / "finance_qa",
    )
    parser.add_argument("--project-root", type=Path, default=project_root)
    parser.add_argument("--prompt-library", type=Path, required=True)
    parser.add_argument("--max-cross-page-groups", type=int, default=20)
    parser.add_argument("--samples-per-bundle", type=int, default=2)
    parser.add_argument(
        "--refresh-control-files",
        action="store_true",
        help="Refresh prompts, schemas, and package_manifest.json without copying assets",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    summary = prepare_package(
        source_root=args.source_root,
        output_root=args.output_root,
        project_root=args.project_root,
        prompt_library=args.prompt_library,
        max_cross_page_groups=args.max_cross_page_groups,
        samples_per_bundle=args.samples_per_bundle,
        refresh_control_files=args.refresh_control_files,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
