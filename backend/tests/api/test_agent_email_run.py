"""SBR RED — запуск агентов с карточки лида: стратег падал, аналитик отвечал заглушкой.

1. `agents/strategist.py` не имел `_analyze` → роут ловил ImportError → 500 «Ошибка загрузки агента».
2. В слоты не клался `lead_id` → `analyst.analyze("analyze_lead", ...)` выходил на первой строке.
3. Переписка летела в промпт целиком (5 тредов × 10 писем × 400 симв.) — лишние токены на каждый запуск.
"""
from __future__ import annotations

import pytest


def test_strategist_exposes_analyze():
    """Роут зовёт `from agents.strategist import _analyze` — функция обязана существовать."""
    from agents.strategist import _analyze

    assert callable(_analyze)


@pytest.mark.asyncio
async def test_strategist_analyze_runs_without_other_agents(monkeypatch):
    """Одиночный запуск с карточки: у стратега нет выводов других агентов, но он должен ответить."""
    import agents.strategist as strategist

    captured: dict[str, list] = {}

    async def fake_chat(messages, **kwargs):
        captured["messages"] = messages
        return '{"decision": "Позвонить сегодня", "final_reply": "Звони до 18:00"}'

    monkeypatch.setattr(strategist, "chat", fake_chat)

    out = await strategist._analyze(
        "analyze_lead",
        {"company": "ООО Ромашка", "stage": "Переговоры", "instruction": "нужен план"},
    )

    assert out.get("decision")
    assert "Ромашка" in str(captured["messages"])


def test_email_digest_limits_volume():
    """Дайджест переписки не должен раздувать промпт: лимиты по тредам, письмам и длине."""
    from core.agent_email_context import (
        EMAIL_DIGEST_MAX_CHARS,
        EMAIL_DIGEST_MAX_MESSAGES,
        EMAIL_DIGEST_MAX_THREADS,
        build_email_digest,
    )

    threads = [
        {
            "subject": f"Тема {t}",
            "messages": [
                {"direction": "inbound", "sent_at": "01.08.2026 10:00", "text": "я" * 4000}
                for _ in range(20)
            ],
        }
        for t in range(9)
    ]
    digest = build_email_digest(threads)

    assert digest.count("Тема ") <= EMAIL_DIGEST_MAX_THREADS
    assert len(digest) <= EMAIL_DIGEST_MAX_THREADS * EMAIL_DIGEST_MAX_MESSAGES * (
        EMAIL_DIGEST_MAX_CHARS + 120
    )
    assert "я" * (EMAIL_DIGEST_MAX_CHARS + 1) not in digest


def test_email_digest_keeps_latest_messages():
    """Обрезаем старое, последние сообщения важнее для агента."""
    from core.agent_email_context import build_email_digest

    threads = [
        {
            "subject": "Переговоры",
            "messages": [
                {"direction": "outbound", "sent_at": "", "text": f"письмо {i}"} for i in range(12)
            ],
        }
    ]
    digest = build_email_digest(threads)

    assert "письмо 11" in digest
    assert "письмо 0\n" not in digest


def test_email_digest_empty():
    from core.agent_email_context import build_email_digest

    assert "нет" in build_email_digest([]).lower()


def test_agent_slots_include_lead_id_and_profile():
    """Без lead_id аналитик возвращает «Не указан лид» вместо анализа."""
    from core.agent_email_context import build_agent_slots

    lead = {
        "id": 42,
        "company": "ООО Ромашка",
        "contact": "Иван",
        "industry": "строительство",
        "city": "Москва",
        "budget": "1 млн",
        "stage": "Переговоры",
        "description": "хотят автоматизацию",
        "employees": "150",
        "website": "romashka.ru",
        "score": 61,
        "next_call": "2026-08-05",
    }
    slots = build_agent_slots(lead, email_block="Переписки нет.", task="дай план")

    assert slots["lead_id"] == 42
    assert slots["company"] == "ООО Ромашка"
    assert slots["employees"] == "150"
    assert slots["website"] == "romashka.ru"
    assert slots["score"] == 61
    assert "дай план" in slots["instruction"]


@pytest.mark.asyncio
async def test_run_route_passes_lead_id_to_analyst(client, monkeypatch):
    """Сквозь роут: аналитик получает lead_id и не отвечает заглушкой."""
    import agents.analyst as analyst_pkg

    seen: dict[str, dict] = {}

    async def fake_analyze(intent, slots):
        seen["intent"] = intent
        seen["slots"] = slots
        return {"summary": "ок", "score": 70}

    monkeypatch.setattr(analyst_pkg, "_analyze", fake_analyze)

    created = await client.post(
        "/api/leads",
        json={"company": "ООО Агент Тест", "email": "agent@test.ru", "stage": "Новый"},
    )
    lead_id = created.json()["id"]

    r = await client.post(
        "/api/agents/email/run",
        json={"lead_id": lead_id, "agent": "analyst", "task": "оцени лид"},
    )

    assert r.status_code == 200, r.text
    assert seen["intent"] == "analyze_lead"
    assert seen["slots"]["lead_id"] == lead_id
    assert "Не указан лид" not in str(r.json())


@pytest.mark.asyncio
async def test_run_route_strategist_no_import_error(client, monkeypatch):
    """Стратег с карточки больше не отдаёт «Ошибка загрузки агента»."""
    import agents.strategist as strategist

    async def fake_chat(messages, **kwargs):
        return '{"decision": "Дожать КП", "final_reply": "Отправь КП сегодня"}'

    monkeypatch.setattr(strategist, "chat", fake_chat)

    created = await client.post(
        "/api/leads",
        json={"company": "ООО Стратег Тест", "email": "strat@test.ru", "stage": "КП отправлено"},
    )
    lead_id = created.json()["id"]

    r = await client.post(
        "/api/agents/email/run",
        json={"lead_id": lead_id, "agent": "strategist", "task": "что делать"},
    )

    assert r.status_code == 200, r.text
    assert "Ошибка загрузки агента" not in r.text
    assert r.json()["result"].get("decision")
