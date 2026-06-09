"""Расширенные интенты лидов: analyze_lead, lead_history, фильтры stage/city."""
from __future__ import annotations

import pytest

from core.hermes.cache import fastpath_route
from core.hermes.rescue import rescue_route
from core.hermes.slot_normalize import normalize_parsed_intent


def _route(text: str) -> dict:
    raw = fastpath_route(text) or rescue_route(text)
    assert raw is not None, text
    return normalize_parsed_intent(text, raw)


@pytest.mark.parametrize(
    "text,intent",
    [
        ("проанализируй лид ООО Ромашка", "analyze_lead"),
        ("покажи историю изменений по лиду Ромашка", "lead_history"),
        ("что менялось у клиента МашПром", "lead_history"),
        ("покажи лидов в стадии переговоры", "list_leads"),
    ],
)
def test_extended_lead_intents(text, intent):
    out = _route(text)
    assert out["intent"] == intent


def test_list_leads_stage_slot():
    out = _route("покажи лидов в стадии переговоры")
    assert out["intent"] == "list_leads"
    assert "stage" in out.get("slots", {})


def test_analyze_lead_agents_fanout():
    out = _route("проанализируй лид компания АКМЕ")
    assert out["intent"] == "analyze_lead"
    assert "economist" in out.get("agents", [])
