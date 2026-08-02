import json
import os
import re
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from PIL import Image


class FakeProcessor:
    def __init__(self):
        self.messages = []
        self.template_kwargs = []

    def apply_chat_template(self, messages, **kwargs):
        self.messages.append(messages)
        self.template_kwargs.append(kwargs)
        return json.dumps(messages, ensure_ascii=False, default=str)


def _bundle(root: Path, package_type: str = "table_qa", media_count: int = 2) -> dict:
    media = []
    for index in range(media_count):
        path = root / "data" / "finance_qa" / "assets" / f"{index}.png"
        path.parent.mkdir(parents=True, exist_ok=True)
        Image.new("RGB", (8, 8), color=(index * 30, 0, 0)).save(path)
        media.append(path.relative_to(root).as_posix())
    text = root / "data" / "finance_qa" / "assets" / "page.txt"
    text.write_text("营业收入100，营业成本70，净利润20，经营现金流15。", encoding="utf-8")
    long_root = (
        root
        / "data"
        / "finance_qa"
        / "assets"
        / "long_document_qa"
        / "demo"
    )
    long_root.mkdir(parents=True, exist_ok=True)
    page_index = []
    for page_number in (1, 2):
        image = long_root / "pages" / f"page_{page_number:04d}.png"
        page_text = long_root / "text" / f"page_{page_number:04d}.txt"
        ocr = long_root / "ocr" / f"page_{page_number:04d}.json"
        image.parent.mkdir(parents=True, exist_ok=True)
        page_text.parent.mkdir(parents=True, exist_ok=True)
        ocr.parent.mkdir(parents=True, exist_ok=True)
        Image.new("RGB", (8, 8), color=(0, page_number * 30, 0)).save(image)
        page_text.write_text(
            (
                "第1页：营业收入、净利润、经营现金流和利润率指标。"
                "营业收入100元，营业成本70元。"
                if page_number == 1
                else "第2页：营业收入、净利润、经营现金流和利润率指标。"
                "净利润20元，"
                "经营活动现金流量净额15元。"
            ),
            encoding="utf-8",
        )
        ocr.write_text('{"blocks":[]}', encoding="utf-8")
        page_index.append(
            {
                "page_number": page_number,
                "image": image.relative_to(root).as_posix(),
                "text": page_text.relative_to(root).as_posix(),
                "ocr": ocr.relative_to(root).as_posix(),
                "tables": [],
                "figures": [],
            }
        )
    (long_root / "bundle.json").write_text(
        json.dumps(
            {
                "bundle_id": "long_document_qa:demo",
                "package_type": "long_document_qa",
                "document_id": "demo",
                "page_numbers": [1, 2],
                "media_paths": [],
                "context_files": {},
                "page_region_map": {"page_index": page_index},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return {
        "bundle_id": f"{package_type}:demo:1",
        "dataset_stage": "generation_input",
        "package_type": package_type,
        "document_id": "demo",
        "source_metadata": {"title": "demo annual report"},
        "page_numbers": [1, 2] if package_type == "cross_page_qa" else [1],
        "media_paths": media,
        "context_files": {
            "pdf_text": [text.relative_to(root).as_posix()],
            "ocr": [],
            "tables": [],
            "figures": [],
        },
        "page_region_map": {
            "pages": [{"page_number": 1}],
            "tables": [{"review_required": False}],
        },
        "samples_requested": 2,
    }


def _question_candidate(bundle: dict, template_id: str = "FM-HTA-01") -> dict:
    return {
        "candidate_id": "cand-1",
        "bundle_id": bundle["bundle_id"],
        "generation_prompt_id": template_id,
        "question": "根据表格和页面披露，先计算毛利率，再比较净利率与经营现金流率，判断利润质量是否弱于盈利水平。",
        "task_type": bundle["package_type"],
        "media_paths": bundle["media_paths"],
        "evidence": [
            {
                "source_ref": bundle["media_paths"][0],
                "page": 1,
                "bbox": [0.1, 0.1, 0.2, 0.2],
                "text_quote": "营业收入100元",
            },
            {
                "source_ref": bundle["media_paths"][-2],
                "page": 1,
                "bbox": [0.2, 0.2, 0.3, 0.3],
                "text_quote": "营业成本70元",
            },
            {
                "source_ref": bundle["media_paths"][-1],
                "page": 2,
                "bbox": [0.3, 0.3, 0.4, 0.4],
                "text_quote": "净利润20元，经营活动现金流量净额15元",
            },
        ],
        "expected_steps": ["读取收入、成本和净利润", "计算毛利率和净利率", "比较现金流率"],
        "metric_refs": [
            {
                "name": "营业收入",
                "page": 1,
                "value": "100",
                "unit": "元",
                "evidence_index": 0,
            },
            {
                "name": "净利润",
                "page": 2,
                "value": "20",
                "unit": "元",
                "evidence_index": 2,
            },
            {
                "name": "经营活动现金流量净额",
                "page": 2,
                "value": "15",
                "unit": "元",
                "evidence_index": 2,
            },
        ],
        "chart_text_alignment": [
            {
                "visual_ref": bundle["media_paths"][0],
                "text_ref": bundle["context_files"]["pdf_text"][0],
                "relationship": "图表指标与文字口径相互校验",
            }
        ],
        "formula_selection_reason": "根据利润质量场景，需比较经营现金流与净利润并结合利润率。",
        "hardness": {
            "independent_evidence_count": 3,
            "table_cell_count": 3,
            "calculation_step_count": 2,
            "page_count": len(set(bundle["page_numbers"])),
            "modality_count": 2,
            "fact_count": 3,
        },
        "finance_checks": {
            "entity": True,
            "report_period": True,
            "scope": True,
            "currency_unit": True,
            "rounding": True,
        },
    }


def _answer_sample(bundle: dict, question: dict, template_id: str = "FM-HTA-01") -> dict:
    return {
        "record_id": "record-1",
        "source_dataset": "finance_reports",
        "source_id": bundle["bundle_id"],
        "modality": "multimodal",
        "question": question["question"],
        "answer": "利润质量弱于盈利水平。",
        "cot": "<think>\n读取收入100、营业成本70、净利润20和经营现金流15。毛利率=(100-70)/100=30%。净利率=20/100=20%。经营现金流率=15/100=15%，低于净利率20%。因此利润质量弱于盈利水平。\n</think>",
        "task_type": bundle["package_type"],
        "media": bundle["media_paths"],
        "is_complete": True,
        "missing_assets": [],
        "metadata": {
            "generation_prompt_id": template_id,
            "generation_status": "accepted",
            "evidence": question["evidence"],
            "solution_trace": {
                "retrieved_metrics": question["metric_refs"],
                "chart_text_alignment": question["chart_text_alignment"],
                "formula_selection_reason": question["formula_selection_reason"],
                "steps": [
                    {"step": 1, "description": "读取四个指标。"},
                    {"step": 2, "description": "计算毛利率、净利率和现金流率。"},
                    {"step": 3, "description": "比较现金流率和净利率。"},
                ],
                "calculations": [
                    {
                        "expression": "(100-70)/100*100",
                        "claimed_result": 30.0,
                        "unit": "%",
                        "rounding_digits": 2,
                        "evidence_indices": [0, 1],
                    },
                    {
                        "expression": "15/20*100",
                        "claimed_result": 75.0,
                        "unit": "%",
                        "rounding_digits": 2,
                        "evidence_indices": [2],
                    }
                ],
                "unit_and_rounding": "统一换算为百分比并保留两位小数。",
                "evidence_conclusion": "经营现金流对净利润的覆盖率低于100%。",
            },
            "verification": {
                "answerable": True,
                "evidence_sufficient": True,
                "external_facts_used": False,
                "citations_valid": True,
            },
        },
    }


class FinanceQaTwoStageTests(unittest.TestCase):
    def test_question_prompt_uses_stage_specific_system_and_disables_native_thinking(self):
        from scripts.generate_finance_qa import (
            PromptLibrary,
            PromptTemplate,
            build_prompt_input,
        )

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            bundle = _bundle(root)
            processor = FakeProcessor()
            library = PromptLibrary(
                system_prompt="OLD_FULL_SAMPLE_SYSTEM",
                templates={},
                few_shots={},
            )
            template = PromptTemplate(
                "FM-HTA-01",
                "HTA",
                "hard table",
                "Generate a question candidate from {{document_text_or_ocr}}",
            )

            build_prompt_input(
                bundle=bundle,
                template=template,
                library=library,
                processor=processor,
                project_root=root,
                generation_seed=7,
            )

            system = processor.messages[-1][0]["content"]
            self.assertNotIn("OLD_FULL_SAMPLE_SYSTEM", system)
            self.assertIn("question", system)
            self.assertIn("metric_refs", system)
            self.assertIn("<think>", system)
            self.assertIn("只输出单个 JSON", system)
            self.assertIn("不得使用目录、封面或报告期释义凑页数", system)
            self.assertIn("不得并列执行两次互不依赖的一步运算", system)
            self.assertIn("不得仅凭负经营现金流断言利润不真实", system)
            self.assertFalse(processor.template_kwargs[-1]["enable_thinking"])

    def test_question_images_are_resized_before_vllm_input(self):
        from scripts.generate_finance_qa import (
            QUESTION_MODEL_IMAGE_MAX_PIXELS,
            PromptLibrary,
            PromptTemplate,
            build_prompt_input,
        )

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            bundle = _bundle(root)
            for relative in bundle["media_paths"]:
                Image.new("RGB", (1860, 2630)).save(root / relative)

            prompt_input = build_prompt_input(
                bundle=bundle,
                template=PromptTemplate(
                    "FM-HTA-01",
                    "HTA",
                    "hard table",
                    "Generate a question candidate from {{document_text_or_ocr}}",
                ),
                library=PromptLibrary("", {}, {}),
                processor=FakeProcessor(),
                project_root=root,
                generation_seed=7,
            )

            model_images = prompt_input["multi_modal_data"]["image"]
            self.assertTrue(model_images)
            self.assertTrue(
                all(
                    image.width * image.height <= QUESTION_MODEL_IMAGE_MAX_PIXELS
                    for image in model_images
                )
            )
            with Image.open(root / bundle["media_paths"][0]) as source:
                self.assertEqual(source.size, (1860, 2630))

    def test_script_injects_question_control_fields(self):
        from scripts.generate_finance_qa import normalize_question_candidate

        bundle = {
            "bundle_id": "table_qa:demo:1",
            "package_type": "table_qa",
            "media_paths": ["data/finance_qa/assets/page1.png"],
        }
        candidate = {
            "generation_prompt_id": "FM-HTA-09",
            "bundle_id": "wrong",
            "candidate_id": "",
            "task_type": "wrong",
            "question": "问题",
        }

        normalized = normalize_question_candidate(
            candidate,
            bundle=bundle,
            generation_prompt_id="FM-HTA-01",
            candidate_index=2,
        )

        self.assertEqual(normalized["candidate_id"], "table_qa:demo:1:FM-HTA-01:2")
        self.assertEqual(normalized["bundle_id"], bundle["bundle_id"])
        self.assertEqual(normalized["generation_prompt_id"], "FM-HTA-01")
        self.assertEqual(normalized["task_type"], "table_qa")

    def test_question_normalization_keeps_evidence_images_with_question(self):
        from scripts.generate_finance_qa import normalize_question_candidate

        bundle = {
            "bundle_id": "page_qa:demo:1",
            "package_type": "page_qa",
            "media_paths": [
                "data/finance_qa/assets/page1.png",
                "data/finance_qa/assets/page4.png",
                "data/finance_qa/assets/page5.png",
            ],
        }
        candidate = {
            "media_paths": ["data/finance_qa/assets/page1.png"],
            "evidence": [
                {
                    "source_ref": "data/finance_qa/assets/page4.png",
                    "page": 4,
                    "media_index": 0,
                },
                {
                    "source_ref": "data/finance_qa/assets/page5.png",
                    "page": 5,
                },
            ],
            "chart_text_alignment": [
                {
                    "visual_ref": "data/finance_qa/assets/page5.png",
                    "text_ref": "data/finance_qa/assets/page5.txt",
                }
            ],
        }

        normalized = normalize_question_candidate(
            candidate,
            bundle=bundle,
            generation_prompt_id="FM-HPA-01",
            candidate_index=0,
        )

        self.assertEqual(
            normalized["media_paths"],
            [
                "data/finance_qa/assets/page1.png",
                "data/finance_qa/assets/page4.png",
                "data/finance_qa/assets/page5.png",
            ],
        )
        self.assertEqual(normalized["evidence"][0]["media_index"], 1)
        self.assertEqual(normalized["evidence"][1]["media_index"], 2)

    def test_question_normalization_infers_evidence_page_from_source_path(self):
        from scripts.generate_finance_qa import normalize_question_candidate

        page8 = "data/finance_qa/assets/long_document_qa/demo/pages/page_0008.png"
        page25 = "data/finance_qa/assets/long_document_qa/demo/pages/page_0025.png"
        bundle = {
            "bundle_id": "page_qa:demo:page_0003",
            "package_type": "page_qa",
            "media_paths": [page8, page25],
        }
        candidate = {
            "media_paths": [page8, page25],
            "evidence": [
                {"source_ref": page8, "text_quote": "指标一"},
                {"source_ref": page25, "page": 999, "text_quote": "指标二"},
            ],
        }

        normalized = normalize_question_candidate(
            candidate,
            bundle=bundle,
            generation_prompt_id="FM-HPA-01",
            candidate_index=0,
        )

        self.assertEqual(
            [item["page"] for item in normalized["evidence"]],
            [8, 25],
        )
        self.assertEqual(
            [item["media_index"] for item in normalized["evidence"]],
            [0, 1],
        )

    def test_answer_prompt_disables_native_thinking_for_json_output(self):
        from scripts.generate_finance_qa import PromptLibrary, build_answer_input

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            bundle = _bundle(root)
            candidate = _question_candidate(bundle)
            processor = FakeProcessor()

            build_answer_input(
                bundle=bundle,
                question_candidate=candidate,
                library=PromptLibrary("answer system", {}, {}),
                processor=processor,
                project_root=root,
                generation_seed=9,
            )

            self.assertFalse(processor.template_kwargs[-1]["enable_thinking"])
            prompt_text = processor.messages[-1][1]["content"][-1]["text"]
            self.assertIn("JSON 外不得输出思考过程", prompt_text)

    def test_answer_normalization_injects_question_prompt_id(self):
        from scripts.generate_finance_qa import normalize_answer_sample

        question = {
            "question": "固定问题",
            "media_paths": ["data/finance_qa/assets/page.png"],
            "generation_prompt_id": "FM-HPA-02",
            "evidence": [{"source_ref": "data/finance_qa/assets/page.png"}],
        }
        sample = {
            "question": "固定问题",
            "media": [],
            "cot": "计算过程",
            "metadata": {"solution_trace": {}},
        }

        normalized = normalize_answer_sample(sample, question, set())

        self.assertEqual(
            normalized["metadata"]["generation_prompt_id"],
            "FM-HPA-02",
        )
        self.assertEqual(normalized["metadata"]["generation_status"], "accepted")
        self.assertEqual(normalized["metadata"]["evidence"], question["evidence"])

    def test_context_reader_caps_each_file_for_model_budget(self):
        from scripts.generate_finance_qa import _read_context

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            context_files = []
            for index in range(5):
                path = root / f"context_{index}.txt"
                path.write_text("甲" * 20000, encoding="utf-8")
                context_files.append(path.relative_to(root).as_posix())
            bundle = {"context_files": {"pdf_text": context_files}}

            context = _read_context(bundle, root)

            self.assertNotIn("甲" * 10001, context)
            self.assertLessEqual(context.count("甲"), 40000)

    def test_failed_question_keeps_raw_model_output(self):
        from scripts.generate_finance_qa import (
            GeneratedText,
            PromptLibrary,
            PromptTemplate,
            process_shard,
        )

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            bundle = _bundle(root)
            bundle["samples_requested"] = 1
            input_path = root / "all.jsonl"
            input_path.write_text(
                json.dumps(bundle, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
            library = PromptLibrary(
                system_prompt="old",
                templates={
                    "FM-HTA-01": PromptTemplate(
                        "FM-HTA-01",
                        "HTA",
                        "hard table",
                        "question {{document_text_or_ocr}}",
                    )
                },
                few_shots={},
            )

            process_shard(
                input_path=input_path,
                project_root=root,
                output_dir=root / "output",
                rank=0,
                world_size=1,
                library=library,
                processor=FakeProcessor(),
                generate_batch=lambda inputs, seeds, temperatures=None: [
                    GeneratedText(
                        "MODEL_OUTPUT_WITHOUT_JSON",
                        finish_reason="length",
                    )
                    for _ in inputs
                ],
                batch_size=1,
                base_seed=42,
                max_records=1,
            )

            error_path = (
                root
                / "output"
                / ".parts"
                / "errors"
                / "rank_0000.jsonl"
            )
            error = json.loads(error_path.read_text(encoding="utf-8").splitlines()[0])
            self.assertEqual(
                error["raw_question_text"],
                "MODEL_OUTPUT_WITHOUT_JSON",
            )
            self.assertEqual(error["question_finish_reason"], "length")

    def test_synthetic_question_uses_question_stage_and_text_validation(self):
        from scripts.generate_finance_qa import (
            PromptLibrary,
            SYNTHETIC_QUESTION_SYSTEM_PROMPT,
            build_synthetic_text_input,
            normalize_question_candidate,
            validate_question_candidate,
        )

        bundle = {
            "bundle_id": "page_qa:demo:cover",
            "package_type": "page_qa",
            "media_paths": [],
            "context_files": {},
            "page_region_map": {},
        }
        processor = FakeProcessor()
        prompt_input = build_synthetic_text_input(
            bundle=bundle,
            library=PromptLibrary("OLD_FULL_SAMPLE_SYSTEM", {}, {}),
            processor=processor,
            generation_seed=7,
        )
        candidate = normalize_question_candidate(
            {
                "question": "某虚构公司收入100、成本60、税费10，先计算毛利率，再计算税费后的利润率。",
                "media_paths": [],
                "evidence": [
                    {"source_ref": f"inline:{bundle['bundle_id']}", "text_quote": "收入100"},
                    {"source_ref": f"inline:{bundle['bundle_id']}", "text_quote": "成本60"},
                    {"source_ref": f"inline:{bundle['bundle_id']}", "text_quote": "税费10"},
                ],
                "expected_steps": ["计算毛利率", "计算税费后的利润率"],
                "metric_refs": [
                    {
                        "name": "收入",
                        "page": None,
                        "value": "100",
                        "unit": "元",
                        "evidence_index": 0,
                    },
                    {
                        "name": "成本",
                        "page": None,
                        "value": "60",
                        "unit": "元",
                        "evidence_index": 1,
                    },
                    {
                        "name": "税费",
                        "page": None,
                        "value": "10",
                        "unit": "元",
                        "evidence_index": 2,
                    },
                ],
                "chart_text_alignment": [],
                "formula_selection_reason": "题目要求计算利润率。",
                "hardness": {
                    "page_count": 0,
                    "independent_evidence_count": 3,
                    "modality_count": 1,
                    "calculation_step_count": 2,
                },
                "finance_checks": {
                    "entity": True,
                    "report_period": True,
                    "scope": True,
                    "currency_unit": True,
                    "rounding": True,
                },
            },
            bundle=prompt_input["_resolved_bundle"],
            generation_prompt_id="SYN-TEXT-HARD",
            candidate_index=0,
        )

        self.assertEqual(prompt_input["_stage"], "question")
        self.assertNotIn(
            "OLD_FULL_SAMPLE_SYSTEM",
            processor.messages[-1][0]["content"],
        )
        self.assertIn('"evidence": [{"source_ref": "inline:', SYNTHETIC_QUESTION_SYSTEM_PROMPT)
        self.assertIn('"metric_refs": [{"name":', SYNTHETIC_QUESTION_SYSTEM_PROMPT)
        self.assertIn('"hardness": {"page_count": 0', SYNTHETIC_QUESTION_SYSTEM_PROMPT)
        self.assertIn("不要输出思考过程", SYNTHETIC_QUESTION_SYSTEM_PROMPT)
        self.assertFalse(processor.template_kwargs[-1]["enable_thinking"])
        validate_question_candidate(
            candidate,
            prompt_input["_resolved_bundle"],
            Path("."),
        )

    def test_core_normalizes_pixel_and_slightly_overflowing_evidence_bboxes(self):
        from scripts.generate_finance_qa import _normalize_evidence_bboxes

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            image_path = root / "page.png"
            Image.new("RGB", (1000, 2000)).save(image_path)
            evidence = [
                {
                    "source_ref": "page.png",
                    "bbox": [100, 400, 900, 600],
                },
                {
                    "source_ref": "page.png",
                    "bbox": [0.359, 0.99, 0.444, 1.018],
                },
            ]

            _normalize_evidence_bboxes(evidence, root)

            self.assertEqual(evidence[0]["bbox"], [0.1, 0.2, 0.9, 0.3])
            self.assertEqual(evidence[1]["bbox"], [0.359, 0.99, 0.444, 1.0])

    def test_local_entry_runs_two_stages_and_writes_merged_outputs(self):
        from local_finance_qa.generate_modelscope import (
            build_parser,
            run_local,
        )

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            bundle = _bundle(root)
            bundle["samples_requested"] = 1
            bundle["page_numbers"] = [1, 2]
            input_path = root / "data" / "finance_qa" / "all.jsonl"
            input_path.parent.mkdir(parents=True, exist_ok=True)
            input_path.write_text(
                json.dumps(bundle, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
            output_dir = root / "output"
            calls = []

            def create(**kwargs):
                prompt = json.dumps(kwargs["messages"], ensure_ascii=False)
                calls.append(prompt)
                match = re.search(
                    r"generation_prompt_id=(FM-[A-Z]+-\d+)",
                    prompt,
                )
                prompt_id = match.group(1) if match else "FM-HTA-01"
                question = _question_candidate(bundle, prompt_id)
                if "STAGE=QUESTION_ONLY" in prompt:
                    payload = question
                else:
                    payload = _answer_sample(bundle, question, prompt_id)
                    payload["record_id"] = "local-record-1"
                return iter(
                    [
                        SimpleNamespace(
                            choices=[
                                SimpleNamespace(
                                    delta=SimpleNamespace(
                                        content=json.dumps(
                                            payload,
                                            ensure_ascii=False,
                                        )
                                    )
                                )
                            ]
                        )
                    ]
                )

            client = SimpleNamespace(
                chat=SimpleNamespace(
                    completions=SimpleNamespace(create=create)
                )
            )
            args = build_parser().parse_args(
                [
                    "--root",
                    str(root),
                    "--input",
                    str(input_path),
                    "--prompts",
                    str(
                        Path(__file__).resolve().parents[1]
                        / "data"
                        / "finance_qa"
                        / "prompts"
                        / "financial_multimodal_prompt_library.md"
                    ),
                    "--output-dir",
                    str(output_dir),
                    "--target-accepted",
                    "1",
                ]
            )

            with patch.dict(
                os.environ,
                {"MODELSCOPE_SDK_TOKEN": "secret-token"},
                clear=True,
            ):
                result = run_local(args, client=client)

            self.assertEqual(
                result["summary"]["accepted_multi"],
                1,
                (output_dir / "errors.jsonl").read_text(encoding="utf-8"),
            )
            self.assertEqual(len(calls), 2)
            self.assertIn("STAGE=QUESTION_ONLY", calls[0])
            self.assertIn("STAGE=ANSWER_ONLY", calls[1])
            self.assertTrue(
                (output_dir / "raw_question_generations.jsonl").is_file()
            )
            self.assertTrue(
                (output_dir / "raw_answer_generations.jsonl").is_file()
            )
            self.assertTrue(
                (output_dir / "finance_generated_multi.jsonl").is_file()
            )

    def test_single_page_bundle_is_expanded_with_same_document_page(self):
        from scripts.generate_finance_qa import (
            PromptTemplate,
            expand_bundle_for_hard_chain,
        )

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            bundle = _bundle(root, package_type="table_qa")
            expanded = expand_bundle_for_hard_chain(
                bundle,
                root,
                PromptTemplate("FM-HTA-01", "HTA", "hard table", "利润质量"),
            )

            self.assertEqual(expanded["page_numbers"], [1, 2])
            self.assertLessEqual(len(expanded["media_paths"]), 5)
            self.assertEqual(len(expanded["context_files"]["pdf_text"]), 2)
            self.assertEqual(len(expanded["context_files"]["ocr"]), 2)
            self.assertEqual(
                expanded["page_region_map"]["retrieval_expansion"]["added_pages"],
                [2],
            )

    def test_profit_cash_template_retrieves_distant_cash_flow_explanation(self):
        from scripts.generate_finance_qa import (
            PromptTemplate,
            expand_bundle_for_hard_chain,
        )

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            bundle = _bundle(root, package_type="page_qa", media_count=1)
            long_root = (
                root
                / "data"
                / "finance_qa"
                / "assets"
                / "long_document_qa"
                / "demo"
            )
            long_bundle_path = long_root / "bundle.json"
            long_bundle = json.loads(long_bundle_path.read_text(encoding="utf-8"))
            page_index = long_bundle["page_region_map"]["page_index"]
            generic = "财务 年度报告 收入 利润 资产 负债 股东 资本 风险 银行 证券 投资 审计 同比 人民币"
            page_text = {
                3: generic,
                4: generic,
                5: generic,
                8: "归属于上市公司股东的净利润，经营活动产生的现金流量净额。",
                25: "经营活动产生的现金流量净额下降，主要系销售收现减少、采购付现增加所致。",
                30: "应收账款增长及其变动原因。",
                31: "存货增长及其变动原因。",
                32: "销售商品收到的现金减少。",
                33: "购买商品支付的现金增加。",
                34: "净利润与经营现金流量勾稽。",
                35: "经营活动现金流量与净利润现金保障关系。",
            }
            for page_number, text in page_text.items():
                image = long_root / "pages" / f"page_{page_number:04d}.png"
                text_path = long_root / "text" / f"page_{page_number:04d}.txt"
                ocr = long_root / "ocr" / f"page_{page_number:04d}.json"
                image.parent.mkdir(parents=True, exist_ok=True)
                text_path.parent.mkdir(parents=True, exist_ok=True)
                ocr.parent.mkdir(parents=True, exist_ok=True)
                Image.new("RGB", (8, 8)).save(image)
                text_path.write_text(text, encoding="utf-8")
                ocr.write_text('{"blocks":[]}', encoding="utf-8")
                page_index.append(
                    {
                        "page_number": page_number,
                        "image": image.relative_to(root).as_posix(),
                        "text": text_path.relative_to(root).as_posix(),
                        "ocr": ocr.relative_to(root).as_posix(),
                        "tables": [],
                        "figures": [],
                    }
                )
            long_bundle_path.write_text(
                json.dumps(long_bundle, ensure_ascii=False),
                encoding="utf-8",
            )

            expanded = expand_bundle_for_hard_chain(
                bundle,
                root,
                PromptTemplate(
                    "FM-HPA-02",
                    "HPA",
                    "page profit cash quality",
                    "reasoning_type=profit_cash_quality",
                ),
                question_min_images=10,
                question_max_images=10,
            )

            self.assertIn(8, expanded["page_numbers"])
            self.assertIn(25, expanded["page_numbers"])
            self.assertEqual(len(expanded["media_paths"]), 10)

    def test_answer_stage_only_sees_question_selected_pages(self):
        from scripts.generate_finance_qa import PromptLibrary, build_answer_input

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            bundle = _bundle(root, package_type="page_qa", media_count=2)
            candidate = _question_candidate(bundle)
            candidate["media_paths"] = [bundle["media_paths"][0]]
            candidate["evidence"] = [candidate["evidence"][0]]
            processor = FakeProcessor()

            build_answer_input(
                bundle=bundle,
                question_candidate=candidate,
                library=PromptLibrary("answer system", {}, {}),
                processor=processor,
                project_root=root,
                generation_seed=9,
            )

            content = processor.messages[-1][1]["content"]
            self.assertEqual(
                sum(item.get("type") == "image" for item in content),
                1,
            )
            prompt_text = content[-1]["text"]
            self.assertIn("第1页", prompt_text)
            self.assertNotIn("第2页", prompt_text)

    def test_hard_templates_are_50_and_selected_by_package_type(self):
        from scripts.generate_finance_qa import (
            HARD_TEMPLATE_PREFIXES,
            parse_prompt_library,
            select_templates,
        )

        prompt_path = Path("data/finance_qa/prompts/financial_multimodal_prompt_library.md")
        library = parse_prompt_library(prompt_path)
        hard_ids = sorted(
            prompt_id for prompt_id in library.templates if prompt_id.startswith("FM-H")
        )

        self.assertEqual(len(hard_ids), 50)
        for prefix in ("HPA", "HTA", "HFI", "HCP", "HLD"):
            self.assertEqual(
                [item for item in hard_ids if item.startswith(f"FM-{prefix}-")],
                [f"FM-{prefix}-{index:02d}" for index in range(1, 11)],
            )
        self.assertEqual(HARD_TEMPLATE_PREFIXES["table_qa"], ("HTA",))
        selected = select_templates(
            library.templates,
            package_type="table_qa",
            count=2,
            usage={},
        )
        self.assertTrue(all(item.prompt_id.startswith("FM-HTA-") for item in selected))

    def test_question_schema_declares_full_cross_page_reasoning_chain(self):
        from scripts.data.prepare_finance_qa_inputs import (
            QUESTION_CANDIDATE_SCHEMA,
            SAMPLE_SCHEMA,
        )

        required = set(QUESTION_CANDIDATE_SCHEMA["required"])
        self.assertTrue(
            {
                "metric_refs",
                "chart_text_alignment",
                "formula_selection_reason",
            }.issubset(required)
        )
        properties = QUESTION_CANDIDATE_SCHEMA["properties"]
        self.assertEqual(properties["question"]["maxLength"], 1200)
        self.assertEqual(properties["evidence"]["minItems"], 3)
        self.assertEqual(properties["evidence"]["maxItems"], 8)
        self.assertEqual(
            properties["evidence"]["items"]["properties"]["text_quote"]["maxLength"],
            600,
        )
        evidence_items = properties["evidence"]["items"]
        self.assertIn("page", evidence_items["properties"])
        self.assertTrue(
            {"source_ref", "page", "text_quote"}.issubset(
                set(evidence_items["required"])
            )
        )
        self.assertEqual(properties["metric_refs"]["minItems"], 3)
        self.assertEqual(properties["metric_refs"]["maxItems"], 8)
        metric_items = properties["metric_refs"]["items"]
        self.assertTrue(
            {"name", "page", "value", "unit", "evidence_index"}.issubset(
                set(metric_items["required"])
            )
        )
        self.assertEqual(properties["expected_steps"]["maxItems"], 6)
        hardness = properties["hardness"]
        self.assertEqual(hardness["required"], [
            "independent_evidence_count",
            "page_count",
            "modality_count",
            "calculation_step_count",
        ])
        solution_trace = (
            SAMPLE_SCHEMA["properties"]["metadata"]["properties"]["solution_trace"]
        )
        self.assertEqual(solution_trace["properties"]["calculations"]["minItems"], 2)
        calculation_items = solution_trace["properties"]["calculations"]["items"]
        self.assertTrue(
            {
                "expression",
                "claimed_result",
                "unit",
                "rounding_digits",
                "evidence_indices",
            }.issubset(set(calculation_items["required"]))
        )
        self.assertIn("formula_selection_reason", solution_trace["required"])

    def test_question_and_answer_validators_enforce_hard_two_stage_contract(self):
        from scripts.generate_finance_qa import (
            validate_answer_sample,
            validate_question_candidate,
        )

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source_bundle = _bundle(root)
            from scripts.generate_finance_qa import (
                PromptTemplate,
                expand_bundle_for_hard_chain,
            )
            bundle = expand_bundle_for_hard_chain(
                source_bundle,
                root,
                PromptTemplate("FM-HTA-01", "HTA", "hard table", "利润质量"),
            )
            question = _question_candidate(bundle)
            validate_question_candidate(question, bundle, root)

            page_text_alignment = json.loads(json.dumps(question))
            page_text_alignment["chart_text_alignment"][0]["text_ref"] = (
                page_text_alignment["media_paths"][-1]
            )
            validate_question_candidate(page_text_alignment, bundle, root)

            leaked = dict(question)
            leaked["answer"] = "30%"
            with self.assertRaisesRegex(ValueError, "must not contain answer"):
                validate_question_candidate(leaked, bundle, root)

            simple = json.loads(json.dumps(question))
            simple["hardness"]["calculation_step_count"] = 1
            simple["hardness"]["table_cell_count"] = 1
            simple["hardness"]["modality_count"] = 1
            simple["hardness"]["fact_count"] = 1
            with self.assertRaisesRegex(ValueError, "not a hard question"):
                validate_question_candidate(simple, bundle, root)

            missing_chain = json.loads(json.dumps(question))
            missing_chain.pop("formula_selection_reason")
            with self.assertRaisesRegex(ValueError, "formula_selection_reason"):
                validate_question_candidate(missing_chain, bundle, root)

            same_page_metrics = json.loads(json.dumps(question))
            for item in same_page_metrics["metric_refs"]:
                item["page"] = 1
            with self.assertRaisesRegex(
                ValueError,
                "metric page does not match evidence",
            ):
                validate_question_candidate(same_page_metrics, bundle, root)

            weak_cross_page = json.loads(json.dumps(question))
            weak_cross_page["evidence"][0]["text_quote"] = "目录"
            weak_cross_page["evidence"][1]["text_quote"] = "报告期、本年度 指 2024年度"
            weak_cross_page["metric_refs"][0]["value"] = "目录"
            validate_question_candidate(weak_cross_page, bundle, root)

            missing_metric_evidence = json.loads(json.dumps(question))
            missing_metric_evidence["metric_refs"][0]["value"] = "101.00"
            with self.assertRaisesRegex(ValueError, "metric value lacks evidence"):
                validate_question_candidate(
                    missing_metric_evidence,
                    bundle,
                    root,
                )

            missing_metric_field = json.loads(json.dumps(question))
            missing_metric_field["metric_refs"][0].pop("value")
            with self.assertRaisesRegex(ValueError, "missing metric field: value"):
                validate_question_candidate(
                    missing_metric_field,
                    bundle,
                    root,
                )

            fabricated_quote = json.loads(json.dumps(question))
            fabricated_quote["evidence"][2]["text_quote"] = (
                "rewritten quote with metric values 20 and 15 plus ungrounded 110.40%"
            )
            validate_question_candidate(
                fabricated_quote,
                bundle,
                root,
            )

            single_page = json.loads(json.dumps(question))
            single_page["hardness"]["page_count"] = 1
            with self.assertRaisesRegex(ValueError, "not a hard question"):
                validate_question_candidate(single_page, bundle, root)

            claimed_cross_page = json.loads(json.dumps(question))
            claimed_cross_page["media_paths"] = source_bundle["media_paths"]
            claimed_cross_page["evidence"] = [
                {
                    "source_ref": source_bundle["media_paths"][index % 2],
                    "page": 1,
                    "bbox": [0.1, 0.1, 0.2, 0.2],
                }
                for index in range(3)
            ]
            claimed_cross_page["chart_text_alignment"][0]["visual_ref"] = (
                source_bundle["media_paths"][0]
            )
            claimed_cross_page["chart_text_alignment"][0]["text_ref"] = (
                source_bundle["context_files"]["pdf_text"][0]
            )
            with self.assertRaisesRegex(ValueError, "fewer than two pages"):
                validate_question_candidate(
                    claimed_cross_page,
                    source_bundle,
                    root,
                )

            missing_selected_media = json.loads(json.dumps(question))
            omitted_media = missing_selected_media["media_paths"][-1]
            missing_selected_media["media_paths"] = missing_selected_media[
                "media_paths"
            ][:-1]
            missing_selected_media["chart_text_alignment"][0]["visual_ref"] = (
                omitted_media
            )
            with self.assertRaisesRegex(ValueError, "not kept in question media"):
                validate_question_candidate(
                    missing_selected_media,
                    bundle,
                    root,
                )

            answer = _answer_sample(bundle, question)
            report = validate_answer_sample(answer, question, bundle, root)
            self.assertTrue(report["metrics_passed"])
            self.assertTrue(report["evidence_grounding_passed"])
            self.assertTrue(report["arithmetic_passed"])
            self.assertEqual(
                answer["metadata"]["programmatic_validation"],
                report,
            )

            wrong_arithmetic = _answer_sample(bundle, question)
            wrong_arithmetic["metadata"]["solution_trace"]["calculations"][0][
                "claimed_result"
            ] = 31.0
            with self.assertRaisesRegex(ValueError, "calculation result mismatch"):
                validate_answer_sample(
                    wrong_arithmetic,
                    question,
                    bundle,
                    root,
                )

            bad_cot = json.loads(json.dumps(answer))
            bad_cot["cot"] = "<think>one</think><think>two</think>"
            with self.assertRaisesRegex(ValueError, "single think block"):
                validate_answer_sample(bad_cot, question, bundle, root)

            incomplete_trace = json.loads(json.dumps(answer))
            incomplete_trace["metadata"]["solution_trace"].pop(
                "formula_selection_reason"
            )
            incomplete_trace["metadata"]["solution_trace"].pop(
                "chart_text_alignment"
            )
            incomplete_trace["metadata"]["solution_trace"].pop(
                "unit_and_rounding"
            )
            incomplete_trace["metadata"]["solution_trace"].pop(
                "evidence_conclusion"
            )
            validate_answer_sample(
                incomplete_trace,
                question,
                bundle,
                root,
            )

    def test_structured_calculation_checks_negative_base_sign_and_abs(self):
        from scripts.generate_finance_qa import _validate_structured_calculations

        evidence = [
            {
                "text_quote": (
                    "扣非净利润14,454,099.30元，"
                    "上年为-1,678,927.16元"
                )
            }
        ]
        signed = {
            "expression": (
                "(14454099.30-(-1678927.16))/(-1678927.16)*100"
            ),
            "claimed_result": 960.91,
            "unit": "%",
            "rounding_digits": 2,
            "evidence_indices": [0],
        }
        with self.assertRaisesRegex(ValueError, "calculation result mismatch"):
            _validate_structured_calculations([signed, signed], evidence)

        absolute_base = dict(signed)
        absolute_base["expression"] = (
            "(14454099.30-(-1678927.16))/abs(-1678927.16)*100"
        )
        results = _validate_structured_calculations(
            [absolute_base, absolute_base],
            evidence,
        )
        self.assertEqual(results[0]["computed_result"], 960.91)

    def test_structured_calculation_allows_standard_financial_constants(self):
        from scripts.generate_finance_qa import _validate_structured_calculations

        evidence = [
            {"text_quote": "营业收入100元，期初资产40元，期末资产60元"}
        ]
        average_asset_turnover = {
            "expression": "100/((40+60)/2)",
            "claimed_result": 2.0,
            "unit": "次",
            "rounding_digits": 2,
            "evidence_indices": [0],
        }
        results = _validate_structured_calculations(
            [average_asset_turnover, average_asset_turnover],
            evidence,
        )
        self.assertEqual(results[0]["computed_result"], 2.0)

    def test_training_record_uses_answer_selected_media(self):
        from scripts.generate_finance_qa import project_training_record

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            bundle = _bundle(root)
            question = _question_candidate(bundle)
            answer = _answer_sample(bundle, question)
            answer["media"] = [bundle["media_paths"][0]]

            record = project_training_record(answer, bundle)

            self.assertEqual(record["images"], answer["media"])
            self.assertEqual(
                record["messages"][0]["content"].count("<image>"),
                1,
            )

    def test_two_stage_process_uses_question_then_answer_temperatures(self):
        from scripts.generate_finance_qa import (
            PromptLibrary,
            PromptTemplate,
            process_shard,
        )

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            bundle = _bundle(root)
            input_path = root / "data" / "finance_qa" / "all.jsonl"
            input_path.parent.mkdir(parents=True, exist_ok=True)
            input_path.write_text(json.dumps(bundle, ensure_ascii=False) + "\n", encoding="utf-8")
            library = PromptLibrary(
                system_prompt="system",
                templates={
                    f"FM-HTA-{index:02d}": PromptTemplate(
                        f"FM-HTA-{index:02d}",
                        "HTA",
                        "hard table",
                        "question template {{source_id}} {{document_text_or_ocr}}",
                    )
                    for index in range(1, 11)
                },
                few_shots={},
            )
            calls = []

            def generate_batch(inputs, seeds, temperatures=None):
                calls.append(list(temperatures or []))
                rows = []
                for prompt_input in inputs:
                    prompt = str(prompt_input["prompt"])
                    if prompt_input.get("_stage") == "answer":
                        question = prompt_input["_question_candidate"]
                        resolved_bundle = prompt_input["_resolved_bundle"]
                        rows.append(
                            json.dumps(
                                _answer_sample(
                                    resolved_bundle,
                                    question,
                                    question["generation_prompt_id"],
                                ),
                                ensure_ascii=False,
                            )
                        )
                    else:
                        template_id = "FM-HTA-01"
                        for index in range(1, 11):
                            candidate = f"FM-HTA-{index:02d}"
                            if candidate in prompt:
                                template_id = candidate
                                break
                        rows.append(
                            json.dumps(
                                _question_candidate(
                                    prompt_input["_resolved_bundle"],
                                    template_id,
                                ),
                                ensure_ascii=False,
                            )
                        )
                return rows

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
                question_temperature=0.9,
                answer_temperature=0.6,
            )

            self.assertEqual(counters["accepted_multi"], 2)
            self.assertIn([0.9, 0.9], calls)
            self.assertIn([0.6], calls)
            self.assertTrue((root / "output" / ".parts" / "questions" / "rank_0000.jsonl").is_file())
            self.assertTrue((root / "output" / ".parts" / "raw_answers" / "rank_0000.jsonl").is_file())
            multi_path = (
                root / "output" / ".parts" / "multi" / "rank_0000.jsonl"
            )
            records = [
                json.loads(line)
                for line in multi_path.read_text(encoding="utf-8").splitlines()
            ]
            for record in records:
                self.assertTrue(
                    all(path.startswith("output/assets/") for path in record["images"])
                )
                self.assertTrue(
                    all((root / path).is_file() for path in record["images"])
                )

    def test_local_pipeline_batches_two_question_and_answer_requests(self):
        from local_finance_qa.generate_modelscope import process_shard_parallel
        from scripts.generate_finance_qa import PromptLibrary, PromptTemplate

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            rows = []
            for index in range(2):
                bundle = _bundle(root)
                bundle["bundle_id"] = f"table_qa:parallel:{index}"
                bundle["samples_requested"] = 1
                rows.append(bundle)
            input_path = root / "data" / "finance_qa" / "all.jsonl"
            input_path.parent.mkdir(parents=True, exist_ok=True)
            input_path.write_text(
                "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
                encoding="utf-8",
            )
            library = PromptLibrary(
                system_prompt="system",
                templates={
                    f"FM-HTA-{index:02d}": PromptTemplate(
                        f"FM-HTA-{index:02d}",
                        "HTA",
                        "hard table",
                        "question template {{source_id}} {{document_text_or_ocr}}",
                    )
                    for index in range(1, 11)
                },
                few_shots={},
            )
            calls = []
            progress = []

            def generate_batch(inputs, seeds, temperatures=None):
                calls.append(
                    (
                        [item["_stage"] for item in inputs],
                        list(temperatures or []),
                    )
                )
                outputs = []
                for prompt_input in inputs:
                    if prompt_input["_stage"] == "question":
                        prompt = str(prompt_input["prompt"])
                        template_id = next(
                            (
                                f"FM-HTA-{index:02d}"
                                for index in range(1, 11)
                                if f"FM-HTA-{index:02d}" in prompt
                            ),
                            "FM-HTA-01",
                        )
                        candidate = _question_candidate(
                            prompt_input["_resolved_bundle"],
                            template_id,
                        )
                        candidate.pop("candidate_id")
                        candidate.pop("bundle_id")
                        candidate.pop("task_type")
                        candidate["generation_prompt_id"] = "MODEL-SHOULD-NOT-SET"
                        candidate["evidence"][0]["bbox"] = [
                            100,
                            100,
                            200,
                            200,
                        ]
                        outputs.append(
                            json.dumps(
                                candidate,
                                ensure_ascii=False,
                            )
                        )
                    else:
                        question = prompt_input["_question_candidate"]
                        sample = _answer_sample(
                            prompt_input["_resolved_bundle"],
                            question,
                            question["generation_prompt_id"],
                        )
                        sample["record_id"] = (
                            f"record-{prompt_input['_resolved_bundle']['bundle_id']}"
                        )
                        sample["question"] = "模型改写的问题"
                        sample["metadata"]["evidence"] = [
                            dict(item)
                            for item in sample["metadata"]["evidence"]
                        ]
                        sample["metadata"]["evidence"][0]["bbox"] = [
                            691,
                            620,
                            903,
                            654,
                        ]
                        outputs.append(
                            json.dumps(sample, ensure_ascii=False)
                        )
                return outputs

            counters = process_shard_parallel(
                input_path=input_path,
                project_root=root,
                output_dir=root / "output",
                library=library,
                processor=FakeProcessor(),
                generate_batch=generate_batch,
                batch_size=2,
                base_seed=42,
                target_accepted=2,
                question_temperature=0.9,
                answer_temperature=0.6,
                progress_callback=progress.append,
            )

            self.assertEqual(
                calls,
                [
                    (["question", "question"], [0.9, 0.9]),
                    (["answer", "answer"], [0.6, 0.6]),
                ],
            )
            self.assertEqual(counters["accepted_multi"], 2)
            self.assertEqual(
                [item["accepted_total"] for item in progress],
                [1, 2],
            )

    def test_local_pipeline_retries_invalid_question_once(self):
        from local_finance_qa.generate_modelscope import process_shard_parallel
        from scripts.generate_finance_qa import PromptLibrary, PromptTemplate

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            bundle = _bundle(root)
            bundle["samples_requested"] = 1
            input_path = root / "data" / "finance_qa" / "all.jsonl"
            input_path.parent.mkdir(parents=True, exist_ok=True)
            input_path.write_text(
                json.dumps(bundle, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
            library = PromptLibrary(
                system_prompt="system",
                templates={
                    "FM-HTA-01": PromptTemplate(
                        "FM-HTA-01",
                        "HTA",
                        "hard table",
                        "question template {{source_id}} {{document_text_or_ocr}}",
                    )
                },
                few_shots={},
            )
            stages = []
            question_attempts = 0
            progress = []

            def generate_batch(inputs, seeds, temperatures=None):
                nonlocal question_attempts
                stage = inputs[0]["_stage"]
                stages.append(stage)
                if stage == "question":
                    question_attempts += 1
                    if question_attempts == 1:
                        return [json.dumps({"question": "invalid"})]
                    candidate = _question_candidate(
                        inputs[0]["_resolved_bundle"],
                        "FM-HTA-01",
                    )
                    return [json.dumps(candidate, ensure_ascii=False)]
                question = inputs[0]["_question_candidate"]
                return [
                    json.dumps(
                        _answer_sample(
                            inputs[0]["_resolved_bundle"],
                            question,
                            "FM-HTA-01",
                        ),
                        ensure_ascii=False,
                    )
                ]

            counters = process_shard_parallel(
                input_path=input_path,
                project_root=root,
                output_dir=root / "output",
                library=library,
                processor=FakeProcessor(),
                generate_batch=generate_batch,
                batch_size=2,
                base_seed=42,
                target_accepted=1,
                question_temperature=0.9,
                answer_temperature=0.6,
                progress_callback=progress.append,
            )

            self.assertEqual(stages, ["question", "question", "answer"])
            self.assertEqual(
                [event["outcome"] for event in progress],
                ["question_retry", "accepted"],
            )
            self.assertEqual(counters["accepted_multi"], 1)
            self.assertEqual(counters["errors"], 0)

    def test_local_pipeline_writes_failed_raw_answer_attempts(self):
        from local_finance_qa.generate_modelscope import process_shard_parallel
        from scripts.generate_finance_qa import PromptLibrary, PromptTemplate

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            bundle = _bundle(root)
            bundle["samples_requested"] = 1
            input_path = root / "data" / "finance_qa" / "all.jsonl"
            input_path.parent.mkdir(parents=True, exist_ok=True)
            input_path.write_text(
                json.dumps(bundle, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
            library = PromptLibrary(
                system_prompt="system",
                templates={
                    "FM-HTA-01": PromptTemplate(
                        "FM-HTA-01",
                        "HTA",
                        "hard table",
                        "question template {{source_id}} {{document_text_or_ocr}}",
                    )
                },
                few_shots={},
            )
            answer_attempts = 0

            def generate_batch(inputs, seeds, temperatures=None):
                nonlocal answer_attempts
                if inputs[0]["_stage"] == "question":
                    return [
                        json.dumps(
                            _question_candidate(
                                inputs[0]["_resolved_bundle"],
                                "FM-HTA-01",
                            ),
                            ensure_ascii=False,
                        )
                    ]
                answer_attempts += 1
                question = inputs[0]["_question_candidate"]
                sample = _answer_sample(
                    inputs[0]["_resolved_bundle"],
                    question,
                    "FM-HTA-01",
                )
                sample["cot"] = "invalid cot"
                return [json.dumps(sample, ensure_ascii=False)]

            counters = process_shard_parallel(
                input_path=input_path,
                project_root=root,
                output_dir=root / "output",
                library=library,
                processor=FakeProcessor(),
                generate_batch=generate_batch,
                batch_size=2,
                base_seed=42,
                target_accepted=1,
                question_temperature=0.9,
                answer_temperature=0.6,
            )

            raw_answer_path = (
                root / "output" / ".parts" / "raw_answers" / "rank_0000.jsonl"
            )
            raw_answers = [
                json.loads(line)
                for line in raw_answer_path.read_text(
                    encoding="utf-8"
                ).splitlines()
            ]
            self.assertEqual(answer_attempts, 2)
            self.assertEqual(counters["accepted_multi"], 0)
            self.assertEqual(counters["errors"], 1)
            self.assertEqual([row["attempt"] for row in raw_answers], [1, 2])
            self.assertIn("invalid cot", raw_answers[0]["raw_text"])

    def test_launcher_uses_two_stage_temperature_environment_variables(self):
        dlc = Path("scripts/dlc/start_finance_qa_generation.sh").read_text(encoding="utf-8")

        self.assertIn('--question-temperature "${FINANCE_QA_QUESTION_TEMPERATURE:-0.9}"', dlc)
        self.assertIn('--answer-temperature "${FINANCE_QA_ANSWER_TEMPERATURE:-0.6}"', dlc)
        self.assertIn('--top-p "${FINANCE_QA_TOP_P:-0.95}"', dlc)
        self.assertNotIn("FINANCE_QA_TEMPERATURE", dlc)

    def test_dsw_launcher_can_stop_after_one_accepted_record(self):
        from scripts.generate_finance_qa import build_parser

        args = build_parser().parse_args(
            [
                "worker",
                "--rank",
                "0",
                "--world-size",
                "1",
                "--target-accepted",
                "1",
                "--max-model-calls",
                "5",
            ]
        )
        self.assertEqual(args.target_accepted, 1)
        self.assertEqual(args.max_model_calls, 5)
        self.assertEqual(args.question_min_images, 6)
        self.assertEqual(args.question_max_images, 10)
        self.assertEqual(args.question_max_tokens, 9216)
        self.assertEqual(args.answer_max_tokens, 16384)

        dsw = Path("scripts/dsw/run_finance_qa_generation.sh").read_text(encoding="utf-8")
        self.assertIn("--target-accepted", dsw)
        self.assertIn('${FINANCE_QA_TARGET_ACCEPTED:-2}', dsw)
        self.assertIn('${FINANCE_QA_MAX_MODEL_CALLS:-5}', dsw)

    def test_vllm_uses_stage_specific_token_limits_and_question_json_schema(self):
        from scripts.generate_finance_qa import VLLMGenerator

        generator = object.__new__(VLLMGenerator)
        generator._sampling_params = lambda **kwargs: kwargs
        generator._structured_outputs_params = lambda **kwargs: kwargs
        generator._top_p = 0.95
        generator._question_max_tokens = 4096
        generator._answer_max_tokens = 16384
        generator._question_schema = {
            "type": "object",
            "required": [
                "candidate_id",
                "bundle_id",
                "generation_prompt_id",
                "question",
                "hardness",
            ],
            "properties": {
                "candidate_id": {"type": "string"},
                "bundle_id": {"type": "string"},
                "generation_prompt_id": {"type": "string"},
                "question": {"type": "string"},
                "hardness": {"type": "object"},
            },
        }

        params = generator._build_sampling_params(
            [{"_stage": "question"}, {"_stage": "answer"}],
            [11, 12],
            [0.9, 0.6],
        )

        self.assertEqual(params[0]["max_tokens"], 4096)
        self.assertEqual(params[1]["max_tokens"], 16384)
        self.assertIn("structured_outputs", params[0])
        self.assertNotIn("candidate_id", params[0]["structured_outputs"]["json"]["required"])
        self.assertNotIn("structured_outputs", params[1])


if __name__ == "__main__":
    unittest.main()
