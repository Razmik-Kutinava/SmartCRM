# SmartCRM — инструкции агента (всегда активны)

Канон: `.cursor/rules/smartcrm-commit-ops.mdc`

## Коммит и ops — всегда

Шаг изменил файлы в репозитории → **до отчёта**:

1. `git commit`
2. `docs/operations/SESSION_STATE.md`
3. В конце шага: `CHANGELOG.md` + `HANDOFF.md`

В отчёте: **`Коммит: <хеш>`**.

## Push

`git push` — только когда пользователь явно написал push.

## Проверка

```bash
python backend/scripts/check_agent_step.py
python backend/scripts/check_rules_commit_conflict.py
```
