"""Смоук Hermes → интенты по лидам (CRUD, стадия, задача)."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from api.routes.ops.eval_cases import BUILTIN_EVAL_CASES

LEAD_BUILTIN = [
    c for c in BUILTIN_EVAL_CASES
    if c["expected"] in ("create_lead", "update_lead", "delete_lead", "list_leads", "create_task")
]


@pytest.mark.asyncio
async def test_voice_command_create_lead(client):
    with patch(
        "voice.pipeline.parse_intent",
        AsyncMock(
            return_value={
                "intent": "create_lead",
                "agents": ["analyst"],
                "slots": {"company": "АКМЕ"},
                "reply": "Создаю лид.",
            }
        ),
    ), patch(
        "agents.orchestrator.run_agents",
        AsyncMock(return_value={"agents_ran": False, "final_reply": "Создаю лид."}),
    ):
        r = await client.post("/api/voice/command", json={"text": "создай лид АКМЕ"})
    assert r.status_code == 200
    data = r.json()
    assert data["intent"] == "create_lead"
    assert data["slots"]["company"] == "АКМЕ"


@pytest.mark.parametrize("case", LEAD_BUILTIN)
def test_builtin_lead_phrases_rescue(case):
    from core.hermes.cache import fastpath_route
    from core.hermes.rescue import rescue_route
    from core.hermes.slot_normalize import normalize_parsed_intent

    text = case["text"]
    raw = fastpath_route(text) or rescue_route(text)
    if not raw:
        pytest.skip(f"нет CPU-маршрута: {text[:40]}")
    out = normalize_parsed_intent(text, raw)
    assert out["intent"] == case["expected"]


@pytest.mark.asyncio
async def test_orchestrator_list_leads_mocked():
    """list_leads — только analyst, без полного fanout."""
    from agents.orchestrator import run_agents

    async def _fake_analyst_run(state):
        state["analyst_output"] = {"summary": "В базе 3 лида.", "stats": {"total": 3}}
        return state

    with patch("agents.analyst.run", _fake_analyst_run):
        result = await run_agents(
            intent="list_leads",
            slots={"filter": "all", "reply": "Показываю."},
            transcript="покажи лиды",
            trace_id="smoke-list",
        )
    assert result.get("agents_ran") is True
    assert "лид" in result.get("final_reply", "").lower()
