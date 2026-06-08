# Cursor User Rules — SmartCRM

**Статус:** вставлено пользователем ✅ (2026-06-07).

Скопируй в **Settings → Rules → User Rules**, если настраиваешь новую машину:

```
## SmartCRM (репозиторий SmartCRM)

Правила `.cursor/rules/smartcrm-*.mdc` **выше** глобальных правил про отложенный коммит.

- **Всегда** `git commit` после логического шага, если есть изменения.
- **Всегда** обновлять `docs/operations/` (SESSION_STATE; в конце шага CHANGELOG + HANDOFF).
- **`git push`** — только с явным апрувом.
- Перед «done»: `python backend/scripts/check_agent_step.py`
```
