"""Зеркало frontend/src/lib/leads/leadListFilter.js."""
from __future__ import annotations

from core.crm_settings_store import DEFAULT_SETTINGS
from core.lead_priority_tier import lead_priority_tier

PRIORITY_RANK = {"critical": 4, "high": 3, "medium": 2, "low": 1}


def priority_rank(tier_key: str) -> int:
    return PRIORITY_RANK.get(tier_key, 0)


def lead_matches_search(lead: dict, query: str) -> bool:
    q = (query or "").strip().lower()
    if not q:
        return True
    hay = " ".join(
        str(lead.get(k) or "").lower()
        for k in ("company", "contact", "description", "city", "industry", "email", "phone")
    )
    return q in hay


def filter_leads(leads: list[dict], *, search="", filter_stage="all", filter_priority="all", tier_fn) -> list:
    out = []
    for l in leads:
        if filter_stage != "all" and l.get("stage") != filter_stage:
            continue
        if filter_priority != "all" and tier_fn(l).get("key") != filter_priority:
            continue
        if not lead_matches_search(l, search):
            continue
        out.append(l)
    return out


def sort_leads(leads: list[dict], sort_by: str = "score_desc", tier_fn=None) -> list:
    rows = list(leads)

    def score_of(l: dict) -> float:
        try:
            return float(l.get("score") or 0)
        except (TypeError, ValueError):
            return 0.0

    if sort_by == "score_asc":
        return sorted(rows, key=score_of)
    if sort_by == "priority_desc" and tier_fn:

        def key(l: dict):
            t = tier_fn(l)
            return (-priority_rank(t.get("key", "")), -score_of(l))

        return sorted(rows, key=key)
    if sort_by == "company_asc":
        return sorted(rows, key=lambda l: str(l.get("company") or "").lower())
    return sorted(rows, key=score_of, reverse=True)


def _tier_stub(lead: dict) -> dict:
    s = float(lead.get("score") or 0)
    if s >= 85:
        return {"key": "critical"}
    if s >= 70:
        return {"key": "high"}
    if s >= 40:
        return {"key": "medium"}
    return {"key": "low"}


def test_filter_stage_and_search():
    leads = [
        {"id": 1, "company": "Ромашка", "stage": "Новый", "score": 50, "contact": ""},
        {"id": 2, "company": "Сталь", "stage": "Выигран", "score": 90, "contact": ""},
    ]
    out = filter_leads(leads, search="ромаш", filter_stage="Новый", tier_fn=_tier_stub)
    assert [x["id"] for x in out] == [1]


def test_sort_score_desc():
    leads = [{"score": 10}, {"score": 90}, {"score": 50}]
    assert [x["score"] for x in sort_leads(leads)] == [90, 50, 10]


def test_sort_priority_desc():
    leads = [
        {"score": 50, "company": "b"},
        {"score": 90, "company": "a"},
        {"score": 75, "company": "c"},
    ]
    out = sort_leads(leads, "priority_desc", tier_fn=_tier_stub)
    assert [x["score"] for x in out] == [90, 75, 50]


def test_filter_priority_uses_crm_thresholds():
    cfg = {
        "priority_thresholds": DEFAULT_SETTINGS["priority_thresholds"],
        "score_range": DEFAULT_SETTINGS["score_range"],
    }
    tier_fn = lambda l: lead_priority_tier(l.get("score"), cfg)
    leads = [
        {"id": 1, "score": 90, "stage": "Новый", "company": "A"},
        {"id": 2, "score": 50, "stage": "Новый", "company": "B"},
    ]
    out = filter_leads(leads, filter_priority="critical", tier_fn=tier_fn)
    assert [x["id"] for x in out] == [1]
