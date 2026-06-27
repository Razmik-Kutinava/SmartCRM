"""Зеркало frontend/src/lib/leads/leadCardCoach.js."""
from __future__ import annotations


def coach_panel_for_code(code: str) -> str:
    c = str(code or "")
    if c.startswith("task_"):
        return "tasks"
    if c in ("needs_enrich", "passport_empty"):
        return "passport"
    if c.startswith("score_"):
        return "card"
    return "stages"


def build_lead_card_coach_items(lead: dict, tasks: list[dict]) -> list[dict]:
    items: list[dict] = []
    if not lead:
        return items
    for h in lead.get("stageHints") or []:
        if h.get("message"):
            items.append(
                {
                    "severity": h.get("severity", "warn"),
                    "code": h.get("code", "hint"),
                    "text": h["message"],
                    "panel": coach_panel_for_code(h.get("code", "")),
                }
            )
    open_tasks = [t for t in tasks if t.get("status") != "done"]
    if not open_tasks and lead.get("stage") != "Проигран":
        items.append(
            {
                "severity": "info",
                "code": "no_tasks",
                "text": "Нет открытых дел",
                "panel": "tasks",
            }
        )
    return items[:8]


def test_coach_panel_routing():
    assert coach_panel_for_code("task_12") == "tasks"
    assert coach_panel_for_code("passport_empty") == "passport"
    assert coach_panel_for_code("stage_stale") == "stages"


def test_build_includes_stage_hints():
    lead = {
        "stage": "Запрос",
        "score": 50,
        "stageHints": [{"severity": "warn", "code": "qual_fields", "message": "Заполни контакт"}],
    }
    items = build_lead_card_coach_items(lead, [])
    assert any("контакт" in i["text"].lower() for i in items)
