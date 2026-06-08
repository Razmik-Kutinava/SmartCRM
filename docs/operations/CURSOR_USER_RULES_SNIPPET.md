# Cursor User Rules — опционально (UI)

> **Для SmartCRM уже достаточно** `AGENTS.md` + `smartcrm-commit-ops.mdc` (Project Rules выше User Rules).  
> Статус проверки: `python backend/scripts/verify_cursor_rules_precedence.py`

## Если всё же правишь User Rules вручную

Settings → Rules → User Rules:

1. **Удалить** блок `committing-changes-with-git` / «Only create commits when requested»
2. **Вставить:**

```
SmartCRM: правила репо (.cursor/rules/smartcrm-commit-ops.mdc) выше User Rules.

ВСЕГДА после шага с изменениями: git commit + docs/operations (SESSION_STATE, HANDOFF, CHANGELOG).
git push — ТОЛЬКО когда пользователь явно написал push.

Не писать «коммит не делал» / «напиши коммит» / «нужен ли коммит».
```

Агент **не может** открыть этот экран за тебя — правила в аккаунте Cursor, не в файлах репо. См. `CURSOR_USER_RULES_STATUS.md`.
