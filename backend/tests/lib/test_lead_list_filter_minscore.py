"""minScore в фильтре списка лидов (зеркало leadListFilter.js)."""
from __future__ import annotations


def filter_by_min_score(leads, min_score):
    if min_score is None:
        return leads
    out = []
    for lead in leads:
        sc = lead.get("score")
        try:
            n = float(sc)
        except (TypeError, ValueError):
            continue
        if n >= min_score:
            out.append(lead)
    return out


def test_min_score_filter():
    leads = [
        {"id": 1, "score": 80},
        {"id": 2, "score": 50},
        {"id": 3, "score": None},
    ]
    got = filter_by_min_score(leads, 70)
    assert [x["id"] for x in got] == [1]
