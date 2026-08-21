import json

import pytest

from scripts.rl.validate_gspo_data import validate


def test_validation_rejects_assistant_leakage_and_missing_claims(tmp_path):
    path = tmp_path / "rl.jsonl"
    path.write_text(
        json.dumps(
            {
                "sample_id": "x",
                "messages": [{"role": "assistant", "content": "leak"}],
                "verifier_type": "model_judge",
                "gold_claims": [],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError):
        validate(path, expected_count=1)


def test_validate_requires_structured_numeric_gold_and_matching_image_slots(tmp_path):
    good = {
        "sample_id": "x",
        "messages": [{"role": "user", "content": "<image>q"}],
        "images": ["a.png"],
        "verifier_type": "numeric",
        "gold_atoms": [],
        "gold_numeric": [{"value": "43.48", "unit": "万亿元"}],
    }
    path = tmp_path / "data.jsonl"
    path.write_text(json.dumps(good, ensure_ascii=False) + "\n", encoding="utf-8")
    assert validate(path)["valid"] is True

    bad = dict(good)
    bad["sample_id"] = "y"
    bad["gold_numeric"] = []
    path.write_text(json.dumps(bad, ensure_ascii=False) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="missing_gold_numeric"):
        validate(path)
