# Руководство для разработчиков SmartCRM

**Структура репо и лимиты кода:** [REPO_LAYOUT.md](REPO_LAYOUT.md) · [LAYOUT_AUDIT.md](LAYOUT_AUDIT.md)  
**Правила агента:** `.cursor/rules/smartcrm-repo-layout.mdc`, `smartcrm-code-split.mdc`  
Переносы файлов и сплит монолитов >200 строк — только после **`go`** (см. аудит).

---

## Структура проекта

```
backend/
  agents/       — 5 агентов + оркестратор (LangGraph)
  api/routes/   — FastAPI роуты (leads, voice, agents)
  core/         — Hermes (Groq+Ollama), llm.py, qa_agent
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

### Размер файлов

| Цель | ≤ 50 строк (новый код) |
| Норма | 51–120 |
| Стоп | > 200 — сначала сплит + `go` |

Один файл — одна ответственность; дробить по домену (`core/hermes/`, не `utils/`).

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
6. Описать в `docs/agents/langgraph.md`

---

## Тестирование

Все backend-тесты — в **`backend/tests/`** (зеркало: `api/`, `core/`, `rag/`, …).

**Правило:** каждая новая или существенно изменённая фича → **минимум 1 pytest** на happy path (моки API/БД, без live Groq/IMAP). Чеклист PR: [PR_CHECKLIST.md](PR_CHECKLIST.md).

```bash
cd backend
python -m venv .venv && .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt -r requirements-dev.txt
python -m pytest -q
python -m pytest --cov=. --cov-config=.coveragerc --cov-report=term-missing   # раз в спринт
python scripts/ci_smoke.py
```

CI печатает **TOTAL %** в логе pytest (без fail-under). Baseline: `docs/operations/COVERAGE_BASELINE.md`.

```bash
# Frontend
cd frontend && npm run test
```
