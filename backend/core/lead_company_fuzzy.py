"""Нечёткий матч названия компании для поиска лидов (зеркало leadCompanyFuzzy.js)."""
from __future__ import annotations

import difflib
import re
from typing import Any

FUZZY_TOP_N = 5

SHORT_QUERY_LEN = 5

_SEARCH_FIELDS = ("company", "contact", "description", "city", "industry", "email", "phone")

MATCH_PRIORITY = {
    "company": 0,
    "contact": 1,
    "city": 2,
    "industry": 3,
    "email": 4,
    "phone": 5,
    "description": 6,
}


def normalize_company_query(raw: str) -> str:
    text = str(raw or "").strip().lower().replace("ё", "е")
    text = re.sub(r"\s+", " ", text)
    return text


def _compact(text: str) -> str:
    return re.sub(r"\s+", "", text)


def company_name_similarity(query: str, company: str) -> float:
    """0..1 — похожесть запроса к названию компании."""
    q = normalize_company_query(query)
    c = normalize_company_query(company)
    if not q or not c:
        return 0.0
    if q == c:
        return 1.0
    if q in c or c in q:
        return 0.96

    q_c = _compact(q)
    c_c = _compact(c)
    ratios = [
        difflib.SequenceMatcher(None, q, c).ratio(),
        difflib.SequenceMatcher(None, q_c, c_c).ratio(),
    ]

    q_tokens = [t for t in q.split(" ") if t]
    c_tokens = [t for t in c.split(" ") if t]
    if q_tokens and c_tokens:
        token_hits = 0.0
        for qt in q_tokens:
            best = max(
                (difflib.SequenceMatcher(None, qt, ct).ratio() for ct in c_tokens),
                default=0.0,
            )
            token_hits += best
        ratios.append(token_hits / len(q_tokens))

    # общий префикс (без пробелов)
    prefix = 0
    for a, b in zip(q_c, c_c):
        if a != b:
            break
        prefix += 1
    if q_c and prefix:
        ratios.append(0.55 + 0.45 * (prefix / max(len(q_c), len(c_c))))

    return max(ratios)


def rank_leads_by_company_fuzzy(
    leads: list[dict[str, Any]],
    query: str,
    *,
    limit: int = FUZZY_TOP_N,
) -> list[dict[str, Any]]:
    q = normalize_company_query(query)
    if not q:
        return list(leads)[:limit]
    scored: list[tuple[float, int, dict[str, Any]]] = []
    for i, lead in enumerate(leads):
        score = company_name_similarity(q, str(lead.get("company") or ""))
        scored.append((score, i, lead))
    scored.sort(key=lambda t: (-t[0], t[1]))
    n = max(1, int(limit or FUZZY_TOP_N))
    return [t[2] for t in scored[:n]]


def search_match_priority(lead: dict[str, Any], query: str) -> int:
    """Вернуть наивысший приоритет поля, где q есть подстрокой; INF — нет матча."""
    q = normalize_company_query(query)
    if not q:
        return float("inf")
    short = len(q) <= SHORT_QUERY_LEN
    best = float("inf")
    for field in _SEARCH_FIELDS:
        prio = MATCH_PRIORITY[field]
        if short and field in ("description", "phone"):
            continue
        val = str(lead.get(field) or "").lower().replace("ё", "е")
        if q in val:
            best = min(best, prio)
    return best


def lead_matches_search_exact(lead: dict[str, Any], query: str) -> bool:
    return search_match_priority(lead, query) != float("inf")


def filter_leads_search(
    leads: list[dict[str, Any]],
    query: str,
    *,
    fuzzy_limit: int = FUZZY_TOP_N,
) -> list[dict[str, Any]]:
    """Exact/includes сначала; если пусто — топ-N по похожести названия."""
    q = str(query or "").strip()
    if not q:
        return list(leads)
    exact = [l for l in leads if lead_matches_search_exact(l, q)]
    if exact:
        # Релевантность पहले: матч в company ≫ description и т.п.
        exact.sort(key=lambda l: search_match_priority(l, q))
        return exact
    ranked = rank_leads_by_company_fuzzy(leads, q, limit=fuzzy_limit)
    out: list[dict[str, Any]] = []
    for lead in ranked:
        row = dict(lead)
        row["_searchMatch"] = "fuzzy"
        out.append(row)
    return out
