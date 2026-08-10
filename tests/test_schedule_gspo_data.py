import json

from scripts.rl.schedule_gspo_data import schedule


def test_schedule_preserves_records_and_writes_cost_report(tmp_path):
    source = tmp_path / "source.jsonl"
    target = tmp_path / "scheduled.jsonl"
    source.write_text("".join(json.dumps({"sample_id": str(i), "estimated_cost": 10 + i}) + "\n" for i in range(8)), encoding="utf-8")
    report = schedule(source, target, workers=2, batch_size=1)
    assert report["stable_sample_ids"] is True
    assert len(target.read_text(encoding="utf-8").splitlines()) == 8
    assert (tmp_path / "scheduled.jsonl.schedule.json").is_file()
