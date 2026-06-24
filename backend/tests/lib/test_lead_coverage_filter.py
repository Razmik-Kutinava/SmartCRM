"""Зеркало фильтра coverage в leadCoverage.js / leadListFilter.js."""


def _matches(lead, filter_id):
    if not filter_id or filter_id == "all":
        return True
    segs = lead.get("coverageSegments") or []
    return filter_id in segs


def test_coverage_filter_bitrix_empty():
    leads = [
        {"id": 1, "coverageSegments": ["bitrix_empty", "no_tasks"]},
        {"id": 2, "coverageSegments": ["bitrix_full"]},
    ]
    out = [l for l in leads if _matches(l, "bitrix_empty")]
    assert [l["id"] for l in out] == [1]


def test_coverage_filter_all():
    leads = [{"id": 1, "coverageSegments": ["empty"]}]
    assert len([l for l in leads if _matches(l, "all")]) == 1


def test_coverage_filter_card_ready():
    leads = [
        {"id": 1, "coverageSegments": ["card_ready", "bitrix_full"]},
        {"id": 2, "coverageSegments": ["bitrix_partial"]},
    ]
    out = [l for l in leads if _matches(l, "card_ready")]
    assert [l["id"] for l in out] == [1]
