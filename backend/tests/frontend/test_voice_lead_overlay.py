"""RED/GREEN: голосовое открытие лида — overlay + blur, не только goto."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
FOCUS = ROOT / "frontend" / "src" / "lib" / "voice" / "voiceLeadFocus.js"
ACTION = ROOT / "frontend" / "src" / "lib" / "voice" / "voiceAction.js"
OVERLAY = ROOT / "frontend" / "src" / "components" / "LeadVoiceOverlay.svelte"
LAYOUT = ROOT / "frontend" / "src" / "routes" / "+layout.svelte"


def test_voice_lead_overlay_store_exists():
    text = FOCUS.read_text(encoding="utf-8")
    assert "voiceLeadOverlay" in text
    assert "openVoiceLeadOverlay" in text
    assert "closeVoiceLeadOverlay" in text


def test_open_lead_opens_overlay_not_only_goto():
    text = ACTION.read_text(encoding="utf-8")
    assert "openVoiceLeadOverlay" in text
    assert "open_lead" in text
    # при успехе должен открывать overlay
    assert "openVoiceLeadOverlay(id" in text or "openVoiceLeadOverlay(" in text


def test_lead_voice_overlay_component_blur():
    assert OVERLAY.is_file(), "нет LeadVoiceOverlay.svelte"
    text = OVERLAY.read_text(encoding="utf-8")
    assert "backdrop-blur" in text
    assert "data-testid=\"lead-voice-overlay\"" in text or "lead-voice-overlay" in text


def test_layout_mounts_voice_overlay():
    text = LAYOUT.read_text(encoding="utf-8")
    assert "LeadVoiceOverlay" in text
