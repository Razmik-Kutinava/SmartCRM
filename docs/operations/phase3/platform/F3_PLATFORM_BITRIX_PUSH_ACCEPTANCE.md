# Платформа — Битрикс push (acceptance)

**PRD_MAP:** «Импорт/экспорт … Битрикс24» (шаг 2)

## Было

- Импорт из Б24 (`import-bitrix`, вебхук, опрос)
- Нет выгрузки лида SmartCRM → Битрикс

## Стало

| Компонент | Изменение |
|-----------|-----------|
| `bitrix24.lead_to_bitrix_fields` | обратный маппинг полей |
| `bitrix24.push_lead_to_bitrix` | `crm.lead.add` / `crm.lead.update` |
| `crm_sync/bitrix_adapter.py` | `CrmPushAdapter` |
| `POST /api/leads/{id}/push-bitrix` | API выгрузки |
| карточка лида | кнопка «В Битрикс» |

## Критерии

- [x] Новый лид → `crm.lead.add`, `bitrix_lead_id` сохраняется
- [x] Лид с `bitrix_lead_id` → `crm.lead.update`
- [x] pytest unit + API mock
- [ ] Ручной smoke с живым `BITRIX24_WEBHOOK_URL` (нужен портал)

## Дальше

- AmoCRM, HubSpot — шаги 3–4 MAP
