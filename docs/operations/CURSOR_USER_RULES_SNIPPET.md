# Cursor User Rules — вставить в Settings → Rules

## Шаг 1 — удалить конфликт

В **User Rules** найти и **полностью удалить** блок вроде:

- `Only create commits when requested`
- `committing-changes-with-git`
- любое «коммит только по запросу»

Он **перебивает** правила репозитория.

## Шаг 2 — вставить этот текст

```
SmartCRM: правила репо (.cursor/rules/smartcrm-commit-ops.mdc) выше User Rules.

ВСЕГДА после шага с изменениями: git commit + docs/operations (SESSION_STATE, HANDOFF, CHANGELOG).
git push — ТОЛЬКО когда пользователь явно написал push.

Не писать «коммит не делал» / «напиши коммит» / «нужен ли коммит».
```

## Проверка

```bash
python backend/scripts/check_rules_commit_conflict.py
python backend/scripts/check_agent_step.py
```

Оба OK — конфликтов нет.
