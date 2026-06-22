"""Зеркало groupLeads из frontend/src/lib/leads/leadListFilter.js."""
from __future__ import annotations

EMPTY = "__empty__"


def group_key(lead: dict, group_by: str) -> str:
    if group_by == "okved_section":
        return str(lead.get("okvedSection") or "").strip() or EMPTY
    if group_by == "employees_band":
        return str(lead.get("employeesBand") or "").strip() or EMPTY
    if group_by == "stage":
        return str(lead.get("stage") or "").strip() or EMPTY
    return ""


def group_leads(leads: list[dict], group_by: str = "none") -> list[dict]:
    if not group_by or group_by == "none":
        return [{"key": "", "label": "", "leads": leads, "count": len(leads)}]
    buckets: dict[str, list] = {}
    for l in leads:
        k = group_key(l, group_by)
        buckets.setdefault(k, []).append(l)
    keys = sorted(buckets.keys(), key=lambda x: (x == EMPTY, x))
    out = []
    for k in keys:
        rows = buckets[k]
        label = k
        if k == EMPTY:
            label = "Без ОКВЭД" if group_by == "okved_section" else k
        elif group_by == "okved_section":
            label = f"Секция {k}"
        out.append({"key": k, "label": label, "leads": rows, "count": len(rows)})
    return out


def test_group_by_okved_section():
    leads = [
        {"id": 1, "okvedSection": "62"},
        {"id": 2, "okvedSection": "10"},
        {"id": 3, "okvedSection": "62"},
        {"id": 4},
    ]
    groups = group_leads(leads, "okved_section")
    assert len(groups) == 3
    assert groups[0]["key"] == "10"
    assert groups[0]["count"] == 1
    sec62 = next(g for g in groups if g["key"] == "62")
    assert sec62["count"] == 2
    empty = next(g for g in groups if g["key"] == EMPTY)
    assert empty["count"] == 1


def test_group_by_employees_band():
    leads = [
        {"id": 1, "employeesBand": "1-50"},
        {"id": 2, "employeesBand": "1000+"},
    ]
    groups = group_leads(leads, "employees_band")
    assert len(groups) == 2
    assert groups[0]["key"] == "1-50"
