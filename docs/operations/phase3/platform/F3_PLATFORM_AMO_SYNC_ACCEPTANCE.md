# Платформа — AmoCRM sync (acceptance)

**PRD_MAP:** «Импорт/экспорт … AmoCRM» (шаг 3)

## Стало

| Компонент | Изменение |
|-----------|-----------|
| `amo_crm.py` | клиент API v4 |
| `crm_sync/amo_adapter.py` | import + push |
| `Lead.amo_lead_id` | дедуп |
| `POST /api/leads/import-amo` | импорт |
| `POST /api/leads/{id}/push-amo` | экспорт в Amo |

ENV: `AMO_SUBDOMAIN`, `AMO_ACCESS_TOKEN`.

- [x] pytest unit + API mock
- [ ] Ручной smoke с живым Amo
