"""Нечёткий поиск компаний для /leads/list (зеркало leadCompanyFuzzy.js)."""
from __future__ import annotations

import pytest

from core.lead_company_fuzzy import (
    FUZZY_TOP_N,
    company_name_similarity,
    filter_leads_search,
    normalize_company_query,
    rank_leads_by_company_fuzzy,
)


def test_normalize_company_query():
    assert normalize_company_query("  ВТБ  Банк ") == "втб банк"
    assert normalize_company_query("Ёлка") == "елка"


def test_vtb_typo_ranks_first():
    """STT: «втф банг» → рядом «ВТБ Банк», лучше первым в топ-5."""
    leads = [
        {"id": 1, "company": "Сбербанк"},
        {"id": 2, "company": "ВТБ Банк"},
        {"id": 3, "company": "Альфа-Банк"},
        {"id": 4, "company": "Тинькофф"},
        {"id": 5, "company": "Ромашка"},
        {"id": 6, "company": "Газпромбанк"},
    ]
    ranked = rank_leads_by_company_fuzzy(leads, "втф банг", limit=5)
    assert len(ranked) == 5
    assert ranked[0]["company"] == "ВТБ Банк"
    assert company_name_similarity("втф банг", "ВТБ Банк") > 0.55


def test_fuzzy_top_n_constant():
    assert FUZZY_TOP_N == 5


def test_exact_includes_not_blurred_by_fuzzy():
    """При substring-матче — только exact, без чужих fuzzy-соседей."""
    leads = [
        {"id": 1, "company": "ВТБ Банк", "contact": "", "city": ""},
        {"id": 2, "company": "Сбербанк", "contact": "", "city": ""},
        {"id": 3, "company": "Ромашка", "contact": "втб", "city": ""},
    ]
    out = filter_leads_search(leads, "втб")
    ids = [x["id"] for x in out]
    assert 1 in ids
    assert 3 in ids  # contact includes
    assert 2 not in ids


def test_no_exact_returns_fuzzy_top_even_if_weak():
    """Нет includes → всё равно топ-N, не пустой список."""
    leads = [
        {"id": 1, "company": "Абрикос", "contact": "", "city": ""},
        {"id": 2, "company": "Берёза", "contact": "", "city": ""},
        {"id": 3, "company": "Вишня", "contact": "", "city": ""},
        {"id": 4, "company": "Груша", "contact": "", "city": ""},
        {"id": 5, "company": "Дуб", "contact": "", "city": ""},
        {"id": 6, "company": "Ель", "contact": "", "city": ""},
    ]
    out = filter_leads_search(leads, "квжпщнл")
    assert len(out) == FUZZY_TOP_N
    assert all("company" in x for x in out)


def test_empty_query_keeps_all():
    leads = [{"id": 1, "company": "A"}, {"id": 2, "company": "B"}]
    assert filter_leads_search(leads, "") == leads
    assert filter_leads_search(leads, "   ") == leads


def test_no_spaces_variant():
    leads = [
        {"id": 1, "company": "Эдуард Строй"},
        {"id": 2, "company": "Другая"},
    ]
    ranked = rank_leads_by_company_fuzzy(leads, "эдуардстрой", limit=5)
    assert ranked[0]["id"] == 1
