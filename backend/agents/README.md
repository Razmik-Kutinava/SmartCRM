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
| `graph.py` | LangGraph: supervisor → fanout → strategist |
| `base.py` | Базовый класс агента |
| `tools.py` | Общие tools; CLI gate — заголовок `X-API-Key` из `SMARTCRM_API_KEY` |
| `marketer.py` | Агент-маркетолог |
| `strategist.py` | Агент-стратег |
| `tech_specialist.py` | Агент по IT/технологиям |
| `economist.py` | Агент-экономист (скор, ROI) |

## Типичный поток

```
Hermes intent → orchestrator.run_agents()
  → ask_marketer / ask_strategist / …
  → run_pipeline / search_by_portrait (лидоген-интенты)
```
