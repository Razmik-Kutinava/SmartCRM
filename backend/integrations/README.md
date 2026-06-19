# Integrations — внешние CRM

| Файл | За что |
|------|--------|
| `bitrix24.py` | REST по входящему вебхуку: list/get, маппинг полей, массовый импорт |
| `bitrix24_sync.py` | Один лид (upsert), фоновый опрос, состояние синка |
| `telegram/` | Бот: уведомления lead hunt, команды /status /queue, polling |
| `crm_sync/csv_adapter.py` | CSV импорт/экспорт лидов, dedup по email/ИНН/bitrix_lead_id |
| `crm_sync/base.py` | Протоколы pull/push для адаптеров CRM |

Переменные: `BITRIX24_WEBHOOK_URL`, `BITRIX_AUTO_SYNC_MINUTES`, `BITRIX_OUTBOUND_TOKEN`.  
Telegram: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `TELEGRAM_NOTIFY_ENABLED`, `TELEGRAM_POLL_ENABLED`.  
Роуты: `api/routes/leads/bitrix_routes.py`, `api/routes/webhooks_bitrix.py`.
