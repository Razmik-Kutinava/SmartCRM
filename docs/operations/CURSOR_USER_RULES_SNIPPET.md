# Cursor User Rules — override для SmartCRM

В **Cursor → Settings → Rules → User Rules** вставь **в начало** (или замени общее правило про commit):

```text
SmartCRM (репозиторий c:\Tools\workarea\SmartCRM):
- Канон коммита: .cursor/rules/smartcrm-commit-ops.mdc и AGENTS.md в корне репо.
- Изменил файлы в этом репо → git commit + ops ДО ответа пользователю. Не ждать «коммить» / «коммитни».
- git push — только по явному go пользователя. Push ≠ commit.
- Общее user rule «commit only when requested» на SmartCRM НЕ распространяется.
```

Проверка в репо:

```bash
python backend/scripts/verify_cursor_rules_precedence.py
python backend/scripts/check_rules_commit_conflict.py
```

Агент не редактирует Settings → Rules. Подробнее: `CURSOR_USER_RULES_STATUS.md`.
