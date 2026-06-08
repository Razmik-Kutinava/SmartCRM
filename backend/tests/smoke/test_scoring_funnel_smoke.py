"""Смоук «Балльная воронка»: scoreAdvisory, формула, приоритеты в конфиге."""
import datetime as dt

import pytest

from core import crm_settings_store
from core.lead_priority_tier import lead_priority_tier
from core.lead_score_advisory import compute_lead_score_advisory


@pytest.mark.asyncio
async def test_crm_config_scoring_flags(client):
    r = await client.get("/api/crm/config")
    assert r.status_code == 200
    data = r.json()
    assert data["priority_thresholds"]["critical"] == 85
    assert data["managerSetsScore"] is True
    assert data["agentsMayUpdateScore"] is False
    assert data["scoringAdvisoryEnabled"] is True


@pytest.mark.asyncio
async def test_lead_card_includes_score_advisory(client):
    r = await client.post("/api/leads", json={"company": "Scoring smoke", "stage": "Новый", "score": 50})
    assert r.status_code == 201
    lid = r.json()["id"]
    card = (await client.get(f"/api/leads/{lid}")).json()
    adv = card.get("scoreAdvisory") or {}
    assert "suggestedScore" in adv
    assert isinstance(adv.get("warnings"), list)
    assert isinstance(adv.get("breakdown"), dict)
    assert 0 <= int(adv["suggestedScore"]) <= 100


@pytest.mark.asyncio
async def test_manager_score_patch_does_not_auto_rewrite(client):
    r = await client.post("/api/leads", json={"company": "Manager owns score", "score": 40})
    lid = r.json()["id"]
    patch = await client.patch(f"/api/leads/{lid}", json={"score": 77})
    assert patch.status_code == 200
    body = patch.json()
    assert body["score"] == 77
    assert body["scoreAdvisory"]["breakdown"]["managerScore"] == 77


def test_formula_golden_novy_with_amount():
    settings = crm_settings_store.load_settings()
    lead = {"stage": "Новый", "score": 50, "amountRub": 500_000, "paidAmountRub": None}
    out = compute_lead_score_advisory(lead, [], settings)
    # base 28 + amount bonus 15 (500k * 3/100k capped 18)
    assert out["breakdown"]["baseFromStage"] == 28
    assert out["breakdown"]["amountBonus"] == 15
    assert out["suggestedScore"] == 43


def test_priority_tier_matches_list_filter_thresholds():
    cfg = crm_settings_store.load_settings()
    assert lead_priority_tier(90, cfg)["key"] == "critical"
    assert lead_priority_tier(50, cfg)["key"] == "medium"


def test_overdue_penalty_in_formula():
    settings = crm_settings_store.load_settings()
    today = dt.date(2026, 6, 8)
    tasks = [{"status": "open", "due": "01.06.2026"}]
    lead = {"stage": "Новый", "score": 50, "amountRub": None}
    from core.lead_score_advisory import count_overdue_open_tasks

    assert count_overdue_open_tasks(tasks, today) == 1
    out = compute_lead_score_advisory(lead, tasks, settings)
    assert out["breakdown"]["overduePenalty"] >= 8
    assert any("просроч" in w.lower() for w in out["warnings"])
