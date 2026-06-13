# Архив: устаревший процесс агента (май 2025, DEPRECATED)

> **Не использовать.** Заменено `.cursor/rules/smartcrm-*.mdc` (июнь 2026).

Историческая фиксация внедрения внешнего процесс-фреймворка в репозитории (май 2025).

## Что было

- Отдельный alwaysApply-файл правил агента (удалён)
- Журналы `docs/operations/*` — заготовки процесса
- Fallback путей `docs/product/PRD.md` / `ARCHITECTURE.md`

## Замена (канон)

- `smartcrm-task-workflow.mdc` — PRD_MAP, go, тесты, honest report
- `smartcrm-agent-workflow.mdc` — коммит, ops (всегда)
- `smartcrm-dev-gates.mdc` — DoD, регрессия, миграции
- Матрица: `docs/operations/baselines/RULES_MATRIX.md`
