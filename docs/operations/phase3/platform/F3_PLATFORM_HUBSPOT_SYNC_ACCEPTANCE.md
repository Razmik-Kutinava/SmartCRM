# Платформа — HubSpot sync (acceptance)

**PRD_MAP:** «Импорт/экспорт … HubSpot» (шаг 4–5)

## Стало

| Компонент | Изменение |
|-----------|-----------|
| `hubspot_crm.py` | Deals API v3 |
| `crm_sync/hubspot_adapter.py` | import + push |
| `Lead.hubspot_deal_id` | дедуп |
| `POST /api/leads/import-hubspot` | импорт сделок |
| `POST /api/leads/{id}/push-hubspot` | экспорт сделки |

ENV: `HUBSPOT_ACCESS_TOKEN`.

- [x] pytest unit + API mock
- [ ] Ручной smoke с живым HubSpot
