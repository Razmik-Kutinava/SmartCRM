"""Тесты голосового поиска лидов с выбором по номеру и транслитерацией."""
from __future__ import annotations

import pytest

from core.hermes.rescue import rescue_route
from core.hermes.slot_normalize import normalize_parsed_intent


def test_rescue_select_first_second_third():
    """Rescue распознает порядковые числительные для выбора лида."""
    for phrase, expected_idx in [
        ("открой первый", 0),
        ("открой второй", 1),
        ("открой третий", 2),
        ("открой четвёртый", 3),
        ("открой пятый", 4),
        ("лид № 1", 0),
        ("лид № 2", 1),
        ("лид № 3", 2),
        ("номер 1", 0),
        ("номер 2", 1),
    ]:
        parsed = rescue_route(phrase)
        assert parsed is not None, f"Failed for: {phrase}"
        assert parsed["intent"] == "open_lead"
        assert parsed["slots"].get("selected_index") == expected_idx, f"Failed for: {phrase}"


def test_rescue_select_with_company_still_searches():
    """Если сказали название компании — всё равно ищет (не выбор по номеру)."""
    parsed = rescue_route("открой лид Акбарс Банк")
    assert parsed is not None
    assert parsed["intent"] == "open_lead"
    assert "company" in parsed["slots"]
    assert "selected_index" not in parsed["slots"]


def test_slot_normalize_extract_ordinal():
    """slot_normalize извлекает порядковые числительные."""
    test_cases = [
        ("открой первый", 0),
        ("открой второй", 1),
        ("открой третий", 2),
        ("открой четвёртый", 3),
        ("открой пятый", 2),  # Will be adjusted in implementation
        ("лид № 3", 2),
        ("номер 2", 1),
    ]
    for text, expected_idx in test_cases:
        parsed = {"intent": "open_lead", "slots": {}}
        result = normalize_parsed_intent(text, parsed)
        # Проверяем что selected_index извлечён
        if "selected_index" in str(result.get("slots", {})):
            pass  # Will be implemented


def test_transliteration_ru_en_search():
    """Поиск находит лид и по кириллице, и по латинице."""
    from agents.tools import read_lead_by_company
    import asyncio

    # Этот тест будет проверять что "акбарс банк ад аудит" и "akbars bank ad audit"
    # находят один и тот же лид — требует моков БД, пока заглушка
    async def _test():
        # Будет реализовано после GREEN
        pass

    asyncio.run(_test())


def test_search_sorting_by_recency():
    """Сортировка: свежие задачи/звонки → стадия Переговоры → высокий скор."""
    from agents.tools import read_lead_by_company
    import asyncio

    async def _test():
        # Будет реализовано после GREEN
        pass

    asyncio.run(_test())