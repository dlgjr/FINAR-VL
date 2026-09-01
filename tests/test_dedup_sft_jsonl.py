import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts.data.dedup_sft_jsonl import dedup_jsonl


class DedupSftJsonlTests(unittest.TestCase):
    def test_minhash_deduplicates_identical_and_highly_similar_messages(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_path = root / "input.jsonl"
            output_path = root / "output.jsonl"
            rows = [
                {
                    "messages": [
                        {"role": "user", "content": "Revenue increased from 10 to 20 in 2024."},
                        {"role": "assistant", "content": "The increase is 10."},
                    ],
                    "source": "a",
                },
                {
                    "messages": [
                        {"role": "user", "content": "Revenue increased from 10 to 20 in 2024. "},
                        {"role": "assistant", "content": "The increase is 10."},
                    ],
                    "source": "b",
                },
                {
                    "messages": [
                        {"role": "user", "content": "Net income fell from 50 to 30 in 2023."},
                        {"role": "assistant", "content": "The decrease is 20."},
                    ],
                    "source": "c",
                },
            ]
            input_path.write_text(
                "".join(json.dumps(row) + "\n" for row in rows),
                encoding="utf-8",
            )

            report = dedup_jsonl(input_path, output_path, threshold=0.90)

            output = [
                json.loads(line)
                for line in output_path.read_text(encoding="utf-8").splitlines()
            ]
            self.assertEqual(len(output), 2)
            self.assertEqual(report["read"], 3)
            self.assertEqual(report["written"], 2)
            self.assertEqual(report["duplicates_removed"], 1)
            self.assertEqual(report["threshold"], 0.90)
            self.assertTrue(report["ignored_images"])

    def test_images_are_ignored_for_multimodal_deduplication(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_path = root / "input.jsonl"
            output_path = root / "output.jsonl"
            rows = [
                {
                    "messages": [{"role": "user", "content": "<image>What is revenue?"}],
                    "images": ["image_a.png"],
                },
                {
                    "messages": [{"role": "user", "content": "<image>What is revenue?"}],
                    "images": ["image_b.png"],
                },
            ]
            input_path.write_text(
                "".join(json.dumps(row) + "\n" for row in rows),
                encoding="utf-8",
            )

            report = dedup_jsonl(input_path, output_path)

            output = output_path.read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(output), 1)
            self.assertEqual(report["duplicates_removed"], 1)

    def test_script_runs_directly_from_file_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            text_dir = project / "data" / "train_text"
            multi_dir = project / "data" / "train_multi"
            text_dir.mkdir(parents=True)
            multi_dir.mkdir(parents=True)
            row = {"messages": [{"role": "user", "content": "q"}]}
            for path in (
                text_dir / "train_text_sft.jsonl",
                multi_dir / "train_multi_sft.jsonl",
            ):
                path.write_text(json.dumps(row) + "\n" + json.dumps(row) + "\n", encoding="utf-8")

            repo = Path(__file__).resolve().parents[1]
            result = subprocess.run(
                [
                    sys.executable,
                    str(repo / "scripts" / "data" / "dedup_sft_jsonl.py"),
                    "--project-root",
                    str(project),
                ],
                cwd=repo,
                text=True,
                capture_output=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(
                len((text_dir / "train_text_sft_minhash_dedup.jsonl").read_text(encoding="utf-8").splitlines()),
                1,
            )
            self.assertEqual(
                len((multi_dir / "train_multi_sft_minhash_dedup.jsonl").read_text(encoding="utf-8").splitlines()),
                1,
            )


if __name__ == "__main__":
    unittest.main()
