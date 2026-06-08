"""Зеркало frontend/src/lib/leads/funnelDnD.js."""
from __future__ import annotations

FUNNEL_DRAG_MIME = "application/x-smartcrm-lead-id"
STAGE_BORDER = {
    "Новый": "border-gray-700",
    "Квалифицирован": "border-blue-800",
    "КП отправлено": "border-yellow-800",
    "Переговоры": "border-indigo-800",
    "Выигран": "border-green-800",
    "Проигран": "border-red-900",
}


def group_leads_by_stage(leads: list[dict], stages: list[str]) -> dict[str, list]:
    m = {s: [] for s in stages}
    fallback = stages[0] if stages else "Новый"
    for l in leads:
        s = l.get("stage")
        if s not in m:
            s = fallback
        m[s].append(l)
    return m


def move_lead_stage(leads: list[dict], lead_id: int, new_stage: str) -> list[dict]:
    lid = int(lead_id)
    return [{**l, "stage": new_stage} if l["id"] == lid else l for l in leads]


def stage_color(stage: str) -> str:
    return STAGE_BORDER.get(stage, "border-gray-700")


def test_group_leads_unknown_stage_goes_to_first_column():
    stages = ["Новый", "Выигран"]
    grouped = group_leads_by_stage(
        [{"id": 1, "stage": "Фантазия"}, {"id": 2, "stage": "Выигран"}],
        stages,
    )
    assert [x["id"] for x in grouped["Новый"]] == [1]
    assert [x["id"] for x in grouped["Выигран"]] == [2]


def test_move_lead_stage_updates_one():
    leads = [{"id": 1, "stage": "Новый"}, {"id": 2, "stage": "Новый"}]
    out = move_lead_stage(leads, 2, "Переговоры")
    assert out[0]["stage"] == "Новый"
    assert out[1]["stage"] == "Переговоры"


def test_stage_color_fallback():
    assert stage_color("Выигран") == "border-green-800"
    assert stage_color("???") == "border-gray-700"
