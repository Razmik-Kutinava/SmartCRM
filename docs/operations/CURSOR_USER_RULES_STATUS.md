# Cursor User Rules — статус

User Rules хранятся в **аккаунте Cursor** (облако), не в файлах репозитория. Агент **не может** править Settings → Rules.

Процесс коммита и ops — только в репо:

| Файл | Роль |
|------|------|
| `AGENTS.md` | всегда в контексте агента |
| `.cursor/rules/smartcrm-commit-ops.mdc` | `alwaysApply: true` |

Проверка:

```bash
python backend/scripts/verify_cursor_rules_precedence.py
python backend/scripts/check_rules_commit_conflict.py
```
