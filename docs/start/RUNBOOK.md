# SmartCRM — операционный справочник

Единая точка входа для разработчика и для ИИ-агента: **что где лежит, как течёт запрос, что читать из `.env`**.

---

## 1. Поток запроса (голос / текст)

1. **Клиент** (SvelteKit) → WebSocket или HTTP к FastAPI.
2. **STT** (если голос): `voice/whisper.py` — Groq Whisper → текст.
3. **Роутер интентов** — `core/hermes.py` → `parse_intent()`:
   - при необходимости: **fastpath** (без LLM), **кэш**, **память** (`HERMES_ENABLE_MEMORY`);
   - **Groq** и/или **Ollama** (см. `docs/stack/LLM.md`);
   - при полном отказе LLM — **rescue** (детерминированные эвристики под CPU-only).
4. **Оркестратор** — `agents/orchestrator.py` → LangGraph по `intent`.
5. **Агенты** — `agents/*.py` → LLM через `core/llm.py` (Groq → Ollama fallback).
6. **Данные** — PostgreSQL, Redis, при RAG — Chroma (`data/chroma_db`).

Подробнее схема: `docs/product/ARCHITECTURE.md`.

---

## 2. LLM: кто за что отвечает

| Компонент | Файл | Назначение |
|-----------|------|------------|
| Чат агентов | `core/llm.py` | `model="auto"` → Groq, иначе Ollama (`OLLAMA_MODEL`) |
| Роутер Hermes | `core/hermes.py` | JSON с `intent` / `slots`; Groq + Ollama по политике |
| STT | `voice/whisper.py` | Whisper (модель из `WHISPER_MODEL` / настроек) |
| Эксперименты NLU | `core/qa_agent.py` | Dr. QA — гипотезы, A/B, метрики Hermes (SQLite `data/qa_lab.sqlite3`) |

Актуальные модели и переменные: **`docs/stack/LLM.md`**.

---

## 3. Данные и артефакты

| Путь | Назначение |
|------|------------|
| `backend/data/agent_memory.sqlite3` | Долгосрочная память Hermes (если `HERMES_ENABLE_MEMORY=1`) |
| `backend/data/qa_lab.sqlite3` | QA Lab (Dr. QA) |
| `backend/data/chroma_db/` | Chroma persistent RAG |
| `backend/data/api_stats.json` | Учёт токенов Groq (для скриптов eval) |
| `backend/data/hermes_system_prompt.txt` | Опциональный override промпта Hermes (режим не `compact`) |

---

## 4. Eval и тесты Hermes

| Механизм | Где | Назначение |
|----------|-----|------------|
| Сценарии в БД | `EvalScenario` (PostgreSQL), скрипты `scripts/run_hermes_*`, `expand_eval_from_traces.py` | Продакшен-подобный eval, KPI |
| Файл `eval/cases.jsonl` | `eval/run_eval.py` | Отдельный офлайн-контур (см. `eval/README.md`) |

---

## 5. Аутентификация API

Если задан `SMARTCRM_API_KEY` в `.env`, защищённые эндпоинты ожидают заголовок **`X-API-Key`**. См. `docs/api/API.md`.

---

## 6. Связанные документы

- Архитектура: `ARCHITECTURE.md`
- LLM / Hermes: `stack/LLM.md`
- Агенты: `AGENTS.md`
- QA-агент (методология): этот файл + `core/qa_agent.py`
- API: `API.md`
- Установка: `SETUP.md`
