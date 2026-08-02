import json
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


def chunks(text):
    return [
        SimpleNamespace(
            choices=[SimpleNamespace(delta=SimpleNamespace(content=text))]
        )
    ]


class FakeCompletions:
    def __init__(self):
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return iter(chunks("generated"))


class FakeClient:
    def __init__(self):
        self.completions = FakeCompletions()
        self.chat = SimpleNamespace(completions=self.completions)


class LocalModelScopeFinanceQATests(unittest.TestCase):
    def test_answer_normalization_restores_question_and_scales_bbox(self):
        from local_finance_qa.generate_modelscope import (
            _normalize_answer_sample,
        )

        sample = {
            "question": "模型改写的问题",
            "metadata": {
                "evidence": [
                    {"bbox": [691, 620, 903, 654]},
                    {"bbox": [0.1, 0.2, 0.3, 0.4]},
                ]
            },
        }
        normalized = _normalize_answer_sample(
            sample,
            {"question": "固定问题"},
        )

        self.assertEqual(normalized["question"], "固定问题")
        self.assertEqual(
            normalized["metadata"]["evidence"][0]["bbox"],
            [0.691, 0.62, 0.903, 0.654],
        )
        self.assertEqual(
            normalized["metadata"]["evidence"][1]["bbox"],
            [0.1, 0.2, 0.3, 0.4],
        )

    def test_answer_normalization_restores_media_and_source_refs(self):
        from local_finance_qa.generate_modelscope import (
            _normalize_answer_sample,
        )

        sample = {
            "question": "model changed question",
            "media": ["wrong.png"],
            "metadata": {
                "evidence": [
                    {
                        "source_ref": "pdf_text:data/finance_qa/images/page.png",
                        "bbox": [0.1, 0.2, 0.3, 0.4],
                    },
                    {"source_ref": "pdf_text:missing.png"},
                ]
            },
        }
        question = {
            "question": "fixed question",
            "media_paths": ["data/finance_qa/images/page.png"],
        }
        normalized = _normalize_answer_sample(
            sample,
            question,
            allowed_source_refs={"data/finance_qa/images/page.png"},
        )

        self.assertEqual(normalized["question"], "fixed question")
        self.assertEqual(
            normalized["media"],
            ["data/finance_qa/images/page.png"],
        )
        self.assertEqual(
            normalized["metadata"]["evidence"][0]["source_ref"],
            "data/finance_qa/images/page.png",
        )
        self.assertEqual(
            normalized["metadata"]["evidence"][1]["source_ref"],
            "pdf_text:missing.png",
        )

    def test_answer_normalization_converts_cot_to_think_block(self):
        from local_finance_qa.generate_modelscope import (
            _normalize_answer_sample,
        )

        question = {
            "question": "fixed question",
            "media_paths": ["page.png"],
        }
        dict_cot = _normalize_answer_sample(
            {
                "question": "fixed question",
                "media": ["page.png"],
                "cot": {"steps": ["step 1", "step 2"]},
                "metadata": {"evidence": []},
            },
            question,
        )
        missing_cot = _normalize_answer_sample(
            {
                "question": "fixed question",
                "media": ["page.png"],
                "metadata": {
                    "evidence": [],
                    "solution_trace": {"steps": ["step 1", "step 2"]},
                },
            },
            question,
        )
        existing_block = _normalize_answer_sample(
            {
                "question": "fixed question",
                "media": ["page.png"],
                "cot": "<think>kept</think>",
                "metadata": {"evidence": []},
            },
            question,
        )

        self.assertRegex(dict_cot["cot"], r"^<think>[\s\S]+</think>$")
        self.assertIn("step 1", dict_cot["cot"])
        self.assertRegex(missing_cot["cot"], r"^<think>[\s\S]+</think>$")
        self.assertEqual(existing_block["cot"], "<think>kept</think>")

    def test_evidence_bbox_uses_image_size_for_pixel_coordinates(self):
        from PIL import Image

        from local_finance_qa.generate_modelscope import (
            _normalize_evidence_bboxes,
        )

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            image_path = root / "page.png"
            Image.new("RGB", (2000, 2000)).save(image_path)
            evidence = [
                {
                    "source_ref": "page.png",
                    "bbox": [190, 1583, 327, 1625],
                }
            ]

            _normalize_evidence_bboxes(evidence, root)

            self.assertEqual(
                evidence[0]["bbox"],
                [0.095, 0.7915, 0.1635, 0.8125],
            )

    def test_only_explicit_synthetic_text_uses_synthetic_prompt(self):
        from local_finance_qa.generate_modelscope import (
            _use_synthetic_prompt,
        )

        self.assertFalse(_use_synthetic_prompt({"package_type": "page_qa"}))
        self.assertFalse(_use_synthetic_prompt({"package_type": "table_qa"}))
        self.assertTrue(
            _use_synthetic_prompt({"package_type": "synthetic_text"})
        )

    def test_run_local_requires_token_before_creating_client(self):
        from local_finance_qa.generate_modelscope import (
            build_parser,
            run_local,
        )

        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(
                RuntimeError,
                "MODELSCOPE_SDK_TOKEN",
            ):
                run_local(build_parser().parse_args([]), client=FakeClient())

    def test_defaults_match_dlc_two_stage_settings(self):
        from local_finance_qa.generate_modelscope import build_parser

        args = build_parser().parse_args([])

        self.assertEqual(
            args.models,
            [
                "Qwen/Qwen3.5-397B-A17B",
                "Qwen/Qwen3-VL-235B-A22B-Instruct",
            ],
        )
        self.assertEqual(args.concurrency, 2)
        self.assertEqual(args.question_temperature, 0.9)
        self.assertEqual(args.answer_temperature, 0.6)
        self.assertEqual(args.top_p, 0.95)
        self.assertEqual(args.max_tokens, 8192)
        self.assertEqual(args.target_accepted, 1500)

    def test_generator_passes_per_request_temperatures_in_order(self):
        from local_finance_qa.generate_modelscope import ModelScopeGenerator

        client = FakeClient()
        generator = ModelScopeGenerator(
            client=client,
            model_assignments={"a": "model-a", "b": "model-b"},
            concurrency=2,
            top_p=0.95,
            max_tokens=8192,
        )
        inputs = [
            {
                "prompt": [{"role": "user", "content": "question"}],
                "_resolved_bundle": {"bundle_id": bundle_id},
                "_stage": stage,
            }
            for bundle_id, stage in (("a", "question"), ("b", "answer"))
        ]

        outputs = generator.generate_batch(inputs, [1, 2], [0.9, 0.6])

        self.assertEqual(outputs, ["generated", "generated"])
        calls = {call["model"]: call for call in client.completions.calls}
        self.assertEqual(calls["model-a"]["temperature"], 0.9)
        self.assertEqual(calls["model-b"]["temperature"], 0.6)

    def test_generator_retries_transient_read_error(self):
        from local_finance_qa.generate_modelscope import ModelScopeGenerator

        class ReadError(Exception):
            pass

        client = FakeClient()
        original_create = client.completions.create
        attempts = 0

        def create(**kwargs):
            nonlocal attempts
            attempts += 1
            if attempts == 1:
                raise ReadError("connection interrupted")
            return original_create(**kwargs)

        client.completions.create = create
        generator = ModelScopeGenerator(
            client=client,
            model_assignments={"a": "model-a"},
            concurrency=2,
            top_p=0.95,
            max_tokens=8192,
        )
        prompt_input = {
            "prompt": [{"role": "user", "content": "question"}],
            "_resolved_bundle": {"bundle_id": "a"},
            "_stage": "question",
        }

        with patch("local_finance_qa.generate_modelscope.time.sleep"):
            outputs = generator.generate_batch([prompt_input], [1], [0.9])

        self.assertEqual(outputs, ["generated"])
        self.assertEqual(attempts, 2)

    def test_matching_legacy_config_is_migrated(self):
        from local_finance_qa.generate_modelscope import (
            build_parser,
            migrate_legacy_run_config,
            run_config,
        )

        desired = run_config(build_parser().parse_args([]))
        legacy = {
            key: value
            for key, value in desired.items()
            if key
            not in {
                "generation_mode",
                "question_temperature",
                "answer_temperature",
            }
        }
        legacy.update(
            {"concurrency": 1, "temperature": 0.7, "top_p": 0.9}
        )
        legacy["models"] = [
            "Qwen/Qwen3.5-397B-A17B",
            "Qwen/Qwen3-VL-235B-A22B-Instruct",
        ]
        with tempfile.TemporaryDirectory() as temporary:
            output_dir = Path(temporary)
            path = output_dir / "run_config.json"
            path.write_text(json.dumps(legacy), encoding="utf-8")

            self.assertTrue(migrate_legacy_run_config(output_dir, desired))
            self.assertEqual(
                json.loads(path.read_text(encoding="utf-8")),
                desired,
            )

    def test_unavailable_thinking_model_config_is_migrated_to_instruct(self):
        from local_finance_qa.generate_modelscope import (
            build_parser,
            migrate_legacy_run_config,
            run_config,
        )

        desired = run_config(build_parser().parse_args([]))
        current = dict(desired)
        current["models"] = [
            "Qwen/Qwen3.5-397B-A17B",
            "Qwen/Qwen3-VL-235B-A22B-Thinking",
        ]
        with tempfile.TemporaryDirectory() as temporary:
            output_dir = Path(temporary)
            path = output_dir / "run_config.json"
            path.write_text(json.dumps(current), encoding="utf-8")

            self.assertTrue(migrate_legacy_run_config(output_dir, desired))
            self.assertEqual(
                json.loads(path.read_text(encoding="utf-8")),
                desired,
            )

    def test_remove_error_records_keeps_unselected_history(self):
        from local_finance_qa.generate_modelscope import remove_error_records

        with tempfile.TemporaryDirectory() as temporary:
            output_dir = Path(temporary)
            path = (
                output_dir
                / ".parts"
                / "errors"
                / "rank_0000.jsonl"
            )
            path.parent.mkdir(parents=True)
            rows = [
                {"record_key": "old:0", "error": "historical"},
                {"record_key": "retry:0", "error": "current"},
                {"record_key": "old:1", "error": "historical"},
            ]
            path.write_text(
                "".join(json.dumps(row) + "\n" for row in rows),
                encoding="utf-8",
            )

            removed = remove_error_records(output_dir, {"retry:0"})

            remaining = [
                json.loads(line)
                for line in path.read_text(encoding="utf-8").splitlines()
            ]
            self.assertEqual(removed, 1)
            self.assertEqual(
                [row["record_key"] for row in remaining],
                ["old:0", "old:1"],
            )

    def test_remove_part_records_removes_duplicate_retry_rows(self):
        from local_finance_qa.generate_modelscope import remove_part_records

        with tempfile.TemporaryDirectory() as temporary:
            output_dir = Path(temporary)
            path = (
                output_dir
                / ".parts"
                / "questions"
                / "rank_0000.jsonl"
            )
            path.parent.mkdir(parents=True)
            rows = [
                {"record_key": "old:0"},
                {"record_key": "retry:0"},
                {"record_key": "retry:0"},
            ]
            path.write_text(
                "".join(json.dumps(row) + "\n" for row in rows),
                encoding="utf-8",
            )

            removed = remove_part_records(
                output_dir,
                "questions",
                {"retry:0"},
            )

            self.assertEqual(removed, 2)
            self.assertEqual(
                path.read_text(encoding="utf-8").splitlines(),
                [json.dumps({"record_key": "old:0"})],
            )

    def test_logs_request_and_progress_without_token(self):
        from local_finance_qa.generate_modelscope import (
            ModelScopeGenerator,
            close_logger,
            configure_logger,
            progress_logger,
        )

        with tempfile.TemporaryDirectory() as temporary:
            output_dir = Path(temporary)
            logger = configure_logger(output_dir)
            generator = ModelScopeGenerator(
                client=FakeClient(),
                model_assignments={"a": "model-a"},
                concurrency=2,
                top_p=0.95,
                max_tokens=8192,
                logger=logger,
            )
            generator.generate_batch(
                [
                    {
                        "prompt": [{"role": "user", "content": "question"}],
                        "_resolved_bundle": {"bundle_id": "a"},
                        "_stage": "question",
                    }
                ],
                [1],
                [0.9],
            )
            progress_logger(logger, 1500, 10)(
                {
                    "accepted_total": 15,
                    "errors": 1,
                    "skipped": 2,
                    "record_key": "0:0",
                    "outcome": "accepted",
                }
            )
            close_logger(logger)

            text = (output_dir / "generation.log").read_text(encoding="utf-8")
            self.assertIn("request_start stage=question model=model-a bundle_id=a", text)
            self.assertIn("request_success stage=question model=model-a bundle_id=a", text)
            self.assertIn("progress accepted=15/1500 errors=11 skipped=2", text)
            self.assertNotIn("secret-token", text)


if __name__ == "__main__":
    unittest.main()
