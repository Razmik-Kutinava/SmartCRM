# SmartCRM — API Reference

Base URL: `http://localhost:8000`

---

## Аутентификация

Если в `.env` задан **`SMARTCRM_API_KEY`**, защищённые маршруты ожидают заголовок:

```http
X-API-Key: <значение SMARTCRM_API_KEY>
```

Тот же ключ на фронте задаётся как `PUBLIC_SMARTCRM_API_KEY` (см. комментарии в `.env`). Без ключа в dev режиме часть эндпоинтов может быть открыта — см. актуальную логику в `main`/middleware бэкенда.

---

## Health

| Method | Path | Описание |
|--------|------|----------|
| GET | `/health` | Статус сервера |
| GET | `/health/ollama` | Статус Ollama |
| GET | `/health/groq` | Статус Groq |

---

## Лиды

| Method | Path | Описание |
|--------|------|----------|
| GET | `/api/leads` | Список лидов (фильтры, пагинация) |
| POST | `/api/leads` | Создать лид |
| GET | `/api/leads/{id}` | Карточка лида |
| PATCH | `/api/leads/{id}` | Обновить лид |
| DELETE | `/api/leads/{id}` | Удалить лид |

---

## Голос

| Method | Path | Описание |
|--------|------|----------|
| WS | `/ws/voice` | WebSocket голосового пайплайна |
| POST | `/api/voice/transcribe` | Аудио → текст (Groq Whisper) |
| POST | `/api/voice/command` | Текст → intent → агент |

---

## Агенты

| Method | Path | Описание |
|--------|------|----------|
| GET | `/api/agents/status` | Статус всех агентов |
| POST | `/api/agents/run` | Запустить задачу на агентах |
| GET | `/api/agents/history` | История выполненных задач |

Операции с промптами агентов: см. таблицу в `docs/AGENTS.md` (`/api/ops/agents`).

---

## RAG / Поиск

| Method | Path | Описание |
|--------|------|----------|
| POST | `/api/rag/search` | Поиск в базе знаний |
| POST | `/api/rag/add` | Добавить документ в RAG |
| POST | `/api/search/web` | Поиск через Brave/Tavily/Serper |

---

## Тендеры

| Method | Path | Описание |
|--------|------|----------|
| GET | `/api/tenders/search` | Поиск тендеров (несколько источников, см. `docs/TENDERS.md`) |
| GET | `/api/tenders/plans/search` | Поиск планов закупок |
| GET | `/api/tenders/plans/detail` | Деталь плана закупок |
| GET | `/api/tenders/enrich/{inn}` | Обогащение контрагента (DataNewton) |
| GET | `/api/tenders/{tender_id}` | Карточка/метаданные по ID (см. реализацию) |
| GET | `/api/tenders/number/{tend_num}` | Поиск по номеру |
| GET | `/api/tenders/search/docs` | Доп. поиск документов (TenderGuru) |
| GET | `/api/tenders/search/products` | Поиск по продуктам |
| GET | `/api/tenders/online` | Онлайн-выдача |
| POST | `/api/tenders/save` | Сохранение записи из UI |

Полное описание провайдеров и env: **`docs/TENDERS.md`**.

---

## См. также

- Полный операционный контекст: `docs/RUNBOOK.md`
