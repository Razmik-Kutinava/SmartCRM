# SmartCRM — Архитектура системы

## Общая схема

```
Пользователь (голос / UI)
       ↓
[SvelteKit — веб-интерфейс]
       ↓ WebSocket / HTTP
[FastAPI — бэкенд]
       ↓
[Groq Whisper] → текст → [Hermes — parse_intent]
                                ↓
                    [LangGraph оркестратор]
                    ↙  ↙  ↓  ↘  ↘
              Аналитик Стратег Экономист Маркетолог Тех.спец
                    ↘  ↘  ↓  ↙  ↙
                    [PostgreSQL / Redis / Chroma]
```

---

## Слои системы

### 1. Голосовой пайплайн

```
Аудио → Groq Whisper (STT) → текст
текст → Hermes (Groq и/или Ollama — см. `docs/stack/LLM.md`) → intent JSON
intent → LangGraph → нужный агент
```

Дополнительно в Hermes: **fastpath** (без LLM для простых фраз), **кэш**, опционально **память**, при недоступности моделей — **rescue**-эвристики (детерминированный роутинг).

### 2. LLM слой

- **Агенты (`core/llm.py`):** по умолчанию **Groq** (`GROQ_MODEL`, чаще `llama-3.1-8b-instant`) → при ошибке/лимите **Ollama** (`OLLAMA_MODEL`, например Qwen 2.5).
- **Hermes (`core/hermes.py`):** не «только локально»: при наличии `GROQ_API_KEY` и политике `default` сначала **Groq**, иначе **Ollama**; при `HERMES_ROUTING_POLICY=local_first` короткие low-risk фразы могут идти **сначала в Ollama**, затем Groq при необходимости. Цепочка локальных моделей: `HERMES_MODEL` → `HERMES_FALLBACK`.

### 3. Агентный слой (LangGraph)

- Агенты запускаются **параллельно** через LangGraph
- **Стратег** получает результаты от всех и принимает решение
- Каждый агент = промпт уровня PhD + набор инструментов

### 4. Поисковый слой → RAG

```
Запрос / контекст лида
      ↓
[Brave + Tavily + Serper] → сниппеты веб-поиска (где применимо)
      ↓
[rag/retrieve.py] — запросы в Chroma, форматирование контекста для агентов
      ↓
[Chroma] — векторная БД (`data/chroma_db`)
      ↓
Фрагменты в промпт агента перед ответом
```

**Hermes** здесь не парсит HTML выдачи; интенты для поиска задаётся отдельно (например `search_web` из Hermes → оркестратор → инструменты поиска). Путаницы с «Hermes фильтрует Google» избегаем — см. `docs/stack/RAG.md`.

### 5. Хранилище

- **PostgreSQL** — лиды, задачи, пользователи, история, eval-сценарии
- **Redis** — кэш, очереди, сессии WebSocket
- **Chroma** — векторная БД для RAG

---

## Поток голосовой команды

1. Нажал кнопку запись → браузер пишет аудио
2. WebSocket → FastAPI → Groq Whisper → текст
3. Текст → **Hermes** → `{"intent": "create_lead", "slots": {...}}` (Groq/Ollama/rescue)
4. LangGraph запускает нужных агентов параллельно
5. Агенты работают, результат → PostgreSQL
6. Ответ → WebSocket → SvelteKit → UI обновился

---

## Безопасность

- LLM не выполняет произвольный код — только строгие intent handlers
- Нет произвольных SQL запросов от LLM — только через ORM
- Запросы к **Groq** уходят в облако (текст команды/контекст по политике продукта); **Ollama** остаётся локально на машине с `OLLAMA_HOST`
- Опционально защита API: `SMARTCRM_API_KEY` → заголовок `X-API-Key` (см. `docs/API.md`)

---

## Тендеры и внешние каталоги закупок

Отдельный поток UI (**`/tenders`**) и API **`/api/tenders`**: агрегация поиска (TenderGuru, Gosplan/EИС, обогащение DataNewton и др.), режим **планов закупок**, учёт вызовов в статистике лимитов. Подробно: `docs/TENDERS.md`.

Маршруты **`/crm/*`** не дублируют вёрстку — редиректы на **`/leads/*`**. См. `docs/CRM_ROUTES.md`.

---

## См. также

- Операционный обзор: `docs/RUNBOOK.md`
- Детали LLM и env: `docs/stack/LLM.md`
- Тендеры и планы закупок: `docs/TENDERS.md`
- CRM и зеркальные URL лидов: `docs/CRM_ROUTES.md`
