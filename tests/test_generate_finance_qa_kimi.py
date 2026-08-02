import base64
import io
import json
import os
import re
import tempfile
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch, sentinel

from PIL import Image
from tests.test_finance_qa_two_stage import (
    _answer_sample as _two_stage_answer,
    _question_candidate as _two_stage_question,
)


class FakeCompletions:
    def __init__(self):
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        text = next(
            part["text"]
            for part in kwargs["messages"][-1]["content"]
            if part["type"] == "text"
        )
        if text.startswith("delay:"):
            delay, value = text.removeprefix("delay:").split(":", 1)
            time.sleep(float(delay))
            content = value
        else:
            content = "generated"
        if kwargs["stream"]:
            midpoint = len(content) // 2
            return iter(
                completion_chunks(content[:midpoint])
                + completion_chunks(content[midpoint:])
            )
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=content))]
        )


class FakeClient:
    def __init__(self):
        self.completions = FakeCompletions()
        self.chat = SimpleNamespace(completions=self.completions)


def completion_chunks(content: str) -> list[SimpleNamespace]:
    return [
        SimpleNamespace(
            choices=[SimpleNamespace(delta=SimpleNamespace(content=content))]
        )
    ]


def accepted_sample(source_id: str, media: list[str]) -> dict:
    return {
        "record_id": "record-1",
        "source_dataset": "finance_reports",
        "source_id": source_id,
        "modality": "multimodal",
        "question": "结合两项指标计算收入与利润增速差，并说明现金流风险。",
        "answer": "收入增速比利润增速高5个百分点。",
        "task_type": "Financial Report",
        "media": media,
        "is_complete": True,
        "missing_assets": [],
        "metadata": {
            "generation_prompt_id": "FM-MNR-01",
            "generation_status": "accepted",
            "evidence": [
                {
                    "source_ref": media[0],
                    "bbox": [0.1, 0.1, 0.9, 0.2],
                },
                {
                    "source_ref": media[1],
                    "bbox": [0.1, 0.2, 0.9, 0.3],
                },
            ],
            "solution_trace": {
                "steps": [
                    {"description": "读取收入和利润增速。"},
                    {"description": "计算两项增速之差。"},
                ]
            },
            "verification": {
                "answerable": True,
                "evidence_sufficient": True,
                "external_facts_used": False,
                "citations_valid": True,
                "passed": True,
            },
        },
    }


class KimiFinanceQATest(unittest.TestCase):
    def test_parser_uses_local_modelscope_defaults(self):
        from scripts.generate_finance_qa_kimi import build_parser

        args = build_parser().parse_args([])

        self.assertEqual(
            args.models,
            [
                "Qwen/Qwen3.5-397B-A17B",
                "Qwen/Qwen3-VL-235B-A22B-Instruct",
            ],
        )
        self.assertEqual(
            args.base_url,
            "https://api-inference.modelscope.cn/v1",
        )
        self.assertEqual(args.concurrency, 1)
        self.assertEqual(args.temperature, 0.7)
        self.assertEqual(args.target_accepted, 1500)
        self.assertTrue(args.input.endswith("data\\finance_qa\\all.jsonl"))
        self.assertTrue(
            args.prompts.endswith(
                "data\\finance_qa\\prompts\\financial_multimodal_prompt_library.md"
            )
        )

    def test_require_modelscope_token_fails_before_api_use(self):
        from scripts.generate_finance_qa_kimi import require_modelscope_token

        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(
                RuntimeError,
                "MODELSCOPE_SDK_TOKEN",
            ):
                require_modelscope_token()

    def test_generator_encodes_images_and_passes_generation_parameters(self):
        from scripts.generate_finance_qa_kimi import ModelScopeGenerator

        client = FakeClient()
        generator = ModelScopeGenerator(
            client=client,
            model_assignments={"demo": "Qwen/Qwen3.5-397B-A17B"},
            concurrency=4,
            temperature=0.3,
            top_p=0.9,
            max_tokens=8192,
        )
        images = [
            Image.new("RGB", (2, 2), color="red"),
            Image.new("RGB", (2, 2), color="blue"),
        ]
        prompt_input = {
            "prompt": [
                {"role": "system", "content": "system"},
                {
                    "role": "user",
                    "content": [
                        {"type": "image"},
                        {"type": "image"},
                        {"type": "text", "text": "question"},
                    ],
                },
            ],
            "multi_modal_data": {"image": images},
            "_resolved_bundle": {"bundle_id": "demo"},
        }

        result = generator.generate_batch([prompt_input], [7])

        self.assertEqual(result, ["generated"])
        call = client.completions.calls[0]
        self.assertEqual(call["model"], "Qwen/Qwen3.5-397B-A17B")
        self.assertEqual(call["temperature"], 0.3)
        self.assertEqual(call["top_p"], 0.9)
        self.assertEqual(call["max_tokens"], 8192)
        self.assertEqual(call["seed"], 7)
        self.assertIs(call["stream"], True)
        content = call["messages"][-1]["content"]
        urls = [
            part["image_url"]["url"] for part in content if part["type"] == "image_url"
        ]
        self.assertEqual(len(urls), 2)
        decoded_colors = []
        for url in urls:
            self.assertTrue(url.startswith("data:image/png;base64,"))
            encoded = url.split(",", 1)[1]
            with Image.open(io.BytesIO(base64.b64decode(encoded))) as image:
                decoded_colors.append(image.convert("RGB").getpixel((0, 0)))
        self.assertEqual(decoded_colors, [(255, 0, 0), (0, 0, 255)])
        self.assertEqual(content[-1], {"type": "text", "text": "question"})

    def test_generator_maps_seed_to_modelscope_signed_integer_range(self):
        from scripts.generate_finance_qa_kimi import ModelScopeGenerator

        client = FakeClient()
        generator = ModelScopeGenerator(
            client=client,
            model_assignments={"demo": "model"},
            concurrency=1,
            temperature=0.3,
            top_p=0.9,
            max_tokens=128,
        )
        prompt_input = {
            "prompt": [
                {
                    "role": "user",
                    "content": [{"type": "text", "text": "question"}],
                }
            ],
            "_resolved_bundle": {"bundle_id": "demo"},
        }

        generator.generate_batch([prompt_input], [2**32 - 1])

        sent_seed = client.completions.calls[0]["seed"]
        self.assertGreaterEqual(sent_seed, 1)
        self.assertLessEqual(sent_seed, 2**31 - 1)

    def test_generator_retries_rate_limit_with_exponential_backoff(self):
        from scripts.generate_finance_qa_kimi import ModelScopeGenerator

        class FakeRateLimitError(Exception):
            status_code = 429

        client = FakeClient()
        attempts = 0

        def create(**kwargs):
            nonlocal attempts
            attempts += 1
            if attempts < 3:
                raise FakeRateLimitError("rate limited")
            return iter(completion_chunks("generated"))

        client.completions.create = create
        generator = ModelScopeGenerator(
            client=client,
            model_assignments={"demo": "model"},
            concurrency=1,
            temperature=0.3,
            top_p=0.9,
            max_tokens=128,
        )
        prompt_input = {
            "prompt": [
                {
                    "role": "user",
                    "content": [{"type": "text", "text": "question"}],
                }
            ],
            "_resolved_bundle": {"bundle_id": "demo"},
        }

        with patch("scripts.generate_finance_qa_kimi.time.sleep") as sleep:
            result = generator.generate_batch([prompt_input], [7])

        self.assertEqual(result, ["generated"])
        self.assertEqual(attempts, 3)
        self.assertEqual([call.args[0] for call in sleep.call_args_list], [2, 4])

    def test_generator_does_not_retry_non_rate_limit_error(self):
        from scripts.generate_finance_qa_kimi import ModelScopeGenerator

        client = FakeClient()
        attempts = 0

        def create(**kwargs):
            nonlocal attempts
            attempts += 1
            raise RuntimeError("request failed")

        client.completions.create = create
        generator = ModelScopeGenerator(
            client=client,
            model_assignments={"demo": "model"},
            concurrency=1,
            temperature=0.3,
            top_p=0.9,
            max_tokens=128,
        )
        prompt_input = {
            "prompt": [
                {
                    "role": "user",
                    "content": [{"type": "text", "text": "question"}],
                }
            ],
            "_resolved_bundle": {"bundle_id": "demo"},
        }

        with self.assertRaisesRegex(RuntimeError, "request failed"):
            generator.generate_batch([prompt_input], [7])

        self.assertEqual(attempts, 1)

    def test_generator_downscales_oversized_images_for_modelscope(self):
        from scripts.generate_finance_qa_kimi import ModelScopeGenerator

        client = FakeClient()
        generator = ModelScopeGenerator(
            client=client,
            model_assignments={"demo": "model"},
            concurrency=1,
            temperature=0.3,
            top_p=0.9,
            max_tokens=128,
        )
        prompt_input = {
            "prompt": [
                {
                    "role": "user",
                    "content": [
                        {"type": "image"},
                        {"type": "text", "text": "question"},
                    ],
                }
            ],
            "multi_modal_data": {
                "image": [Image.new("RGB", (1861, 2631), color="white")]
            },
            "_resolved_bundle": {"bundle_id": "demo"},
        }

        generator.generate_batch([prompt_input], [7])

        url = client.completions.calls[0]["messages"][0]["content"][0]["image_url"][
            "url"
        ]
        encoded = url.split(",", 1)[1]
        with Image.open(io.BytesIO(base64.b64decode(encoded))) as image:
            self.assertEqual(image.size, (1449, 2048))

    def test_generator_preserves_input_order_under_concurrency(self):
        from scripts.generate_finance_qa_kimi import ModelScopeGenerator

        client = FakeClient()
        generator = ModelScopeGenerator(
            client=client,
            model_assignments={
                "bundle-1": "model-1",
                "bundle-2": "model-2",
                "bundle-3": "model-1",
            },
            concurrency=4,
            temperature=0.3,
            top_p=0.9,
            max_tokens=128,
        )
        inputs = [
            {
                "prompt": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": f"delay:{delay}:{value}",
                            }
                        ],
                    }
                ],
                "_resolved_bundle": {"bundle_id": f"bundle-{index}"},
            }
            for index, (delay, value) in enumerate(
                ((0.03, "first"), (0.01, "second"), (0, "third")),
                start=1,
            )
        ]

        result = generator.generate_batch(inputs, [1, 2, 3])

        self.assertEqual(result, ["first", "second", "third"])

    def test_model_assignments_alternate_by_input_and_survive_reuse(self):
        from scripts.generate_finance_qa_kimi import build_model_assignments

        models = ["model-a", "model-b"]
        with tempfile.TemporaryDirectory() as temporary:
            input_path = Path(temporary) / "all.jsonl"
            rows = [{"bundle_id": f"bundle-{index}"} for index in range(5)]
            input_path.write_text(
                "".join(json.dumps(row) + "\n" for row in rows),
                encoding="utf-8",
            )

            first = build_model_assignments(input_path, models)
            second = build_model_assignments(input_path, models)

        expected = {
            "bundle-0": "model-a",
            "bundle-1": "model-b",
            "bundle-2": "model-a",
            "bundle-3": "model-b",
            "bundle-4": "model-a",
        }
        self.assertEqual(first, expected)
        self.assertEqual(second, expected)

    def test_passthrough_processor_preserves_structured_messages(self):
        from scripts.generate_finance_qa_kimi import PassthroughProcessor

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "image"},
                    {"type": "text", "text": "question"},
                ],
            }
        ]

        result = PassthroughProcessor().apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
        )

        self.assertIs(result, messages)

    def test_run_local_reuses_pipeline_without_persisting_token(self):
        from scripts.generate_finance_qa_kimi import build_parser, run_local

        client = FakeClient()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            input_path = root / "all.jsonl"
            prompt_path = root / "library.md"
            output_dir = root / "output"
            input_path.write_text("", encoding="utf-8")
            prompt_path.write_text("", encoding="utf-8")
            args = build_parser().parse_args(
                [
                    "--root",
                    str(root),
                    "--input",
                    str(input_path),
                    "--prompts",
                    str(prompt_path),
                    "--output-dir",
                    str(output_dir),
                ]
            )
            with (
                patch.dict(
                    os.environ,
                    {"MODELSCOPE_SDK_TOKEN": "secret-token"},
                    clear=True,
                ),
                patch(
                    "scripts.generate_finance_qa_kimi.parse_prompt_library",
                    return_value=sentinel.library,
                ),
                patch(
                    "scripts.generate_finance_qa_kimi.process_shard",
                    return_value={"accepted_multi": 2},
                ) as process,
                patch(
                    "scripts.generate_finance_qa_kimi.merge_parts",
                    return_value={"accepted_multi": 2},
                ),
            ):
                result = run_local(args, client=client)

            config = json.loads(
                (output_dir / "run_config.json").read_text(encoding="utf-8")
            )
            self.assertNotIn("secret-token", json.dumps(config))
            self.assertEqual(
                config["models"],
                [
                    "Qwen/Qwen3.5-397B-A17B",
                    "Qwen/Qwen3-VL-235B-A22B-Instruct",
                ],
            )
            self.assertEqual(
                config["model_assignment"],
                "input_order_round_robin",
            )
            self.assertEqual(config["concurrency"], 1)
            self.assertEqual(config["target_accepted"], 1500)
            self.assertEqual(result["summary"], {"accepted_multi": 2})
            call = process.call_args.kwargs
            self.assertIs(call["library"], sentinel.library)
            self.assertEqual(call["rank"], 0)
            self.assertEqual(call["world_size"], 1)
            self.assertEqual(call["batch_size"], 1)
            self.assertEqual(call["target_accepted"], 1500)

    def test_main_returns_failure_until_accepted_target_is_reached(self):
        from scripts.generate_finance_qa_kimi import main

        with (
            patch(
                "scripts.generate_finance_qa_kimi.run_local",
                return_value={
                    "summary": {
                        "accepted_multi": 1499,
                        "accepted_text": 0,
                    }
                },
            ),
            patch("builtins.print"),
        ):
            self.assertEqual(main([]), 1)

        with (
            patch(
                "scripts.generate_finance_qa_kimi.run_local",
                return_value={
                    "summary": {
                        "accepted_multi": 1499,
                        "accepted_text": 1,
                    }
                },
            ),
            patch("builtins.print"),
        ):
            self.assertEqual(main([]), 0)

    def test_run_local_projects_api_json_to_existing_output_schema(self):
        from scripts.generate_finance_qa_kimi import build_parser, run_local

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            asset_dir = root / "data" / "finance_qa" / "assets"
            asset_dir.mkdir(parents=True)
            media = []
            for index, color in enumerate(("red", "blue")):
                image_path = asset_dir / f"{index}.png"
                Image.new("RGB", (4, 4), color=color).save(image_path)
                media.append(image_path.relative_to(root).as_posix())
            text_path = asset_dir / "page.txt"
            text_path.write_text(
                "营业收入100元，营业成本70元，净利润20元，经营活动现金流15元。",
                encoding="utf-8",
            )
            bundle = {
                "bundle_id": "table_qa:demo:1",
                "package_type": "table_qa",
                "document_id": "demo",
                "page_numbers": [1, 2],
                "media_paths": media,
                "context_files": {
                    "pdf_text": [text_path.relative_to(root).as_posix()],
                    "ocr": [],
                    "tables": [],
                    "figures": [],
                },
                "page_region_map": {"pages": [{"page_number": 1}]},
                "samples_requested": 1,
            }
            input_path = root / "data" / "finance_qa" / "all.jsonl"
            input_path.write_text(
                json.dumps(bundle, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
            prompt_path = (
                root
                / "data"
                / "finance_qa"
                / "prompts"
                / "financial_multimodal_prompt_library.md"
            )
            prompt_path.parent.mkdir(parents=True)
            prompt_path.write_text(
                "# 提示词\n\n"
                "## 2. 公共 System Prompt\n\n"
                "```text\n只使用输入证据。\n```\n\n"
                "### FM-MNR-01｜数值推理\n\n"
                "```text\n对 {{source_id}} 生成多步问题。"
                "{{document_text_or_ocr}}\n```\n",
                encoding="utf-8",
            )
            output_dir = root / "output"
            client = FakeClient()

            def staged_completion(**kwargs):
                prompt = json.dumps(kwargs["messages"], ensure_ascii=False)
                match = re.search(
                    r"generation_prompt_id=(FM-[A-Z]+-\d+)",
                    prompt,
                )
                prompt_id = match.group(1) if match else "FM-MNR-01"
                question = _two_stage_question(bundle, prompt_id)
                if "STAGE=QUESTION_ONLY" in prompt:
                    payload = question
                else:
                    payload = _two_stage_answer(bundle, question, prompt_id)
                    payload["record_id"] = "record-1"
                return iter(
                    completion_chunks(
                        json.dumps(payload, ensure_ascii=False)
                    )
                )

            client.completions.create = staged_completion
            args = build_parser().parse_args(
                [
                    "--root",
                    str(root),
                    "--input",
                    str(input_path),
                    "--prompts",
                    str(prompt_path),
                    "--output-dir",
                    str(output_dir),
                ]
            )

            with patch.dict(
                os.environ,
                {"MODELSCOPE_SDK_TOKEN": "secret-token"},
                clear=True,
            ):
                result = run_local(args, client=client)

            self.assertEqual(result["summary"]["accepted_multi"], 1)
            rows = [
                json.loads(line)
                for line in (output_dir / "finance_generated_multi.jsonl")
                .read_text(encoding="utf-8")
                .splitlines()
            ]
            self.assertEqual(rows[0]["record_id"], "record-1")
            self.assertTrue(
                all(
                    path.startswith("output/assets/")
                    for path in rows[0]["images"]
                )
            )
            self.assertTrue(
                all((root / path).is_file() for path in rows[0]["images"])
            )
            self.assertEqual(len(rows[0]["images"]), len(media))
            self.assertEqual(
                rows[0]["messages"][0]["content"].count("<image>"),
                2,
            )


if __name__ == "__main__":
    unittest.main()
