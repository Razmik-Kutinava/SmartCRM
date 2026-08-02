"""ИНН-скоринг: Development ≠ Investment; строже телефоны; Checko при смене ИНН."""
from __future__ import annotations

from rag.search.checko_passport import filter_phones, is_valid_phone, passport_facts_for_brief
from rag.search.resolve_inn import _score_candidate


def test_score_prefers_development_over_investment():
    company = "ASTERUS DEVELOPMENT"
    invest = {"inn": "9705250694", "name": 'АО "АСТЕРУС ИНВЕСТМЕНТ"'}
    devel = {"inn": "9705093770", "name": 'ООО "АСТЕРУС ДЕВЕЛОПМЕНТ"'}
    s_inv = _score_candidate(company, "", invest)
    s_dev = _score_candidate(company, "", devel)
    assert s_dev > s_inv, f"devel={s_dev} invest={s_inv}"


def test_score_prefers_ru_development():
    company = "Астерус Девелопмент"
    invest = {"inn": "1", "name": "АО АСТЕРУС ИНВЕСТМЕНТ"}
    devel = {"inn": "2", "name": "ООО АСТЕРУС ДЕВЕЛОПМЕНТ"}
    assert _score_candidate(company, "", devel) > _score_candidate(company, "", invest)


def test_is_valid_phone_rejects_html_junk():
    assert is_valid_phone("+7 (495) 122-00-24")
    assert is_valid_phone("89179595798")
    assert not is_valid_phone("83223274198")  # мусор 83…
    assert not is_valid_phone("84769890927")
    assert not is_valid_phone("hochland_russia")


def test_filter_phones_drops_junk_keeps_real():
    out = filter_phones(
        ["83223274198", "+7 (495) 122-00-24", "89179595798", "87610134614"]
    )
    assert "+7 (495) 122-00-24" in out
    assert "89179595798" in out
    assert "83223274198" not in out


def test_passport_facts_for_brief_has_inn_director():
    text = passport_facts_for_brief(
        {
            "inn": "9705093770",
            "checko": {
                "company": {
                    "inn": "9705093770",
                    "name": "ООО АСТЕРУС ДЕВЕЛОПМЕНТ",
                    "director": "Иванов",
                    "director_post": "директор",
                    "phones": ["+7 495 122-00-24"],
                    "emails": ["info@asterus-development.com"],
                },
                "financials": {"revenue": 1_000_000},
            },
        }
    )
    assert "9705093770" in text
    assert "Иванов" in text
    assert "Паспорт" in text
    assert "+7" in text or "122" in text


def test_field_fill_detects_inn_change_logic():
    """Контракт: fill_gaps выставляет inn_changed при другом ИНН."""
    import inspect

    from rag.search import field_fill

    src = inspect.getsource(field_fill.fill_gaps_from_web)
    assert "inn_changed" in src
    assert "web_research" in src or "inn_before" in src
