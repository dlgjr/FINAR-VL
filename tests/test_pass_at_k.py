import json
import os
import tempfile
import threading
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from PIL import Image


class FakeProcessor:
    def __init__(self):
        self.messages = None

    def apply_chat_template(self, messages, **kwargs):
        self.messages = messages
        return str(messages[-1]["content"])


class PassAtKTests(unittest.TestCase):
    def test_vllm_multiprocessing_uses_spawn(self):
        from scripts.pass_at_k import configure_vllm_multiprocessing

        original = os.environ.pop("VLLM_WORKER_MULTIPROC_METHOD", None)
        try:
            configure_vllm_multiprocessing()
            self.assertEqual(
                os.environ["VLLM_WORKER_MULTIPROC_METHOD"],
                "spawn",
            )
        finally:
            if original is None:
                os.environ.pop("VLLM_WORKER_MULTIPROC_METHOD", None)
            else:
                os.environ["VLLM_WORKER_MULTIPROC_METHOD"] = original

    def test_vllm_judge_batch_uses_deterministic_generation_and_parses_verdicts(self):
        from scripts.pass_at_k import VLLMGenerator

        class FakeSamplingParams:
            def __init__(self, **kwargs):
                self.kwargs = kwargs

        class FakeLLM:
            def __init__(self):
                self.sampling_params = None

            def generate(self, inputs, *, sampling_params, use_tqdm):
                self.sampling_params = sampling_params
                return [
                    SimpleNamespace(outputs=[SimpleNamespace(text="正确")]),
                    SimpleNamespace(outputs=[SimpleNamespace(text="错误")]),
                ]

        generator = object.__new__(VLLMGenerator)
        generator._sampling_params_class = FakeSamplingParams
        generator._llm = FakeLLM()

        verdicts = generator.judge_batch([{"prompt": "a"}, {"prompt": "b"}])

        self.assertEqual(verdicts, [True, False])
        self.assertEqual(
            generator._llm.sampling_params.kwargs,
            {"n": 1, "temperature": 0.0, "max_tokens": 4},
        )

    def test_launchers_export_spawn_without_strict_shell_mode(self):
        root = Path(__file__).resolve().parents[1]
        for relative_path in (
            "scripts/dsw/run_pass_at_k.sh",
            "scripts/dlc/start_pass_at_k.sh",
        ):
            script = (root / relative_path).read_text(encoding="utf-8")
            self.assertIn("export VLLM_WORKER_MULTIPROC_METHOD=spawn", script)
            self.assertNotIn("set -euo pipefail", script)

    def test_launchers_merge_even_when_worker_returns_nonzero(self):
        root = Path(__file__).resolve().parents[1]
        for relative_path in (
            "scripts/dsw/run_pass_at_k.sh",
            "scripts/dlc/start_pass_at_k.sh",
        ):
            script = (root / relative_path).read_text(encoding="utf-8")
            self.assertIn('wait "${pids[$index]}" || true', script)
            self.assertNotIn("worker_status", script)

    def test_extract_answer_uses_last_supported_marker(self):
        from scripts.pass_at_k import extract_answer

        self.assertEqual(extract_answer(r"分析 \boxed{A}，修正为 \boxed{B}"), "B")
        self.assertEqual(extract_answer("<answer>\n42\n</answer>"), "42")
        self.assertEqual(extract_answer("答案：1\n答案：2"), "2")
        self.assertEqual(extract_answer("Reasoning\nAnswer: positive"), "positive")

    def test_answers_equal_handles_choice_numeric_json_and_text(self):
        from scripts.pass_at_k import answers_equal

        self.assertTrue(answers_equal("答案：B", "B. 会计分期"))
        self.assertTrue(answers_equal("答案：1,200.00", "1200"))
        self.assertTrue(answers_equal('{"b": 2, "a": 1}', '{"a":1,"b":2}'))
        self.assertTrue(answers_equal("答案：Ｎｅｕｔｒａｌ。", "neutral"))
        self.assertFalse(answers_equal('["a", "b"]', '["b", "a"]'))
        self.assertFalse(answers_equal("10", "10%"))
        self.assertFalse(answers_equal('{"value": true}', '{"value": 1}'))

    def test_requires_model_judge_only_for_non_choice_non_numeric_answers(self):
        from scripts.pass_at_k import requires_model_judge

        self.assertFalse(requires_model_judge("答案：B"))
        self.assertFalse(requires_model_judge("答案：1,200.00"))
        self.assertTrue(requires_model_judge("答案：营收显著增长"))
        self.assertTrue(requires_model_judge('{"label": "positive"}'))

    def test_parse_judge_verdict_accepts_only_exact_supported_labels(self):
        from scripts.pass_at_k import parse_judge_verdict

        self.assertTrue(parse_judge_verdict(" 正确\n"))
        self.assertFalse(parse_judge_verdict("错误"))
        with self.assertRaisesRegex(ValueError, "invalid judge verdict"):
            parse_judge_verdict("答案正确")

    def test_stable_seed_depends_on_dataset_and_byte_offset(self):
        from scripts.pass_at_k import stable_seed

        value = stable_seed(42, "train_text", 100)
        self.assertEqual(value, stable_seed(42, "train_text", 100))
        self.assertNotEqual(value, stable_seed(42, "train_multi", 100))
        self.assertNotEqual(value, stable_seed(42, "train_text", 101))

    def test_jsonl_byte_shards_cover_every_record_once(self):
        from scripts.pass_at_k import iter_jsonl_shard

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "data.jsonl"
            rows = [{"id": index, "text": "x" * (index + 1)} for index in range(17)]
            path.write_text(
                "".join(json.dumps(row) + "\n" for row in rows),
                encoding="utf-8",
            )

            seen = []
            for rank in range(4):
                seen.extend(
                    row["id"]
                    for _, row in iter_jsonl_shard(path, rank=rank, world_size=4)
                )

        self.assertEqual(sorted(seen), list(range(17)))
        self.assertEqual(len(seen), len(set(seen)))

    def test_malformed_jsonl_record_is_reported_and_next_record_continues(self):
        from scripts.pass_at_k import JsonlRecordError, iter_jsonl_shard

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "data.jsonl"
            path.write_text(
                '{"id":1}\n{"broken":\n{"id":2}\n',
                encoding="utf-8",
            )
            records = list(iter_jsonl_shard(path, rank=0, world_size=1))

        self.assertEqual(records[0][1]["id"], 1)
        self.assertIsInstance(records[1][1], JsonlRecordError)
        self.assertEqual(records[2][1]["id"], 2)

    def test_build_prompt_input_removes_reference_and_maps_image(self):
        from scripts.pass_at_k import build_prompt_input

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            image_path = root / "data" / "image.png"
            image_path.parent.mkdir(parents=True)
            Image.new("RGB", (4, 4), "white").save(image_path)
            row = {
                "messages": [
                    {"role": "system", "content": "system"},
                    {"role": "user", "content": "<image>问题"},
                    {"role": "assistant", "content": "秘密答案"},
                ],
                "images": ["data/image.png"],
            }
            processor = FakeProcessor()

            prompt_input = build_prompt_input(row, processor, root)

        self.assertIn("问题", prompt_input["prompt"])
        self.assertEqual(len(prompt_input["multi_modal_data"]["image"]), 1)
        serialized = json.dumps(processor.messages, ensure_ascii=False, default=str)
        self.assertNotIn("秘密答案", serialized)
        self.assertNotIn("<image>", serialized)
        self.assertIn("问题", serialized)

    def test_build_judge_input_includes_question_answers_and_image(self):
        from scripts.pass_at_k import build_judge_input

        processor = FakeProcessor()
        image = Image.new("RGB", (4, 4), "white")
        row = {
            "messages": [
                {"role": "user", "content": "<image>图表中的公司表现如何？"},
                {"role": "assistant", "content": "公司营收显著增长。"},
            ],
            "images": ["unused.png"],
        }
        prompt_input = {
            "prompt": "unused",
            "multi_modal_data": {"image": [image]},
        }

        judge_input = build_judge_input(
            row,
            "公司营收显著增长。",
            "营收有明显提升。",
            processor,
            prompt_input,
        )

        serialized = json.dumps(processor.messages, ensure_ascii=False)
        self.assertIn("图表中的公司表现如何？", serialized)
        self.assertIn("公司营收显著增长。", serialized)
        self.assertIn("营收有明显提升。", serialized)
        self.assertNotIn("<image>", serialized)
        self.assertIs(
            judge_input["multi_modal_data"]["image"][0],
            image,
        )

    def test_process_dataset_writes_only_zero_through_k_minus_two_buckets(self):
        from scripts.pass_at_k import process_dataset

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_path = root / "input.jsonl"
            output_dir = root / "output"
            rows = [
                {
                    "messages": [
                        {"role": "user", "content": "q0"},
                        {"role": "assistant", "content": "A"},
                    ]
                },
                {
                    "messages": [
                        {"role": "user", "content": "q6"},
                        {"role": "assistant", "content": "B"},
                    ]
                },
                {
                    "messages": [
                        {"role": "user", "content": "q7"},
                        {"role": "assistant", "content": "C"},
                    ]
                },
            ]
            input_path.write_text(
                "".join(json.dumps(row) + "\n" for row in rows),
                encoding="utf-8",
            )

            def generate_batch(inputs, seeds):
                counts = {"q0": 0, "q6": 6, "q7": 7}
                answers = {"q0": "A", "q6": "B", "q7": "C"}
                return [
                    [answers[item["prompt"]]] * counts[item["prompt"]]
                    + ["wrong"] * (8 - counts[item["prompt"]])
                    for item in inputs
                ]

            process_dataset(
                dataset="train_text",
                input_path=input_path,
                root=root,
                output_dir=output_dir,
                rank=0,
                world_size=1,
                processor=FakeProcessor(),
                generate_batch=generate_batch,
                judge_batch=lambda inputs: self.fail("choice answers must not be judged"),
                k=8,
                base_seed=42,
                batch_size=3,
            )

            results = [
                json.loads(line)
                for line in (output_dir / "train_text" / "results" / "rank_0000.jsonl")
                .read_text(encoding="utf-8")
                .splitlines()
            ]
            zero_rows = [
                json.loads(line)
                for line in (
                    output_dir
                    / ".parts"
                    / "train_text"
                    / "correct_0"
                    / "rank_0000.jsonl"
                )
                .read_text(encoding="utf-8")
                .splitlines()
            ]
            six_rows = [
                json.loads(line)
                for line in (
                    output_dir
                    / ".parts"
                    / "train_text"
                    / "correct_6"
                    / "rank_0000.jsonl"
                )
                .read_text(encoding="utf-8")
                .splitlines()
            ]
            seven_bucket_exists = (
                output_dir / ".parts" / "train_text" / "correct_7" / "rank_0000.jsonl"
            ).exists()

        self.assertEqual([item["correct_count"] for item in results], [0, 6, 7])
        self.assertEqual(len(results[0]["generations"]), 8)
        self.assertEqual(zero_rows[0]["_pass_at_k"]["correct_count"], 0)
        self.assertEqual(six_rows[0]["_pass_at_k"]["correct_count"], 6)
        self.assertFalse(seven_bucket_exists)

    def test_process_dataset_batches_only_open_answers_for_model_judging(self):
        from scripts.pass_at_k import process_dataset

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_path = root / "input.jsonl"
            output_dir = root / "output"
            rows = [
                {
                    "messages": [
                        {"role": "user", "content": "公司的利润趋势如何？"},
                        {"role": "assistant", "content": "利润明显上升。"},
                    ]
                },
                {
                    "messages": [
                        {"role": "user", "content": "计算结果是多少？"},
                        {"role": "assistant", "content": "答案：10"},
                    ]
                },
            ]
            input_path.write_text(
                "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
                encoding="utf-8",
            )

            def generate_batch(inputs, seeds):
                return [
                    ["利润有所提高。", "利润下降。"],
                    ["10", "11"],
                ]

            judge_calls = []

            def judge_batch(inputs):
                judge_calls.extend(inputs)
                return [True, False]

            process_dataset(
                dataset="train_text",
                input_path=input_path,
                root=root,
                output_dir=output_dir,
                rank=0,
                world_size=1,
                processor=FakeProcessor(),
                generate_batch=generate_batch,
                judge_batch=judge_batch,
                k=2,
                base_seed=42,
                batch_size=2,
            )

            results = [
                json.loads(line)
                for line in (
                    output_dir / "train_text" / "results" / "rank_0000.jsonl"
                )
                .read_text(encoding="utf-8")
                .splitlines()
            ]

        self.assertEqual(len(judge_calls), 2)
        self.assertIn("公司的利润趋势如何？", judge_calls[0]["prompt"])
        self.assertIn("利润明显上升。", judge_calls[0]["prompt"])
        self.assertIn("利润有所提高。", judge_calls[0]["prompt"])
        self.assertEqual(
            [generation["correct"] for generation in results[0]["generations"]],
            [True, False],
        )
        self.assertEqual(
            [generation["correct"] for generation in results[1]["generations"]],
            [True, False],
        )

    def test_model_judge_failure_records_open_question_as_error(self):
        from scripts.pass_at_k import process_dataset

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_path = root / "input.jsonl"
            output_dir = root / "output"
            input_path.write_text(
                json.dumps(
                    {
                        "messages": [
                            {"role": "user", "content": "公司的利润趋势如何？"},
                            {"role": "assistant", "content": "利润明显上升。"},
                        ]
                    },
                    ensure_ascii=False,
                )
                + "\n",
                encoding="utf-8",
            )

            def judge_batch(inputs):
                raise ValueError("invalid judge verdict")

            process_dataset(
                dataset="train_text",
                input_path=input_path,
                root=root,
                output_dir=output_dir,
                rank=0,
                world_size=1,
                processor=FakeProcessor(),
                generate_batch=lambda inputs, seeds: [["回答一", "回答二"]],
                judge_batch=judge_batch,
                k=2,
                base_seed=42,
                batch_size=1,
            )

            errors = [
                json.loads(line)
                for line in (output_dir / "errors" / "rank_0000.jsonl")
                .read_text(encoding="utf-8")
                .splitlines()
            ]

        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0]["error"], "invalid judge verdict")

    def test_process_dataset_records_input_error_and_resume_skips_completed(self):
        from scripts.pass_at_k import process_dataset

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_path = root / "input.jsonl"
            output_dir = root / "output"
            rows = [
                {
                    "messages": [
                        {"role": "user", "content": "valid"},
                        {"role": "assistant", "content": "A"},
                    ]
                },
                {"messages": [{"role": "user", "content": "invalid"}]},
            ]
            input_path.write_text(
                "".join(json.dumps(row) + "\n" for row in rows),
                encoding="utf-8",
            )
            calls = []

            def generate_batch(inputs, seeds):
                calls.extend(inputs)
                return [["A"] * 8 for _ in inputs]

            kwargs = dict(
                dataset="train_text",
                input_path=input_path,
                root=root,
                output_dir=output_dir,
                rank=0,
                world_size=1,
                processor=FakeProcessor(),
                generate_batch=generate_batch,
                judge_batch=lambda inputs: self.fail("choice answers must not be judged"),
                k=8,
                base_seed=42,
                batch_size=2,
            )
            process_dataset(**kwargs)
            process_dataset(**kwargs)

            result_lines = (
                (output_dir / "train_text" / "results" / "rank_0000.jsonl")
                .read_text(encoding="utf-8")
                .splitlines()
            )
            error_lines = (
                (output_dir / "errors" / "rank_0000.jsonl")
                .read_text(encoding="utf-8")
                .splitlines()
            )

        self.assertEqual(len(calls), 1)
        self.assertEqual(len(result_lines), 1)
        self.assertEqual(len(error_lines), 1)
        self.assertEqual(json.loads(error_lines[0])["dataset"], "train_text")

    def test_merge_outputs_deduplicates_parts_and_builds_summary(self):
        from scripts.pass_at_k import merge_outputs

        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            result_dir = output_dir / "train_text" / "results"
            part_dir = output_dir / ".parts" / "train_text" / "correct_0"
            result_dir.mkdir(parents=True)
            part_dir.mkdir(parents=True)
            result = {
                "dataset": "train_text",
                "byte_offset": 0,
                "result_index": "train_text:0",
                "correct_count": 0,
                "generations": [],
            }
            (result_dir / "rank_0000.jsonl").write_text(
                json.dumps(result) + "\n",
                encoding="utf-8",
            )
            bucket = {
                "messages": [],
                "_pass_at_k": {
                    "k": 8,
                    "correct_count": 0,
                    "dataset": "train_text",
                    "result_index": "train_text:0",
                },
            }
            (part_dir / "rank_0000.jsonl").write_text(
                json.dumps(bucket) + "\n" + json.dumps(bucket) + "\n",
                encoding="utf-8",
            )

            summary = merge_outputs(
                output_dir=output_dir,
                datasets=("train_text",),
                k=8,
            )

            merged = (
                (output_dir / "train_text" / "correct_0.jsonl")
                .read_text(encoding="utf-8")
                .splitlines()
            )

        self.assertEqual(len(merged), 1)
        self.assertEqual(summary["datasets"]["train_text"]["correct_counts"]["0"], 1)
        self.assertEqual(summary["datasets"]["train_text"]["pass_at_k"]["1"], 0.0)

    def test_merge_filters_orphan_bucket_and_result_error_overlap(self):
        from scripts.pass_at_k import merge_outputs

        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            result_dir = output_dir / "train_text" / "results"
            part_dir = output_dir / ".parts" / "train_text" / "correct_0"
            error_dir = output_dir / "errors"
            result_dir.mkdir(parents=True)
            part_dir.mkdir(parents=True)
            error_dir.mkdir()
            result = {
                "dataset": "train_text",
                "byte_offset": 0,
                "result_index": "train_text:0",
                "correct_count": 0,
                "generations": [],
            }
            (result_dir / "rank_0000.jsonl").write_text(
                json.dumps(result) + "\n",
                encoding="utf-8",
            )
            valid_bucket = {
                "_pass_at_k": {
                    "result_index": "train_text:0",
                    "correct_count": 0,
                }
            }
            orphan_bucket = {
                "_pass_at_k": {
                    "result_index": "train_text:10",
                    "correct_count": 0,
                }
            }
            (part_dir / "rank_0000.jsonl").write_text(
                json.dumps(valid_bucket) + "\n" + json.dumps(orphan_bucket) + "\n",
                encoding="utf-8",
            )
            errors = [
                {
                    "dataset": "train_text",
                    "result_index": "train_text:0",
                    "byte_offset": 0,
                },
                {
                    "dataset": "train_text",
                    "result_index": "train_text:20",
                    "byte_offset": 20,
                },
            ]
            (error_dir / "rank_0000.jsonl").write_text(
                "".join(json.dumps(item) + "\n" for item in errors),
                encoding="utf-8",
            )

            summary = merge_outputs(
                output_dir=output_dir,
                datasets=("train_text",),
                k=8,
            )
            merged = (
                (output_dir / "train_text" / "correct_0.jsonl")
                .read_text(encoding="utf-8")
                .splitlines()
            )

        self.assertEqual(len(merged), 1)
        self.assertEqual(summary["datasets"]["train_text"]["completed"], 1)
        self.assertEqual(summary["datasets"]["train_text"]["errors"], 1)
        self.assertEqual(summary["datasets"]["train_text"]["total"], 2)

    def test_ensure_run_config_rejects_mismatch(self):
        from scripts.pass_at_k import ensure_run_config

        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            ensure_run_config(output_dir, {"k": 8, "seed": 42})
            ensure_run_config(output_dir, {"k": 8, "seed": 42})
            with self.assertRaisesRegex(ValueError, "configuration"):
                ensure_run_config(output_dir, {"k": 8, "seed": 43})

    def test_worker_parser_uses_required_platform_defaults(self):
        from scripts.pass_at_k import build_parser

        args = build_parser().parse_args(["worker", "--rank", "0", "--world-size", "4"])

        self.assertEqual(args.k, 8)
        self.assertEqual(args.model, "/mnt/nas/bihaoran/qwen3vl/models/qwen4")
        self.assertEqual(args.max_model_len, 131072)
        self.assertEqual(args.batch_size_multi, 4)
        self.assertEqual(args.batch_size_text, 8)

    def test_wait_for_workers_accepts_success_and_rejects_failure(self):
        from scripts.pass_at_k import wait_for_workers

        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            status_dir = output_dir / "_status"
            status_dir.mkdir()
            (status_dir / "rank_0000.success").write_text("", encoding="utf-8")
            (status_dir / "rank_0001.success").write_text("", encoding="utf-8")
            wait_for_workers(
                output_dir,
                world_size=2,
                timeout_seconds=0.1,
                poll_seconds=0.01,
            )

            (status_dir / "rank_0001.success").unlink()
            (status_dir / "rank_0001.failed.json").write_text(
                '{"error":"boom"}',
                encoding="utf-8",
            )
            with self.assertRaisesRegex(RuntimeError, "rank 1"):
                wait_for_workers(
                    output_dir,
                    world_size=2,
                    timeout_seconds=0.1,
                    poll_seconds=0.01,
                )

    def test_wait_for_workers_rejects_stale_heartbeat(self):
        from scripts.pass_at_k import wait_for_workers

        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            status_dir = output_dir / "_status"
            status_dir.mkdir()
            heartbeat = status_dir / "rank_0000.heartbeat"
            heartbeat.write_text("", encoding="utf-8")
            old = time.time() - 100
            os.utime(heartbeat, (old, old))

            with self.assertRaisesRegex(RuntimeError, "stale"):
                wait_for_workers(
                    output_dir,
                    world_size=1,
                    timeout_seconds=0,
                    poll_seconds=0.01,
                    startup_timeout_seconds=0.1,
                    stale_timeout_seconds=1,
                )

    def test_generation_failure_is_recorded_without_zero_bucket(self):
        from scripts.pass_at_k import process_dataset

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_path = root / "input.jsonl"
            output_dir = root / "output"
            input_path.write_text(
                json.dumps(
                    {
                        "messages": [
                            {"role": "user", "content": "q"},
                            {"role": "assistant", "content": "A"},
                        ]
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            def fail_generation(inputs, seeds):
                raise RuntimeError("generation failed")

            process_dataset(
                dataset="train_text",
                input_path=input_path,
                root=root,
                output_dir=output_dir,
                rank=0,
                world_size=1,
                processor=FakeProcessor(),
                generate_batch=fail_generation,
                judge_batch=lambda inputs: self.fail("choice answers must not be judged"),
                k=8,
                base_seed=42,
                batch_size=1,
            )

            errors = (
                (output_dir / "errors" / "rank_0000.jsonl")
                .read_text(encoding="utf-8")
                .splitlines()
            )
            zero_part = (
                output_dir / ".parts" / "train_text" / "correct_0" / "rank_0000.jsonl"
            )
            zero_part_exists = zero_part.exists()

        self.assertEqual(len(errors), 1)
        self.assertFalse(zero_part_exists)

    def test_validate_summary_totals_detects_missing_records(self):
        from scripts.pass_at_k import validate_summary_totals

        with tempfile.TemporaryDirectory() as tmp:
            input_path = Path(tmp) / "input.jsonl"
            input_path.write_text('{"id":1}\n{"id":2}\n', encoding="utf-8")
            summary = {
                "datasets": {
                    "train_text": {
                        "total": 1,
                    }
                }
            }

            with self.assertRaisesRegex(RuntimeError, "train_text"):
                validate_summary_totals(
                    summary,
                    {"train_text": input_path},
                )

            summary["datasets"]["train_text"]["total"] = 2
            validate_summary_totals(summary, {"train_text": input_path})

    def test_batch_failure_retries_individually_to_isolate_bad_record(self):
        from scripts.pass_at_k import process_dataset

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_path = root / "input.jsonl"
            output_dir = root / "output"
            rows = [
                {
                    "messages": [
                        {"role": "user", "content": question},
                        {"role": "assistant", "content": "A"},
                    ]
                }
                for question in ("good", "bad")
            ]
            input_path.write_text(
                "".join(json.dumps(row) + "\n" for row in rows),
                encoding="utf-8",
            )

            def generate_batch(inputs, seeds):
                if any(item["prompt"] == "bad" for item in inputs):
                    raise RuntimeError("bad request")
                return [["A"] * 8 for _ in inputs]

            process_dataset(
                dataset="train_text",
                input_path=input_path,
                root=root,
                output_dir=output_dir,
                rank=0,
                world_size=1,
                processor=FakeProcessor(),
                generate_batch=generate_batch,
                judge_batch=lambda inputs: self.fail("choice answers must not be judged"),
                k=8,
                base_seed=42,
                batch_size=2,
            )

            results = (
                (output_dir / "train_text" / "results" / "rank_0000.jsonl")
                .read_text(encoding="utf-8")
                .splitlines()
            )
            errors = (
                (output_dir / "errors" / "rank_0000.jsonl")
                .read_text(encoding="utf-8")
                .splitlines()
            )

        self.assertEqual(len(results), 1)
        self.assertEqual(len(errors), 1)

    def test_worker_preflight_failure_writes_failure_marker(self):
        from scripts.pass_at_k import build_parser, run_worker

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output_dir = root / "output"
            args = build_parser().parse_args(
                [
                    "worker",
                    "--root",
                    str(root),
                    "--model",
                    str(root / "missing-model"),
                    "--train-multi",
                    str(root / "missing-multi.jsonl"),
                    "--train-text",
                    str(root / "missing-text.jsonl"),
                    "--output-dir",
                    str(output_dir),
                    "--rank",
                    "3",
                    "--world-size",
                    "4",
                ]
            )

            with self.assertRaises(FileNotFoundError):
                run_worker(args)

            failure = json.loads(
                (output_dir / "_status" / "rank_0003.failed.json").read_text(
                    encoding="utf-8"
                )
            )

        self.assertEqual(failure["rank"], 3)
        self.assertEqual(failure["error_type"], "FileNotFoundError")

    def test_worker_passes_model_judge_to_dataset_processor(self):
        from scripts.pass_at_k import build_parser, run_worker

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            model = root / "model"
            model.mkdir()
            train_text = root / "train_text.jsonl"
            train_text.write_text("{}\n", encoding="utf-8")
            output_dir = root / "output"
            args = build_parser().parse_args(
                [
                    "worker",
                    "--root",
                    str(root),
                    "--model",
                    str(model),
                    "--train-text",
                    str(train_text),
                    "--output-dir",
                    str(output_dir),
                    "--datasets",
                    "train_text",
                    "--rank",
                    "0",
                    "--world-size",
                    "1",
                ]
            )
            generator = SimpleNamespace(
                processor=FakeProcessor(),
                generate_batch=lambda inputs, seeds: [],
                judge_batch=lambda inputs: [],
            )
            captured = {}

            def capture_process_dataset(**kwargs):
                captured.update(kwargs)
                return {"completed": 0, "errors": 0, "skipped": 0}

            with (
                patch("scripts.pass_at_k.VLLMGenerator", return_value=generator),
                patch(
                    "scripts.pass_at_k.process_dataset",
                    side_effect=capture_process_dataset,
                ),
            ):
                run_worker(args)

        self.assertIs(captured["judge_batch"], generator.judge_batch)

    def test_ensure_run_config_waits_for_concurrent_writer(self):
        from scripts.pass_at_k import ensure_run_config

        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            config_path = output_dir / "run_config.json"
            config_path.write_text("", encoding="utf-8")
            expected = {"k": 8, "seed": 42}

            def finish_write():
                time.sleep(0.05)
                config_path.write_text(json.dumps(expected), encoding="utf-8")

            writer = threading.Thread(target=finish_write)
            writer.start()
            ensure_run_config(output_dir, expected)
            writer.join()

    def test_runtime_dependency_check_reports_missing_package(self):
        from importlib.metadata import PackageNotFoundError

        from scripts.pass_at_k import validate_runtime_dependencies

        versions = {
            "vllm": "0.11.0",
            "transformers": "4.57.0",
            "Pillow": "11.0.0",
        }

        def version_getter(name):
            if name not in versions:
                raise PackageNotFoundError(name)
            return versions[name]

        with self.assertRaisesRegex(RuntimeError, "qwen-vl-utils"):
            validate_runtime_dependencies(version_getter)

    def test_runtime_dependency_check_does_not_require_wandb(self):
        from importlib.metadata import PackageNotFoundError

        from scripts.pass_at_k import validate_runtime_dependencies

        versions = {
            "vllm": "0.11.0",
            "qwen-vl-utils": "0.0.14",
            "transformers": "4.57.0",
            "Pillow": "11.0.0",
        }

        def version_getter(name):
            if name not in versions:
                raise PackageNotFoundError(name)
            return versions[name]

        installed = validate_runtime_dependencies(version_getter)
        self.assertEqual(installed, versions)

    def test_repair_jsonl_tail_truncates_partial_last_record(self):
        from scripts.pass_at_k import repair_jsonl_tail

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "results.jsonl"
            path.write_bytes(b'{"id":1}\n{"id":')

            repair_jsonl_tail(path)

            self.assertEqual(path.read_bytes(), b'{"id":1}\n')

            path.write_bytes(b'{"id":2}')
            repair_jsonl_tail(path)
            self.assertEqual(path.read_bytes(), b'{"id":2}\n')


if __name__ == "__main__":
    unittest.main()
