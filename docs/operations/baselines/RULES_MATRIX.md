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
| ops + `git commit` (**одним** коммитом, в журнале `Коммит: \`этот\``) | **Всегда**, если шаг менял файлы |
| `git push` | **Только** явный апрув пользователя |

Проверки: `cmd /c scripts\check_step.cmd` (три валидатора разом, UTF-8) + `verify_cursor_rules_precedence.py`.

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
| R7 | BACKLOG ↔ чеклист фазы | `BACKLOG.md` | таблица |
| R8 | Сплит >200 строк | `workflow/file-size-split.mdc` (globs) | ревью |
| R9 | Backend README sync | `workflow/repo-layout` §5 (globs) | финиш-чеклист |
| R10 | SBR RED/GREEN + todo.md + scope | `workflow/spec-build-review.mdc` § Scope | дисциплина |
| R11 | Project rules по globs | `.cursor/rules/project/smartcrm-*.mdc` | Cursor globs |
| R12 | Отчёт: Сделано/Не сделано + A/B/C | `workflow/task-workflow` § Отчёт | `check_agent_step.py` |
| R13 | Ops-журналы: записи старше текущего месяца → `docs/archive/ops/` | `workflow/smartcrm-commit-ops.mdc` § Ops | дисциплина |
| R14 | ISSUES: открытые записи старше месяца — «должки», показать пользователю и просить подтвердить закрытие | `workflow/task-workflow` § Старт сессии | дисциплина |

## SBR scope (апрув 2026-07-18)

**Да:** пункт чеклиста фазы, фича, API, миграция, 2+ файла логики, hot-path по плану.
**Нет:** one-liner, docs/rules-only, chore.
**Вход (PHASE 0 INTAKE, апрув 2026-07-21):** заказ пользователя дословной цитатой в `todo.md`; пункт чеклиста фазы и доки области создаются до кода.
**Серая зона:** спросить один раз. Канон: [`spec-build-review.mdc`](../../../.cursor/rules/workflow/spec-build-review.mdc) § Scope.

## Старт сессии

| Поле | Источник |
|------|----------|
| `last_done:` | `HANDOFF.md` |
| `current_state:` | `SESSION_STATE`, `ISSUES` 🔴 |
| `next_step:` | `HANDOFF`, чеклист активной фазы ([`Чеклист: Фаза 4 — Тюнинг и MVP`](../phase4/CHECKLIST.md)) — один шаг |

## Финиш шага

1. Тесты зелёные (или docs-only)
2. **ops + `git commit` одним коммитом** (`workflow/commit-ops.mdc`)
3. `cmd /c scripts\check_step.cmd` (+ `verify_cursor_rules_precedence.py` при правке правил)
4. Отчёт с **таблицей + A/B/C + хеш** → **стоп до `go`**

## Регрессия

| Затронуто | Команда (`cd backend`) |
|-----------|------------------------|
| CRM лиды | `python scripts/run_zone_regression.py crm_leads` |
| Лидоген | `… leadgen` |
| Голос | `… voice` |
| Hermes | `… hermes_eval` |
| Несколько зон | `… p6` |
| Только docs/rules | `cmd /c scripts\check_step.cmd` + `verify_cursor_rules_precedence.py` |
