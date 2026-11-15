"""Тесты TTL-памяти последнего найденного лида для голосового пайплайна."""
from __future__ import annotations

import time
import pytest

from core.agent_memory import (
    set_last_lead,
    get_last_lead,
    clear_last_lead,
)


def test_set_and_get_last_lead():
    session_id = "test-session-1"
    candidates = [
        {"id": 1, "company": "Акбарс Банк"},
        {"id": 2, "company": "Акбарс Инвест"},
        {"id": 3, "company": "Акбарс Страхование"},
    ]
    set_last_lead(session_id, 1, "Акбарс Банк", candidates)

    result = get_last_lead(session_id, max_age_sec=60)
    assert result is not None
    assert result["lead_id"] == 1
    assert result["company"] == "Акбарс Банк"
    assert result["candidates"] == candidates


def test_get_last_lead_expired():
    session_id = "test-session-2"
    candidates = [{"id": 1, "company": "Тест"}]
    set_last_lead(session_id, 1, "Тест", candidates)

    # Имитируем истечение TTL: меняем время в БД на старое
    import sqlite3
    from core.agent_memory import _DB_PATH
    conn = sqlite3.connect(str(_DB_PATH))
    conn.execute(
        "UPDATE voice_last_lead SET ts = ? WHERE session_id = ?",
        (time.time() - 120, session_id),
    )
    conn.commit()
    conn.close()

    result = get_last_lead(session_id, max_age_sec=60)
    assert result is None


def test_clear_last_lead():
    session_id = "test-session-3"
    candidates = [{"id": 1, "company": "Тест"}]
    set_last_lead(session_id, 1, "Тест", candidates)

    clear_last_lead(session_id)

    result = get_last_lead(session_id, max_age_sec=60)
    assert result is None


def test_isolated_sessions():
    """Разные session_id не видят память друг друга."""
    candidates1 = [{"id": 1, "company": "Сессия 1"}]
    candidates2 = [{"id": 2, "company": "Сессия 2"}]
    set_last_lead("sess-A", 1, "Сессия 1", candidates1)
    set_last_lead("sess-B", 2, "Сессия 2", candidates2)

    r1 = get_last_lead("sess-A", max_age_sec=60)
    r2 = get_last_lead("sess-B", max_age_sec=60)

    assert r1["lead_id"] == 1
    assert r2["lead_id"] == 2


def test_clear_on_new_search():
    """Новый поиск (list_leads) очищает память."""
    session_id = "test-session-4"
    candidates_old = [{"id": 1, "company": "Старый"}]
    candidates_new = [{"id": 2, "company": "Новый"}]
    set_last_lead(session_id, 1, "Старый", candidates_old)

    # Симулируем новый поиск
    clear_last_lead(session_id)
    set_last_lead(session_id, 2, "Новый", candidates_new)

    result = get_last_lead(session_id, max_age_sec=60)
    assert result["lead_id"] == 2
    assert result["company"] == "Новый"