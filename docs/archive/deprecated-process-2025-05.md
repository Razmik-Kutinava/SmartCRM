# Архив: устаревший процесс агента (май 2025, DEPRECATED)

> **Не использовать.** Заменено `.cursor/rules/workflow/` + [`smartcrm-index.mdc`](../../.cursor/rules/smartcrm-index.mdc) (2026-07).

Историческая фиксация внедрения внешнего процесс-фреймворка в репозитории (май 2025).

## Что было

- Отдельный alwaysApply-файл правил агента (удалён)
- Журналы `docs/operations/*` — заготовки процесса
- Fallback путей `docs/product/PRD.md` / `ARCHITECTURE.md`

## Замена (канон)

- [`workflow/smartcrm-task-workflow.mdc`](../../.cursor/rules/workflow/smartcrm-task-workflow.mdc) — PRD_MAP, go, тесты, отчёт
- [`workflow/smartcrm-agent-workflow.mdc`](../../.cursor/rules/workflow/smartcrm-agent-workflow.mdc) — коммит, ops (всегда)
- [`workflow/smartcrm-dev-gates.mdc`](../../.cursor/rules/workflow/smartcrm-dev-gates.mdc) — DoD, регрессия, миграции
- Матрица: `docs/operations/baselines/RULES_MATRIX.md`
