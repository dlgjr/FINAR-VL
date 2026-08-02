import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image
from tests.test_finance_qa_two_stage import (
    _answer_sample as _two_stage_answer,
    _question_candidate as _two_stage_question,
)


class FakeProcessor:
    def __init__(self):
        self.messages = None

    def apply_chat_template(self, messages, **kwargs):
        self.messages = messages
        return json.dumps(messages, ensure_ascii=False, default=str)


def _accepted_sample(
    *,
    record_id: str,
    source_id: str,
    prompt_id: str,
    media: list[str],
) -> dict:
    return {
        "record_id": record_id,
        "source_dataset": "finance_reports",
        "source_file": media[0] if media else f"inline:{source_id}",
        "source_id": source_id,
        "modality": "multimodal" if media else "text",
        "question": "结合两项指标计算收入与利润增速差，并说明现金流风险。",
        "answer": "收入增速比利润增速高5个百分点，现金流仍需结合经营现金流数据判断。",
        "choices": {},
        "task_type": "Financial Report",
        "media": media,
        "context_files": [],
        "is_complete": True,
        "missing_assets": [],
        "metadata": {
            "generation_prompt_id": prompt_id,
            "difficulty": "hard",
            "generation_status": "accepted",
            "rejection_reason": None,
            "evidence": [
                {
                    "evidence_id": "E1",
                    "source_ref": media[0] if media else f"inline:{source_id}",
                    "page": 1,
                    "media_index": 0 if media else None,
                    "bbox": [0.1, 0.1, 0.9, 0.2] if media else None,
                    "table_cell": None,
                    "text_quote": "收入同比增长10%",
                },
                {
                    "evidence_id": "E2",
                    "source_ref": media[-1] if media else f"inline:{source_id}",
                    "page": 1,
                    "media_index": len(media) - 1 if media else None,
                    "bbox": [0.1, 0.2, 0.9, 0.3] if media else None,
                    "table_cell": None,
                    "text_quote": "利润同比增长5%",
                },
            ],
            "solution_trace": {
                "summary": "读取两项增速并计算差值。",
                "formulae": ["增速差=收入增速-利润增速"],
                "steps": [
                    {
                        "step": 1,
                        "description": "读取收入和利润增速。",
                        "evidence_ids": ["E1", "E2"],
                    },
                    {
                        "step": 2,
                        "description": "计算10%-5%=5个百分点。",
                        "evidence_ids": ["E1", "E2"],
                    },
                ],
                "intermediate_values": [],
                "rounding_rule": None,
            },
            "confidence": 0.9,
            "verification": {
                "answerable": True,
                "evidence_sufficient": True,
                "arithmetic_checked": True,
                "external_facts_used": False,
                "citations_valid": True,
                "passed": True,
            },
        },
    }


def _staged_sample(
    prompt_input: dict,
    seed: int,
    prompt_id: str | None = None,
) -> dict:
    resolved = prompt_input["_resolved_bundle"]
    if prompt_input.get("_stage") == "answer":
        question = prompt_input["_question_candidate"]
        answer_bundle = dict(resolved)
        answer_bundle["media_paths"] = question["media_paths"]
        sample = _two_stage_answer(
            answer_bundle,
            question,
            question["generation_prompt_id"],
        )
        sample["record_id"] = f"record-{seed}"
        return sample
    match = re.search(
        r"generation_prompt_id=(FM-[A-Z]+-\d+)",
        str(prompt_input["prompt"]),
    )
    selected_prompt_id = match.group(1) if match else (prompt_id or "FM-MNR-01")
    safe_bundle = dict(resolved)
    media = list(resolved["media_paths"])
    safe_bundle["media_paths"] = media if len(media) >= 2 else media * 2
    safe_bundle["page_numbers"] = [1, 2]
    candidate = _two_stage_question(
        safe_bundle,
        selected_prompt_id,
    )
    candidate["candidate_id"] = f"candidate-{seed}"
    return candidate


class GenerateFinanceQaTests(unittest.TestCase):
    def _prompt_library(self, root: Path) -> Path:
        path = root / "library.md"
        path.write_text(
            "# 提示词\n\n"
            "## 2. 公共 System Prompt\n\n```text\n只使用输入证据。\n```\n\n"
            "### FM-TAB-01｜表格计算\n\n```text\n"
            "source_id={{source_id}}\nmedia={{media_paths}}\n"
            "text={{document_text_or_ocr}}\nmap={{page_region_map}}\n"
            "seed={{generation_seed}}\n```\n\n"
            "### FM-MNR-01｜数值推理\n\n```text\n"
            "对 {{source_id}} 生成多步问题。{{document_text_or_ocr}}\n"
            "```\n\n"
            "### FM-CHT-01｜图表推理\n\n```text\n"
            "对 {{source_id}} 生成图表困难问题。{{document_text_or_ocr}}\n"
            "```\n\n"
            "### FS-2｜表格示例\n\n```text\n示例输入\n```\n"
            "```json\n{\"question\":\"示例\"}\n```\n",
            encoding="utf-8",
        )
        return path

    def _bundle(self, root: Path, media_count: int = 2) -> dict:
        media = []
        for index in range(media_count):
            path = root / "data" / "finance_qa" / "assets" / f"{index}.png"
            path.parent.mkdir(parents=True, exist_ok=True)
            Image.new("RGB", (8, 8), color=(index * 20, 0, 0)).save(path)
            media.append(path.relative_to(root).as_posix())
        text = root / "data" / "finance_qa" / "assets" / "page.txt"
        text.write_text(
            "营业收入100元，营业成本70元，净利润20元，"
            "经营活动现金流量净额15元；营业收入同比增长10%，"
            "净利润同比增长5%，经营现金流下降。",
            encoding="utf-8",
        )
        return {
            "bundle_id": "table_qa:demo:table_1",
            "dataset_stage": "generation_input",
            "package_type": "table_qa",
            "document_id": "demo",
            "source_metadata": {"title": "示例年报"},
            "page_numbers": [1, 2],
            "media_paths": media,
            "context_files": {
                "pdf_text": [text.relative_to(root).as_posix()],
                "ocr": [],
                "tables": [],
                "figures": [],
            },
            "page_region_map": {"pages": [{"page_number": 1}]},
            "samples_requested": 2,
        }

    def test_parses_templates_and_selects_two_distinct_compatible_prompts(self):
        from scripts.generate_finance_qa import (
            parse_prompt_library,
            select_templates,
        )

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            library = parse_prompt_library(self._prompt_library(root))
            usage = {}

            selected = select_templates(
                library.templates,
                package_type="table_qa",
                count=2,
                usage=usage,
            )

            self.assertEqual(library.system_prompt, "只使用输入证据。")
            self.assertEqual(
                [template.prompt_id for template in selected],
                ["FM-MNR-01", "FM-TAB-01"],
            )
            self.assertEqual(len({item.prompt_id for item in selected}), 2)
            self.assertEqual(usage, {"FM-MNR-01": 1, "FM-TAB-01": 1})

    def test_build_prompt_supports_multiple_images_and_omits_reference_answer(self):
        from scripts.generate_finance_qa import (
            build_prompt_input,
            parse_prompt_library,
        )

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            bundle = self._bundle(root)
            library = parse_prompt_library(self._prompt_library(root))
            processor = FakeProcessor()

            prompt_input = build_prompt_input(
                bundle=bundle,
                template=library.templates["FM-TAB-01"],
                library=library,
                processor=processor,
                project_root=root,
                generation_seed=7,
            )

            self.assertEqual(
                len(prompt_input["multi_modal_data"]["image"]),
                2,
            )
            user = processor.messages[-1]["content"]
            self.assertEqual(
                [part["type"] for part in user[:2]],
                ["image", "image"],
            )
            serialized = json.dumps(processor.messages, ensure_ascii=False)
            self.assertIn("营业收入同比增长10%", serialized)
            self.assertNotIn("标准答案", serialized)

    def test_validation_rejects_simple_or_untraceable_sample(self):
        from scripts.generate_finance_qa import validate_generated_sample

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            bundle = self._bundle(root)
            sample = _accepted_sample(
                record_id="r1",
                source_id=bundle["bundle_id"],
                prompt_id="FM-TAB-01",
                media=bundle["media_paths"],
            )

            validate_generated_sample(sample, bundle, root)

            simple = json.loads(json.dumps(sample))
            simple["metadata"]["evidence"] = simple["metadata"]["evidence"][:1]
            simple["metadata"]["solution_trace"]["steps"] = simple["metadata"][
                "solution_trace"
            ]["steps"][:1]
            simple_bundle = dict(bundle)
            simple_bundle["page_numbers"] = [1]
            with self.assertRaisesRegex(ValueError, "not a hard question"):
                validate_generated_sample(simple, simple_bundle, root)

            missing = json.loads(json.dumps(sample))
            missing["metadata"]["evidence"][0]["source_ref"] = "missing.png"
            with self.assertRaisesRegex(ValueError, "evidence source"):
                validate_generated_sample(missing, bundle, root)

    def test_question_prompt_forbids_fabricated_numbers_for_real_materials(self):
        from scripts.generate_finance_qa import QUESTION_SYSTEM_PROMPT

        self.assertIn("真实素材阶段", QUESTION_SYSTEM_PROMPT)
        self.assertIn("不得新增虚构数字", QUESTION_SYSTEM_PROMPT)
        self.assertIn("不得把真实公司与假设收入", QUESTION_SYSTEM_PROMPT)
        self.assertIn("禁止把整体指标改称特定产品或特定业务指标", QUESTION_SYSTEM_PROMPT)
        self.assertNotIn("verification", QUESTION_SYSTEM_PROMPT)
        self.assertNotIn("passed", QUESTION_SYSTEM_PROMPT)

    def test_prompt_library_removes_model_self_verification_contract(self):
        from scripts.generate_finance_qa import parse_prompt_library

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            prompt = root / "library.md"
            prompt.write_text(
                "# 金融多模态 Prompt Library\n\n"
                "## 2. 公共 System Prompt\n\n"
                "```text\n"
                "输出证据、指标和计算字段；程序会做校验。不要输出模型自检字段。\n"
                "```\n\n"
                "## 3. 模板\n\n"
                "### FM-HPA-01｜demo\n\n"
                "```text\npackage_type=page_qa\n{{document_text_or_ocr}}\n```\n",
                encoding="utf-8",
            )
            library = parse_prompt_library(prompt)

        self.assertIn("程序会做校验", library.system_prompt)
        self.assertNotIn("verification", library.system_prompt)
        self.assertNotIn("passed", library.system_prompt)

    def test_programmatic_grounding_rejects_incomplete_metric_refs(self):
        from scripts.generate_finance_qa import _validate_metric_and_evidence_grounding

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            bundle = self._bundle(root)
            candidate = {
                "evidence": [
                    {"text_quote": "营业收入100元", "page": 1},
                    {"text_quote": "营业成本70元", "page": 1},
                    {"text_quote": "净利润20元", "page": 1},
                ],
                "metric_refs": [
                    {
                        "name": "营业收入",
                        "page": 1,
                        "value": "100",
                        "unit": "元",
                        "evidence_index": 0,
                    },
                    {
                        "name": "营业成本",
                        "page": 1,
                        "value": "70",
                        "unit": "元",
                        "evidence_index": 1,
                    },
                    {
                        "name": "净利润",
                        "unit": "元",
                        "evidence_index": 2,
                    },
                ],
            }

            with self.assertRaisesRegex(ValueError, "missing metric field: page"):
                _validate_metric_and_evidence_grounding(candidate, bundle, root)

    def test_programmatic_calculation_rejects_mismatched_result(self):
        from scripts.generate_finance_qa import _validate_structured_calculations

        evidence = [
            {"text_quote": "营业收入100元"},
            {"text_quote": "营业成本70元"},
        ]
        calculations = [
            {
                "expression": "(100-70)/100*100",
                "claimed_result": 31,
                "unit": "%",
                "rounding_digits": 2,
                "evidence_indices": [0, 1],
            },
            {
                "expression": "100-70",
                "claimed_result": 30,
                "unit": "元",
                "rounding_digits": 2,
                "evidence_indices": [0, 1],
            },
        ]

        with self.assertRaisesRegex(ValueError, "calculation result mismatch"):
            _validate_structured_calculations(calculations, evidence)

    def test_programmatic_calculation_allows_ungrounded_expression_numbers(self):
        from scripts.generate_finance_qa import _validate_structured_calculations

        evidence = [{"text_quote": "revenue 100"}, {"text_quote": "cost 70"}]
        calculations = [
            {
                "expression": "999-1",
                "claimed_result": 998,
                "unit": "yuan",
                "rounding_digits": 0,
                "evidence_indices": [0],
            },
            {
                "expression": "100-70",
                "claimed_result": 30,
                "unit": "yuan",
                "rounding_digits": 0,
                "evidence_indices": [0, 1],
            },
        ]

        results = _validate_structured_calculations(calculations, evidence)

        self.assertEqual(results[0]["computed_result"], 998.0)

    def test_evidence_path_validation_allows_invalid_bbox_shape(self):
        from scripts.generate_finance_qa import _validate_evidence_paths

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            bundle = self._bundle(root, media_count=1)
            evidence = [
                {
                    "source_ref": bundle["media_paths"][0],
                    "page": 1,
                    "bbox": [87, 340, 927, 473],
                    "text_quote": "revenue 100",
                }
            ]

            _validate_evidence_paths(evidence, bundle, root)

    def test_evidence_path_validation_normalizes_short_page_names(self):
        from scripts.generate_finance_qa import _validate_evidence_paths

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            bundle = self._bundle(root, media_count=1)
            evidence = [
                {
                    "source_ref": Path(bundle["media_paths"][0]).name,
                    "page": 1,
                    "bbox": [0, 0, 1, 1],
                    "text_quote": "revenue 100",
                }
            ]

            _validate_evidence_paths(evidence, bundle, root)

            self.assertEqual(evidence[0]["source_ref"], bundle["media_paths"][0])

    def test_question_validation_normalizes_short_paths_in_media_and_alignment(self):
        from scripts.generate_finance_qa import validate_question_candidate

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            bundle = self._bundle(root, media_count=2)
            candidate = {
                "candidate_id": "cand-1",
                "bundle_id": bundle["bundle_id"],
                "generation_prompt_id": "FM-HPA-01",
                "task_type": bundle["package_type"],
                "question": "hard question",
                "media_paths": [
                    Path(bundle["media_paths"][0]).name,
                    Path(bundle["media_paths"][1]).stem,
                ],
                "evidence": [
                    {
                        "source_ref": Path(bundle["media_paths"][0]).name,
                        "page": 1,
                        "text_quote": "revenue 100",
                    },
                    {
                        "source_ref": Path(bundle["media_paths"][1]).stem,
                        "page": 2,
                        "text_quote": "cost 70",
                    },
                    {
                        "source_ref": Path(bundle["context_files"]["pdf_text"][0]).name,
                        "page": 1,
                        "text_quote": "profit 30",
                    },
                ],
                "metric_refs": [
                    {
                        "name": "revenue",
                        "page": 1,
                        "value": "100",
                        "unit": "yuan",
                        "evidence_index": 0,
                    },
                    {
                        "name": "cost",
                        "page": 2,
                        "value": "70",
                        "unit": "yuan",
                        "evidence_index": 1,
                    },
                    {
                        "name": "profit",
                        "page": 1,
                        "value": "30",
                        "unit": "yuan",
                        "evidence_index": 2,
                    },
                ],
                "chart_text_alignment": [
                    {
                        "visual_ref": Path(bundle["media_paths"][0]).name,
                        "text_ref": Path(bundle["context_files"]["pdf_text"][0]).name,
                        "relationship": "visual-text",
                    }
                ],
                "expected_steps": ["step 1", "step 2"],
                "formula_selection_reason": "reason",
                "hardness": {
                    "independent_evidence_count": 3,
                    "page_count": 2,
                    "modality_count": 2,
                    "calculation_step_count": 2,
                },
                "finance_checks": {
                    "entity": True,
                    "report_period": True,
                    "scope": True,
                    "currency_unit": True,
                    "rounding": True,
                },
            }

            validate_question_candidate(candidate, bundle, root)

            self.assertEqual(candidate["media_paths"], bundle["media_paths"])
            self.assertEqual(candidate["evidence"][0]["source_ref"], bundle["media_paths"][0])
            self.assertEqual(candidate["evidence"][1]["source_ref"], bundle["media_paths"][1])
            self.assertEqual(
                candidate["evidence"][2]["source_ref"],
                bundle["context_files"]["pdf_text"][0],
            )
            self.assertEqual(
                candidate["chart_text_alignment"][0]["visual_ref"],
                bundle["media_paths"][0],
            )
            self.assertEqual(
                candidate["chart_text_alignment"][0]["text_ref"],
                bundle["context_files"]["pdf_text"][0],
            )

    def test_grounding_allows_rewritten_evidence_quote(self):
        from scripts.generate_finance_qa import _validate_metric_and_evidence_grounding

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            bundle = self._bundle(root)
            candidate = {
                "evidence": [
                    {"text_quote": "rewritten page quote 999", "page": 1},
                    {"text_quote": "metric evidence 100", "page": 1},
                    {"text_quote": "other metric evidence 70", "page": 1},
                ],
                "metric_refs": [
                    {
                        "name": "revenue",
                        "page": 1,
                        "value": "100",
                        "unit": "yuan",
                        "evidence_index": 1,
                    },
                    {
                        "name": "cost",
                        "page": 1,
                        "value": "70",
                        "unit": "yuan",
                        "evidence_index": 2,
                    },
                    {
                        "name": "difference",
                        "page": 1,
                        "value": "30",
                        "unit": "yuan",
                        "evidence_index": 0,
                    },
                ],
            }
            candidate["evidence"][0]["text_quote"] = "rewritten page quote 30"

            _validate_metric_and_evidence_grounding(candidate, bundle, root)

    def test_answer_validation_ignores_model_self_verification_flags(self):
        from scripts.generate_finance_qa import validate_answer_sample

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            bundle = self._bundle(root, media_count=2)
            question = _two_stage_question(bundle, "FM-HTA-01")
            sample = _two_stage_answer(bundle, question, "FM-HTA-01")
            sample["metadata"]["verification"] = {
                "answerable": False,
                "evidence_sufficient": False,
                "citations_valid": False,
                "passed": False,
                "external_facts_used": True,
            }

            report = validate_answer_sample(sample, question, bundle, root)

        self.assertTrue(report["metrics_passed"])
        self.assertTrue(report["arithmetic_passed"])

    def test_answer_normalization_restores_cot_media_and_source_refs(self):
        from scripts.generate_finance_qa import normalize_answer_sample

        question = {
            "question": "固定问题",
            "media_paths": ["data/finance_qa/assets/demo/page.png"],
        }
        sample = {
            "question": "模型改写的问题",
            "media": ["wrong.png"],
            "cot": {"steps": ["读取证据", "计算结果"]},
            "metadata": {
                "evidence": [
                    {
                        "source_ref": "pdf_text:data/finance_qa/assets/demo/page.txt",
                    },
                    {
                        "source_ref": "pdf_text:missing.txt",
                    },
                ],
            },
        }

        normalized = normalize_answer_sample(
            sample,
            question,
            allowed_source_refs={
                "data/finance_qa/assets/demo/page.png",
                "data/finance_qa/assets/demo/page.txt",
            },
        )

        self.assertEqual(normalized["question"], "固定问题")
        self.assertEqual(
            normalized["media"],
            ["data/finance_qa/assets/demo/page.png"],
        )
        self.assertRegex(normalized["cot"], r"^<think>[\s\S]+</think>$")
        self.assertIn("读取证据", normalized["cot"])
        self.assertEqual(
            normalized["metadata"]["evidence"][0]["source_ref"],
            "data/finance_qa/assets/demo/page.txt",
        )
        self.assertEqual(
            normalized["metadata"]["evidence"][1]["source_ref"],
            "pdf_text:missing.txt",
        )

    def test_projects_multimodal_and_text_records_to_training_schema(self):
        from scripts.generate_finance_qa import project_training_record

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            bundle = self._bundle(root)
            sample = _accepted_sample(
                record_id="r1",
                source_id=bundle["bundle_id"],
                prompt_id="FM-TAB-01",
                media=bundle["media_paths"],
            )

            multi = project_training_record(sample, bundle)
            self.assertEqual(
                multi["messages"][0]["content"].count("<image>"),
                len(multi["images"]),
            )
            self.assertIn("答案：", multi["messages"][1]["content"])
            self.assertNotIn("OCR", multi["messages"][0]["content"])
            self.assertEqual(multi["task"], "table_qa")

            text_sample = _accepted_sample(
                record_id="r2",
                source_id="synthetic",
                prompt_id="SYN-TEXT-HARD",
                media=[],
            )
            text = project_training_record(
                text_sample,
                {**bundle, "package_type": "synthetic_text", "media_paths": []},
            )
            self.assertNotIn("images", text)
            self.assertNotIn("<image>", text["messages"][0]["content"])

    def test_process_and_merge_generate_two_records_and_resume_without_duplicates(self):
        from scripts.generate_finance_qa import (
            merge_parts,
            parse_prompt_library,
            process_shard,
        )

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            bundle = self._bundle(root)
            input_path = root / "data" / "finance_qa" / "all.jsonl"
            input_path.write_text(
                json.dumps(bundle, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
            library = parse_prompt_library(self._prompt_library(root))
            output = root / "output"
            processor = FakeProcessor()

            def generate_batch(inputs, seeds):
                results = []
                for index, prompt_input in enumerate(inputs):
                    prompt_id = (
                        "FM-MNR-01"
                        if "多步问题" in str(prompt_input["prompt"])
                        else "FM-TAB-01"
                    )
                    results.append(
                        json.dumps(
                            _staged_sample(
                                prompt_input,
                                seeds[index],
                                prompt_id,
                            ),
                            ensure_ascii=False,
                        )
                    )
                return results

            first = process_shard(
                input_path=input_path,
                project_root=root,
                output_dir=output,
                rank=0,
                world_size=1,
                library=library,
                processor=processor,
                generate_batch=generate_batch,
                batch_size=2,
                base_seed=42,
            )
            second = process_shard(
                input_path=input_path,
                project_root=root,
                output_dir=output,
                rank=0,
                world_size=1,
                library=library,
                processor=processor,
                generate_batch=generate_batch,
                batch_size=2,
                base_seed=42,
            )
            summary = merge_parts(output, world_size=1)

            self.assertEqual(first["accepted_multi"], 2)
            self.assertEqual(second["skipped"], 2)
            self.assertEqual(summary["accepted_multi"], 2)
            rows = [
                json.loads(line)
                for line in (
                    output / "finance_generated_multi.jsonl"
                ).read_text(encoding="utf-8").splitlines()
            ]
            self.assertEqual(len(rows), 2)
            self.assertEqual(len({row["record_id"] for row in rows}), 2)

    def test_process_shard_resumes_until_unique_accepted_target(self):
        from scripts.generate_finance_qa import (
            merge_parts,
            parse_prompt_library,
            process_shard,
        )

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            rows = []
            for index in range(2):
                bundle = self._bundle(root)
                bundle["bundle_id"] = f"table_qa:demo:{index}"
                rows.append(bundle)
            input_path = root / "data" / "finance_qa" / "all.jsonl"
            input_path.write_text(
                "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
                encoding="utf-8",
            )
            library = parse_prompt_library(self._prompt_library(root))
            output = root / "output"

            def generate_batch(inputs, seeds):
                results = []
                for prompt_input, seed in zip(inputs, seeds):
                    prompt_id = (
                        "FM-TAB-01"
                        if "source_id=" in str(prompt_input["prompt"])
                        else "FM-MNR-01"
                    )
                    results.append(
                        json.dumps(
                            _staged_sample(prompt_input, seed, prompt_id),
                            ensure_ascii=False,
                        )
                    )
                return results

            first = process_shard(
                input_path=input_path,
                project_root=root,
                output_dir=output,
                rank=0,
                world_size=1,
                library=library,
                processor=FakeProcessor(),
                generate_batch=generate_batch,
                batch_size=2,
                base_seed=42,
                target_accepted=1,
            )
            second = process_shard(
                input_path=input_path,
                project_root=root,
                output_dir=output,
                rank=0,
                world_size=1,
                library=library,
                processor=FakeProcessor(),
                generate_batch=generate_batch,
                batch_size=2,
                base_seed=42,
                target_accepted=3,
            )
            summary = merge_parts(output, world_size=1)

            self.assertEqual(first["accepted_multi"], 1)
            self.assertEqual(second["accepted_multi"], 2)
            self.assertEqual(
                summary["accepted_multi"] + summary["accepted_text"],
                3,
            )

    def test_process_shard_generates_before_input_iterator_is_exhausted(self):
        from scripts.generate_finance_qa import (
            parse_prompt_library,
            process_shard,
        )

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            rows = []
            for index in range(3):
                bundle = self._bundle(root)
                bundle["bundle_id"] = f"table_qa:stream:{index}"
                bundle["samples_requested"] = 1
                rows.append(bundle)
            exhausted = False
            observed_states = []

            def iter_rows(*args, **kwargs):
                nonlocal exhausted
                for offset, row in enumerate(rows):
                    yield offset, row
                exhausted = True

            def generate_batch(inputs, seeds):
                observed_states.append(exhausted)
                return [
                    json.dumps(
                        _staged_sample(
                            prompt_input,
                            seeds[index],
                            "FM-MNR-01",
                        ),
                        ensure_ascii=False,
                    )
                    for index, prompt_input in enumerate(inputs)
                ]

            with patch(
                "scripts.generate_finance_qa.iter_jsonl_shard",
                side_effect=iter_rows,
            ):
                counters = process_shard(
                    input_path=root / "unused.jsonl",
                    project_root=root,
                    output_dir=root / "output",
                    rank=0,
                    world_size=1,
                    library=parse_prompt_library(self._prompt_library(root)),
                    processor=FakeProcessor(),
                    generate_batch=generate_batch,
                    batch_size=1,
                    base_seed=42,
                    target_accepted=1,
                )

            self.assertTrue(observed_states)
            self.assertTrue(all(state is False for state in observed_states))
            self.assertEqual(counters["accepted_multi"], 1)

    def test_max_model_calls_caps_individual_requests_and_summary(self):
        from scripts.generate_finance_qa import (
            merge_parts,
            parse_prompt_library,
            process_shard,
        )

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            bundle = self._bundle(root)
            input_path = root / "data" / "finance_qa" / "all.jsonl"
            input_path.write_text(
                json.dumps(bundle, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
            batches = []

            def generate_batch(inputs, seeds):
                batches.append(len(inputs))
                return ["not json" for _ in inputs]

            output = root / "output"
            counters = process_shard(
                input_path=input_path,
                project_root=root,
                output_dir=output,
                rank=0,
                world_size=1,
                library=parse_prompt_library(self._prompt_library(root)),
                processor=FakeProcessor(),
                generate_batch=generate_batch,
                batch_size=4,
                base_seed=42,
                max_model_calls=5,
            )
            summary = merge_parts(output, world_size=1)

            self.assertEqual(batches, [2])
            self.assertEqual(counters["model_calls"], 2)
            self.assertEqual(counters["stop_reason"], "input_exhausted")
            self.assertEqual(summary["model_calls"], 2)
            self.assertEqual(summary["accepted_total"], 0)
            self.assertEqual(summary["stop_reason"], "input_exhausted")

    def test_max_model_calls_limits_second_batch_to_remaining_budget(self):
        from scripts.generate_finance_qa import (
            parse_prompt_library,
            process_shard,
        )

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            rows = []
            for index in range(3):
                bundle = self._bundle(root)
                bundle["bundle_id"] = f"table_qa:max-calls:{index}"
                rows.append(bundle)
            input_path = root / "data" / "finance_qa" / "all.jsonl"
            input_path.write_text(
                "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
                encoding="utf-8",
            )
            batches = []

            def generate_batch(inputs, seeds):
                batches.append(len(inputs))
                return ["not json" for _ in inputs]

            counters = process_shard(
                input_path=input_path,
                project_root=root,
                output_dir=root / "output",
                rank=0,
                world_size=1,
                library=parse_prompt_library(self._prompt_library(root)),
                processor=FakeProcessor(),
                generate_batch=generate_batch,
                batch_size=4,
                base_seed=42,
                max_model_calls=5,
            )

            self.assertEqual(batches, [4, 1])
            self.assertEqual(counters["model_calls"], 5)
            self.assertEqual(counters["stop_reason"], "max_model_calls")

    def test_max_model_calls_saves_fifth_question_without_unexecuted_answer_error(self):
        from scripts.generate_finance_qa import (
            parse_prompt_library,
            process_shard,
        )

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            rows = []
            for index in range(3):
                bundle = self._bundle(root)
                bundle["bundle_id"] = f"table_qa:fifth-question:{index}"
                rows.append(bundle)
            input_path = root / "data" / "finance_qa" / "all.jsonl"
            input_path.write_text(
                "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
                encoding="utf-8",
            )
            call_count = 0

            def generate_batch(inputs, seeds):
                nonlocal call_count
                results = []
                for prompt_input, seed in zip(inputs, seeds):
                    call_count += 1
                    if call_count < 5:
                        results.append("not json")
                    else:
                        results.append(
                            json.dumps(
                                _staged_sample(prompt_input, seed),
                                ensure_ascii=False,
                            )
                        )
                return results

            output = root / "output"
            counters = process_shard(
                input_path=input_path,
                project_root=root,
                output_dir=output,
                rank=0,
                world_size=1,
                library=parse_prompt_library(self._prompt_library(root)),
                processor=FakeProcessor(),
                generate_batch=generate_batch,
                batch_size=1,
                base_seed=42,
                max_model_calls=5,
            )

            questions = (output / ".parts" / "questions" / "rank_0000.jsonl").read_text(
                encoding="utf-8"
            ).splitlines()
            answers = output / ".parts" / "raw_answers" / "rank_0000.jsonl"
            errors = (output / ".parts" / "errors" / "rank_0000.jsonl").read_text(
                encoding="utf-8"
            ).splitlines()
            self.assertEqual(counters["model_calls"], 5)
            self.assertEqual(counters["stop_reason"], "max_model_calls")
            self.assertEqual(len(questions), 1)
            self.assertEqual(answers.read_text(encoding="utf-8"), "")
            self.assertEqual(len(errors), 4)

    def test_target_accepted_stops_before_max_model_calls(self):
        from scripts.generate_finance_qa import (
            parse_prompt_library,
            process_shard,
        )

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            bundle = self._bundle(root)
            input_path = root / "data" / "finance_qa" / "all.jsonl"
            input_path.write_text(
                json.dumps(bundle, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )

            def generate_batch(inputs, seeds):
                return [
                    json.dumps(
                        _staged_sample(prompt_input, seed),
                        ensure_ascii=False,
                    )
                    for prompt_input, seed in zip(inputs, seeds)
                ]

            counters = process_shard(
                input_path=input_path,
                project_root=root,
                output_dir=root / "output",
                rank=0,
                world_size=1,
                library=parse_prompt_library(self._prompt_library(root)),
                processor=FakeProcessor(),
                generate_batch=generate_batch,
                batch_size=2,
                base_seed=42,
                target_accepted=2,
                max_model_calls=5,
            )

            self.assertEqual(counters["accepted_multi"], 2)
            self.assertEqual(counters["model_calls"], 4)
            self.assertEqual(counters["stop_reason"], "target_accepted")

    def test_process_shard_writes_failed_raw_answer_attempts(self):
        from scripts.generate_finance_qa import (
            parse_prompt_library,
            process_shard,
        )

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            bundle = self._bundle(root)
            bundle["samples_requested"] = 1
            input_path = root / "data" / "finance_qa" / "all.jsonl"
            input_path.write_text(
                json.dumps(bundle, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
            answer_attempts = 0

            def generate_batch(inputs, seeds):
                nonlocal answer_attempts
                if inputs[0]["_stage"] == "question":
                    return [
                        json.dumps(
                            _staged_sample(inputs[0], seeds[0], "FM-MNR-01"),
                            ensure_ascii=False,
                        )
                    ]
                answer_attempts += 1
                return [f"not json attempt {answer_attempts}"]

            output = root / "output"
            counters = process_shard(
                input_path=input_path,
                project_root=root,
                output_dir=output,
                rank=0,
                world_size=1,
                library=parse_prompt_library(self._prompt_library(root)),
                processor=FakeProcessor(),
                generate_batch=generate_batch,
                batch_size=1,
                base_seed=42,
            )

            raw_answer_path = output / ".parts" / "raw_answers" / "rank_0000.jsonl"
            raw_answers = [
                json.loads(line)
                for line in raw_answer_path.read_text(encoding="utf-8").splitlines()
            ]
            self.assertEqual(answer_attempts, 2)
            self.assertEqual(counters["accepted_multi"], 0)
            self.assertEqual(counters["errors"], 1)
            self.assertEqual([row["attempt"] for row in raw_answers], [1, 2])
            self.assertIn("not json attempt 1", raw_answers[0]["raw_text"])

    def test_max_records_per_type_limits_dsw_smoke_selection(self):
        from scripts.generate_finance_qa import (
            parse_prompt_library,
            process_shard,
        )

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            rows = []
            for package_type in ("table_qa", "figure_qa"):
                for index in range(3):
                    bundle = self._bundle(root, media_count=1)
                    bundle["bundle_id"] = f"{package_type}:demo:{index}"
                    bundle["package_type"] = package_type
                    bundle["samples_requested"] = 1
                    rows.append(bundle)
            input_path = root / "data" / "finance_qa" / "all.jsonl"
            input_path.write_text(
                "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
                encoding="utf-8",
            )
            library = parse_prompt_library(self._prompt_library(root))

            def generate_batch(inputs, seeds):
                output = []
                for item, seed in zip(inputs, seeds):
                    if "图表困难问题" in item["prompt"]:
                        prompt_id = "FM-CHT-01"
                    elif "多步问题" in item["prompt"]:
                        prompt_id = "FM-MNR-01"
                    else:
                        prompt_id = "FM-TAB-01"
                    output.append(
                        json.dumps(
                            _staged_sample(item, seed, prompt_id),
                            ensure_ascii=False,
                        )
                    )
                return output

            counters = process_shard(
                input_path=input_path,
                project_root=root,
                output_dir=root / "output",
                rank=0,
                world_size=1,
                library=library,
                processor=FakeProcessor(),
                generate_batch=generate_batch,
                batch_size=2,
                base_seed=42,
                max_records_per_type=2,
            )

            self.assertEqual(counters["accepted_multi"], 4)

    def test_debug_smoke_skips_weak_cover_page_bundles(self):
        from scripts.generate_finance_qa import (
            _skip_nonfinancial_debug_bundle,
            _skip_weak_debug_bundle,
        )

        weak = self._bundle(Path(tempfile.mkdtemp()), media_count=1)
        weak["package_type"] = "page_qa"
        weak["page_numbers"] = [1]
        weak["context_files"]["tables"] = []
        weak["context_files"]["figures"] = []

        strong = dict(weak)
        strong["package_type"] = "table_qa"

        self.assertTrue(_skip_weak_debug_bundle(weak, debug_mode=True))
        self.assertFalse(_skip_weak_debug_bundle(strong, debug_mode=True))
        self.assertFalse(_skip_weak_debug_bundle(weak, debug_mode=False))
        weak["page_numbers"] = [2]
        self.assertTrue(
            _skip_nonfinancial_debug_bundle(
                weak,
                financial=False,
                debug_mode=True,
            )
        )
        self.assertFalse(
            _skip_nonfinancial_debug_bundle(
                weak,
                financial=True,
                debug_mode=True,
            )
        )
        self.assertFalse(
            _skip_nonfinancial_debug_bundle(
                weak,
                financial=False,
                debug_mode=False,
            )
        )

    def test_launchers_use_requested_models_and_compatible_parallelism(self):
        import inspect

        from scripts.generate_finance_qa import VLLMGenerator

        root = Path(__file__).resolve().parents[1]
        dsw = root / "scripts" / "dsw" / "run_finance_qa_generation.sh"
        dlc = root / "scripts" / "dlc" / "start_finance_qa_generation.sh"

        dsw_text = dsw.read_text(encoding="utf-8")
        self.assertIn("/mnt/nas/bihaoran/model/qwen30", dsw_text)
        self.assertIn("--tensor-parallel-size 1", dsw_text)
        self.assertIn("--max-records-per-type", dsw_text)
        self.assertIn('FINANCE_QA_MAX_MODEL_CALLS:-5', dsw_text)
        self.assertIn('--max-model-calls "$MAX_MODEL_CALLS"', dsw_text)
        self.assertIn('FINANCE_QA_TARGET_ACCEPTED:-2', dsw_text)
        self.assertIn(
            '--question-min-images "${FINANCE_QA_QUESTION_MIN_IMAGES:-6}"',
            dsw_text,
        )
        self.assertIn(
            '--question-max-images "${FINANCE_QA_QUESTION_MAX_IMAGES:-10}"',
            dsw_text,
        )
        self.assertIn(
            '--question-max-tokens "${FINANCE_QA_QUESTION_MAX_TOKENS:-9216}"',
            dsw_text,
        )
        self.assertIn(
            '--answer-max-tokens "${FINANCE_QA_ANSWER_MAX_TOKENS:-16384}"',
            dsw_text,
        )
        self.assertIn("WANDB_DISABLED=true", dsw_text)

        dlc_text = dlc.read_text(encoding="utf-8")
        self.assertIn("/mnt/nas/bihaoran/model/qwen235", dlc_text)
        self.assertIn("TENSOR_PARALLEL_SIZE=4", dlc_text)
        self.assertIn("WORKERS_PER_NODE=2", dlc_text)
        self.assertIn(
            "GLOBAL_WORLD_SIZE=$((NODE_WORLD_SIZE * WORKERS_PER_NODE))",
            dlc_text,
        )
        self.assertIn('device_groups=("0,1,2,3" "4,5,6,7")', dlc_text)
        self.assertIn('--rank "$global_rank"', dlc_text)
        self.assertIn('--world-size "$GLOBAL_WORLD_SIZE"', dlc_text)
        self.assertIn('--tensor-parallel-size "$TENSOR_PARALLEL_SIZE"', dlc_text)
        self.assertIn(
            '--question-temperature "${FINANCE_QA_QUESTION_TEMPERATURE:-0.9}"',
            dlc_text,
        )
        self.assertIn(
            '--answer-temperature "${FINANCE_QA_ANSWER_TEMPERATURE:-0.6}"',
            dlc_text,
        )
        self.assertIn('--top-p "${FINANCE_QA_TOP_P:-0.95}"', dlc_text)
        self.assertIn('--batch-size "${FINANCE_QA_BATCH_SIZE:-2}"', dlc_text)
        self.assertIn(
            '--question-min-images "${FINANCE_QA_QUESTION_MIN_IMAGES:-6}"',
            dlc_text,
        )
        self.assertIn(
            '--question-max-images "${FINANCE_QA_QUESTION_MAX_IMAGES:-10}"',
            dlc_text,
        )
        self.assertIn(
            '--question-max-tokens "${FINANCE_QA_QUESTION_MAX_TOKENS:-9216}"',
            dlc_text,
        )
        self.assertIn(
            '--answer-max-tokens "${FINANCE_QA_ANSWER_MAX_TOKENS:-16384}"',
            dlc_text,
        )
        self.assertNotIn("--max-model-calls", dlc_text)
        self.assertIn("WANDB_DISABLED=true", dlc_text)
        generator_source = inspect.getsource(VLLMGenerator)
        self.assertIn(
            'limit_mm_per_prompt={"image": max_images_per_prompt, "video": 0}',
            generator_source,
        )
        self.assertIn("StructuredOutputsParams", generator_source)

    def test_script_path_entrypoint_can_import_project_modules(self):
        root = Path(__file__).resolve().parents[1]
        result = subprocess.run(
            [sys.executable, "scripts/generate_finance_qa.py", "--help"],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("worker", result.stdout)

    def test_parse_generated_sample_accepts_qwen_wrapped_json(self):
        from scripts.generate_finance_qa import parse_generated_sample

        expected = {"record_id": "demo", "question": "问题"}
        outputs = [
            (
                "<think>先检查字段 {不属于最终答案}</think>\n"
                "```json\n"
                + json.dumps(expected, ensure_ascii=False)
                + "\n```"
            ),
            "以下是结果：\n" + json.dumps(expected, ensure_ascii=False),
            (
                "<think>分析过程</think>\n"
                + json.dumps(expected, ensure_ascii=False)
                + "\n生成完毕。"
            ),
        ]

        for output in outputs:
            with self.subTest(output=output):
                self.assertEqual(parse_generated_sample(output), expected)

    def test_parse_generated_sample_prefers_outer_final_json_after_thinking(self):
        from scripts.generate_finance_qa import parse_generated_sample

        expected = {
            "question": "根据三项指标计算毛利率。",
            "media_paths": ["data/finance_qa/assets/demo/page.png"],
            "evidence": [{"source_ref": "data/finance_qa/assets/demo/page.png"}],
            "expected_steps": ["计算收入", "计算毛利率"],
            "metric_refs": [{"name": "收入"}],
            "chart_text_alignment": [{"relationship": "图文对应"}],
            "formula_selection_reason": "需要使用毛利率公式。",
            "hardness": {
                "page_count": 2,
                "independent_evidence_count": 3,
                "modality_count": 2,
                "calculation_step_count": 2,
            },
            "finance_checks": {
                "entity": True,
                "report_period": True,
                "scope": True,
                "currency_unit": True,
                "rounding": True,
            },
        }
        output = (
            '<think>先列一个片段 {"hardness":{"page_count":2}}，'
            '再列一个片段 {"finance_checks":{"entity":true}}</think>\n\n'
            + json.dumps(expected, ensure_ascii=False)
        )

        self.assertEqual(parse_generated_sample(output), expected)

    def test_batch_generation_failure_isolates_records_instead_of_stopping_shard(self):
        from scripts.generate_finance_qa import (
            parse_prompt_library,
            process_shard,
        )

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            rows = []
            for index in range(2):
                bundle = self._bundle(root, media_count=1)
                bundle["bundle_id"] = f"table_qa:demo:{index}"
                bundle["samples_requested"] = 1
                rows.append(bundle)
            input_path = root / "data" / "finance_qa" / "all.jsonl"
            input_path.write_text(
                "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
                encoding="utf-8",
            )
            library = parse_prompt_library(self._prompt_library(root))

            def generate_batch(inputs, seeds):
                if len(inputs) > 1:
                    raise RuntimeError("batch failed")
                prompt_id = (
                    "FM-MNR-01"
                    if "多步问题" in inputs[0]["prompt"]
                    else "FM-TAB-01"
                )
                return [
                    json.dumps(
                        _staged_sample(inputs[0], seeds[0], prompt_id),
                        ensure_ascii=False,
                    )
                ]

            counters = process_shard(
                input_path=input_path,
                project_root=root,
                output_dir=root / "output",
                rank=0,
                world_size=1,
                library=library,
                processor=FakeProcessor(),
                generate_batch=generate_batch,
                batch_size=2,
                base_seed=42,
            )

            self.assertEqual(counters["accepted_multi"], 2)
            self.assertEqual(counters["errors"], 0)

if __name__ == "__main__":
    unittest.main()
