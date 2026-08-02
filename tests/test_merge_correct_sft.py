import json
import tempfile
import unittest
from pathlib import Path

from scripts.data.merge_correct_sft import merge_correct_files


class MergeCorrectSftTests(unittest.TestCase):
    def test_merges_correct_zero_to_three_and_deduplicates_training_payload(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_dir = root / "train_text"
            input_dir.mkdir()
            records = [
                {"messages": [{"role": "user", "content": "q0"}], "source": "a"},
                {"messages": [{"role": "user", "content": "q1"}], "source": "a"},
                {"messages": [{"role": "user", "content": "q1"}], "source": "b"},
                {
                    "messages": [{"role": "user", "content": "q2"}],
                    "images": ["image.png"],
                    "source": "a",
                },
            ]
            (input_dir / "correct_0.jsonl").write_text(
                json.dumps(records[0]) + "\n", encoding="utf-8"
            )
            (input_dir / "correct_1.jsonl").write_text(
                json.dumps(records[1]) + "\n", encoding="utf-8"
            )
            (input_dir / "correct_2.jsonl").write_text(
                json.dumps(records[2]) + "\n", encoding="utf-8"
            )
            (input_dir / "correct_3.jsonl").write_text(
                json.dumps(records[3]) + "\n", encoding="utf-8"
            )
            (input_dir / "correct_4.jsonl").write_text(
                json.dumps({"messages": [{"role": "user", "content": "q4"}]}) + "\n",
                encoding="utf-8",
            )

            report = merge_correct_files(input_dir, root / "train_text_sft.jsonl")

            output = [
                json.loads(line)
                for line in (root / "train_text_sft.jsonl").read_text(encoding="utf-8").splitlines()
            ]
            self.assertEqual([row["messages"][0]["content"] for row in output], ["q0", "q1", "q2"])
            self.assertEqual(report["read"], 4)
            self.assertEqual(report["written"], 3)
            self.assertEqual(report["duplicates_removed"], 1)


if __name__ == "__main__":
    unittest.main()
