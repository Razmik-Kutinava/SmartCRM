"""Контракт voice_action UI (Ф2 Voice Layer)."""
from __future__ import annotations

from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
_VOICE_JS = _REPO / "frontend" / "src" / "lib" / "voice" / "voiceAction.js"
_HOST = _REPO / "frontend" / "src" / "components" / "VoiceActionHost.svelte"
_LAYOUT = _REPO / "frontend" / "src" / "routes" / "+layout.svelte"


def test_voice_action_js_exports():
    text = _VOICE_JS.read_text(encoding="utf-8")
    for sym in (
        "voiceAnalyticsContext",
        "voiceSearchQuery",
        "registerVoiceApproveHandler",
        "voiceHighlight",
        "voiceToast",
    ):
        assert sym in text


def test_layout_handles_voice_action():
    text = _LAYOUT.read_text(encoding="utf-8")
    assert "voice_action" in text
    assert "registerVoiceApproveHandler" in text
    assert "voice-highlight" in text


def test_voice_modal_rag_section():
    text = _HOST.read_text(encoding="utf-8")
    assert "rag_answer" in text
    assert 'data-testid="voice-modal"' in text


def test_voice_modal_tender_section():
    text = _HOST.read_text(encoding="utf-8")
    assert "payload.tender" in text


def test_voice_modal_synthesis_section():
    text = _HOST.read_text(encoding="utf-8")
    assert 'data-testid="voice-synthesis"' in text
    assert "payload.synthesis" in text


def test_analytics_voice_context_marker():
    path = _REPO / "frontend" / "src" / "routes" / "leads" / "analytics" / "+page.svelte"
    text = path.read_text(encoding="utf-8")
    assert "voice-analytics-context" in text
    assert "voiceAnalyticsContext" in text
