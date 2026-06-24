# Ф4 — mass-resync полей Битрикс (bitrix_extra, contacts, deal_amount)

**Цель:** выгрузить из Битрикс24 в CRM все UF лицензии/подписки, мультиконтакты и сумму сделки **без потери данных** и без затирания ручных правок.

## Скрипты

| Команда | Назначение |
|---------|------------|
| `python scripts/check_bitrix_fields_backfill.py` | Счётчики в БД + `data/bitrix_fields_resync_state.json` |
| `python -u scripts/resync_bitrix_lead_fields.py --workers 3 --batch-size 25 --delay-ms 20` | Полный прогон |
| `python -u scripts/resync_bitrix_lead_fields.py --resume` | Продолжить с последнего `processed` |
| `python -u scripts/resync_bitrix_lead_fields.py --offset 40` | С указанного смещения |
| `python -u scripts/resync_bitrix_lead_fields.py --no-api` | Только UF из `tech_json` (offline) |

## Что синкается

- `bitrix_extra` — подписка, тип поставки, лицензия, повторный лид…
- `contacts[]` — все контакты лида (`crm.lead.contact.items`)
- `deal_amount` / `deal_currency` — OPPORTUNITY + CURRENCY_ID

**Лёгкий enrich** (`enrich_fields_for_resync`): без productrows/КП/сделок — иначе прогон зависает на часах.

## Merge (без потери)

- `merge_bitrix_contacts` — ручные контакты CRM не затираются
- `merge_bitrix_extra` — пустые UF не стирают заполненные поля
- `deal_amount` — не затирается пустым при upsert

## Состояние прогона

Файл: `backend/data/bitrix_fields_resync_state.json`

```json
{
  "status": "running|done|failed",
  "processed": 120,
  "total_b24": 3225,
  "updated": 115,
  "with_bitrix_extra": 80,
  "eta_sec": 3600
}
```

## Портал crm.agneko.com — числовые UF (REST без подписей)

| UF поле | bitrix_extra |
|---------|----------------|
| `UF_CRM_1684590906` | `subscription_end` (date) |
| `UF_CRM_1684590938` | `delivery_type` или `license_registration` (если email) |
| `UF_CRM_1697732648936` | `reserved_until` (date) |
| `UF_CRM_1704976364045` | `license_registration` (домен) |
| `UF_CRM_1706632424941` = 1 | `is_repeat_lead` |

Код: `core/lead_bitrix_extra.py` + кэш `data/bitrix_lead_uf_labels.json` (опционально).

## Инцидент 2026-06-24 (Access denied)

**Симптом:** после первой пачки `25/3225` (`extra 25` в БД) — `crm.lead.get: HTTP 400 Access denied`.

**Вероятная причина:** лимит REST при `workers=3` + параллельный `BITRIX_AUTO_SYNC` / uvicorn `--reload`.

**Фикс в скрипте:** retry до 5× с backoff на `access denied`; не валить весь прогон.

**Оператору:** `BITRIX_AUTO_SYNC_MINUTES=0` на время прогона; перезапуск:
`python -u scripts/resync_bitrix_lead_fields.py --resume --workers 1 --delay-ms 80`

## Инцидент 2026-06-24 (зависание 40/3225)

**Симптом:** прогон остановился на `40/3225`, `extra 0`.

**Причина:** (1) старый enrich тянул productrows; (2) UF на портале — `UF_CRM_1684590906` без семантических имён, hint не срабатывал.

**Фикс:** `enrich_fields_for_resync`, таймаут 90 с, `--resume`, state-файл, **явный маппинг agneko UF** в `lead_bitrix_extra.py`.

## Рекомендации оператору

1. На время mass-resync: `BITRIX_AUTO_SYNC_MINUTES=0` в `.env` или uvicorn **без** `--reload`
2. Не запускать два resync параллельно
3. После прогона: `check_bitrix_fields_backfill.py` → сверить `with_sub` / `with_deal`
4. Scope **task** на вебхуке — отдельно (`resync_bitrix_lead_tasks.py`)

## ETA (ориентир)

~3–8 REST на лид × 3225 ÷ workers(3) ≈ **2–4 часа** при `delay-ms 20`.
