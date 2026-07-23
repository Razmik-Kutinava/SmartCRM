"""Тех. спец (tech_specialist) на карточке лида — UI + email/run."""
from __future__ import annotations

from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
_LEAD_CARD = _REPO / "frontend" / "src" / "routes" / "leads" / "[id]" / "+page.svelte"
_HUB = _REPO / "frontend" / "src" / "lib" / "leads" / "leadHubPreview.js"
_AGENT_EMAIL = _REPO / "backend" / "api" / "routes" / "agent_email.py"


def test_lead_card_agent_list_has_tech_specialist():
    text = _LEAD_CARD.read_text(encoding="utf-8")
    assert "tech_specialist" in text
    # внутри AGENT_LIST
    block = text.split("const AGENT_LIST", 1)[1].split("];", 1)[0]
    assert "tech_specialist" in block
    assert "Тех" in block or "тех" in block.lower()


def test_agent_email_run_supports_tech_specialist():
    text = _AGENT_EMAIL.read_text(encoding="utf-8")
    assert 'body.agent == "tech_specialist"' in text or "body.agent == 'tech_specialist'" in text
    assert "tech_specialist" in text and "_analyze" in text


def test_hub_agents_preview_mentions_tech():
    text = _HUB.read_text(encoding="utf-8")
    agents = text.split("agents:", 1)[1].split("},", 1)[0] if "agents:" in text else text
    assert "тех" in agents.lower() or "tech" in agents.lower()
