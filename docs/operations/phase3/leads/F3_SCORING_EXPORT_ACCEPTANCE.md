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

- [x] 2026-06-19 DevTools: `/leads/analytics` → Excel → «Баллы» → `GET /api/leads/scoring/export?format=xlsx` **200**
- [x] `smoke_scoring_export.py`: pytest 13 + live xlsx (листы KPI/FunnelScores/Leads)

## Отложено

- нет
