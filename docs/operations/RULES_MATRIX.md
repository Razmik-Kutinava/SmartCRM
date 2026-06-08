# Матрица правил SmartCRM

> Обновлять при изменении `.cursor/rules/smartcrm-*.mdc`.

## Канон коммита

**Один источник:** [`smartcrm-commit-ops.mdc`](../../.cursor/rules/smartcrm-commit-ops.mdc)

| Действие | Когда |
|----------|--------|
| `git commit` + ops | **Всегда**, если шаг менял файлы |
| `git push` | **Только** явный апрув пользователя |

Проверки: `check_agent_step.py`, `check_rules_commit_conflict.py`.

## Сводка правил

| # | Правило | Где | Enforcement |
|---|---------|-----|-------------|
| R0 | `.mdc` выше User Rules | `commit-ops`, `dev-gates` п.0 | User Rules snippet |
| R1 | Всегда commit + ops | `commit-ops.mdc` | `check_agent_step.py` FAIL |
| R2 | Push только по апруву | `commit-ops.mdc` | дисциплина |
| R3 | Старт сессии: 3 строки | `task-workflow` | дисциплина |
| R4 | `go` на новую задачу; стоп после шага | `task-workflow` | дисциплина |
| R5 | Тест + регрессия зоны | `task-workflow`, `dev-gates` | `run_zone_regression.py` |
| R6 | Honest report | `task-workflow` | дисциплина |
| R7 | BACKLOG ↔ PRD_MAP | `BACKLOG.md` | таблица |
| R8 | Сплит >200 строк | `code-split.mdc` | ревью |
| R9 | Backend README sync | `repo-layout` §5 | финиш-чеклист |

## Старт сессии

| Поле | Источник |
|------|----------|
| `last_done:` | `HANDOFF.md` |
| `current_state:` | `SESSION_STATE`, `ISSUES` 🔴 |
| `next_step:` | `HANDOFF`, `PRD_MAP` — один шаг |

## Финиш шага

1. Тесты зелёные (или docs-only)
2. **`git commit` + ops** (`commit-ops.mdc`)
3. `check_agent_step.py` + `check_rules_commit_conflict.py`
4. Отчёт → **стоп до `go`**

## Регрессия

| Затронуто | Команда (`cd backend`) |
|-----------|------------------------|
| CRM лиды | `python scripts/run_zone_regression.py crm_leads` |
| Лидоген | `… leadgen` |
| Голос | `… voice` |
| Hermes | `… hermes_eval` |
| Несколько зон | `… p6` |
| Только docs/rules | `check_agent_step.py` + `check_rules_commit_conflict.py` |
