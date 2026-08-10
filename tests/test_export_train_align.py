import json
from pathlib import Path

import pytest
from PIL import Image

from scripts.data.export_train_align import export_train_align


def _row(image_path: str, *, rendered: bool) -> dict:
    row = {
        "messages": [
            {"role": "user", "content": "<image>请根据图中材料抽取金融事件。"},
            {"role": "assistant", "content": '[[0, "EquityPledge", {}]]'},
        ],
        "images": [image_path],
        "target_capability": "financial_event_extraction",
        "source": "unit_test",
    }
    if rendered:
        row["rendered_from"] = {"evidence_rendered": True}
    return row


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )


def test_export_copies_generated_images_and_rewrites_project_relative_route(tmp_path):
    source_image = tmp_path / "data" / "staging" / "page.png"
    source_image.parent.mkdir(parents=True)
    Image.new("RGB", (32, 24), "white").save(source_image)
    source_jsonl = tmp_path / "selected.jsonl"
    _write_jsonl(source_jsonl, [_row("data/staging/page.png", rendered=True)])

    output = tmp_path / "data" / "train_multi" / "train_align.jsonl"
    assets = tmp_path / "data" / "train_multi" / "assets" / "align"
    stats = export_train_align([source_jsonl], output, assets, tmp_path)

    exported = json.loads(output.read_text(encoding="utf-8"))
    assert exported["images"] == [
        "data/train_multi/assets/align/financial_event_extraction_page.png"
    ]
    assert (assets / "financial_event_extraction_page.png").exists()
    assert stats["rows"] == 1
    assert stats["copied_images"] == 1


def test_export_preserves_missing_original_multimodal_reference(tmp_path):
    source_jsonl = tmp_path / "selected.jsonl"
    original_path = "data/train_multi/assets/original/not_local.png"
    _write_jsonl(source_jsonl, [_row(original_path, rendered=False)])

    output = tmp_path / "data" / "train_multi" / "train_align.jsonl"
    assets = tmp_path / "data" / "train_multi" / "assets" / "align"
    export_train_align([source_jsonl], output, assets, tmp_path)

    exported = json.loads(output.read_text(encoding="utf-8"))
    assert exported["images"] == [original_path]


def test_export_copies_downloaded_external_image_to_align(tmp_path):
    source_image = tmp_path / "data" / "external" / "chart.png"
    source_image.parent.mkdir(parents=True)
    Image.new("RGB", (32, 24), "white").save(source_image)
    row = _row("data/external/chart.png", rendered=False)
    row["external_image_local"] = True
    row["target_capability"] = "image_caption"
    source_jsonl = tmp_path / "selected.jsonl"
    _write_jsonl(source_jsonl, [row])

    output = tmp_path / "data" / "train_multi" / "train_align.jsonl"
    assets = tmp_path / "data" / "train_multi" / "assets" / "align"
    export_train_align([source_jsonl], output, assets, tmp_path)

    exported = json.loads(output.read_text(encoding="utf-8"))
    assert exported["images"] == ["data/train_multi/assets/align/image_caption_unit_test_chart.png"]
    assert (assets / "image_caption_unit_test_chart.png").exists()


def test_export_external_images_with_same_basename_use_unique_source_names(tmp_path):
    rows = []
    for source_id in ("candlestick/1/a", "candlestick/2/a"):
        source_image = tmp_path / "data" / "external" / source_id / "a.png"
        source_image.parent.mkdir(parents=True)
        Image.new("RGB", (32, 24), "white").save(source_image)
        row = _row(source_image.relative_to(tmp_path).as_posix(), rendered=False)
        row["external_image_local"] = True
        row["source"] = f"MME-Finance/MMfin_CN/{source_id}"
        rows.append(row)
    source_jsonl = tmp_path / "selected.jsonl"
    _write_jsonl(source_jsonl, rows)

    output = tmp_path / "data" / "train_multi" / "train_align.jsonl"
    assets = tmp_path / "data" / "train_multi" / "assets" / "align"
    export_train_align([source_jsonl], output, assets, tmp_path)

    exported = [json.loads(line) for line in output.read_text(encoding="utf-8").splitlines()]
    routed = [row["images"][0] for row in exported]
    assert len(set(routed)) == 2
    assert all((tmp_path / path).exists() for path in routed)


def test_export_rejects_missing_image_already_routed_to_align(tmp_path):
    source_jsonl = tmp_path / "selected.jsonl"
    _write_jsonl(
        source_jsonl,
        [_row("data/train_multi/assets/align/missing.png", rendered=False)],
    )

    with pytest.raises(FileNotFoundError, match="missing.png"):
        export_train_align(
            [source_jsonl],
            tmp_path / "data" / "train_multi" / "train_align.jsonl",
            tmp_path / "data" / "train_multi" / "assets" / "align",
            tmp_path,
        )


def test_export_deduplicates_cross_capability_rows_and_records_all_capabilities(tmp_path):
    row = {
        "messages": [
            {"role": "user", "content": "请分析公司利润下降的原因。"},
            {"role": "assistant", "content": "收入下降和成本上升共同压低利润。"},
        ],
        "source": "unit_test",
    }
    first = tmp_path / "explanation_anomaly_causality.jsonl"
    second = tmp_path / "financial_audit_fundamentals.jsonl"
    _write_jsonl(first, [row])
    _write_jsonl(second, [row])

    output = tmp_path / "data" / "train_multi" / "train_align.jsonl"
    stats = export_train_align(
        [first, second],
        output,
        tmp_path / "data" / "train_multi" / "assets" / "align",
        tmp_path,
    )

    exported = [json.loads(line) for line in output.read_text(encoding="utf-8").splitlines()]
    assert len(exported) == 1
    assert exported[0]["target_capabilities"] == [
        "explanation_anomaly_causality",
        "financial_audit_fundamentals",
    ]
    assert stats["duplicate_rows"] == 1


def test_export_uses_reviewed_capability_filename_instead_of_stale_row_label(tmp_path):
    row = {
        "messages": [
            {"role": "user", "content": "为什么公司利润下降？"},
            {"role": "assistant", "content": "收入下降和成本上升导致利润下降。"},
        ],
        "target_capability": "portfolio_allocation_risk_return",
    }
    source = tmp_path / "explanation_anomaly_causality.jsonl"
    _write_jsonl(source, [row])

    output = tmp_path / "data" / "train_multi" / "train_align.jsonl"
    export_train_align(
        [source],
        output,
        tmp_path / "data" / "train_multi" / "assets" / "align",
        tmp_path,
    )

    exported = json.loads(output.read_text(encoding="utf-8"))
    assert exported["target_capability"] == "explanation_anomaly_causality"
    assert exported["target_capabilities"] == ["explanation_anomaly_causality"]
