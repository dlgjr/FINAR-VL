import json
import tempfile
import unittest
from pathlib import Path

from scripts.data.merge_train_sft_text import (
    OUTPUT_COLUMNS,
    merge_train_text_files,
)


def write_jsonl(path: Path, records: list) -> None:
    path.write_text(
        "\n".join(json.dumps(record, ensure_ascii=False) for record in records) + "\n",
        encoding="utf-8",
    )


class MergeTrainSftTextTests(unittest.TestCase):
    def test_merges_all_source_formats_with_unified_columns(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            supplement = root / "supplement.jsonl"
            official = root / "official.jsonl"
            cfinbench = root / "cfinbench.jsonl"
            v1 = root / "v1.jsonl"
            write_jsonl(
                supplement,
                [
                    {
                        "messages": [
                            {"role": "user", "content": "q?"},
                            {"role": "assistant", "content": "<answer>OUTOFCLAIM</answer>"},
                        ],
                        "source": "gtfintechlab/Numclaim",
                        "split": "train",
                        "task": "financial_time_reasoning",
                        "task_detail": "financial_numeric_claim_temporality_classification",
                        "quality_tier": "final_5000",
                    }
                ],
            )
            write_jsonl(
                official,
                [
                    {
                        "messages": [
                            {"role": "user", "content": "q?"},
                            {"role": "assistant", "content": "计算：4.35-4.14=0.21。"},
                        ],
                        "source": "中国证监会/上市公司2024年年度财务报告会计监管报告",
                        "split": "train",
                        "task": "multi_step_numerical_reasoning",
                    }
                ],
            )
            write_jsonl(
                cfinbench,
                [
                    {
                        "messages": [
                            {"role": "user", "content": "q?"},
                            {"role": "assistant", "content": "<answer>Yes</answer>"},
                        ],
                        "source": "Linq-AI-Research/FinDER",
                        "split": "train",
                        "task": "risk_sentiment_policy",
                        "split_original": "train",
                        "task_original": "risk_sentiment_policy",
                        "task_group": "risk_policy",
                        "output_format": "free_text",
                        "source_file": "train_text/a.jsonl",
                        "source_line": 1,
                        "answer_source": "Answer",
                    }
                ],
            )
            write_jsonl(
                v1,
                [
                    {
                        "messages": [
                            {"role": "user", "content": "q?"},
                            {"role": "assistant", "content": "a"},
                        ],
                        "source": "x",
                        "split": "train",
                        "task": "financial_time_reasoning",
                        "task_original": "financial_time_reasoning",
                        "task_group": "numerical_reasoning",
                        "output_format": "free_text",
                        "task_needs_review": False,
                        "task_normalization_version": "text_task_taxonomy_v3_semantic_merge",
                    },
                    {
                        "messages": [
                            {"role": "user", "content": "q?"},
                            {"role": "assistant", "content": "正确"},
                        ],
                        "source": "cfinbench",
                        "split": "train",
                        "task": "financial_true_false",
                        "task_original": "judgment",
                        "task_group": "choice_and_judgment",
                        "output_format": "true_false",
                        "task_needs_review": False,
                        "task_normalization_version": "text_task_taxonomy_v3_semantic_merge",
                    },
                    {
                        "messages": [
                            {"role": "user", "content": "q?"},
                            {"role": "assistant", "content": "错误"},
                        ],
                        "source": "cfinbench",
                        "split": "test",
                        "task": "financial_true_false",
                        "split_original": "dev",
                        "task_original": "judgment",
                        "task_group": "choice_and_judgment",
                        "output_format": "true_false",
                        "source_file": "dev/judgment/1-1.jsonl",
                        "source_line": 1,
                        "answer_source": "Answer",
                    },
                ],
            )

            report = merge_train_text_files(
                (supplement, official, cfinbench, v1), root
            )

            output = [
                json.loads(line)
                for line in (root / "train_sft_text_final.jsonl")
                .read_text(encoding="utf-8")
                .splitlines()
            ]
            self.assertEqual(report["written"], 6)
            self.assertEqual(report["errors_total"], 0)
            self.assertEqual([list(row) for row in output], [list(OUTPUT_COLUMNS)] * 6)
            self.assertEqual(
                [row["_pass_at_k"]["result_index"] for row in output],
                [
                    "train_text:0",
                    "train_text:1",
                    "train_text:2",
                    "train_text:3",
                    "train_text:4",
                    "train_text:5",
                ],
            )
            self.assertEqual(output[0]["messages"][-1]["content"], "OUTOFCLAIM")
            self.assertEqual(output[0]["task_group"], "numerical_reasoning")
            self.assertEqual(output[0]["output_format"], "free_text")
            self.assertEqual(output[0]["task_original"], "financial_time_reasoning")
            self.assertEqual(output[1]["task_group"], "numerical_reasoning")
            self.assertEqual(output[1]["output_format"], "number_or_free_text")
            self.assertEqual(output[2]["task_group"], "risk_policy")
            self.assertEqual(output[2]["task_original"], "risk_sentiment_policy")
            self.assertEqual(output[2]["messages"][-1]["content"], "Yes")
            self.assertNotIn("split_original", output[5])
            self.assertNotIn("source_file", output[5])
            self.assertEqual(output[5]["split"], "test")
            self.assertFalse(output[4]["task_needs_review"])
            self.assertEqual(
                output[4]["task_normalization_version"],
                "text_task_taxonomy_v3_semantic_merge",
            )
            self.assertEqual(
                output[5]["task_normalization_version"],
                "text_task_taxonomy_v3_semantic_merge",
            )

    def test_answer_tags_removed_only_from_assistant_content(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            supplement = root / "supplement.jsonl"
            v1 = root / "v1.jsonl"
            write_jsonl(v1, [])
            write_jsonl(
                supplement,
                [
                    {
                        "messages": [
                            {
                                "role": "user",
                                "content": "请看 <answer>保持原样</answer>",
                            },
                            {"role": "assistant", "content": "开头<answer>答案</answer>结尾"},
                        ],
                        "source": "s",
                        "split": "train",
                        "task": "financial_time_reasoning",
                    }
                ],
            )
            merge_train_text_files((supplement, v1, v1, v1), root)
            output = json.loads(
                (root / "train_sft_text_final.jsonl").read_text(encoding="utf-8").strip()
            )
            self.assertEqual(output["messages"][0]["content"], "请看 <answer>保持原样</answer>")
            self.assertEqual(output["messages"][1]["content"], "开头答案结尾")

    def test_error_rows_moved_to_merge_error_and_do_not_consume_index(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            supplement = root / "supplement.jsonl"
            v1 = root / "v1.jsonl"
            write_jsonl(v1, [])
            write_jsonl(
                supplement,
                [
                    {"messages": [{"role": "user", "content": "q"}], "task": ""},
                    {"messages": [{"role": "user", "content": "q"}], "task": "t"},
                    {
                        "messages": [
                            {"role": "user", "content": "q"},
                            {"role": "assistant", "content": "<answer></answer>"},
                        ],
                        "task": "t",
                    },
                    {
                        "messages": [
                            {"role": "user", "content": "q"},
                            {"role": "assistant", "content": "ok"},
                        ],
                        "source": "s",
                        "split": "train",
                        "task": "financial_time_reasoning",
                    },
                ],
            )
            bad = root / "bad.jsonl"
            bad.write_text('{"broken": \n', encoding="utf-8")

            report = merge_train_text_files((bad, supplement, v1, v1), root)

            output = [
                json.loads(line)
                for line in (root / "train_sft_text_final.jsonl")
                .read_text(encoding="utf-8")
                .splitlines()
            ]
            errors = (root / "merge_error.jsonl").read_text(encoding="utf-8").splitlines()
            self.assertEqual(report["written"], 1)
            self.assertEqual(report["errors_total"], 4)
            self.assertEqual(report["error_kinds"]["parse_error"], 1)
            self.assertEqual(report["error_kinds"]["empty_task"], 1)
            self.assertEqual(report["error_kinds"]["missing_assistant"], 1)
            self.assertEqual(report["error_kinds"]["empty_supervision"], 1)
            self.assertEqual(len(errors), 4)
            self.assertEqual(output[0]["_pass_at_k"]["result_index"], "train_text:0")
            self.assertTrue(errors[0].startswith('{"broken"'))
            self.assertEqual(json.loads(errors[1])["task"], "")
            self.assertEqual(json.loads(errors[2])["messages"][0]["content"], "q")
            self.assertEqual(
                json.loads(errors[3])["messages"][-1]["content"],
                "<answer></answer>",
            )

    def test_taxonomy_defaults_for_uncovered_tasks(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            supplement = root / "supplement.jsonl"
            v1 = root / "v1.jsonl"
            write_jsonl(v1, [])
            tasks = [
                "long_context_citation_grounded_qa",
                "statistics_comparison_ranking",
                "multi_step_numerical_reasoning",
                "industry_trend_inference",
            ]
            write_jsonl(
                supplement,
                [
                    {
                        "messages": [
                            {"role": "user", "content": "q"},
                            {"role": "assistant", "content": "a"},
                        ],
                        "source": "s",
                        "split": "train",
                        "task": task,
                    }
                    for task in tasks
                ],
            )
            merge_train_text_files((supplement, v1, v1, v1), root)
            output = [
                json.loads(line)
                for line in (root / "train_sft_text_final.jsonl")
                .read_text(encoding="utf-8")
                .splitlines()
            ]
            expected = {
                "long_context_citation_grounded_qa": (
                    "document_qa_and_retrieval",
                    "free_text",
                ),
                "statistics_comparison_ranking": ("table_reasoning", "free_text"),
                "multi_step_numerical_reasoning": (
                    "numerical_reasoning",
                    "number_or_free_text",
                ),
                "industry_trend_inference": ("financial_reasoning", "free_text"),
            }
            for row in output:
                self.assertEqual(
                    (row["task_group"], row["output_format"]),
                    expected[row["task"]],
                )

    def test_taxonomy_built_from_v1_first_seen_values(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            supplement = root / "supplement.jsonl"
            v1 = root / "v1.jsonl"
            write_jsonl(
                supplement,
                [
                    {
                        "messages": [
                            {"role": "user", "content": "q"},
                            {"role": "assistant", "content": "a"},
                        ],
                        "source": "s",
                        "split": "train",
                        "task": "evidence_retrieval",
                    }
                ],
            )
            write_jsonl(
                v1,
                [
                    {
                        "messages": [],
                        "source": "x",
                        "split": "train",
                        "task": "evidence_retrieval",
                        "task_group": "document_qa_and_retrieval",
                        "output_format": "free_text",
                    },
                    {
                        "messages": [],
                        "source": "x",
                        "split": "train",
                        "task": "evidence_retrieval",
                        "task_group": "other",
                        "output_format": "other",
                    },
                ],
            )
            merge_train_text_files((supplement, v1, v1, v1), root)
            output = json.loads(
                (root / "train_sft_text_final.jsonl").read_text(encoding="utf-8").strip()
            )
            self.assertEqual(
                (output["task_group"], output["output_format"]),
                ("document_qa_and_retrieval", "free_text"),
            )


if __name__ == "__main__":
    unittest.main()
