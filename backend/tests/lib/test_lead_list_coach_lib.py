"""Зеркало frontend/src/lib/leads/leadListCoach.js."""
from __future__ import annotations


def coach_items_for_lead(lead: dict) -> list[dict]:
    rows = lead.get("listCoach")
    if not isinstance(rows, list):
        return []
    return [r for r in rows if r and r.get("text")]


def test_coach_items_for_lead_filters_empty():
    lead = {
        "listCoach": [
            {"code": "a", "text": "Просрочено"},
            {"code": "b", "text": ""},
        ]
    }
    out = coach_items_for_lead(lead)
    assert len(out) == 1
    assert out[0]["text"] == "Просрочено"
