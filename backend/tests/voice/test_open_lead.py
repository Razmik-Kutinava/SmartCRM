"""SBR: open_lead + «открой её» (ref=last) + найди лид → list_leads."""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from core.hermes.rescue import rescue_route
from voice.voice_action import build_voice_action


def test_voice_action_open_lead_by_id_navigates_card():
    va = build_voice_action(
        intent="open_lead",
        slots={"lead_id": 42},
        reply="Открываю лид.",
        agents=["analyst"],
    )
    assert va is not None
    assert va["ui"] == "navigate"
    assert va["route"] == "/leads/42"


def test_voice_action_open_lead_ref_last_payload():
    va = build_voice_action(
        intent="open_lead",
        slots={"ref": "last"},
        reply="Открываю найденный лид.",
        agents=["analyst"],
    )
    assert va is not None
    assert va["ui"] == "navigate"
    assert va["payload"].get("ref") == "last" or va["slots"].get("ref") == "last"


def test_rescue_open_her_is_open_lead_last():
    parsed = rescue_route("открой её")
    assert parsed is not None
    assert parsed["intent"] == "open_lead"
    assert parsed["slots"].get("ref") == "last"


def test_rescue_open_lead_by_company():
    parsed = rescue_route("открой лид Центральный банк Армении")
    assert parsed is not None
    assert parsed["intent"] == "open_lead"
    company = str(parsed["slots"].get("company") or "")
    assert "армен" in company.lower() or "банк" in company.lower()


def test_rescue_find_lead_is_list_leads_with_query():
    parsed = rescue_route("найди лид центральный банк армении")
    assert parsed is not None
    assert parsed["intent"] == "list_leads"
    q = str(parsed["slots"].get("query") or parsed["slots"].get("company") or "").lower()
    assert "банк" in q or "армен" in q
