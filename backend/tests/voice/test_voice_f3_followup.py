"""Ф3 Voice: follow-up да/нет/короче, revise-draft API, ops history."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from starlette.testclient import TestClient

from main import app
from voice.approval_followup import parse_voice_followup
from voice.revise_draft import revise_email_draft, _parse_draft_json

import core.auth as auth_module

_TEST_KEY = "pytest-smartcrm-key"
_REPO = Path(__file__).resolve().parents[3]


@pytest.mark.parametrize(
    "text,expected",
    [
        ("да, отправляй", "confirm"),
        ("нет, отмена", "reject"),
        ("переделай короче", "revise"),
        ("сократи текст письма", "revise"),
        ("покажи лиды", None),
        ("", None),
    ],
)
def test_parse_voice_followup(text, expected):
    assert parse_voice_followup(text) == expected


def test_parse_reject_before_confirm():
    assert parse_voice_followup("нет, не отправляй") == "reject"


def test_parse_draft_json_fallback():
    out = _parse_draft_json("not json", "Тема", "A" * 200)
    assert out["subject"] == "Тема"
    assert len(out["body"]) <= 100


@pytest.mark.asyncio
async def test_revise_email_draft_mocked_llm():
    raw = '{"subject":"Коротко","body":"Здравствуйте, кратко."}'
    with patch("core.llm.chat", AsyncMock(return_value=raw)):
        out = await revise_email_draft("Длинная тема", "Очень длинный текст письма " * 20)
    assert out["subject"] == "Коротко"
    assert "кратко" in out["body"].lower()


def test_revise_draft_api():
    auth_module._API_KEY = _TEST_KEY
    with patch(
        "voice.revise_draft.revise_email_draft",
        AsyncMock(return_value={"subject": "S", "body": "Коротко"}),
    ):
        with TestClient(app) as tc:
            r = tc.post(
                "/api/voice/revise-draft",
                json={"subject": "S", "body": "Длинный текст"},
                headers={"X-API-Key": _TEST_KEY},
            )
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True
    assert data["body"] == "Коротко"


def test_revise_draft_api_empty_body_400():
    auth_module._API_KEY = _TEST_KEY
    with TestClient(app) as tc:
        r = tc.post(
            "/api/voice/revise-draft",
            json={"subject": "", "body": ""},
            headers={"X-API-Key": _TEST_KEY},
        )
    assert r.status_code == 400


def test_ops_voice_history_api():
    auth_module._API_KEY = _TEST_KEY
    sample = [
        {
            "id": "abc",
            "text": "покажи лиды",
            "intent": "list_leads",
            "reply": "Ок",
            "source": "text",
            "duration_ms": 120,
            "model": "mock",
            "feedback": None,
            "error": None,
            "ts": 1_700_000_000.0,
        }
    ]
    with patch("core.traces.get_traces", return_value=sample):
        with TestClient(app) as tc:
            r = tc.get("/api/ops/voice/history?limit=5", headers={"X-API-Key": _TEST_KEY})
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 1
    assert data["items"][0]["intent"] == "list_leads"


def test_voice_approve_ui_contract():
    host = (_REPO / "frontend" / "src" / "components" / "VoiceActionHost.svelte").read_text(
        encoding="utf-8"
    )
    assert 'data-testid="voice-approve-hint"' in host
    assert 'data-testid="voice-revise-hint"' in host


def test_voice_followup_js_contract():
    js = (_REPO / "frontend" / "src" / "lib" / "voice" / "voiceFollowup.js").read_text(
        encoding="utf-8"
    )
    assert "parseVoiceFollowup" in js
    assert "tryHandleVoiceFollowup" in js


def test_ops_voice_page_has_history():
    page = (_REPO / "frontend" / "src" / "routes" / "ops" / "voice" / "+page.svelte").read_text(
        encoding="utf-8"
    )
    assert "voice-history-table" in page
    assert "/api/ops/voice/history" in page
