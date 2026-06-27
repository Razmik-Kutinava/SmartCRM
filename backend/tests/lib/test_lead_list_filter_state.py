"""Зеркало frontend/src/lib/leads/leadListFilterState.js."""
from __future__ import annotations

import json

LEADS_LIST_FILTER_STORAGE_KEY = "smartcrm_leads_list_filters"

LEADS_LIST_FILTER_DEFAULTS = {
    "search": "",
    "filterStage": "all",
    "filterPriority": "all",
    "filterScoreRisk": "all",
    "filterIndustry": "",
    "filterCity": "",
    "filterEmployeesBand": "all",
    "filterOkvedSection": "all",
    "filterIndustryBucket": "all",
    "filterTaskDue": "all",
    "filterTaskDueDate": "",
    "filterSubscription": "all",
    "filterDeliveryType": "all",
    "filterCoverage": "all",
    "filterManager": "all",
    "filterMinScore": None,
    "groupBy": "none",
    "sortBy": "my_day",
    "collapsedGroupKeys": [],
}

STRING_KEYS = [
    "search",
    "filterStage",
    "filterPriority",
    "filterScoreRisk",
    "filterIndustry",
    "filterCity",
    "filterEmployeesBand",
    "filterOkvedSection",
    "filterIndustryBucket",
    "filterTaskDue",
    "filterTaskDueDate",
    "filterSubscription",
    "filterDeliveryType",
    "filterCoverage",
    "filterManager",
    "groupBy",
    "sortBy",
]


def parse_leads_list_filters(raw):
    if raw is None or not isinstance(raw, dict):
        return None
    out = dict(LEADS_LIST_FILTER_DEFAULTS)
    for key in STRING_KEYS:
        v = raw.get(key)
        if isinstance(v, str):
            out[key] = v
    min_score = raw.get("filterMinScore")
    if min_score is None:
        out["filterMinScore"] = None
    elif isinstance(min_score, (int, float)) and min_score == min_score:
        out["filterMinScore"] = float(min_score)
    elif isinstance(min_score, str) and min_score.strip():
        try:
            out["filterMinScore"] = float(min_score)
        except ValueError:
            pass
    collapsed = raw.get("collapsedGroupKeys")
    if isinstance(collapsed, list):
        out["collapsedGroupKeys"] = [k for k in collapsed if isinstance(k, str)]
    return out


def serialize_leads_list_filters(state: dict) -> dict:
    d = LEADS_LIST_FILTER_DEFAULTS
    collapsed = state.get("collapsedGroupKeys")
    return {
        "search": state.get("search", d["search"]),
        "filterStage": state.get("filterStage", d["filterStage"]),
        "filterPriority": state.get("filterPriority", d["filterPriority"]),
        "filterScoreRisk": state.get("filterScoreRisk", d["filterScoreRisk"]),
        "filterIndustry": state.get("filterIndustry", d["filterIndustry"]),
        "filterCity": state.get("filterCity", d["filterCity"]),
        "filterEmployeesBand": state.get("filterEmployeesBand", d["filterEmployeesBand"]),
        "filterOkvedSection": state.get("filterOkvedSection", d["filterOkvedSection"]),
        "filterIndustryBucket": state.get("filterIndustryBucket", d["filterIndustryBucket"]),
        "filterTaskDue": state.get("filterTaskDue", d["filterTaskDue"]),
        "filterTaskDueDate": state.get("filterTaskDueDate", d["filterTaskDueDate"]),
        "filterSubscription": state.get("filterSubscription", d["filterSubscription"]),
        "filterDeliveryType": state.get("filterDeliveryType", d["filterDeliveryType"]),
        "filterCoverage": state.get("filterCoverage", d["filterCoverage"]),
        "filterManager": state.get("filterManager", d["filterManager"]),
        "filterMinScore": state.get("filterMinScore", d["filterMinScore"]),
        "groupBy": state.get("groupBy", d["groupBy"]),
        "sortBy": state.get("sortBy", d["sortBy"]),
        "collapsedGroupKeys": [k for k in (collapsed or []) if isinstance(k, str)],
    }


def had_saved_leads_list_filters(saved) -> bool:
    return saved is not None


def test_parse_leads_list_filters_manager_and_sort():
    raw = {"filterManager": "Иванов", "sortBy": "score_desc", "filterMinScore": 70}
    out = parse_leads_list_filters(raw)
    assert out is not None
    assert out["filterManager"] == "Иванов"
    assert out["sortBy"] == "score_desc"
    assert out["filterMinScore"] == 70.0
    assert out["filterStage"] == "all"


def test_parse_leads_list_filters_invalid_returns_none():
    assert parse_leads_list_filters(None) is None
    assert parse_leads_list_filters([]) is None


def test_serialize_roundtrip_json():
    state = {
        "filterManager": "Петров",
        "filterTaskDue": "on_date",
        "filterTaskDueDate": "2026-06-27",
        "collapsedGroupKeys": ["stage:Новый", 42],
    }
    blob = json.dumps(serialize_leads_list_filters(state))
    restored = parse_leads_list_filters(json.loads(blob))
    assert restored["filterManager"] == "Петров"
    assert restored["filterTaskDue"] == "on_date"
    assert restored["collapsedGroupKeys"] == ["stage:Новый"]


def test_had_saved_filters():
    assert had_saved_leads_list_filters(None) is False


def test_parse_empty_dict_returns_defaults():
    out = parse_leads_list_filters({})
    assert out is not None
    assert out["filterManager"] == "all"
    assert out["sortBy"] == "my_day"
