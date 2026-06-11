# Аналитика baseline — acceptance (2026-06-11)

PRD_MAP: **«Аналитика (базовая)»** · Ф1 baseline **закрыт** (кроме голоса → Ф2).

## Команда

```bash
cd backend && python scripts/smoke_analytics_baseline.py
```

## Источник данных

| Метрика | Откуда | Мок? |
|---------|--------|------|
| Воронка по этапам | `GET /api/leads` → `stage` | Нет |
| Конверсия | `Выигран / всего × 100` | Нет |
| Средний чек | `amountRub` (или `budget`) у выигранных | Нет |
| Цикл сделки | `createdAt` → `updatedAt` у выигранных | Нет |
| Экспорт | `GET /api/leads/analytics/export` (CSV) | Нет |

Канон UI: **`/leads/analytics`**. Старый **`/analytics`** (mock) → **308** на `/leads/analytics`.

## Закрыто

| # | Пункт | Проверка |
|---|--------|----------|
| 1 | Воронка | KPI-карточки + бары по `CRM_STAGES` |
| 2 | Конверсия | `%` + win-rate среди закрытых |
| 3 | Средний чек | ₽ по выигранным с суммой |
| 4 | Цикл сделки | дни (если есть выигранные с датами) |
| 5 | Экспорт | кнопка → CSV `metric,value` + `stage,count,pct` |
| 6 | API | `GET /api/leads/analytics/summary` |

## DevTools (2026-06-11)

- URL: `http://localhost:5173/leads/analytics`
- h1: «Аналитика CRM»
- Данные из БД (3184 лида, не mock 48)
- Экспорт: `fetch /api/leads/analytics/export` → 200, `text/csv`

## Не в scope Ф1

| Пункт | Куда |
|-------|------|
| Голосовые запросы к метрикам | Фаза 2 (`PRD_MAP` п.188) |
| Тренды «+1.2% к прошлому месяцу» | Ф2 / углублённая аналитика |
| Период-фильтр «Апрель 2026» | Ф2 |
