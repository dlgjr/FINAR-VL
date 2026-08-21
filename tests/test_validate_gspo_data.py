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
        "output_format": "numeric_or_short_text",
        "verifier_type": "numeric",
        "gold_atoms": [],
        "gold_numeric": [{"value": "43.48", "unit": "万亿元", "aliases": [{"value": "43480000000000", "unit": "元"}]}],
        "gold_source": "metadata.official_answer",
        "gold_verification": {"status": "verified", "independent": True},
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


def test_validate_checks_page_range_true_false_and_choice_cardinality(tmp_path):
    rows = [
        {
            "sample_id": "page",
            "messages": [{"role": "user", "content": "<image>q"}],
            "images": ["a.png"],
            "output_format": "page_numbers",
            "verifier_type": "page_numbers",
            "gold_atoms": ["2"],
            "gold_verification": {"status": "verified"},
        },
        {
            "sample_id": "tf",
            "messages": [{"role": "user", "content": "q"}],
            "output_format": "true_false",
            "verifier_type": "true_false",
            "gold_atoms": ["yes"],
            "gold_verification": {"status": "source_only"},
        },
        {
            "sample_id": "choice",
            "messages": [{"role": "user", "content": "q"}],
            "output_format": "single_choice",
            "verifier_type": "single_choice",
            "gold_atoms": ["A", "B"],
            "gold_verification": {"status": "source_only"},
        },
    ]
    path = tmp_path / "bad.jsonl"
    path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n", encoding="utf-8")
    with pytest.raises(ValueError) as exc:
        validate(path)
    message = str(exc.value)
    assert "page_out_of_range" in message
    assert "invalid_true_false_gold" in message
    assert "invalid_single_choice_gold" in message


def test_validate_source_only_gold_is_diagnostic_and_never_blocks(tmp_path):
    row = {
        "sample_id": "hard",
        "messages": [{"role": "user", "content": "q"}],
        "output_format": "numeric_or_short_text",
        "verifier_type": "numeric",
        "gold_atoms": [],
        "gold_numeric": [{"value": "2", "unit": ""}],
        "gold_source": "assistant.final_answer",
        "gold_verification": {"status": "hard_negative_unverified", "independent": False},
    }
    path = tmp_path / "hard.jsonl"
    path.write_text(json.dumps(row, ensure_ascii=False) + "\n", encoding="utf-8")
    report = validate(path)
    assert report["valid"] is True
    assert report["warnings"][0]["warning"] == "source_only"
    assert validate(path, fail_on_unverified=True)["valid"] is True


def test_validate_rejects_output_format_verifier_mismatch(tmp_path):
    row = {
        "sample_id": "x",
        "messages": [{"role": "user", "content": "q"}],
        "output_format": "true_false",
        "verifier_type": "single_choice",
        "gold_atoms": ["A"],
        "gold_verification": {"status": "source_only"},
    }
    path = tmp_path / "bad.jsonl"
    path.write_text(json.dumps(row, ensure_ascii=False) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="verifier_type_mismatch"):
        validate(path)
