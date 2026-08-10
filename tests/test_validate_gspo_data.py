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
