# Матрица правил SmartCRM

> Обновлять при изменении `.cursor/rules/workflow/` или `.cursor/rules/project/`.

## Дерево правил

| Слой | Папка | Назначение | Подключение |
|------|-------|------------|-------------|
| Индекс | [`.cursor/rules/smartcrm-index.mdc`](../../../.cursor/rules/smartcrm-index.mdc) | карта workflow + project, приоритет | всегда |
| Workflow | [`.cursor/rules/workflow/`](../../../.cursor/rules/workflow/) | commit-ops, task-workflow, dev-gates, SBR — всегда; repo-layout, file-size-split — по globs | смешанное |
| Project | [`.cursor/rules/project/`](../../../.cursor/rules/project/) | core, tests, http, data, agents (globs); performance (всегда) | по globs |

## Канон коммита

**Один источник:** [`workflow/smartcrm-commit-ops.mdc`](../../../.cursor/rules/workflow/smartcrm-commit-ops.mdc)

| Действие | Когда |
|----------|--------|
| `git commit` + ops | **Всегда**, если шаг менял файлы |
| `git push` | **Только** явный апрув пользователя |

Проверки: `verify_cursor_rules_precedence.py`, `check_agent_step.py`, `check_rules_commit_conflict.py`.

`AGENTS.md` в корне — краткий дубль канона коммита (нужен для не-Cursor агентов).

## Сводка правил

| # | Правило | Где | Enforcement |
|---|---------|-----|-------------|
| R1 | Всегда commit + ops | `workflow/commit-ops.mdc` | `check_agent_step.py` FAIL |
| R2 | Push только по явному go | `workflow/commit-ops.mdc` | дисциплина |
| R3 | Старт сессии: 3 строки | `workflow/task-workflow` | дисциплина |
| R4 | `go` на новую задачу; стоп после шага | `workflow/task-workflow` | дисциплина |
| R5 | Тест + регрессия зоны | `workflow/task-workflow`, `dev-gates` | `run_zone_regression.py` |
| R6 | Хвост прогона A+B+C | `workflow/task-workflow` | `check_agent_step.py` FAIL |
| R7 | BACKLOG ↔ PRD_MAP | `BACKLOG.md` | таблица |
| R8 | Сплит >200 строк | `workflow/file-size-split.mdc` (globs) | ревью |
| R9 | Backend README sync | `workflow/repo-layout` §5 (globs) | финиш-чеклист |
| R10 | SBR RED/GREEN + todo.md + scope | `workflow/spec-build-review.mdc` § Scope | дисциплина |
| R11 | Project rules по globs | `.cursor/rules/project/smartcrm-*.mdc` | Cursor globs |
| R12 | Отчёт: Сделано/Не сделано + A/B/C | `workflow/task-workflow` § Отчёт | `check_agent_step.py` |
| R13 | Ops-журналы: записи старше текущего месяца → `docs/archive/ops/` | `workflow/smartcrm-commit-ops.mdc` § Ops | дисциплина |

## SBR scope (апрув 2026-07-18)

**Да:** PRD_MAP, фича, API, миграция, 2+ файла логики, hot-path по плану.
**Нет:** one-liner, docs/rules-only, chore.
**Серая зона:** спросить один раз. Канон: [`spec-build-review.mdc`](../../../.cursor/rules/workflow/spec-build-review.mdc) § Scope.

## Старт сессии

| Поле | Источник |
|------|----------|
| `last_done:` | `HANDOFF.md` |
| `current_state:` | `SESSION_STATE`, `ISSUES` 🔴 |
| `next_step:` | `HANDOFF`, `PRD_MAP` — один шаг |

## Финиш шага

1. Тесты зелёные (или docs-only)
2. **`git commit` + ops** (`workflow/commit-ops.mdc`)
3. `check_agent_step.py` + `check_rules_commit_conflict.py` + `verify_cursor_rules_precedence.py`
4. Отчёт с **таблицей + A/B/C** → **стоп до `go`**

## Регрессия

| Затронуто | Команда (`cd backend`) |
|-----------|------------------------|
| CRM лиды | `python scripts/run_zone_regression.py crm_leads` |
| Лидоген | `… leadgen` |
| Голос | `… voice` |
| Hermes | `… hermes_eval` |
| Несколько зон | `… p6` |
| Только docs/rules | `check_agent_step.py` + `check_rules_commit_conflict.py` + `verify_cursor_rules_precedence.py` |
