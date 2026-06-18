# Платформа — экспорт Excel/PDF (acceptance)

**PRD_MAP:** «Экспорт Excel/PDF (воронка, карточка, тендеры)»

## Было

- Аналитика: только **CSV** (`GET /api/leads/analytics/export`)
- Карточка лида и списки тендеров — без выгрузки файлов

## Стало

| Объект | API | Форматы | UI |
|--------|-----|---------|-----|
| Воронка / KPI | `GET /api/leads/analytics/export` | csv, **xlsx**, **pdf** | `/leads/analytics` — селект + кнопка |
| Карточка лида | `GET /api/leads/{id}/export` | **pdf** | кнопка «PDF» в шапке карточки |
| Мои / архив тендеров | `GET /api/tenders/saved/export` | **xlsx**, **pdf** | вкладки «Мои» / «Архив» |

**Код:** `core/export_reports.py` (openpyxl + fpdf2), роуты `export_routes.py`, расширение `analytics_routes` / `saved_routes`.

## Критерии

- [x] Excel воронки: листы KPI, Sources, Forecast
- [x] PDF воронки и карточки лида (кириллица: Arial на Windows / latin-1 fallback)
- [x] Excel/PDF списка сохранённых тендеров
- [x] pytest unit + API

## Ручная проверка

1. `/leads/analytics` → Excel/PDF — файл скачивается, открывается.
2. Карточка лида → PDF — поля компании/стадии на месте.
3. `/tenders` → Мои → Excel — таблица с сохранёнными тендерами.

## Отложено

- Telegram-бот → `BACKLOG.md` (нужен токен BotFather)
