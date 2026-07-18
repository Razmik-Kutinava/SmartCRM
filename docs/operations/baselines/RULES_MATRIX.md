# Матрица правил SmartCRM

> Обновлять при изменении `.cursor/rules/workflow/` или `.cursor/rules/project/`.

## Дерево правил (CoffeeOS workflow)

| Слой | Папка | Назначение |
|------|-------|------------|
| Индекс | [`.cursor/rules/smartcrm-index.mdc`](../../.cursor/rules/smartcrm-index.mdc) | alwaysApply, карта workflow + project |
| Workflow | [`.cursor/rules/workflow/`](../../.cursor/rules/workflow/) | процесс: commit, go, тесты, layout |
| Project | [`.cursor/rules/project/`](../../.cursor/rules/project/) | стек и домены (шаг 3+) |

## Канон коммита

**Один источник:** [`workflow/smartcrm-commit-ops.mdc`](../../.cursor/rules/workflow/smartcrm-commit-ops.mdc)

| Действие | Когда |
|----------|--------|
| `git commit` + ops | **Всегда**, если шаг менял файлы |
| `git push` | **Только** явный апрув пользователя |

Проверки: `verify_cursor_rules_precedence.py`, `check_agent_step.py`, `check_rules_commit_conflict.py`.

`AGENTS.md` в корне — краткий дубль канона коммита.

## Сводка правил

| # | Правило | Где | Enforcement |
|---|---------|-----|-------------|
| R1 | Всегда commit + ops | `workflow/commit-ops.mdc` | `check_agent_step.py` FAIL |
| R2 | Push только по явному go | `workflow/commit-ops.mdc` | дисциплина |
| R3 | Старт сессии: 3 строки | `workflow/task-workflow` | дисциплина |
| R4 | `go` на новую задачу; стоп после шага | `workflow/task-workflow` | дисциплина |
| R5 | Тест + регрессия зоны | `workflow/task-workflow`, `dev-gates` | `run_zone_regression.py` |
| R6 | Хвост прогона A+B+C | `workflow/commit-ops`, `task-workflow` | `check_agent_step.py` FAIL |
| R7 | BACKLOG ↔ PRD_MAP | `BACKLOG.md` | таблица |
| R8 | Сплит >200 строк | `workflow/file-size-split.mdc` | ревью |
| R9 | Backend README sync | `workflow/repo-layout` §5 | финиш-чеклист |

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
4. Отчёт с **A / B / C** → **стоп до `go`**

## Регрессия

| Затронуто | Команда (`cd backend`) |
|-----------|------------------------|
| CRM лиды | `python scripts/run_zone_regression.py crm_leads` |
| Лидоген | `… leadgen` |
| Голос | `… voice` |
| Hermes | `… hermes_eval` |
| Несколько зон | `… p6` |
| Только docs/rules | `check_agent_step.py` + `check_rules_commit_conflict.py` + `verify_cursor_rules_precedence.py` |
