# Ф3 — A/B промптов по трейсам Hermes

**PRD_MAP:** Self-improvement → A/B промптов по трейсам.

## Критерии

| # | Пункт | Проверка |
|---|-------|----------|
| 1 | Кейсы из 👎 трейсов | `collect_bad_trace_cases` |
| 2 | Baseline vs variant | `run_prompt_ab_on_traces` |
| 3 | API | `POST /api/ops/hermes/prompt/ab-traces` |
| 4 | UI | `/ops/intents/improve` — блок «A/B по плохим трейсам» |
| 5 | Эталон intent | подтягивается из eval-сценария с той же фразой |

## Команды

```bash
cd backend
python -m pytest tests/core/test_prompt_ab_traces.py tests/core/test_hermes_eval.py -q
```

## Поток

1. 👎 на `/ops/traces` (или ошибка в трейсе)
2. Опционально: «в сценарий eval» с правильным intent
3. `/ops/intents/improve` — правка промпта в редакторе
4. **A/B по трейсам** — сравнение с сохранённым промптом (hermes3)
5. Если лучше → сохранить → снимок на «Обзор»

## Файлы

- `core/prompt_ab_traces.py`
- `core/eval_runner.py` — `system_prompt` override
- `api/routes/ops/hermes_routes.py`
