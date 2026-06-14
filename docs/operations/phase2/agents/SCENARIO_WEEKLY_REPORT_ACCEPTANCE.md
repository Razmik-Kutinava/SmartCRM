# Сценарий weekly report — acceptance (Ф2 §2 п.395)

**PRD_MAP:** «Сценарий: еженедельный отчёт»

## Было

- «Еженедельный отчёт» голосом не запускал fanout агентов
- `analytics_report` только navigate на `/leads/analytics` без синтеза
- Нет modal с KPI + решением стратега по неделе

## Стало

| Компонент | Изменение |
|-----------|-----------|
| `scenarios/weekly_report.py` | intent `weekly_report`, analyst+economist+marketer |
| `scenarios/report_context.py` | CRM-метрики из `read_leads` + `compute_analytics` |
| `supervisor` + `rescue` | parallel fanout 3 агента + CPU-маршрут |
| `analyst` / `economist` / `marketer` | `_analyze_weekly_*` |
| `strategist` | executive summary недели |
| `voice_action` | modal + `payload.report` KPI, route `/leads/analytics` |
| `VoiceActionHost` | блок KPI dashboard |
| `module_contract` | module `analytics`, ui `modal` |

## Критерии

- [x] «еженедельный отчёт» → `weekly_report`, agents analyst+economist+marketer, parallel
- [x] Strategist синтезирует решение → modal `payload.synthesis`
- [x] KPI в `payload.report` + секции analysis/economics/marketer
- [x] pytest зелёный

## Не в scope

- п.396 (похожие клиенты)
- live LLM eval weekly_report фраз

## Коммит

См. CHANGELOG текущего шага.
