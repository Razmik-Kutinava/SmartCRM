# /sbr — RED → GREEN по todo

SmartCRM SBR BUILD. Канон: `spec-build-review.mdc` § PHASE 2, `smartcrm-commit-ops.mdc`, `smartcrm-dev-gates.mdc`.

## Сделай

1. Работай **только** по файлам из todo «Файлы (ожидаемо)» (+ зеркальные тесты; добор +1 путь — дописать в todo).
2. **RED:** падающий тест → коммит `test: … [RED]` (без CHANGELOG/HANDOFF; SESSION_STATE `in_progress`) → стоп до `go`/`ебашь`, **кроме** явного «до конца / сразу GREEN».
3. **GREEN:** реализация (до 3 попыток; откат только реализации) → тесты задачи зелёные → **регрессия зоны** из «Проверка» / таблицы dev-gates → `[x]` в todo → коммит `feat:`/`fix: … [GREEN]`.
4. Счётчик `Регрессия_счёт`: +1; на `3/3` → ещё `all` (или p1+p6), сброс `0/3`.
5. Не `@codebase` зря. Не рой репо «на всякий».
6. Docs/rules-only — без RED; тесты не обязательны; `check_step.cmd` + при правке rules `verify_cursor_rules_precedence.py`.

## Качество (не ослаблять)

- Зонная регрессия на GREEN — **обязательна** (не «один раз на этап» как в APU).
- Hot-path — минимальный diff + зона из todo «Проверка».
- Push — **не** здесь; только по явному go (commit-ops).

## Отчёт

Сделано | Не сделано + команды + PASS/FAIL (2–3 строки) + A/B/C + `Коммит: <хеш>`.

## Обязательно в конце

После успешного GREEN: `Next: /review`  
После только RED: `Next: /sbr` (GREEN) или ждать `go`
