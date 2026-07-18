# SmartCRM — project rules (Cursor)

Правила по стеку и доменам. Подключаются по **globs** при работе в зоне (кроме `smartcrm-performance.mdc` — alwaysApply).

| Файл | Зона |
|------|------|
| `smartcrm-core.mdc` | стек, security, архитектура |
| `smartcrm-tests.mdc` | pytest, eval, регрессия |
| `smartcrm-http.mdc` | FastAPI routes, API-контракт |
| `smartcrm-data.mdc` | ORM, миграции, PostgreSQL |
| `smartcrm-agents.mdc` | Hermes, LangGraph, голос |
| `smartcrm-performance.mdc` | N+1, batch, hot-path |

Индекс: [`.cursor/rules/smartcrm-index.mdc`](../smartcrm-index.mdc)
