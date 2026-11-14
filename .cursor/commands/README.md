# Slash-команды SmartCRM

Цепочка фичи: **`/start` → `/spec` → `/sbr` → `/review`**.  
Вне цепочки: **`/ctx-trim`**, **`/crit-audit`**.

После каждой команды агент пишет одну строку **`Next: /…`**.

| Команда | Фаза | Канон в rules |
|---------|------|----------------|
| [`start.md`](start.md) | Старт / PHASE 0 | `smartcrm-task-workflow` |
| [`spec.md`](spec.md) | PHASE 1 SPEC | `spec-build-review` |
| [`sbr.md`](sbr.md) | PHASE 2 RED→GREEN | `spec-build-review` + `dev-gates` |
| [`review.md`](review.md) | PHASE 3 REVIEW | `spec-build-review` + ops |
| [`ctx-trim.md`](ctx-trim.md) | Гигиена токенов | `smartcrm-context-hygiene` |
| [`crit-audit.md`](crit-audit.md) | K1–K5 PII/голос | `CRITICAL_LEDGER.md` |

**Не отменяют:** зонная регрессия на GREEN · хвост A/B/C · push только по go · `[x]` чеклиста после «ок».

Синонимы апрува шага: `go` · `ебашь` · `дальше` · `сделай` (не deploy/миграция/push).
