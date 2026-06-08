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
├── tests/            # удалено — все pytest в backend/tests/
├── docker-compose.yml
├── .env.example      # Шаблон; .env только локально
└── README.md
```

**Не класть в корень:** выводы скриптов, openapi, логи, sqlite, кэши.

| Что | Куда |
|-----|------|
| OpenAPI | `docs/api/openapi/` |
| Артефакты бенчмарков | `backend/data/artifacts/` (gitignore, в репо только `.gitkeep`) |

### Анти-мусор (для агентов и людей)

1. Новый файл — в **существующую** папку по домену; новая подпапка только при 3+ файлах или чёткой зоне (`api/`, `openapi/`).
2. Скрипт пишет JSON → сразу `backend/data/artifacts/{домен}/`, не cwd.
3. Конец шага: проверить корень репо — лишнее убрать в том же коммите.
4. Не плодить `utils/`, `temp/`, `misc/`.

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

**Карта папок простыми словами:** [`backend/README.md`](../../backend/README.md) и README в каждой зоне (`api/`, `core/`, `leadgen/`, …).

**Правила разработки агента:** `.cursor/rules/smartcrm-*.mdc` (workflow, dev-gates, layout, code-split).

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
    └── integration/        # интеграционные смоуки (email и др.)
```

**Не класть:** тесты в `backend/test_*.py` вне `tests/`. Скрипты запускать из `backend/` — иначе артефакты уйдут в `backend/backend/data/` (удалено в P3).

---

## `backend/tests/` — зеркало кода

| Код | Тест |
|-----|------|
| `api/routes/leads.py` | `tests/api/routes/test_leads.py` |
| `core/hermes.py` | `tests/core/test_hermes.py` |
| `services/tenderguru.py` | `tests/services/test_tenderguru.py` |
| `agents/analyst.py` | `tests/agents/test_analyst.py` |

Все pytest — только `backend/tests/` (зеркало `backend/`).

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
