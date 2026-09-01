import hashlib
import json
import tempfile
import unittest
from pathlib import Path


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")


class PrepareFinanceQaInputsTests(unittest.TestCase):
    def _build_source(self, root: Path) -> tuple[Path, Path]:
        source = root / "finance_data"
        document_id = "sse_demo"
        raw = source / "raw" / document_id
        processed = source / "processed" / document_id

        _write_json(
            raw / "metadata.json",
            {
                "document_id": document_id,
                "title": "示例银行年度报告",
                "company_name": "示例银行",
                "allowed_for_training": False,
                "original_file": "original.pdf",
                "mime_type": "application/pdf",
            },
        )
        (raw / "original.pdf").write_bytes(b"%PDF-demo")

        pages = []
        for page_number, text in (
            (1, "营业收入 100 亿元，净利润 20 亿元。"),
            (2, "营业收入同比增长 10%，净利润同比增长 5%。"),
        ):
            stem = f"page_{page_number:04d}"
            (processed / "pages").mkdir(parents=True, exist_ok=True)
            (processed / "pages" / f"{stem}.png").write_bytes(
                b"\x89PNG\r\n\x1a\n" + bytes([page_number])
            )
            _write_text(processed / "text" / f"{stem}.txt", text)
            _write_json(
                processed / "ocr" / f"{stem}.json",
                {
                    "page_number": page_number,
                    "width": 1000,
                    "height": 2000,
                    "blocks": [
                        {
                            "text": text,
                            "bbox": [100, 200, 900, 400],
                            "confidence": 0.99,
                        }
                    ],
                    "full_text": text,
                },
            )
            pages.append(
                {
                    "page_number": page_number,
                    "image": f"pages/{stem}.png",
                    "text": f"text/{stem}.txt",
                    "ocr": f"ocr/{stem}.json",
                    "tables": ["table_0001_01"] if page_number == 1 else [],
                    "figures": ["figure_0002_01"] if page_number == 2 else [],
                    "errors": [],
                }
            )

        _write_json(
            processed / "tables" / "table_0001_01" / "table.json",
            {
                "table_id": "table_0001_01",
                "page_number": 1,
                "bbox": [100, 500, 900, 1500],
                "title": "主要指标",
                "unit": "亿元",
                "columns": ["指标", "本期", "上期"],
                "rows": [["营业收入", "100", "90"]],
                "cells": [
                    {
                        "text": "100",
                        "bbox": [400, 700, 600, 800],
                        "confidence": 0.99,
                    }
                ],
                "review_required": False,
            },
        )
        _write_text(
            processed / "tables" / "table_0001_01" / "table.md",
            "| 指标 | 本期 | 上期 |\n|---|---|---|\n| 营业收入 | 100 | 90 |\n",
        )
        (
            processed / "tables" / "table_0001_01" / "image.png"
        ).write_bytes(b"\x89PNG\r\n\x1a\ntable")

        _write_json(
            processed / "figures" / "figure_0002_01.json",
            {
                "figure_id": "figure_0002_01",
                "page_number": 2,
                "bbox": [200, 600, 800, 1400],
                "crop_bbox": [180, 580, 820, 1420],
                "figure_type": "chart",
                "confidence": 0.9,
            },
        )
        (processed / "figures" / "figure_0002_01.png").write_bytes(
            b"\x89PNG\r\n\x1a\nfigure"
        )
        _write_json(
            processed / "document.json",
            {
                "document_id": document_id,
                "metadata": {"title": "示例银行年度报告"},
                "pages": pages,
            },
        )

        invalid = source / "raw" / "invalid_html"
        _write_json(
            invalid / "metadata.json",
            {
                "document_id": "invalid_html",
                "mime_type": "text/html",
                "original_file": "original.html",
                "allowed_for_training": False,
            },
        )
        _write_text(invalid / "original.html", "<html>blocked</html>")

        prompt = root / "financial_multimodal_prompt_library.md"
        _write_text(
            prompt,
            "# 金融多模态数据生成提示词库\n\n"
            "## 2. 公共 System Prompt\n\n```text\n系统要求\n```\n\n"
            "### FM-TAB-01｜示例\n\n```text\n表格问题 {{source_id}}\n```\n",
        )
        return source, prompt

    def test_prepare_package_creates_five_portable_bundle_types(self):
        from scripts.data.prepare_finance_qa_inputs import prepare_package

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source, prompt = self._build_source(root)
            project = root / "project"
            output = project / "data" / "finance_qa"

            summary = prepare_package(
                source_root=source,
                output_root=output,
                project_root=project,
                prompt_library=prompt,
                max_cross_page_groups=20,
                samples_per_bundle=2,
            )

            rows = [
                json.loads(line)
                for line in (output / "all.jsonl").read_text(
                    encoding="utf-8"
                ).splitlines()
            ]
            counts = {}
            for row in rows:
                counts[row["package_type"]] = counts.get(row["package_type"], 0) + 1
                self.assertEqual(row["dataset_stage"], "generation_input")
                self.assertEqual(row["samples_requested"], 2)
                for path in row["media_paths"]:
                    self.assertNotIn("\\", path)
                    self.assertFalse(Path(path).is_absolute())
                    self.assertTrue((project / path).is_file())

            self.assertEqual(
                counts,
                {
                    "page_qa": 2,
                    "table_qa": 1,
                    "figure_qa": 1,
                    "cross_page_qa": 1,
                    "long_document_qa": 1,
                },
            )
            self.assertEqual(summary["bundle_counts"], counts)

            page = next(row for row in rows if row["package_type"] == "page_qa")
            region = page["page_region_map"]["pages"][0]["regions"][0]
            self.assertEqual(region["bbox"], [0.1, 0.1, 0.9, 0.2])

            table = next(row for row in rows if row["package_type"] == "table_qa")
            self.assertEqual(
                table["page_region_map"]["tables"][0]["bbox"],
                [0.1, 0.25, 0.9, 0.75],
            )
            self.assertEqual(len(table["media_paths"]), 2)

            cross_page = next(
                row for row in rows if row["package_type"] == "cross_page_qa"
            )
            self.assertEqual(cross_page["page_numbers"], [1, 2])
            self.assertEqual(len(cross_page["media_paths"]), 2)

            self.assertTrue(
                (output / "prompts" / prompt.name).is_file()
            )
            self.assertTrue(
                (
                    output
                    / "schemas"
                    / "financial_multimodal_sample.schema.json"
                ).is_file()
            )
            sample_schema = json.loads(
                (
                    output
                    / "schemas"
                    / "financial_multimodal_sample.schema.json"
                ).read_text(encoding="utf-8")
            )
            metadata_required = sample_schema["properties"]["metadata"]["required"]
            self.assertNotIn("verification", metadata_required)

    def test_manifest_hashes_files_and_records_permission_override(self):
        from scripts.data.prepare_finance_qa_inputs import prepare_package

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source, prompt = self._build_source(root)
            project = root / "project"
            output = project / "data" / "finance_qa"
            prepare_package(
                source_root=source,
                output_root=output,
                project_root=project,
                prompt_library=prompt,
            )

            manifest = json.loads(
                (output / "package_manifest.json").read_text(encoding="utf-8")
            )
            self.assertEqual(manifest["valid_documents"], 1)
            self.assertEqual(manifest["excluded_documents"][0]["document_id"], "invalid_html")
            self.assertEqual(
                manifest["training_permission_overrides"][0]["document_id"],
                "sse_demo",
            )
            self.assertFalse(
                manifest["training_permission_overrides"][0][
                    "original_allowed_for_training"
                ]
            )

            all_entry = next(
                item for item in manifest["files"] if item["path"] == "all.jsonl"
            )
            payload = (output / "all.jsonl").read_bytes()
            self.assertEqual(all_entry["size"], len(payload))
            self.assertEqual(
                all_entry["sha256"],
                hashlib.sha256(payload).hexdigest(),
            )
            self.assertEqual(manifest["file_count"], len(manifest["files"]))
            self.assertTrue(
                all(
                    not (output / item["path"]).is_symlink()
                    for item in manifest["files"]
                )
            )


if __name__ == "__main__":
    unittest.main()
