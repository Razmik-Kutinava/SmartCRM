# Agents — AI-агенты

LangGraph-агенты для анализа лидов, стратегии, писем. Оркестратор связывает их с голосовыми интентами Hermes.

---

## Пакет `analyst/` — аналитик компании

| Файл | За что |
|------|--------|
| `analyze.py` | Главный анализ профиля |
| `runner.py` | Запуск с контекстом |
| `formatters.py` | Форматирование ответа |
| `prompts_data.py` | Тексты промптов |

Импорт: `from agents.analyst import ...`

---

## Файлы в корне `agents/`

| Файл | За что |
|------|--------|
| `orchestrator.py` | Маршрутизация интентов → supervisor → LangGraph fanout |
| `supervisor.py` | Выбор подмножества агентов (Hermes agents[] или дефолт) |
| `fanout_parallel.py` | Параллельный gather 2+ агентов, merge state, метрики fanout |
| `scenarios/analysis_email.py` | Именованный сценарий «анализ + письмо» (analyze_and_email) |
| `scenarios/tender_evaluation.py` | Сценарий «оценка тендера» (tech∥economist) |
| `scenarios/tender_context.py` | Слоты тендера → контекст агентов |
| `scenarios/weekly_report.py` | Сценарий «еженедельный отчёт» (analyst∥economist∥marketer) |
| `scenarios/report_context.py` | CRM-метрики для еженедельного отчёта |
| `scenarios/similar_clients.py` | Сценарий «похожие клиенты» (analyst∥marketer) |
| `scenarios/similar_context.py` | Lookalike: won/эталон → search_by_portrait |
| `graph.py` | LangGraph: supervisor → fanout → strategist |
| `base.py` | Базовый класс агента |
| `tools.py` | Общие tools; CLI gate — заголовок `X-API-Key` из `SMARTCRM_API_KEY` |
| `marketer.py` | Агент-маркетолог |
| `marketer_gate_enrich.py` | Дополнение marketer_output для eval gate |
| `analyst_gate_enrich.py` | Дополнение analyst_output для eval gate |
| `strategist.py` | Агент-стратег |
| `tech_specialist.py` | Агент по IT/технологиям |
| `tech_gate_enrich.py` | Дополнение tech_output для eval gate (ключевые слова) |
| `economist_gate_enrich.py` | Дополнение economist_output для eval gate |
| `strategist_gate_enrich.py` | Дополнение strategist_output по скору аналитика |
| `economist.py` | Агент-экономист (скор, ROI) |

## Типичный поток

```
Hermes intent → orchestrator.run_agents()
  → ask_marketer / ask_strategist / …
  → run_pipeline / search_by_portrait (лидоген-интенты)
```
