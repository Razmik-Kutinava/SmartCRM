# SmartCRM — инструкции агента

Канон: `.cursor/rules/workflow/smartcrm-commit-ops.mdc`

## Жёстко: commit до ответа

Изменил файлы → **`git commit` → ops (`SESSION_STATE`) → ответ** с `Коммит: <хеш>`.

Commit **без согласования пользователя** — не ждать «коммить».

Глобальные User Rules Cursor про отложенный commit **не действуют** — канон только `workflow/smartcrm-commit-ops.mdc`.

Ответ без коммита при изменённых файлах = шаг не закрыт.

## Индекс правил

- **Workflow:** `.cursor/rules/workflow/` — процесс (alwaysApply)
- **SBR:** `workflow/spec-build-review.mdc` — scope: PRD_MAP + фичи; one-liner без SBR
- **Project:** `.cursor/rules/project/` — core, tests, http, data, agents, performance
- **Матрица:** `docs/operations/baselines/RULES_MATRIX.md`

## Отчёт (каждый шаг)

Таблица **Сделано | Не сделано** + блоки **B / C** + **`Коммит: <hash>`**.  
A = колонка «Не сделано». Канон: `workflow/smartcrm-task-workflow.mdc` § «Формат отчёта».

## Хвост A / B / C (SESSION_STATE)

## Push

`git push` — только по явному go пользователя.

## Проверка

```bash
python backend/scripts/check_agent_step.py
python backend/scripts/check_rules_commit_conflict.py
python backend/scripts/verify_cursor_rules_precedence.py
```
