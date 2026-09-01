from scripts.sft.swift_sft_plugin import use_kl_for_task


def test_default_kl_route_only_matches_generation(monkeypatch):
    monkeypatch.delenv("SFT_KL_TASKS", raising=False)

    assert use_kl_for_task("generation") is True
    assert use_kl_for_task("general_dialogue") is False
    assert use_kl_for_task("generation_dialogue") is False
    assert use_kl_for_task("financial_summarization") is False
    assert use_kl_for_task(None) is False


def test_kl_route_can_be_explicitly_extended(monkeypatch):
    monkeypatch.setenv("SFT_KL_TASKS", "generation,retention_dialogue")

    assert use_kl_for_task("generation") is True
    assert use_kl_for_task("retention_dialogue") is True
    assert use_kl_for_task("general_dialogue") is False
