# Ф4 — X5-gap шаг 3: сумма + валюта (deal_amount)

**PRD_MAP:** «Сумма + валюта» · «UI карточки X5-gap» (шапка `15 780 $`).

**Код:** ✅ закрыт (`85f88ef`, `cd62bbf`). **Данные:** mass-resync `resync_bitrix_lead_fields.py` (OPPORTUNITY + CURRENCY_ID → `deal_amount` / `deal_currency`).

---

## Цепочка данных

```
Битрикс crm.lead.get
  OPPORTUNITY + CURRENCY_ID
    → row_to_lead_fields (integrations/bitrix24.py)
    → deal_amount / deal_currency / budget
    → API GET /api/leads/{id}: amount + currency
    → UI formatDealAmountLabel → «15 780 $»
```

**Merge:** пустой `deal_amount` из upsert не затирает уже заполненное (`merge_bitrix_field_updates`).

---

## Эталон для browser-апрува

| Поле | Значение |
|------|----------|
| Bitrix lead ID | **5227** (ИКС 5) |
| CRM URL | `/leads/289` (id может отличаться — ищи по `bitrix_lead_id=5227`) |
| OPPORTUNITY | 15780 |
| CURRENCY_ID | USD |
| Ожидаемая подпись в шапке | **`15 780 $`** (`data-testid="lead-card-deal-amount"`) |
| Панель «Суммы сделки» | та же подпись в блоке карточки |

**API smoke (без браузера):**

```bash
cd backend
python -m pytest tests/lib/test_lead_card_money.py::test_format_deal_amount_label_usd tests/api/test_leads_api.py::test_lead_deal_amount_currency_in_api tests/core/test_lead_deal_amount.py -q
```

**Проверка БД:**

```bash
python scripts/check_bitrix_fields_backfill.py
# deal_amount: N / bitrix_lead_id: 3228
```

---

## 👤 Чеклист оператора (browser)

1. Открыть `http://127.0.0.1:5173/leads/289` (или id лида с `bitrix_lead_id=5227`).
2. В шапке карточки — amber текст **`15 780 $`** рядом с названием.
3. Прокрутить панель «Карточка» / «Суммы сделки» — дублирование суммы с валютой.
4. Лид без OPPORTUNITY (например bitrix `4008`) — сумма не показывается или fallback `budget`, без `$` от пустого amount.
5. После mass-resync: выборочно 3 лида с суммой в Битриксе — сверить с порталом.

**Критерий закрытия шага 3:** backfill **≥95%** b24-лидов с ненулевым OPPORTUNITY в Битриксе (или полный прогон `status=done`) + пункты 1–3 чеклиста **ок**.

---

## Backfill (шаг 6 — тот же скрипт)

```bash
cd backend
python -u scripts/resync_bitrix_lead_fields.py --resume --workers 2 --batch-size 20 --delay-ms 100
python scripts/check_bitrix_fields_backfill.py
```

Runbook: [`F4_BITRIX_FIELDS_RESYNC.md`](F4_BITRIX_FIELDS_RESYNC.md).

---

## Статус

| Часть | Статус |
|-------|--------|
| Код API + UI | ✅ |
| Mirror-тест `15 780 $` | ✅ `test_lead_card_money.py` |
| Mass backfill | 🔄 in_progress (см. `check_bitrix_fields_backfill.py`) |
| 👤 Browser апрув | 🔲 |
