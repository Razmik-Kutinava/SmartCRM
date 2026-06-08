# SmartCRM — инструкции агента (всегда активны)

Канон: `.cursor/rules/smartcrm-commit-ops.mdc`

## Коммит и ops — всегда

Шаг изменил файлы в репозитории → **до отчёта**:

1. `git commit`
2. `docs/operations/SESSION_STATE.md`
3. В конце шага: `CHANGELOG.md` + `HANDOFF.md`

**Не спрашивать** «нужен ли коммит». **Не писать** «коммит не делал».

## Push — только по явному апруву

`git push` — только когда пользователь явно написал push.

## Приоритет правил (Cursor)

**Project Rules** (этот файл + `.cursor/rules/*.mdc`) **выше** глобальных User Rules.

Глобальное «Only create commits when requested» **не действует** в SmartCRM.

Проверка: `python backend/scripts/verify_cursor_rules_precedence.py`
