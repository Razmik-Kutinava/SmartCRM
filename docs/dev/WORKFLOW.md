# Рабочий процесс разработки

## Порядок разработки

### Фаза 1 — MVP (сейчас)
1. `core/llm.py` — Groq → Ollama fallback
2. `voice/whisper.py` — Groq Whisper STT
3. `core/hermes.py` — парсинг интентов
4. `db/models/lead.py` — модель лида (Битрикс-совместимая)
5. `api/routes/leads.py` — CRUD API
6. `agents/orchestrator.py` — LangGraph граф
7. `agents/analyst.py` — первый агент
8. Frontend: VoiceInput + LeadsList

### Фаза 2 — Поиск и RAG
1. `rag/search.py` — Brave/Tavily/Serper
2. `rag/chroma.py` — векторная БД
3. `agents/marketer.py` — письма и касания
4. `agents/economist.py` — финансовый анализ

### Фаза 3 — Все агенты
1. `agents/strategist.py` — координатор
2. `agents/tech_specialist.py`
3. Параллельная оркестрация всех 5 агентов

---

## Как тестировать голосовой пайплайн

```bash
# Текстовая симуляция (без микрофона)
curl -X POST http://localhost:8000/api/voice/command \
  -H "Content-Type: application/json" \
  -d '{"text": "создай лид компания АКМЕ контакт Иван"}'
```

---

## Переменные окружения для разработки

```bash
DEBUG=true
GROQ_API_KEY=gsk_...
OLLAMA_HOST=http://localhost:11434
DATABASE_URL=postgresql+asyncpg://smartcrm:smartcrm@localhost:5432/smartcrm
```
