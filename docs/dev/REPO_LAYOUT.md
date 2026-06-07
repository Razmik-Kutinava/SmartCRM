# SmartCRM — канон структуры репозитория

> Правила для агентов: `.cursor/rules/smartcrm-repo-layout.mdc`, `.cursor/rules/smartcrm-code-split.mdc`  
> Что ещё не на месте: [LAYOUT_AUDIT.md](LAYOUT_AUDIT.md) — переносы только после **`go`**.

---

## Корень репозитория

```
SmartCRM/
├── backend/          # Python FastAPI — всё серверное
├── frontend/         # SvelteKit UI
├── docs/             # Вся документация (не в корне)
├── eval/             # Eval-наборы и скрипты вне pytest
├── scripts/          # Репо-уровень (setup_db.sh и т.п.)
├── tests/            # ⚠ LEGACY — цель: объединить в backend/tests/
├── docker-compose.yml
├── .env.example      # Шаблон; .env только локально
└── README.md
```

**Не класть в корень:** `result.json`, `swagger.json`, openapi-схемы, логи, sqlite, артефакты бенчмарков.

---

## `docs/`

```
docs/
├── README.md           # Карта доков — входная точка
├── product/            # PRD, ARCHITECTURE, PRD_MAP, PRD_NOTES
├── modules/            # Описание модулей продукта
├── agents/             # LangGraph, Hermes
├── stack/              # LLM, RAG, LangGraph, SvelteKit
├── start/              # SETUP, RUNBOOK
├── api/                # HTTP API, OpenAPI
├── email/              # Почта
├── voice/              # Голосовые команды
├── operations/         # HANDOFF, ISSUES, CHANGELOG, SESSION_STATE
├── dev/                # CONTRIBUTING, REPO_LAYOUT, LAYOUT_AUDIT, code-review
├── archive/            # Устаревшие доки
└── reference/          # Внешний референс (CRM Points) — не прод-код
```

Новый документ модуля → `docs/modules/{имя}.md`.  
Операционные записи → только `docs/operations/`.

---

## `backend/`

```
backend/
├── main.py                 # Точка входа FastAPI
├── api/routes/             # HTTP + WS роуты (тонкие handlers)
├── agents/                 # LangGraph-агенты
├── core/                     # Hermes, llm, auth, доменная логика
├── db/
│   ├── models/             # SQLAlchemy
│   └── session.py
├── rag/                    # Chroma, ingest, retrieve
├── services/               # Внешние API (тендеры, checko, …)
├── leadgen/                # Пайплайн лидогена
├── email_sync/             # IMAP/SMTP
├── voice/                  # Аудио/STT
├── integrations/           # Bitrix и др.
├── scripts/                # CLI, бенчмарки, seed (не pytest)
├── data/                   # JSON-кэш, chroma_db, sqlite артефакты
└── tests/                  # Все pytest + fixtures
    ├── fixtures/
    └── integration/        # (целевая папка)
```

**Не класть:** тесты в `backend/test_*.py` вне `tests/`; данные в `backend/backend/` (ошибочная вложенность).

---

## `backend/tests/` — зеркало кода

| Код | Тест |
|-----|------|
| `api/routes/leads.py` | `tests/api/routes/test_leads.py` |
| `core/hermes.py` | `tests/core/test_hermes.py` |
| `services/tenderguru.py` | `tests/services/test_tenderguru.py` |
| `agents/analyst.py` | `tests/agents/test_analyst.py` |

Корневой `tests/` → перенос в `backend/tests/` по [LAYOUT_AUDIT.md](LAYOUT_AUDIT.md).

---

## `frontend/`

```
frontend/src/
├── routes/         # Страницы по URL (+page.svelte, +page.js)
├── components/     # Переиспользуемые Svelte-компоненты
└── lib/            # TS/JS логика, API-клиент, stores
    └── {домен}/    # leads/, crm/, ops/ — при росте файлов
```

Логика > ~50 строк — в `lib/`, не в `+page.svelte`.

---

## `eval/`

Сценарии оценки Hermes/агентов: `cases.jsonl`, `run_eval.py` — отдельно от `backend/tests/`.

---

## Новая папка верхнего уровня

Только после согласования в `LAYOUT_AUDIT.md` + **`go`** пользователя.
