"""Голосовые команды email: list_emails, write_email, send_email."""
from __future__ import annotations

import os
import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from core.hermes.rescue import rescue_route
from core.hermes.slot_normalize import normalize_parsed_intent
from voice.voice_action import build_voice_action


def test_rescue_list_emails_inbox():
    raw = rescue_route("открой входящие письма")
    assert raw is not None
    out = normalize_parsed_intent("открой входящие письма", raw)
    assert out["intent"] == "list_emails"
    assert out["module"] == "email"
    assert out["ui_action"] == "navigate"


def test_rescue_list_emails_sent():
    raw = rescue_route("покажи отправленные письма")
    assert raw is not None
    assert raw["intent"] == "list_emails"
    assert raw["slots"]["filter"] == "sent"


def test_rescue_write_email_slots():
    raw = rescue_route("напиши письмо клиенту Ромашка про автоматизацию")
    assert raw is not None
    assert raw["intent"] == "write_email"
    assert raw["slots"].get("company") or raw["slots"].get("target")


def test_rescue_send_email_target():
    raw = rescue_route("отправь письмо на client@example.com")
    assert raw is not None
    assert raw["intent"] == "send_email"
    assert raw["slots"]["target"] == "client@example.com"


def test_list_emails_navigate_payload():
    va = build_voice_action(
        intent="list_emails",
        slots={"filter": "sent"},
        reply="Открываю почту.",
        agents=["marketer"],
        module="email",
        ui_action="navigate",
    )
    assert va["route"] == "/email"
    assert va["payload"]["folder"] == "sent"


def test_write_email_modal_route():
    va = build_voice_action(
        intent="write_email",
        slots={"target": "ACME"},
        reply="Черновик готов.",
        agents=["marketer"],
        module="email",
        ui_action="modal",
        agent_result={
            "marketer_output": {
                "first_email": {"subject": "Re: Тест", "body": "Текст"},
                "summary": "ok",
            }
        },
    )
    assert va["ui"] == "modal"
    assert va["route"] == "/email"
    assert va["payload"]["draft_email"]["body"] == "Текст"
    assert "send" in va["payload"]["actions"]


@pytest.mark.asyncio
async def test_orchestrator_write_email_uses_marketer():
    from agents.orchestrator import run_agents

    mock_out = {
        "summary": "Готово",
        "first_email": {"subject": "Привет", "body": "Текст письма"},
    }
    with patch("agents.marketer._analyze", new_callable=AsyncMock, return_value=mock_out):
        result = await run_agents(
            intent="write_email",
            slots={"target": "ACME", "topic": "CRM", "reply": "Пишу."},
            hermes_agents=["marketer"],
        )
    assert result["agents_ran"] is True
    assert result["marketer_output"]["first_email"]["subject"] == "Привет"


def test_email_page_voice_context_store():
    repo = Path(__file__).resolve().parents[3]
    page = repo / "frontend" / "src" / "routes" / "email" / "+page.svelte"
    action = repo / "frontend" / "src" / "lib" / "voice" / "voiceAction.js"
    text = page.read_text(encoding="utf-8")
    assert "voiceEmailContext" in text
    assert "voiceEmailContext.subscribe" in text
    assert "voiceEmailContext" in action.read_text(encoding="utf-8")


def test_voice_modal_send_queues_approve():
    host = Path(__file__).resolve().parents[3] / "frontend" / "src" / "components" / "VoiceActionHost.svelte"
    text = host.read_text(encoding="utf-8")
    assert "queueSendEmailApprove" in text
    assert "voiceApprove.set" in text
