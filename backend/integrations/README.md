# Integrations — внешние CRM

| Файл | За что |
|------|--------|
| `bitrix24.py` | REST по входящему вебхуку: list/get, маппинг полей, массовый импорт |
| `bitrix24_uf.py` | ИНН/домен/продукты/ОКВЭД/сотрудники из UF-полей лида |
| `bitrix24_related.py` | company/contact/requisites → enrich полей Lead |
| `bitrix24_timeline.py` | activity + comments → `lead_communication_logs` |
| `bitrix24_upsert.py` | upsert лида + таймлайн (общий для import/webhook/poll) |
| `bitrix24_sync.py` | Один лид (upsert), фоновый опрос, состояние синка |
| `telegram/` | Бот: уведомления lead hunt, команды /status /queue, polling |
| `crm_sync/csv_adapter.py` | CSV импорт/экспорт лидов, dedup по email/ИНН/bitrix_lead_id |
| `crm_sync/bitrix_adapter.py` | Push лида SmartCRM → Битрикс24 (`crm.lead.add/update`) |
| `crm_sync/amo_adapter.py` | Импорт/экспорт лидов AmoCRM |
| `crm_sync/hubspot_adapter.py` | Импорт/экспорт сделок HubSpot |
| `amo_crm.py` | HTTP-клиент AmoCRM API v4 |
| `hubspot_crm.py` | HTTP-клиент HubSpot Deals API |
| `crm_sync/base.py` | Протоколы pull/push для адаптеров CRM |

Переменные: `BITRIX24_WEBHOOK_URL`, `BITRIX_AUTO_SYNC_MINUTES`, `BITRIX_SYNC_MODIFY_DAYS`, `BITRIX_SYNC_BATCH_SIZE`, `BITRIX_OUTBOUND_TOKEN`.  
Telegram: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `TELEGRAM_NOTIFY_ENABLED`, `TELEGRAM_POLL_ENABLED`.  
AmoCRM: `AMO_SUBDOMAIN`, `AMO_ACCESS_TOKEN`. HubSpot: `HUBSPOT_ACCESS_TOKEN`.  
Роуты: `api/routes/leads/bitrix_routes.py`, `amo_routes.py`, `hubspot_routes.py`, `api/routes/webhooks_bitrix.py`.
