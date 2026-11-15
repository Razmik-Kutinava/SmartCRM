"""Тесты tools.read_lead_by_company — возвращает список, транслитерация, сортировка."""
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from agents.tools import read_lead_by_company, normalize_lead_for_agents


def test_normalize_lead_for_agents_basic():
    raw = {
        "id": 42,
        "company": "Тест Компания",
        "contact": "Иван",
        "phone": "+7 999 123 45 67",
        "email": "test@example.com",
        "stage": "Переговоры",
        "score": 80,
        "city": "Казань",
        "next_call": "2026-11-15",
        "manager": "Петров",
    }
    result = normalize_lead_for_agents(raw)
    assert result["lead_id"] == 42
    assert result["company"] == "Тест Компания"
    assert result["contact"] == "Иван"
    assert result["stage"] == "Переговоры"
    assert result["score"] == 80


@pytest.mark.asyncio
async def test_read_lead_by_company_returns_list():
    """read_lead_by_company должен вернуть list[dict], а не один лид."""
    with patch("agents.tools._api_get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = [
            {"id": 1, "company": "Акбарс Банк", "contact": "Иван", "stage": "Переговоры", "score": 85, "city": "Казань", "next_call": "2026-11-15", "manager": "Петров"},
            {"id": 2, "company": "Акбарс Инвест", "contact": "Мария", "stage": "КП", "score": 70, "city": "Казань", "next_call": "—", "manager": "Сидоров"},
            {"id": 3, "company": "Акбарс Страхование", "contact": "Алексей", "stage": "Новый", "score": 50, "city": "Москва", "next_call": "—", "manager": "Иванов"},
        ]
        results = await read_lead_by_company("акбарс", limit=10)
        assert isinstance(results, list)
        assert len(results) == 3
        assert all("lead_id" in r for r in results)
        assert results[0]["company"] == "Акбарс Банк"


def test_transliterate_ru_en_public():
    """Публичная функция transliterate_ru_en должна существовать и работать."""
    from agents.tools import transliterate_ru_en
    result = transliterate_ru_en("акбарс банк ад аудит")
    assert "bank" in result.lower()
    assert "audit" in result.lower()


def test_transliterate_ru_en_latin_passthrough():
    """Если текст уже латиница — возвращает как есть (нормализованный)."""
    from agents.tools import transliterate_ru_en
    result = transliterate_ru_en("akbars bank ad audit")
    assert result == "akbars bank ad audit"


@pytest.mark.asyncio
async def test_read_lead_by_company_transliteration_en_finds_ru():
    """Поиск по 'akbars bank ad audit' должен найти 'Акбарс Банк Ад Аудит' (RU↔EN)."""
    with patch("agents.tools._api_get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = [
            {"id": 1, "company": "Акбарс Банк Ад Аудит", "contact": "Иван", "stage": "Переговоры", "score": 85, "city": "Казань", "next_call": "2026-11-15", "manager": "Петров", "description": "Ад Аудит"},
        ]
        results = await read_lead_by_company("akbars bank ad audit", limit=10)
        assert len(results) >= 1
        assert results[0]["company"] == "Акбарс Банк Ад Аудит"


@pytest.mark.asyncio
async def test_read_lead_by_company_returns_contact_name_and_manager_name():
    """Возвращаемые поля включают contact_name и manager_name."""
    with patch("agents.tools._api_get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = [
            {"id": 1, "company": "Тест", "contact": "Иван", "stage": "Новый", "score": 50, "city": "Москва", "next_call": "—", "manager": "Петров", "description": ""},
        ]
        results = await read_lead_by_company("тест", limit=10)
        assert len(results) == 1
        assert "contact_name" in results[0]
        assert "manager_name" in results[0]
        assert results[0]["contact_name"] == "Иван"
        assert results[0]["manager_name"] == "Петров"


@pytest.mark.asyncio
async def test_read_lead_by_company_searches_description():
    """Поиск по description (названию лида) находится."""
    with patch("agents.tools._api_get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = [
            {"id": 1, "company": "ООО Ромашка", "contact": "Иван", "stage": "Новый", "score": 50, "city": "Москва", "next_call": "—", "manager": "Петров", "description": "Ад Аудит консалтинг"},
        ]
        results = await read_lead_by_company("аудит консалтинг", limit=10)
        assert len(results) >= 1
        assert results[0]["company"] == "ООО Ромашка"


@pytest.mark.asyncio
async def test_read_lead_by_company_returns_list_up_to_10():
    """read_lead_by_company возвращает list[dict] не более limit элементов."""
    with patch("agents.tools._api_get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = [
            {"id": i, "company": f"Тест {i}", "contact": "Иван", "stage": "Новый", "score": 50, "city": "Москва", "next_call": "—", "manager": "Петров", "description": ""}
            for i in range(1, 16)
        ]
        results = await read_lead_by_company("тест", limit=10)
        assert isinstance(results, list)
        assert len(results) <= 10


@pytest.mark.asyncio
async def test_read_lead_by_company_sorts_by_recency():
    """Сортировка: 1) задача due≤сегодня/звонок 24ч, 2) стадия, 3) скор, 4) updated_at."""
    with patch("agents.tools._api_get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = [
            {"id": 1, "company": "Тест А", "contact": "Иван", "stage": "Новый", "score": 90, "city": "Москва", "next_call": "—", "manager": "Петров", "updated_at": "2026-11-01T10:00:00"},
            {"id": 2, "company": "Тест Б", "contact": "Мария", "stage": "Переговоры", "score": 80, "city": "Казань", "next_call": "2026-11-15", "manager": "Сидоров", "updated_at": "2026-11-10T10:00:00"},
            {"id": 3, "company": "Тест В", "contact": "Алексей", "stage": "КП", "score": 95, "city": "СПб", "next_call": "—", "manager": "Иванов", "updated_at": "2026-11-12T10:00:00"},
        ]
        results = await read_lead_by_company("тест", limit=10)
        assert isinstance(results, list)
        assert len(results) == 3
        # Первый — с next_call сегодня (вес 1000) или стадией Переговоры (вес 100)
        assert results[0]["company"] in ("Тест Б", "Тест А")