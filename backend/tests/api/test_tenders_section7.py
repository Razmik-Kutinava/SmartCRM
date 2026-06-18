"""§7 Тендеры: связь с лидом, голосовой поиск, evaluate API."""
from unittest.mock import AsyncMock, patch

import pytest

from agents.scenarios.tender_search import INTENT as SEARCH_INTENT, matches_search, tender_search_slots
from core.hermes.rescue import rescue_route
from core.hermes.slot_normalize import normalize_parsed_intent
from core.tender_lead_link import create_lead_from_saved_tender, link_saved_tender_to_lead, tender_link_for_lead
from db.models import Lead
from db.models.tender_saved import TenderSaved
from voice.voice_action import build_voice_action


def test_matches_search_tenders():
    assert matches_search("найди тендеры по manageengine")
    assert not matches_search("оцени тендер на siem")


def test_rescue_search_tenders():
    raw = rescue_route("найди тендеры по CRM")
    assert raw is not None
    parsed = normalize_parsed_intent("x", raw)
    assert parsed["intent"] == SEARCH_INTENT
    assert parsed["module"] == "tenders"
    assert parsed["ui_action"] == "navigate"
    assert "CRM" in (parsed["slots"].get("query") or "")


def test_rescue_list_tenders():
    raw = rescue_route("покажи мои тендеры")
    assert raw is not None
    parsed = normalize_parsed_intent("x", raw)
    assert parsed["intent"] == "list_tenders"
    assert parsed["slots"].get("tab") == "my"


def test_voice_action_search_tenders_route():
    va = build_voice_action(
        intent="search_tenders",
        slots=tender_search_slots("найди тендеры по SIEM"),
        reply="Ищу.",
        agents=["analyst"],
        module="tenders",
        ui_action="navigate",
    )
    assert va["route"].startswith("/tenders?")
    assert "q=" in va["route"]


@pytest.mark.asyncio
async def test_link_and_create_lead_from_tender(db_session):
    row = TenderSaved(
        external_id="test:1",
        source="gosplan",
        snapshot_json={"title": "Поставка CRM", "customer": "Банк", "budget": "5 млн"},
    )
    db_session.add(row)
    await db_session.commit()
    await db_session.refresh(row)

    created = await create_lead_from_saved_tender(db_session, row.id)
    assert created["leadId"] > 0
    assert created["created"] is True

    lead = await db_session.get(Lead, created["leadId"])
    assert lead is not None
    assert lead.source == "Тендер"

    link = await tender_link_for_lead(db_session, lead.id)
    assert link is not None
    assert link["title"] == "Поставка CRM"

    lead2 = Lead(company="Другой", source="—")
    db_session.add(lead2)
    await db_session.flush()
    linked = await link_saved_tender_to_lead(db_session, saved_id=row.id, lead_id=lead2.id)
    assert linked["leadId"] == lead2.id


@pytest.mark.asyncio
async def test_evaluate_tender_api(client):
    state = {
        "final_reply": "Участвовать с оговорками.",
        "strategist_output": {"decision": "Участвовать", "final_reply": "Участвовать с оговорками."},
        "tech_output": {"summary": "ok"},
        "economist_output": {"summary": "ok"},
        "fanout_parallel": True,
    }
    with patch("api.routes.tenders.evaluate_routes.run_agents", new=AsyncMock(return_value=state)):
        r = await client.post(
            "/api/tenders/evaluate",
            json={
                "tender": {"title": "SIEM", "budget": "10 млн"},
                "document_text": "Требуется SOC 24/7",
            },
        )
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert body["has_document"] is True
    assert "Участвовать" in body["result"]["final_reply"]
    assert body["participation"]["verdict"] in ("participate", "caution", "no")
    assert body["participation"]["label"]


@pytest.mark.asyncio
async def test_tender_link_lead_api(client):
    saved = await client.post(
        "/api/tenders/saved",
        json={
            "external_id": "link:test:1",
            "snapshot": {"title": "Закупка", "customer": "АО Тест"},
        },
    )
    assert saved.status_code == 200
    saved_id = saved.json()["item"]["id"]

    lead = await client.post("/api/leads", json={"company": "АО Тест", "stage": "Новый"})
    assert lead.status_code == 201
    lead_id = lead.json()["id"]

    link = await client.post(f"/api/tenders/saved/{saved_id}/link-lead", json={"lead_id": lead_id})
    assert link.status_code == 200
    assert link.json()["leadId"] == lead_id

    card = await client.get(f"/api/leads/{lead_id}")
    assert card.status_code == 200
    assert card.json().get("tenderLink", {}).get("title") == "Закупка"
