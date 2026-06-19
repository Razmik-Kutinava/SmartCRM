"""Юнит-тесты флагов scoreAdvisory в списке лидов."""
from core import crm_settings_store
from core.lead_score_list_flags import attach_lead_score_flags, lead_score_flags


def test_lead_score_flags_warnings():
    settings = crm_settings_store.load_settings()
    lead = {"id": 1, "stage": "Новый", "score": 50}
    tasks = [{"status": "open", "due": "01.01.2020"}]
    flags = lead_score_flags(lead, tasks, settings)
    assert flags["hasScoreWarnings"] is True
    assert flags["scoreWarningsCount"] >= 1
    assert flags["suggestedScore"] is not None


def test_lead_score_flags_divergent():
    settings = crm_settings_store.load_settings()
    lead = {"id": 2, "stage": "Новый", "score": 90, "amountRub": None}
    flags = lead_score_flags(lead, [], settings)
    assert flags["scoreDivergent"] is True


def test_attach_lead_score_flags_batch():
    settings = crm_settings_store.load_settings()
    leads = [{"id": 1, "stage": "Новый", "score": 50}]
    tasks = {1: [{"status": "open", "due": "01.01.2020"}]}
    out = attach_lead_score_flags(leads, tasks, settings)
    assert out[0]["hasScoreWarnings"] is True
    assert "suggestedScore" in out[0]
