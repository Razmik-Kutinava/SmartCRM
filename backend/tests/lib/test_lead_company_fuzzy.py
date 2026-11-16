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


def test_company_match_above_description_long_query():
    """При длинном запросе (>5)company-матч идёт выше description-матча."""
    leads = [
        {"id": 1, "company": "АО СИТРОНИКС", "contact": "", "description": "арман холдинг оборудование", "city": "", "industry": "", "email": "", "phone": ""},
        {"id": 2, "company": "Арман Холдинг", "contact": "", "description": "", "city": "", "industry": "", "email": "", "phone": ""},
    ]
    out = filter_leads_search(leads, "арман холдинг")
    assert out[0]["id"] == 2, f"Ожидался Арман Холдинг первым, получил {out[0]['company']}"
    citro_idx = next(i for i, x in enumerate(out) if x["id"] == 1)
    arman_idx = next(i for i, x in enumerate(out) if x["id"] == 2)
    assert citro_idx > arman_idx, "Ситроникс не должен быть выше Арман Холдинг"


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


def test_arman_company_first_over_description_noise():
    """При поиске 'arman' сначала компания с arman в названии, не шум в description."""
    leads = [
        {
            "id": 1, "company": "АО СИТРОНИКС", "contact": "",
            "description": "arman поставщик оборудования и услуг", "city": "",
            "industry": "", "email": "", "phone": "",
        },
        {
            "id": 2, "company": "Арман Холдинг", "contact": "",
            "description": "", "city": "", "industry": "",
            "email": "arman-holding.com", "phone": "",
        },
    ]
    out = filter_leads_search(leads, "arman")
    assert out[0]["id"] == 2, f"Ожидался Арман Холдинг первым, получил {out[0]['company']}"
    ids = [x["id"] for x in out]
    assert 1 not in ids, "Ситроникс не должен попадать в выдачу по шумному description при коротком запросе"
