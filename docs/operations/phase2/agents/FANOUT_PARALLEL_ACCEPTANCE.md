# Fanout parallel — acceptance (Ф2 §2 п.2)

**PRD_MAP:** «Параллельный fanout 2+ агентов»

## Было

- `node_fanout` в `graph.py` вызывал `asyncio.gather`, но без явного контракта и метрик.
- Hermes `parallel: true` не передавался в supervisor/orchestrator.
- В ответе оркестратора не было `fanout_parallel` / `fanout_agent_count`.
- `generate_lead` с 4 агентами шёл только в leadgen pipeline без параллельного обогащения.

## Стало

| Компонент | Изменение |
|-----------|-----------|
| `agents/fanout_parallel.py` | `run_parallel_fanout()` — gather 2+ агентов, merge state, метрики |
| `agents/supervisor.py` | `FanoutPlan.parallel_fanout`, `hermes_parallel`, `is_parallel_fanout()` |
| `agents/graph.py` | fanout node через `run_parallel_fanout` |
| `agents/orchestrator.py` | `hermes_parallel`; leadgen: fanout до pipeline; поля в result |
| `voice/pipeline.py` | `hermes_parallel` из Hermes `parallel` |
| `agents/base.py` | поля `fanout_parallel`, `fanout_agent_count`, `fanout_elapsed_ms` |

## Критерии приёмки

- [x] CRM intents (`run_analysis`, `create_lead`, …) — fanout ≥2 агентов через `asyncio.gather`
- [x] `fanout_parallel: true` в state/result при ≥2 агентах
- [x] Hermes `parallel: true` прокидывается в orchestrator
- [x] `generate_lead`: parallel fanout агентов **до** leadgen pipeline (route остаётся `leadgen`)
- [x] pytest: `tests/agents/test_parallel_fanout.py` + supervisor + voice_pipeline

## Тесты

```bash
cd backend
python -m pytest tests/agents/test_parallel_fanout.py tests/agents/test_supervisor.py tests/test_voice_pipeline.py -q
```

## Не в scope (следующие пункты MAP)

- п.392: синтез в модалку voice_action
- п.393–396: именованные сценарии (анализ+письмо, тендер, отчёт, похожие клиенты)

## Коммит

См. CHANGELOG / HANDOFF текущего шага.
