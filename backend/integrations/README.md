# Integrations — внешние CRM

| Файл | За что |
|------|--------|
| `bitrix24.py` | REST по входящему вебхуку: list/get, маппинг полей, массовый импорт |
| `bitrix24_uf.py` | ИНН/домен/продукты/ОКВЭД/сотрудники/лицензия UF → `bitrix_extra` |
| `bitrix24_uf_labels.py` | Кэш подписей UF (`crm.lead.userfield.list`) для hint-поиска |
| `bitrix24_related.py` | company/contact/requisites + **все контакты** (`crm.lead.contact.items`) → `contacts` JSON |
| `bitrix24_products.py` | productrows лида/сделок/КП + UF + opportunity → `lead_products` |
| `bitrix24_timeline.py` | activity + comments → `lead_communication_logs` |
| `bitrix24_timeline_extra.py` | «Создан лид», logmessage (бизнес-процессы) в таймлайн |
| `bitrix24_tasks.py` | встречи/дела/звонки (`crm.activity`) + опц. `tasks.task` → `tasks` |
| `bitrix24_upsert.py` | upsert лида + таймлайн (общий для import/webhook/poll) |
| `bitrix24_sync.py` | Один лид (upsert), фоновый опрос, состояние синка |
| `telegram/` | Бот: уведомления lead hunt, команды /status /queue, polling |
| `crm_sync/csv_adapter.py` | CSV импорт/экспорт лидов, алиасы колонок, scoped dedup по метке базы, `import_leads_from_rows` (`source` жёстко / `source_fallback` из имени файла) |
| `crm_sync/import_table.py` | Экран импорта: `read_table` (CSV/XLSX → заголовки+строки), `guess_mapping`, `rows_to_dicts`, `IMPORT_FIELDS`, имя базы из файла |
| `crm_sync/xlsx_adapter.py` | Разбор .xlsx → строки для импорта лидов (legacy-путь `import_leads_from_xlsx`) |
| `crm_sync/bitrix_adapter.py` | Push лида SmartCRM → Битрикс24 (`crm.lead.add/update`) |
| `crm_sync/amo_adapter.py` | Импорт/экспорт лидов AmoCRM |
| `crm_sync/hubspot_adapter.py` | Импорт/экспорт сделок HubSpot |
| `amo_crm.py` | HTTP-клиент AmoCRM API v4 |
| `hubspot_crm.py` | HTTP-клиент HubSpot Deals API |
| `crm_sync/base.py` | Протоколы pull/push для адаптеров CRM |

Переменные: `BITRIX24_WEBHOOK_URL`, `BITRIX_AUTO_SYNC_MINUTES`, `BITRIX_SYNC_MODIFY_DAYS`, `BITRIX_SYNC_BATCH_SIZE`, `BITRIX_OUTBOUND_TOKEN`.  
**Scope вебхука:** `crm` + `user` + **`task`**. Проверка: `scripts/check_bitrix_webhook_scopes.py` → `data/bitrix_webhook_scope_report.json`. Acceptance: `docs/operations/phase4/leads/F4_X5_WEBHOOK_TASK_SCOPE_ACCEPTANCE.md`.
Telegram: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `TELEGRAM_NOTIFY_ENABLED`, `TELEGRAM_POLL_ENABLED`.  
AmoCRM: `AMO_SUBDOMAIN`, `AMO_ACCESS_TOKEN`. HubSpot: `HUBSPOT_ACCESS_TOKEN`.  
Роуты: `api/routes/leads/bitrix_routes.py`, `amo_routes.py`, `hubspot_routes.py`, `api/routes/webhooks_bitrix.py`.
