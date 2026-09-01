import json
import io
import tarfile
import tempfile
import unittest
import zipfile
from pathlib import Path

import scripts.data.prepare_training_data as prepare_module
from scripts.data.prepare_training_data import (
    RecordWriter,
    _finchart_image_name,
    _iter_jsonl,
    _normalize_bizfin_record,
    build_record,
    chartqa_multimodal_record,
    convert_chartqa_parquets,
    convert_fintabnet_tar,
    normalize_split,
    prepare_all,
    table_to_markdown,
)


class PrepareTrainingDataTests(unittest.TestCase):
    def test_multihiertt_record_includes_document_tables_and_program(self):
        self.assertTrue(hasattr(prepare_module, "multihiertt_record"))
        record = prepare_module.multihiertt_record(
            {
                "paragraphs": ["Revenue increased.", "## Table 0"],
                "tables": ["<table><tr><td>Revenue</td><td>10</td></tr></table>"],
                "question": "What is revenue?",
                "answer": "10",
                "program": "table_sum(10)",
            },
            split="train",
        )
        self.assertIn("Revenue increased.", record["messages"][0]["content"])
        self.assertIn("<table>", record["messages"][0]["content"])
        self.assertIn("table_sum(10)", record["messages"][1]["content"])
        self.assertEqual(record["source"], "multihiertt")

    def test_multihiertt_record_accepts_official_nested_qa(self):
        record = prepare_module.multihiertt_record(
            {
                "paragraphs": ["## Table 0 ##"],
                "tables": ["<table><tr><td>10</td></tr></table>"],
                "qa": {
                    "question": "What is revenue?",
                    "answer": 10,
                    "program": "add(6,4)",
                },
            },
            split="dev",
        )
        self.assertIn("What is revenue?", record["messages"][0]["content"])
        self.assertEqual(record["split"], "dev")

    def test_finer139_record_maps_numeric_labels_to_names(self):
        self.assertTrue(hasattr(prepare_module, "finer139_record"))
        record = prepare_module.finer139_record(
            {"tokens": ["Revenue", "10"], "ner_tags": [0, 1]},
            label_names=["O", "B-Revenue"],
            split="train",
        )
        labels = json.loads(record["messages"][1]["content"])
        self.assertEqual(
            labels,
            [
                {"token": "Revenue", "label": "O"},
                {"token": "10", "label": "B-Revenue"},
            ],
        )
        self.assertEqual(record["task"], "financial_ner")

    def test_finer139_record_accepts_labels_stored_as_names(self):
        record = prepare_module.finer139_record(
            {"tokens": ["Revenue", "10"], "ner_tags": ["O", "B-Revenues"]},
            label_names=["O", "B-Revenues"],
            split="validation",
        )
        labels = json.loads(record["messages"][1]["content"])
        self.assertEqual(labels[1], {"token": "10", "label": "B-Revenues"})

    def test_pixiu_record_uses_instruction_query_and_answer(self):
        self.assertTrue(hasattr(prepare_module, "pixiu_record"))
        record = prepare_module.pixiu_record(
            {"id": "fpb0", "query": "Classify sentiment.\nAnswer:", "answer": "positive"},
            source_name="flare-fpb",
            split="train",
        )
        self.assertEqual(record["messages"][0]["content"], "Classify sentiment.\nAnswer:")
        self.assertEqual(record["messages"][1]["content"], "positive")
        self.assertEqual(record["source"], "pixiu_flare_fpb")

    def test_pixiu_record_normalizes_instruct_download_directory_suffix(self):
        record = prepare_module.pixiu_record(
            {"query": "Question", "answer": "Answer"},
            source_name="flare-fpb-instruct",
            split="train",
        )
        self.assertEqual(record["source"], "pixiu_flare_fpb")

    def test_finmme_record_writes_embedded_image(self):
        self.assertTrue(hasattr(prepare_module, "finmme_record"))
        with tempfile.TemporaryDirectory() as tmp:
            asset_root = Path(tmp)
            record = prepare_module.finmme_record(
                {
                    "id": 7,
                    "image": {"bytes": b"jpeg", "path": "sample.jpg"},
                    "question_text": "Which quarter increased?",
                    "options": "A: Q1\nB: Q2",
                    "answer": "B",
                    "verified_caption": "Quarterly revenue",
                    "related_sentences": "Revenue increased in Q2.",
                },
                asset_root=asset_root,
                manifest_image_root="data/train_multi/assets/finmme",
            )
            self.assertTrue((asset_root / "7.jpg").is_file())
            self.assertEqual(record["images"], ["data/train_multi/assets/finmme/7.jpg"])
            self.assertTrue(record["messages"][0]["content"].startswith("<image>"))
            self.assertEqual(record["messages"][1]["content"], "B")

    def test_tatdqa_records_create_one_multimodal_example_per_question(self):
        self.assertTrue(hasattr(prepare_module, "tatdqa_records"))
        records = prepare_module.tatdqa_records(
            {
                "doc": {"uid": "doc1", "page": 2, "source": "report.pdf"},
                "questions": [
                    {
                        "uid": "q1",
                        "question": "What is revenue?",
                        "answer": 10,
                        "derivation": "6 + 4",
                        "scale": "million",
                    }
                ],
            },
            split="dev",
            image_path="data/train_multi/assets/tatdqa/doc1_2.png",
        )
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["images"], ["data/train_multi/assets/tatdqa/doc1_2.png"])
        self.assertIn("6 + 4", records[0]["messages"][1]["content"])
        self.assertEqual(records[0]["split"], "dev")

    def test_normalize_split_separates_training_and_evaluation(self):
        self.assertEqual(normalize_split("train"), "train")
        self.assertEqual(normalize_split("validation"), "eval")
        self.assertEqual(normalize_split("dev"), "eval")
        self.assertEqual(normalize_split("test"), "eval")

    def test_build_record_uses_ms_swift_messages_schema(self):
        record = build_record(
            "问题",
            "答案",
            source="demo",
            source_split="train",
        )
        self.assertEqual(
            record["messages"],
            [
                {"role": "user", "content": "问题"},
                {"role": "assistant", "content": "答案"},
            ],
        )
        self.assertEqual(record["source"], "demo")
        self.assertEqual(record["split"], "train")
        self.assertNotIn("images", record)

    def test_chartqa_multimodal_record_writes_image_and_relative_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            asset_root = Path(tmp)
            record = chartqa_multimodal_record(
                {
                    "chart_id": "chart-1",
                    "Question": "图中数值是多少？",
                    "Answer": "16",
                    "Explanation": "柱状图显示为 16。",
                    "image_path": {"bytes": b"fake-png", "path": None},
                },
                asset_root=asset_root,
                manifest_image_root="data/train_multi/assets/chart_qa",
            )
            self.assertTrue((asset_root / "chart-1.png").is_file())
            self.assertEqual(
                record["images"],
                ["data/train_multi/assets/chart_qa/chart-1.png"],
            )
            self.assertTrue(record["messages"][0]["content"].startswith("<image>"))

    def test_record_writer_deduplicates_identical_training_examples(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "train.jsonl"
            record = build_record("同一问题", "同一答案", source="a", source_split="train")
            with RecordWriter(output) as writer:
                self.assertTrue(writer.write(record))
                self.assertFalse(writer.write({**record, "source": "b"}))
            rows = [json.loads(line) for line in output.read_text(encoding="utf-8").splitlines()]
            self.assertEqual(len(rows), 1)

    def test_table_to_markdown_handles_ragged_rows(self):
        self.assertEqual(
            table_to_markdown([["项目", "2023"], ["收入", "10"], ["利润"]]),
            "| 项目 | 2023 |\n| --- | --- |\n| 收入 | 10 |\n| 利润 |  |",
        )

    def test_convert_chartqa_parquets_converts_text_and_embedded_images(self):
        import pyarrow as pa
        import pyarrow.parquet as pq

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "chart-qa"
            source.mkdir()
            pq.write_table(
                pa.table(
                    {
                        "_id": ["t1", "t2"],
                        "text": ["计算收入变化。", "没有答案的问题。"],
                        "reasoning": [True, False],
                        "category": ["Financials", "Financials"],
                        "references": [["2022 年收入 10，2023 年收入 12。"], ["资料"]],
                        "answer": ["增加 2。", ""],
                        "type": ["Subtract", "Other"],
                    }
                ),
                source / "text.parquet",
            )
            image_type = pa.struct([("bytes", pa.binary()), ("path", pa.string())])
            pq.write_table(
                pa.table(
                    {
                        "chart_id": ["m1"],
                        "Question": ["柱高是多少？"],
                        "Answer": ["12"],
                        "Explanation": ["图中柱高为 12。"],
                        "image_path": pa.array(
                            [{"bytes": b"image", "path": None}],
                            type=image_type,
                        ),
                    }
                ),
                source / "multi.parquet",
            )
            text_path = root / "text.jsonl"
            multi_path = root / "multi.jsonl"
            with RecordWriter(text_path) as text_writer, RecordWriter(multi_path) as multi_writer:
                counts = convert_chartqa_parquets(
                    source,
                    text_writer=text_writer,
                    multi_writer=multi_writer,
                    asset_root=root / "assets",
                )
            self.assertEqual(counts, {"text": 1, "multi": 1, "skipped_text": 1})
            self.assertEqual(len(text_path.read_text(encoding="utf-8").splitlines()), 1)
            multi = json.loads(multi_path.read_text(encoding="utf-8"))
            self.assertEqual(multi["images"], ["data/train_multi/assets/chart_qa/m1.png"])
            self.assertTrue((root / "assets" / "m1.png").is_file())

    def test_prepare_all_creates_four_split_manifests_and_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source"
            project = root / "project"
            source.mkdir()
            project.mkdir()
            (source / "financebench_open_source.jsonl").write_text(
                json.dumps(
                    {
                        "question": "收入是多少？",
                        "answer": "10",
                        "evidence": [{"evidence_text": "收入为 10。"}],
                    },
                    ensure_ascii=False,
                )
                + "\n",
                encoding="utf-8",
            )
            cfin = source / "CFinBench_W_Answer/CFinBench_W_Answer/test/single_choice"
            cfin.mkdir(parents=True)
            (cfin / "missing.jsonl").write_text(
                json.dumps({"text": "无答案题", "OptionList": ["甲", "乙"]}, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
            cflue = source / "cflue-master/cflue-master/data/knowledge"
            cflue.mkdir(parents=True)
            (cflue / "knowledge.json").write_text(
                json.dumps(
                    [{"question": "请选择。", "choices": {"A": "甲", "B": "乙"}, "answer": "B"}],
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            conv = source / "ConvFinQA-main/ConvFinQA-main"
            conv.mkdir(parents=True)
            base = {"pre_text": [], "post_text": [], "table": [["项目", "值"], ["收入", "10"]]}
            with zipfile.ZipFile(conv / "data.zip", "w") as archive:
                archive.writestr(
                    "data/train.json",
                    json.dumps(
                        [
                            {
                                **base,
                                "qa_0": {"question": "收入？", "answer": "10"},
                                "qa_1": {"question": "值？", "answer": "10"},
                            }
                        ],
                        ensure_ascii=False,
                    ),
                )
                archive.writestr("data/dev.json", "[]")
                archive.writestr("data/test_private.json", json.dumps([base], ensure_ascii=False))
            disc_eval = source / "DISC-FinLLM-main/DISC-FinLLM-main/eval"
            disc_eval.mkdir(parents=True)
            (disc_eval / "retriever_eval.json").write_text(
                json.dumps([{"question": "无标准答案", "reference": ["资料"]}], ensure_ascii=False),
                encoding="utf-8",
            )
            fineval_test = source / "FinEval/test"
            fineval_test.mkdir(parents=True)
            (fineval_test / "sample_test.csv").write_text(
                "id,question,A,B,C,D\n0,无答案题,甲,乙,丙,丁\n",
                encoding="utf-8",
            )
            report = prepare_all(source, project, include_fintabnet=False)
            self.assertTrue((project / "data/train_text/train.jsonl").is_file())
            self.assertTrue((project / "data/train_text/eval.jsonl").is_file())
            self.assertTrue((project / "data/train_multi/train.jsonl").is_file())
            self.assertTrue((project / "data/train_multi/eval.jsonl").is_file())
            self.assertEqual(report["outputs"]["text_eval"], 1)
            self.assertEqual(report["outputs"]["text_train"], 3)
            self.assertEqual(report["skipped_records"]["cfinbench_missing_answer"], 1)
            self.assertEqual(report["skipped_records"]["convfinqa_missing_answer"], 1)
            self.assertEqual(report["skipped_records"]["disc_finllm_missing_answer"], 1)
            self.assertEqual(report["skipped_records"]["fineval_missing_answer"], 1)

    def test_prepare_all_reports_only_unavailable_and_user_excluded_sources(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source"
            project = root / "project"
            source.mkdir()
            project.mkdir()

            biz = source / "BizFinBench.v2-main/BizFinBench.v2-main/datasets/cn"
            biz.mkdir(parents=True)
            (biz / "sample.jsonl").write_text(
                json.dumps(
                    {
                        "messages": [{"role": "user", "content": [{"text": "问题"}]}],
                        "choices": [
                            {
                                "message": {
                                    "role": "assistant",
                                    "content": [{"text": "答案"}],
                                }
                            }
                        ],
                    },
                    ensure_ascii=False,
                )
                + "\n",
                encoding="utf-8",
            )

            multi = (
                source
                / "MultiHiertt-main/MultiHiertt-main/dataset/multihiertt_data"
            )
            multi.mkdir(parents=True)
            (multi / "train.json").write_text(
                json.dumps(
                    [
                        {
                            "paragraphs": ["## Table 0 ##"],
                            "tables": ["<table><tr><td>10</td></tr></table>"],
                            "qa": {"question": "Revenue?", "answer": 10, "program": ""},
                        }
                    ]
                ),
                encoding="utf-8",
            )

            finchain = source / "finchain-main/finchain-main/data/testset/domain"
            finchain.mkdir(parents=True)
            (finchain / "sample.jsonl").write_text(
                json.dumps({"question": "Compute.", "solution": "Step 1."}) + "\n",
                encoding="utf-8",
            )

            finch = source / "Finch-main/Finch-main/dataset"
            finch.mkdir(parents=True)
            (finch / "finch_workflows_test.jsonl").write_text(
                json.dumps(
                    {
                        "instruction_en": "Edit workbook.",
                        "reference_outputs": {"files": ["ref.xlsx"], "text": ""},
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            report = prepare_all(source, project, include_fintabnet=False)
            self.assertEqual(report["records_by_source"]["bizfinbench_v2"], 1)
            self.assertEqual(report["records_by_source"]["multihiertt"], 1)
            self.assertEqual(report["records_by_source"]["finchain"], 1)
            self.assertEqual(
                report["skipped_no_local_supervised_data"],
                ["Fin-R1-main"],
            )
            self.assertEqual(report["excluded_by_user"], ["FinRAGBench-V-main"])
            self.assertEqual(
                report["downloaded_but_not_direct_sft"]["Finch-main"],
                "1 workflows require binary spreadsheet or document outputs",
            )

    def test_prepare_all_converts_downloaded_zip_and_parquet_sources(self):
        import pyarrow as pa
        import pyarrow.parquet as pq

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source"
            project = root / "project"
            source.mkdir()
            project.mkdir()

            finer = source / "finer-main/finer-main/data/hf_finer139"
            finer.mkdir(parents=True)
            (finer / "dataset_infos.json").write_text(
                json.dumps(
                    {
                        "finer-139": {
                            "features": {
                                "ner_tags": {
                                    "feature": {"names": ["O", "B-Revenues"]}
                                }
                            }
                        }
                    }
                ),
                encoding="utf-8",
            )
            with zipfile.ZipFile(finer / "finer139.zip", "w") as archive:
                archive.writestr(
                    "train.jsonl",
                    json.dumps(
                        {
                            "tokens": ["Revenue", "10"],
                            "ner_tags": ["O", "B-Revenues"],
                        }
                    )
                    + "\n",
                )

            finmme = source / "FinMME-main/FinMME-main/data/data"
            finmme.mkdir(parents=True)
            image_type = pa.struct([("bytes", pa.binary()), ("path", pa.string())])
            pq.write_table(
                pa.table(
                    {
                        "id": pa.array([1, 2], type=pa.int32()),
                        "image": pa.array(
                            [
                                {"bytes": b"png", "path": "image.png"},
                                {"bytes": b"png", "path": "image.png"},
                            ],
                            type=image_type,
                        ),
                        "question_text": ["Question?", "Missing answer?"],
                        "question_type": ["single_choice", "single_choice"],
                        "options": ["A: 1\nB: 2", "A: 1\nB: 2"],
                        "answer": ["A", ""],
                        "verified_caption": ["Chart", "Chart"],
                        "related_sentences": ["", ""],
                    }
                ),
                finmme / "train.parquet",
            )

            pixiu = source / "PIXIU-main/PIXIU-main/data/hf/flare-headlines/data"
            pixiu.mkdir(parents=True)
            pq.write_table(
                pa.table({"query": ["Is price rising?"], "answer": ["Yes"]}),
                pixiu / "train.parquet",
            )
            pixiu_raw = source / "PIXIU-main/PIXIU-main/data/hf/flare-fiqasa/data"
            pixiu_raw.mkdir(parents=True)
            pq.write_table(
                pa.table({"sentence": ["Revenue rose."], "score": [0.8]}),
                pixiu_raw / "train.parquet",
            )
            pixiu_instruct = (
                source
                / "PIXIU-main/PIXIU-main/data/hf/flare-fiqasa-instruct/data"
            )
            pixiu_instruct.mkdir(parents=True)
            pq.write_table(
                pa.table(
                    {
                        "query": ["Classify sentiment."],
                        "answer": ["positive"],
                    }
                ),
                pixiu_instruct / "train.parquet",
            )

            tatdqa = source / "TAT-DQA-master/TAT-DQA-master/dataset"
            tatdqa.mkdir(parents=True)
            (tatdqa / "tatdqa_dataset_train.json").write_text(
                json.dumps(
                    [
                        {
                            "doc": {"uid": "doc1", "page": 1},
                            "questions": [
                                {
                                    "question": "Revenue?",
                                    "answer": 10,
                                    "derivation": "6 + 4",
                                    "answer_type": "arithmetic",
                                }
                            ],
                        }
                    ]
                ),
                encoding="utf-8",
            )
            with zipfile.ZipFile(tatdqa / "tatdqa_docs_train.zip", "w") as archive:
                archive.writestr("train/doc1_1.png", b"png")

            report = prepare_all(source, project, include_fintabnet=False)
            self.assertEqual(report["records_by_source"]["finer139"], 1)
            self.assertEqual(report["records_by_source"]["finmme"], 1)
            self.assertEqual(report["records_by_source"]["pixiu_flare_headlines"], 1)
            self.assertEqual(report["records_by_source"]["pixiu_flare_fiqasa"], 1)
            self.assertEqual(report["records_by_source"]["tatdqa"], 1)
            self.assertEqual(report["skipped_records"]["finmme_missing_answer"], 1)
            self.assertNotIn("pixiu_missing_supervision", report["skipped_records"])
            multi_rows = [
                json.loads(line)
                for line in (
                    project / "data/train_multi/train.jsonl"
                ).read_text(encoding="utf-8").splitlines()
            ]
            self.assertTrue(
                all((project / row["images"][0]).is_file() for row in multi_rows)
            )

    def test_iter_jsonl_repairs_raw_newline_inside_string(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "broken.jsonl"
            path.write_text('{"text":"第一行\n第二行","answer":"A"}\n', encoding="utf-8")
            self.assertEqual(
                list(_iter_jsonl(path)),
                [{"text": "第一行\n第二行", "answer": "A"}],
            )

    def test_iter_jsonl_repairs_unescaped_quote(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "broken_quote.jsonl"
            path.write_text(
                '{"text":"他说 "hello"","answer":"A"}\n',
                encoding="utf-8",
            )
            self.assertEqual(
                list(_iter_jsonl(path)),
                [{"text": '他说 "hello"', "answer": "A"}],
            )

    def test_finchart_image_name_removes_question_suffix(self):
        self.assertEqual(
            _finchart_image_name("1243210261_13_crop_0_q2.jpg"),
            "1243210261_13_crop_0.jpg",
        )

    def test_normalize_bizfin_record_extracts_choice_and_flattens_content(self):
        record = _normalize_bizfin_record(
            {
                "messages": [
                    {"role": "system", "content": [{"text": ""}]},
                    {"role": "user", "content": [{"text": "问题"}]},
                ],
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": [{"text": "答案", "type": "text"}],
                        }
                    }
                ],
            }
        )
        self.assertEqual(
            record,
            [
                {"role": "user", "content": "问题"},
                {"role": "assistant", "content": "答案"},
            ],
        )
        self.assertIsNone(
            _normalize_bizfin_record(
                {
                    "messages": [{"role": "user", "content": [{"text": "问题"}]}],
                    "choices": [{"message": {"role": "assistant", "content": [{"text": ""}]}}],
                }
            )
        )

    def test_convert_fintabnet_tar_handles_images_before_train_xml(self):
        xml = b"""<annotation><object><name>table</name><bndbox>
        <xmin>1</xmin><ymin>2</ymin><xmax>3</xmax><ymax>4</ymax>
        </bndbox></object></annotation>"""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive_path = root / "sample.tar"
            with tarfile.open(archive_path, "w") as archive:
                image_info = tarfile.TarInfo("FinTabNet.c-Structure/images/sample.jpg")
                image_info.size = len(b"jpg")
                archive.addfile(image_info, io.BytesIO(b"jpg"))
                xml_info = tarfile.TarInfo("FinTabNet.c-Structure/train/sample.xml")
                xml_info.size = len(xml)
                archive.addfile(xml_info, io.BytesIO(xml))
            train_path = root / "train.jsonl"
            eval_path = root / "eval.jsonl"
            with RecordWriter(train_path) as train_writer, RecordWriter(eval_path) as eval_writer:
                counts = convert_fintabnet_tar(
                    archive_path,
                    train_writer=train_writer,
                    eval_writer=eval_writer,
                    asset_dir=root / "assets",
                )
            self.assertEqual(counts, {"train": 1, "eval": 0})
            self.assertTrue((root / "assets/sample.jpg").is_file())


if __name__ == "__main__":
    unittest.main()
