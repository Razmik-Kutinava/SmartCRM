# P3 — экспорт отчёта по баллам и воронке (acceptance)

**PRD_MAP:** «Экспорт отчёта по баллам и воронке»

## Было

- `scoreAdvisory` только в карточке лида и списке
- Общая аналитика `/api/leads/analytics/export` без breakdown баллов по лидам

## Стало

| Объект | API | Форматы | UI |
|--------|-----|---------|-----|
| Баллы + воронка | `GET /api/leads/scoring/export` | csv, xlsx, pdf | `/leads/analytics` — кнопка «Баллы» |

**Содержимое отчёта:**
- KPI: ср. балл менеджера, ср. подсказка, число расхождений
- Воронка по стадиям: count + avg manager / suggested score
- Распределение приоритетов (critical/high/medium/low)
- Лист лидов: company, stage, managerScore, suggestedScore, priority, warnings, просрочки

**Код:** `core/scoring_funnel_report.py`, `export_reports.scoring_*`, `scoring_export_routes.py`.

## Критерии

- [x] CSV / Excel / PDF скачиваются
- [x] Учитываются фильтры `period`, `source` (как аналитика)
- [x] pytest unit + API

## Ручная проверка

1. `/leads/analytics` → «Баллы» → Excel — лист Leads с баллами.
2. Лид с просроченной задачей — в отчёте warningsCount > 0.

## Отложено

- Живой smoke DevTools — по желанию оператора
