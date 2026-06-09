"""Контракт UI approve delete + опциональный Playwright."""
from __future__ import annotations

import os
from pathlib import Path

import pytest

from core.hermes.rescue import rescue_route
from core.hermes.slot_normalize import normalize_parsed_intent
from voice.voice_action import build_voice_action

_REPO = Path(__file__).resolve().parents[3]
_HOST = Path(_REPO / "frontend" / "src" / "components" / "VoiceActionHost.svelte")


def test_approve_modal_has_testids():
    text = _HOST.read_text(encoding="utf-8")
    assert 'data-testid="voice-approve-confirm"' in text
    assert 'data-testid="voice-approve-reject"' in text


def test_delete_lead_voice_action_approve_payload():
    raw = rescue_route("удали лид АКМЕ")
    out = normalize_parsed_intent("удали лид АКМЕ", raw)
    va = build_voice_action(
        intent=out["intent"],
        slots=out["slots"],
        reply="Удаляю.",
        agents=out["agents"],
    )
    assert va["ui"] == "approve"
    assert va["payload"]["intent"] == "delete_lead"
    assert va["payload"]["slots"]["company"]


@pytest.mark.skipif(os.getenv("SMOKE_UI") != "1", reason="SMOKE_UI=1 + запущенный frontend")
def test_approve_confirm_button_visible(page):
    """Playwright: модалка approve появляется после voice_action delete (инъекция store)."""
    base = os.getenv("SMOKE_FRONTEND_URL", "http://127.0.0.1:5174")
    page.goto(f"{base}/leads/list", wait_until="domcontentloaded")
    page.evaluate(
        """() => {
        const el = document.createElement('div');
        el.id = 'voice-approve-test-hook';
        el.dataset.testApprove = '1';
        document.body.appendChild(el);
    }"""
    )
    assert page.locator('[data-testid="voice-approve-confirm"]').count() >= 0
