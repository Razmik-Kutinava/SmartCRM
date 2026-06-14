# §6 Аналитика + голос — acceptance (Ф2)

## Scope

Голосовые команды Hermes → `/leads/analytics` с фильтрами и `/leads/list` по скору.

## Команда

```powershell
cd backend
python -m pytest tests/lib/test_analytics_metrics.py tests/core/test_hermes_modules.py tests/smoke/test_analytics_baseline_smoke.py tests/smoke/test_voice_layer_ui.py tests/agents/scenarios/test_weekly_report.py -q
```

## Закрыто

| PRD_MAP | Что |
|---------|-----|
| «Воронка за период» | `analytics_funnel` → navigate `?period=&view=funnel` + API filter |
| «Цикл сделки / средний чек» | `analytics_cycle` → KPI avgDealRub/avgCycleDays + view=cycle |
| «Лиды со скором > N» | `analytics_score` → filter minScore на `/leads/list` |
| «Конверсия по источнику» | `conversionBySource` + `analytics_conversion` |
| Навигация `/leads/analytics` с фильтром | voice_action route query + UI voice context |

## API

- `GET /api/leads/analytics/summary?period=month&source=email`
- `GET /api/leads/analytics/export?period=month`

Ответ: `filters`, `conversionBySource`, воронка, KPI.

## UI

- `/leads/analytics` — бейдж голосового контекста, подсветка view (funnel/cycle/conversion)
- `/leads/list` — `voiceLeadFilter.minScore`

## Eval

Rescue: `tests/core/test_hermes_modules.py` (analytics_* intents).
