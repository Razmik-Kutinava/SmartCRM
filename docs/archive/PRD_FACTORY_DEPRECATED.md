# PRD Factory — архив (DEPRECATED)

> **Не использовать.** Заменено правилами `.cursor/rules/smartcrm-*.mdc` (2026-06-07).

Историческая фиксация внедрения PRD Factory v10 в репозитории (май 2025).

## Что было сделано (2026-05-03)

| Артефакт | Назначение |
|----------|------------|
| `.cursor/rules/prd-factory-agent.mdc` | Полный текст PRD Factory v10, `alwaysApply: true` |
| `.cursorrules` | Ссылка на `.mdc`, приоритет операционки |
| `docs/agents/AGENTS.md` | Точка входа агентов + LangGraph/Hermes |
| `docs/operations/*` | Журналы ISSUES, SESSION_STATE, HANDOFF, CHANGELOG |

## Разрывы на момент архивации (май 2025)

- Нет каталога `docs/product/` в полном объёме ролевых промптов `docs/agents/AGENTS/*` (200+ строк).
- Тесты в `backend/tests/` — сводка для QA-матрицы отдельной задачей.

## Замена

Канон процесса SmartCRM:

- `smartcrm-task-workflow.mdc` — PRD_MAP, go, тесты, honest report
- `smartcrm-agent-workflow.mdc` — коммит, ops (всегда)
- `smartcrm-dev-gates.mdc` — DoD, регрессия, миграции
