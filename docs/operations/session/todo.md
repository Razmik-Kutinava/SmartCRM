# todo — микро-чеклист текущей фичи

## Заказ (дословно)

> C — Полный пакет  
> B + zone-notes Ф4 + owner-checks + эконом-режим в gates + опц. crit-ledger для PII/голоса.  
> ебашь чтобы у нас все было лучшее и могли экономить токены и все все что нужно и чтобы качество кода не терялось  
> ебашь

**Как понял:** перенести из CoffeeOS+APU slash-SBR, ctx-trim, шапка-only старт, ZONE_NOTES, OWNER_CHECKS, эконом-gates, CRITICAL_LEDGER; зону/A/B/C/push-по-go/PHASE 0 не ослаблять.

## Файлы (ожидаемо)

- `.cursor/rules/workflow/smartcrm-context-hygiene.mdc`
- `.cursor/commands/{start,spec,sbr,review,ctx-trim,crit-audit,README}.md`
- `.cursor/skills/ctx-trim/SKILL.md`
- правки: task-workflow, SBR, dev-gates, index, RULES_MATRIX
- `docs/operations/phase4/{ZONE_NOTES,OWNER_CHECKS}.md`
- `docs/operations/session/CRITICAL_LEDGER.md`

## Читать

- CoffeeOS: context-hygiene, agent-workflow (шапка/explore), commands, эконом-gates
- APU: trim, main (reading budget), owner-checks, crit-audit K1–K5
- SmartCRM: index, task-workflow, SBR, RULES_MATRIX (не весь HANDOFF)

## Не ломать

- Зонная регрессия на GREEN
- A/B/C + check_step + push только по go
- PHASE 0 дословный заказ

## Проверка

- `cmd /c scripts\check_step.cmd`
- `python scripts/verify_cursor_rules_precedence.py` (если есть)

## Чеклист микро

- [x] context-hygiene + /ctx-trim + skill
- [x] slash start/spec/sbr/review/README + crit-audit
- [x] task-workflow шапка-only + намерение + explore
- [x] SBR: Читать/Файлы/Не ломать + slash
- [x] эконом-режим в dev-gates
- [x] ZONE_NOTES + OWNER_CHECKS + CRITICAL_LEDGER
- [x] RULES_MATRIX R16–R20 + ops шапки
- [x] check_step + commit

## Не вошло

Перенос Entire/Fly/auto-push; снятие alwaysApply с SBR/dev-gates (качество важнее токенов).
