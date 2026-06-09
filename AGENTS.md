# SmartCRM — инструкции агента (всегда активны)

Канон: `.cursor/rules/smartcrm-commit-ops.mdc`

## Коммит и ops — всегда

Шаг изменил файлы в репозитории → **до отчёта**:

1. `git commit`
2. `docs/operations/SESSION_STATE.md`
3. В конце шага: `CHANGELOG.md` + `HANDOFF.md`

В отчёте: **`Коммит: <хеш>`**.

## Хвост прогона — всегда три блока

После commit + ops в ответе и в `SESSION_STATE` — **обязательно**:

- **A** — из плана прогона не сделано (`нет` или список)
- **B** — BACKLOG появился в прогоне (`нет` или список; отложенное → `BACKLOG.md` в том же коммите)
- **C** — доп. починки / новые задачи в прогоне (`нет` или список; баг → `ISSUES.md`)

Без A+B+C шаг не закрыт. Детали: `smartcrm-task-workflow.mdc`.

## Push

`git push` — только когда пользователь явно написал push.

## Проверка

```bash
python backend/scripts/check_agent_step.py
python backend/scripts/check_rules_commit_conflict.py
```
