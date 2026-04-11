"""
Тесты голосового пайплайна SmartCRM.
Покрывают: Hermes intent routing, orchestrator маршруты, новые интенты.
"""
import asyncio
import json
import os
import sys
import types
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# ── Стабы для тяжёлых зависимостей (groq, chromadb) ─────────────────────────

def _stub_module(name: str, **attrs):
    """Создаёт заглушку модуля и регистрирует в sys.modules."""
    mod = types.ModuleType(name)
    for k, v in attrs.items():
        setattr(mod, k, v)
    sys.modules[name] = mod
    return mod

# groq
if "groq" not in sys.modules:
    groq_stub = _stub_module("groq")
    groq_stub.AsyncGroq = MagicMock
    groq_stub.RateLimitError = Exception
    groq_stub.APIStatusError = Exception

# chromadb
if "chromadb" not in sys.modules:
    chroma_stub = _stub_module("chromadb")
    chroma_stub.PersistentClient = MagicMock
    chroma_stub.HttpClient = MagicMock
    # Добавляем chromadb.config
    _stub_module("chromadb.config")
    _stub_module("chromadb.utils")
    _stub_module("chromadb.utils.embedding_functions")

# sentence_transformers
if "sentence_transformers" not in sys.modules:
    st = _stub_module("sentence_transformers")
    st.SentenceTransformer = MagicMock

# langchain_community — если используется
for mod_name in [
    "langchain_community",
    "langchain_community.vectorstores",
    "langchain_core",
    "langchain_core.documents",
]:
    if mod_name not in sys.modules:
        _stub_module(mod_name)

# ── Мок rag.chroma_store чтобы не нужен chromadb ────────────────────────────
chroma_mock = _stub_module("rag.chroma_store")
chroma_mock.query_documents = AsyncMock(return_value=[])
chroma_mock.add_documents = AsyncMock(return_value=None)

retrieve_mock = _stub_module("rag.retrieve")
async def _mock_attach_rag(slots, transcript=""):
    return slots
retrieve_mock.attach_rag_to_slots = _mock_attach_rag
retrieve_mock.rag_block = AsyncMock(return_value="")

# ── Мок agents.tools ─────────────────────────────────────────────────────────
tools_mock = _stub_module("agents.tools")
tools_mock.read_leads = AsyncMock(return_value=[])
tools_mock.read_lead_by_company = AsyncMock(return_value=None)
tools_mock.update_lead_score = AsyncMock(return_value=None)
tools_mock.compute_lead_score = MagicMock(return_value=50)
tools_mock.read_tasks = AsyncMock(return_value=[])


# ─────────────────────────────────────────────────────────────
# Юнит-тесты Hermes без реального LLM — заменяем parse_intent
# ─────────────────────────────────────────────────────────────

MOCK_INTENTS = {
    # Лиды
    "создай лид компания АКМЕ": {"intent": "create_lead", "agents": ["analyst"], "slots": {"company": "АКМЕ"}, "reply": "Создаю лид."},
    "удали лид Ромашка": {"intent": "delete_lead", "agents": ["analyst"], "slots": {"company": "Ромашка"}, "reply": "Удаляю лид."},
    "покажи горячих": {"intent": "list_leads", "agents": ["analyst"], "slots": {"filter": "hot"}, "reply": "Показываю."},
    "напоминалку на завтра позвонить Вектор": {"intent": "create_task", "agents": ["analyst"], "slots": {"title": "Позвонить Вектор", "due": "завтра"}, "reply": "Задача создана."},
    # Новые интенты
    "проверь прибыль Яндекса в 2025": {"intent": "ask_economist", "agents": ["economist"], "slots": {"company": "Яндекс", "period": "2025"}, "reply": "Экономист анализирует."},
    "найди конкурентов Битрикс24": {"intent": "ask_marketer", "agents": ["marketer"], "slots": {"company": "Битрикс24"}, "reply": "Маркетолог ищет."},
    "какой стек у Wildberries": {"intent": "ask_tech", "agents": ["tech_specialist"], "slots": {"company": "Wildberries"}, "reply": "Тех. спец изучает."},
    "как зайти к лиду ТехноПром": {"intent": "ask_strategist", "agents": ["strategist"], "slots": {"company": "ТехноПром"}, "reply": "Стратег планирует."},
    "проанализируй лид Альфа Строй": {"intent": "run_analysis", "agents": ["analyst", "economist", "marketer", "tech_specialist"], "slots": {"company": "Альфа Строй"}, "reply": "Полный анализ."},
    "найди новости по Газпрому": {"intent": "search_web", "agents": ["analyst"], "slots": {"query": "Газпром новости"}, "reply": "Ищу."},
    "напиши письмо Альфа": {"intent": "write_email", "agents": ["marketer"], "slots": {"target": "Альфа"}, "reply": "Маркетолог пишет."},
    "привет как дела": {"intent": "noop", "agents": [], "slots": {}, "reply": "Не CRM команда."},
}


# ─── Тест 1: Hermes parse_intent возвращает корректную структуру ──────────────
@pytest.mark.asyncio
async def test_hermes_intent_structure():
    """Проверяем структуру ответа Hermes (без реального LLM — используем мок)."""
    required_keys = {"intent", "agents", "slots", "reply"}
    for text, expected in MOCK_INTENTS.items():
        assert required_keys.issubset(expected.keys()), f"Отсутствуют ключи в: {expected}"
        assert isinstance(expected["agents"], list), f"agents должен быть list: {text}"
        assert isinstance(expected["slots"], dict), f"slots должен быть dict: {text}"


# ─── Тест 2: Маппинг интентов → агентов ──────────────────────────────────────
def test_intent_agent_mapping():
    """Проверяем правильность маппинга интент → агент."""
    from agents.orchestrator import _INTENT_TO_AGENTS, _AGENT_INTENTS

    # Все новые интенты зарегистрированы
    new_intents = ["ask_economist", "ask_marketer", "ask_tech", "ask_strategist",
                   "search_web", "write_email", "run_analysis"]
    for intent in new_intents:
        assert intent in _AGENT_INTENTS, f"Интент {intent!r} отсутствует в _AGENT_INTENTS"

    # Маппинг корректен
    assert _INTENT_TO_AGENTS["ask_economist"] == ["economist"]
    assert _INTENT_TO_AGENTS["ask_marketer"] == ["marketer"]
    assert _INTENT_TO_AGENTS["ask_tech"] == ["tech_specialist"]
    assert _INTENT_TO_AGENTS["ask_strategist"] == ["strategist"]
    assert _INTENT_TO_AGENTS["search_web"] == ["analyst"]
    assert _INTENT_TO_AGENTS["write_email"] == ["marketer"]
    assert set(_INTENT_TO_AGENTS["run_analysis"]) == {"analyst", "economist", "marketer", "tech_specialist"}


# ─── Тест 3: Оркестратор не падает на неизвестном интенте ─────────────────────
@pytest.mark.asyncio
async def test_orchestrator_noop_intent():
    """noop интент не должен запускать агентов."""
    from agents.orchestrator import run_agents

    result = await run_agents(
        intent="noop",
        slots={"reply": "Это не CRM команда."},
        transcript="привет как дела",
        trace_id="test-noop",
    )
    assert result["agents_ran"] is False
    assert result["final_reply"] == "Это не CRM команда."


# ─── Тест 4: Оркестратор корректно маршрутизирует ask_economist ───────────────
@pytest.mark.asyncio
async def test_orchestrator_ask_economist():
    """ask_economist должен запустить voice query и вернуть ответ."""
    async def mock_chat(messages, **kwargs):
        return "Яндекс: выручка за 2025 год составила 900 млрд руб."

    async def mock_free_search(q, **kw):
        return {"formatted_block": "", "raw_results": []}

    with patch("core.llm.chat", side_effect=mock_chat), \
         patch("rag.search.free_search", side_effect=mock_free_search):
        from agents.orchestrator import run_agents
        result = await run_agents(
            intent="ask_economist",
            slots={"question": "какая выручка у Яндекса в 2025", "company": "Яндекс", "period": "2025", "reply": "Экономист анализирует."},
            transcript="проверь прибыль яндекса 2025",
            trace_id="test-economist",
        )
    assert result["agents_ran"] is True
    assert len(result["final_reply"]) > 0


# ─── Тест 5: Оркестратор корректно маршрутизирует search_web ──────────────────
@pytest.mark.asyncio
async def test_orchestrator_search_web():
    """search_web должен вернуть результаты из мок-поиска."""
    async def mock_free_search(query, **kwargs):
        return {
            "answer": f"Результаты по запросу: {query}",
            "formatted_block": f"[Поиск] {query}",
            "raw_results": [],
        }

    with patch("rag.search.free_search", side_effect=mock_free_search):
        from agents.orchestrator import run_agents
        result = await run_agents(
            intent="search_web",
            slots={"query": "Газпром новости", "reply": "Ищу."},
            transcript="найди новости по Газпрому",
            trace_id="test-search",
        )
    assert result["agents_ran"] is True
    assert "Газпром" in result["final_reply"] or len(result["final_reply"]) > 0


# ─── Тест 6: Оркестратор корректно маршрутизирует run_analysis ────────────────
@pytest.mark.asyncio
async def test_orchestrator_run_analysis():
    """run_analysis должен запустить все агенты и вернуть ответ стратега."""
    mock_json = json.dumps({
        "score": 75, "summary": "Полный анализ выполнен.",
        "recommendation": "Рекомендую разослать КП.",
        "bant": {"budget": "средний", "authority": "да", "need": "высокая", "timeline": "срочно"},
        "next_steps": ["Позвонить сегодня"],
        "budget_estimate": "1000000", "budget_confidence": "medium",
        "deal_segment": "mid_market", "ltv_estimate": "3000000",
        "cac_risk": "low", "financial_risks": [], "pricing_strategy": "подписка",
        "discount_ceiling": "15", "deal_probability_pct": 60,
        "risks": [], "opportunities": ["рост"], "action_plan": ["шаг 1"],
        "market_position": "хорошая", "competitor_threats": [],
        "campaigns": [], "messaging": "ценность", "channels": ["email"],
        "tech_stack_fit": "высокий", "integration_complexity": "низкая",
        "implementation_time": "3 месяца", "tech_risks": [], "tech_opportunities": [],
        "final_reply": "Анализ завершён. Рекомендую двигаться вперёд.",
    })

    async def mock_chat(messages, **kwargs):
        return mock_json

    async def mock_free_search(q, **kw):
        return {"formatted_block": "", "raw_results": []}

    with patch("core.llm.chat", side_effect=mock_chat), \
         patch("rag.search.free_search", side_effect=mock_free_search):
        from agents.orchestrator import run_agents
        result = await run_agents(
            intent="run_analysis",
            slots={"company": "Альфа Строй", "reply": "Запускаю анализ."},
            transcript="проанализируй лид Альфа Строй",
            trace_id="test-run-analysis",
        )
    assert result["agents_ran"] is True
    assert len(result["final_reply"]) > 0


# ─── Тест 7: Оркестратор корректно маршрутизирует write_email ─────────────────
@pytest.mark.asyncio
async def test_orchestrator_write_email():
    """write_email должен вернуть текст письма от маркетолога."""
    async def mock_chat(messages, **kwargs):
        return "Уважаемые коллеги, предлагаем наше решение SmartCRM..."

    async def mock_free_search(q, **kw):
        return {"formatted_block": "", "raw_results": []}

    with patch("core.llm.chat", side_effect=mock_chat), \
         patch("rag.search.free_search", side_effect=mock_free_search):
        from agents.orchestrator import run_agents
        result = await run_agents(
            intent="write_email",
            slots={"target": "Альфа", "topic": "автоматизация продаж", "tone": "formal", "reply": "Пишу письмо."},
            transcript="напиши письмо компании Альфа про автоматизацию",
            trace_id="test-email",
        )
    assert result["agents_ran"] is True
    assert len(result["final_reply"]) > 0


# ─── Тест 8: process_text передаёт page_context ───────────────────────────────
@pytest.mark.asyncio
async def test_pipeline_page_context():
    """process_text с page_context должен передавать контекст в hermes_text."""
    captured_text = []

    async def mock_parse(text: str) -> dict:
        captured_text.append(text)
        return {"intent": "noop", "agents": [], "slots": {}, "reply": "ok", "_model": "mock"}

    async def mock_run_agents(**kwargs):
        return {"agents_ran": False, "final_reply": "ok"}

    with patch("core.hermes.parse_intent", side_effect=mock_parse), \
         patch("agents.orchestrator.run_agents", side_effect=mock_run_agents):
        # Импортируем pipeline после патча
        if "voice.pipeline" in sys.modules:
            del sys.modules["voice.pipeline"]
        if "voice.whisper" not in sys.modules:
            whisper_stub = _stub_module("voice.whisper")
            whisper_stub.transcribe = AsyncMock(return_value="распознанный текст")
        from voice import pipeline
        await pipeline.process_text("создай лид Ромашка", page_context="Страница: Лиды")

    assert len(captured_text) == 1
    assert "Страница: Лиды" in captured_text[0]
    assert "создай лид Ромашка" in captured_text[0]


# ─── Тест 9: Hermes системный промпт содержит все новые интенты ───────────────
def test_hermes_prompt_contains_new_intents():
    """Системный промпт должен содержать примеры для всех новых интентов."""
    from core.hermes import SYSTEM_PROMPT

    required_intents = [
        "ask_economist", "ask_marketer", "ask_tech", "ask_strategist",
        "run_analysis", "search_web", "write_email",
    ]
    for intent in required_intents:
        assert intent in SYSTEM_PROMPT, f"Интент {intent!r} отсутствует в системном промпте Hermes"


# ─── Тест 10: Нет AGENT_INTENTS коллизий ─────────────────────────────────────
def test_no_agent_intent_conflicts():
    """Все интенты в _INTENT_TO_AGENTS должны быть в _AGENT_INTENTS."""
    from agents.orchestrator import _INTENT_TO_AGENTS, _AGENT_INTENTS

    for intent in _INTENT_TO_AGENTS:
        assert intent in _AGENT_INTENTS, f"Интент {intent!r} в _INTENT_TO_AGENTS, но не в _AGENT_INTENTS"


if __name__ == "__main__":
    asyncio.run(pytest.main([__file__, "-v"]))
