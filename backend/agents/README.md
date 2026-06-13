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
| `orchestrator.py` | Маршрутизация интентов → агенты / leadgen |
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
