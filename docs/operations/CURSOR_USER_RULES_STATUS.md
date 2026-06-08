# Cursor User Rules — статус (2026-06-08)

## Почему агент не правит Settings → Rules сам

Проверено на машине пользователя:

| Где искали | Результат |
|------------|-----------|
| `settings.json` | User Rules **нет** |
| `state.vscdb` ItemTable (592 ключей) | ключей `*rule*` / `userRules` **нет** |
| `~/.cursor/rules` | папки **нет** |
| Workspace `state.vscdb` (SmartCRM) | только история чатов, не User Rules |

**Вывод:** User Rules хранятся в **аккаунте Cursor** (синхронизация с сервером) и подмешиваются в чат при старте сессии. Редактирование только через UI: **Cursor Settings → Rules → User Rules**.

Агент в репозитории **не имеет API** к этому экрану.

## Что сделано вместо ручной правки (работает без UI)

По [документации Cursor](https://cursor.com/docs/rules): **Project Rules > User Rules**.

| Файл | Роль |
|------|------|
| `AGENTS.md` | всегда в контексте агента |
| `.cursor/rules/smartcrm-commit-ops.mdc` | `alwaysApply: true` |
| `.cursorrules` | индекс на канон |

Проверка:

```bash
python backend/scripts/verify_cursor_rules_precedence.py
python backend/scripts/check_rules_commit_conflict.py
```

## Опционально (1 раз вручную в UI)

Если хочешь убрать дубль в User Rules (не обязательно для SmartCRM после AGENTS.md):

1. Settings → Rules → User Rules
2. Удалить блок `committing-changes-with-git`
3. Вставить текст из `CURSOR_USER_RULES_SNIPPET.md` (шаг 2)

После этого конфликт исчезнет и в других проектах.
