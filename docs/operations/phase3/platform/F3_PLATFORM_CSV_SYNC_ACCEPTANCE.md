# Платформа — CSV лиды (acceptance)

**PRD_MAP:** «Импорт/экспорт … CSV» (шаг 1)

## Было

- Массовый импорт лидов только через Битрикс / lookalike / ручное создание
- Экспорт CSV — только аналитика воронки, не вся база

## Стало

| Компонент | Изменение |
|-----------|-----------|
| `integrations/crm_sync/csv_adapter.py` | parse, dedup (bitrix_lead_id / inn / email), export |
| `POST /api/leads/import-csv` | загрузка `.csv`, mode `upsert` \| `skip` |
| `GET /api/leads/export?format=csv` | все лиды |
| `/leads/list` | кнопки «Импорт CSV» / «Экспорт CSV» |

## Критерии

- [x] Импорт из выгрузки любой CRM (стандартные колонки + русские заголовки)
- [x] Повторный импорт обновляет по email/ИНН/bitrix_lead_id (upsert)
- [x] Экспорт полной базы для миграции / бэкапа
- [x] pytest unit + API

## Дальше (не этот шаг)

- Битрикс push (шаг 2), AmoCRM, HubSpot — отдельные шаги MAP
