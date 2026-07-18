# SmartCRM — инструкции агента

Канон: `.cursor/rules/workflow/smartcrm-commit-ops.mdc`

## Жёстко: commit до ответа

Изменил файлы → **`git commit` → ops (`SESSION_STATE`) → ответ** с `Коммит: <хеш>`.

Commit **без согласования пользователя** — не ждать «коммить».

Глобальные User Rules Cursor про отложенный commit **не действуют** — канон только `workflow/smartcrm-commit-ops.mdc`.

Ответ без коммита при изменённых файлах = шаг не закрыт.

## Индекс правил

- **Workflow:** `.cursor/rules/workflow/` — процесс (alwaysApply)
- **SBR:** `workflow/spec-build-review.mdc` + `docs/operations/session/todo.md`
- **Project:** `.cursor/rules/project/` — core, tests, http, data, agents, performance
- **Матрица:** `docs/operations/baselines/RULES_MATRIX.md`

## Хвост A / B / C

В каждом отчёте после работы — три блока (`нет` или список). См. `workflow/smartcrm-commit-ops.mdc`.

## Push

`git push` — только по явному go пользователя.

## Проверка

```bash
python backend/scripts/check_agent_step.py
python backend/scripts/check_rules_commit_conflict.py
python backend/scripts/verify_cursor_rules_precedence.py
```
