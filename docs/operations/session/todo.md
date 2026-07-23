# todo — микро-чеклист текущей фичи

> **Живой чеклист шага.** Макро-веха — пункт [`Чеклист: Фаза 4 — Тюнинг и MVP`](../phase4/CHECKLIST_F4.md).  
> SBR: PHASE 1 заполняет этот файл → PHASE 3 очищает или архивирует.  
> Канон: [`spec-build-review.mdc`](../../../.cursor/rules/workflow/spec-build-review.mdc)

---

## Заказ (дословно)

> «итак добавляю фичу · хочу чтобы квадраты с описанием как на скрине я мог хватать и передвигатьс ставить что первее что второе» → «ебашь давай как нгадо го хуй го»

**Как понял:** DnD порядка плиток хаба на `/leads/[id]`, persist в localStorage.

---

## Текущая задача

| Поле | Значение |
|------|----------|
| **Пункт чеклиста** | Ф4 · Лиды · DnD порядка плиток хаба |
| **Started** | 2026-07-23 |

---

## Чеклист

- [x] **RED:** `tests/frontend/test_hub_tile_order.py` — 3 FAIL (`40dd5f2`)
- [x] **GREEN:** `hubTileOrder.js` + DnD в `LeadHubTile` / `+page.svelte` + persist — 3 PASS
- [x] Доки: `CHECKLIST_F4.md`, `F4_LEADS_ACCEPTANCE.md` §2b2, `tests/README.md`

## Архив (последние закрытые)

- 2026-07-23 · DnD порядка плиток хаба — RED `40dd5f2`, GREEN+REVIEW
- 2026-07-21 · Ф4 Email «база → рассылка по source»
