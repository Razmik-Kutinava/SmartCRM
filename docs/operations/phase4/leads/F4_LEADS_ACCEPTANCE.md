# Ф4 — Лиды (обход и доводка)

**Порядок в MAP:** сразу после блока «Дашборд». Личный обход `/leads/*` владельцем.

---

## П.1 — Создание лида

**Сделано (2026-06-19):** модалка `LeadCreateModal` — дашборд «Быстрые действия» + `/leads/list` → POST `/api/leads`.

См. также: [`../dashboard/F4_DASHBOARD_ACCEPTANCE.md`](../dashboard/F4_DASHBOARD_ACCEPTANCE.md) · pytest `test_lead_create_ui.py` · апрув «ок».

---

## П.2 — Удаление лида

**Было:** кнопка «Удалить» только при hover на списке; на карточке не было; DELETE без `apiDelete` (401 при ключе); FK nurture/email блокировали удаление.

**Стало:**
- `confirmAndDeleteLead` — confirm + `apiDelete` + кэш
- `/leads/list` — кнопка «Удалить» всегда видна (`leads-list-delete-lead`)
- `/leads/{id}` — «🗑 Удалить» в шапке (`lead-card-delete`) → редирект на список
- Backend: `_purge_lead_dependencies` (nurture, email, тендеры) перед DELETE

### Критерии приёмки

| # | Проверка | Статус |
|---|----------|--------|
| 1 | Список → «Удалить» → confirm → лид исчезает, GET 404 | ✅ апрув 2026-06-19 |
| 2 | Карточка → «Удалить» → confirm → переход на список, лид нет в БД | ✅ апрув 2026-06-19 |
| 3 | Лид с цепочкой nurture удаляется без 500 | pytest |
| 4 | pytest `test_lead_delete_ui.py` + `test_leads_api` DELETE — PASS | ✅ |

### testid

- `leads-list-delete-lead`
- `lead-card-delete`

---

## Дальше (обход Ф4)

Карточка, фильтры, голос, интеграции — по обходу владельца.
