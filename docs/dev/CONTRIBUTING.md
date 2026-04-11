# Руководство для разработчиков SmartCRM

## Структура проекта

```
backend/
  agents/       — 5 агентов + оркестратор (LangGraph)
  api/routes/   — FastAPI роуты (leads, voice, agents)
  core/         — Hermes роутер, LLM клиент (Groq→Ollama)
  db/models/    — SQLAlchemy модели
  rag/          — Chroma + поисковики
  voice/        — Whisper пайплайн
  services/     — бизнес-логика

frontend/
  src/routes/   — страницы SvelteKit
  src/components/ — UI компоненты
  src/lib/      — API клиент, WebSocket
```

---

## Соглашения по коду

### Python (backend)
- Python 3.11+
- Async везде (`async def`, `await`)
- Pydantic для валидации данных
- SQLAlchemy async для БД
- Типизация обязательна
- Форматирование: `black`, `ruff`

### Svelte (frontend)
- SvelteKit + Tailwind CSS
- Компоненты в `PascalCase.svelte`
- Состояние через Svelte stores
- WebSocket через `src/lib/websocket.js`

---

## Ветки и коммиты

```
main          — стабильная версия
dev           — разработка
feature/xxx   — новые фичи
fix/xxx       — баги
```

Формат коммитов:
```
feat: добавить голосовой ввод
fix: исправить роутинг Hermes
refactor: рефактор LLM клиента
```

---

## Добавить нового агента

1. Создать `backend/agents/my_agent.py`
2. Определить промпт уровня PhD эксперта
3. Добавить инструменты (tools)
4. Зарегистрировать в `orchestrator.py`
5. Добавить роутинг в `core/hermes.py`
6. Описать в `docs/AGENTS.md`

---

## Тестирование

```bash
# Backend
cd backend && pytest

# Frontend
cd frontend && npm run test
```
