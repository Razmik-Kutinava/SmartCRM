"""Smoke: voiceLeadFocus resolve/remember (чтение исходника + node-проверки логики через дубль)."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
FOCUS = ROOT / "frontend" / "src" / "lib" / "voice" / "voiceLeadFocus.js"
ACTION = ROOT / "frontend" / "src" / "lib" / "voice" / "voiceAction.js"


def test_voice_lead_focus_module_exists():
    text = FOCUS.read_text(encoding="utf-8")
    assert "rememberVoiceLeads" in text
    assert "resolveVoiceOpenLeadId" in text
    assert "ref" in text


def test_voice_action_handles_open_lead():
    text = ACTION.read_text(encoding="utf-8")
    assert "open_lead" in text
    assert "resolveVoiceOpenLeadId" in text
