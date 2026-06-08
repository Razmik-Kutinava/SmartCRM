# Integrations — внешние CRM

| Файл | За что |
|------|--------|
| `bitrix24.py` | REST по входящему вебхуку: list/get, маппинг полей, массовый импорт |
| `bitrix24_sync.py` | Один лид (upsert), фоновый опрос, состояние синка |

Переменные: `BITRIX24_WEBHOOK_URL`, `BITRIX_AUTO_SYNC_MINUTES`, `BITRIX_OUTBOUND_TOKEN`.  
Роуты: `api/routes/leads/bitrix_routes.py`, `api/routes/webhooks_bitrix.py`.
