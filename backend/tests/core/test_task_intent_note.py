"""Маркер intent:xxx в note задачи."""
from core.task_intent_note import extract_intent_from_note, note_for_display, upsert_intent_in_note


def test_upsert_intent_prepends_marker():
    note = upsert_intent_in_note("Позвонить завтра", "kp_followup")
    assert note.startswith("intent:kp_followup")
    assert "Позвонить завтра" in note


def test_extract_and_display_strip_marker():
    raw = "intent:call\nУточнить детали"
    assert extract_intent_from_note(raw) == "call"
    assert note_for_display(raw) == "Уточнить детали"


def test_upsert_replaces_existing_intent():
    note = upsert_intent_in_note("intent:old\nТекст", "trial_request")
    assert extract_intent_from_note(note) == "trial_request"
    assert "intent:old" not in note


def test_clear_intent_removes_marker():
    note = upsert_intent_in_note("intent:call\nКоммент", None)
    assert extract_intent_from_note(note) is None
    assert note == "Коммент"
