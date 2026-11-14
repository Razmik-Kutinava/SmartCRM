"""SBR RED — синтез 5 агентов на карточке лида.

Тест проверяет:
1. Контекст собирается (build_agent_slots + веб-исследование / паспорт / задачи / переписка)
2. 5 агентов вызываются (analyst, economist, marketer, tech_specialist, strategist)
3. Есть `next_action` + `missing_data` в итоговом ответе для UI
4. Результат возвращается в структурированном виде
"""
from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_agent_synthesis_collects_context_and_runs_5_agents(monkeypatch):
    """Синтез собирает слоты, вызывает 5 агентов, возвращает next_action + missing_data."""
    from agents import agent_synthesis  # новый модуль — пока не существует

    captured_calls: dict[str, list] = {"agents": []}

    async def fake_analyze(agent_name: str, intent: str, slots: dict):
        captured_calls["agents"].append(agent_name)
        # Каждый агент возвращает свой JSON с минимальными полями
        if agent_name == "analyst":
            return {
                "summary": "Лид теплый, скор 60",
                "score": 60,
                "stage_view": "Переговоры",
                "bant": {"budget": "есть", "authority": "ЛПР известен", "need": "высокая", "timeline": "этот месяц"},
                "next_steps": ["позвонить", "отправить КП"],
                "missing_data": ["история покупок"],
            }
        if agent_name == "economist":
            return {
                "summary": "Бюджет ~1М, сегмент SMB",
                "budget_estimate": "1 000 000 ₽",
                "deal_segment": "smb",
                "ltv_estimate": "3 000 000 ₽ (чек × 3 года × 0.8)",
                "deal_probability_pct": 55,
                "missing_data": ["точная выручка"],
            }
        if agent_name == "marketer":
            return {
                "summary": "Крючок: автоматизация смет",
                "value_hook": "сократит 30% времени на сметы",
                "product_to_offer": "SmartCRM Estimate",
                "first_email": {"subject": "Автоматизация смет для ООО Ромашка", "body": "Иван, увидели что вы..."},
                "missing_data": ["конкуренты в сделке"],
            }
        if agent_name == "tech_specialist":
            return {
                "summary": "Стек: 1С, Excel, сайт на Bitrix",
                "likely_stack": ["1С", "Excel", "Bitrix"],
                "portfolio_fit": [{"product": "SmartCRM Integration", "why": "API 1С", "fit": "high"}],
                "missing_data": ["доступ к тестовому контуру"],
            }
        if agent_name == "strategist":
            return {
                "decision": "Позвонить Ивану до 18:00 и уточнить бюджет на КП",
                "priority": "high",
                "urgency": "today",
                "next_action": "Позвонить Ивану до 18:00 и уточнить бюджет на КП",
                "rationale": "Скор 60, есть бюджет, нужен КП — звоним сегодня",
                "final_reply": "Звони Ивану сегодня до 18:00, уточни бюджет и отправь КП.",
                "missing_data": ["история покупок", "конкуренты", "доступ к тестовому контуру"],
                "missing_from_agents": [],
            }
        return {}

    monkeypatch.setattr(agent_synthesis, "_run_agent", fake_analyze)

    # Входные слоты (как приходит из build_agent_slots)
    slots = {
        "lead_id": 42,
        "company": "ООО Ромашка",
        "contact": "Иван Петров",
        "email": "ivan@romashka.ru",
        "phone": "+7 495 123-45-67",
        "industry": "Строительство",
        "city": "Москва",
        "stage": "Переговоры",
        "employees": "150",
        "website": "romashka.ru",
        "score": 60,
        "next_call": "2026-11-15",
        "description": "Хотят автоматизацию смет",
        "web_research_brief": "Веб-исследование: компания занимается строительством, 150 чел, сайт на Bitrix",
        "tech_stack_brief": "1С, Excel, Bitrix",
        "financials": {"revenue": "500M"},
        "context_gaps": ["история покупок", "конкуренты в сделке", "доступ к тестовому контуру"],
    }

    # Вызов синтеза (функция пока не существует — тест упадёт)
    result = await agent_synthesis.run_synthesis(slots)

    # Проверки
    assert "analyst" in captured_calls["agents"]
    assert "economist" in captured_calls["agents"]
    assert "marketer" in captured_calls["agents"]
    assert "tech_specialist" in captured_calls["agents"]
    assert "strategist" in captured_calls["agents"]
    assert len(captured_calls["agents"]) == 5

    # Единый совет: 1-3 шага простым языком
    assert result.get("next_action")
    assert "Позвонить" in result["next_action"]
    assert result.get("final_reply")
    assert "звони" in result["final_reply"].lower()

    # Блок missing_data для суфлёра на карточке
    missing = result.get("missing_data") or []
    assert isinstance(missing, list)
    assert len(missing) >= 3
    assert any("история" in m for m in missing)
    assert any("конкурент" in m for m in missing)
    assert any("доступ" in m for m in missing)

    # Рекомендация / priority / urgency
    assert result.get("priority") in ("high", "medium", "low")
    assert result.get("urgency") in ("today", "this_week", "next_week", "nurture")


@pytest.mark.asyncio
async def test_agent_synthesis_works_with_minimal_context(monkeypatch):
    """Даже при минимальном контексте синтез возвращает решение + missing_data."""
    from agents import agent_synthesis

    captured = {"agents": []}

    async def fake_analyze(agent_name: str, intent: str, slots: dict):
        captured["agents"].append(agent_name)
        return {"summary": f"{agent_name} ok", "missing_data": []}

    monkeypatch.setattr(agent_synthesis, "_run_agent", fake_analyze)

    minimal_slots = {
        "lead_id": 99,
        "company": "Тест Лид",
        "stage": "Новый",
        "context_gaps": ["всё"],
    }

    result = await agent_synthesis.run_synthesis(minimal_slots)

    assert len(captured["agents"]) == 5
    assert result.get("next_action")
    assert result.get("missing_data")