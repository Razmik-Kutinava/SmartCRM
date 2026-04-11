# SmartCRM — API Reference

Base URL: `http://localhost:8000`

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

---

## RAG / Поиск

| Method | Path | Описание |
|--------|------|----------|
| POST | `/api/rag/search` | Поиск в базе знаний |
| POST | `/api/rag/add` | Добавить документ в RAG |
| POST | `/api/search/web` | Поиск через Brave/Tavily/Serper |
