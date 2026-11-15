"""Фронт: «открой третий» берёт N-й лид из запомненного списка (selected_index)."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
FOCUS = ROOT / "frontend" / "src" / "lib" / "voice" / "voiceLeadFocus.js"
ACTION = ROOT / "frontend" / "src" / "lib" / "voice" / "voiceAction.js"
LIST = ROOT / "frontend" / "src" / "routes" / "leads" / "list" / "+page.svelte"
VOICE_ACTION_PY = ROOT / "backend" / "voice" / "voice_action.py"


def test_resolve_uses_selected_index_before_lead_id():
    text = FOCUS.read_text(encoding="utf-8")
    assert "selected_index" in text
    # Порядок: сначала индекс из focus.leads, потом lead_id
    idx_pos = text.find("selected_index")
    lid_pos = text.find("merged.lead_id")
    assert 0 <= idx_pos < lid_pos, "selected_index должен резолвиться раньше lead_id"


def test_resolve_reads_focus_leads_by_index():
    text = FOCUS.read_text(encoding="utf-8")
    assert "focus.leads?.[idx]" in text or "focus.leads[idx]" in text


def test_voice_action_does_not_wipe_focus_list_on_open():
    """После успешного open_lead не вызывать rememberVoiceLeads([one]) — иначе ломается «открой второй»."""
    text = ACTION.read_text(encoding="utf-8")
    open_block_start = text.find("if (intent === 'open_lead')")
    assert open_block_start >= 0
    open_block = text[open_block_start : open_block_start + 900]
    assert "openVoiceLeadOverlay" in open_block
    assert "rememberVoiceLeads([{ id, company }])" not in open_block


def test_list_page_findLead_supports_selected_index():
    text = LIST.read_text(encoding="utf-8")
    assert "selected_index" in text
    assert "rowList[idx]" in text or "rowList[idx]" in text.replace(" ", "")


def test_backend_payload_passes_selected_index():
    text = VOICE_ACTION_PY.read_text(encoding="utf-8")
    assert 'payload["selected_index"]' in text
