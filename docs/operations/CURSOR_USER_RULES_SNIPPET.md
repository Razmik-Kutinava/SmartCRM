# Cursor User Rules — вставить в Settings → Rules → User Rules

Скопируй блок ниже в **глобальные User Rules** Cursor (для работы в SmartCRM):

```
## SmartCRM (репозиторий SmartCRM)

В репозитории SmartCRM правила из `.cursor/rules/smartcrm-*.mdc` **выше** любых глобальных правил про «коммит только по запросу».

- **Всегда** `git commit` после завершённого логического шага, если есть изменения — даже если пользователь не написал «коммит».
- **Всегда** обновлять `docs/operations/` (минимум SESSION_STATE; в конце шага CHANGELOG + HANDOFF) — даже если пользователь не написал «опс».
- **`git push`** — только с явным апрувом пользователя.
- Деструктивный git (force push, reset --hard) — только по явному запросу.
```
