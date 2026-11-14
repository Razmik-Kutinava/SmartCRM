# /review — PHASE 3 REVIEW

**Канон:** [`spec-build-review.mdc`](../rules/workflow/spec-build-review.mdc) § PHASE 3.

## Порядок

1. **Local зона** — todo «Проверка» / `smartcrm-dev-gates` (если код менялся). Docs/rules-only → `cmd /c scripts\check_step.cmd` (+ `verify_cursor_rules_precedence.py` при rules).
2. Ручной дифф. Hot-path / PII / голос / агенты — **`/crit-audit`** (см. `crit-audit.md`); иначе skip с причиной `skip: не hot-path/PII`.
3. Ops: SESSION_STATE + CHANGELOG + HANDOFF; todo очистить/архивировать указатель; ZONE_NOTES — дописать межзадачные контракты зоны при необходимости.
4. Отчёт: **Сделано | Не сделано** + **B/C** + `Коммит: <хеш>` + регрессия PASS/FAIL.
5. **Стоп.** `git push` / deploy — **только** по явному go владельца (не как CoffeeOS auto-push).

## bugbot / security-review

**Не** автозапуск на каждый review.  
≥2–3 закрытых шага с прошлого батча **или** перед опасным релизом → в отчёте строка `⚠️ Субагенты: пора` (не блокер). Старт — только по явной просьбе.

## OWNER_CHECKS

Если закрыт пакет/пункт фазы с UI — дописать ≤12 пунктов «действие → ожидание» в `docs/operations/phase4/OWNER_CHECKS.md` + «Не проверено агентом». `[x]` в CHECKLIST_F4 — только после «ок» владельца.

## Обязательно в конце

`Next: push/deploy — только по апруву`  
или дыры: `Next: /sbr`  
после пакета: `Next: /start` · при раздутых ops: `Next: /ctx-trim`
