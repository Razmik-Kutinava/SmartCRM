# Hermes → интенты по лидам — acceptance (2026-06-08)

## Что это

Hermes разбирает голос/текст в JSON: `intent` + `slots` + `agents`.  
Базовые интенты лидов: **create_lead**, **update_lead** (вкл. стадию), **delete_lead**, **list_leads**, **create_task**.

## Команда

```powershell
cd backend; python scripts/smoke_hermes_leads.py
```

40 pytest (детерминированные rescue/fastpath + voice API + orchestrator list_leads).  
LLM-интеграция `TestHermesIntents` — отдельно: `pytest tests/core/test_hermes_eval.py::TestHermesIntents -v`

## Покрытие

| Зона | Файлы |
|------|--------|
| slot_normalize + rescue | `core/hermes/slot_normalize.py`, `rescue.py` |
| CPU-маршруты лидов | `tests/core/test_hermes_lead_rescue.py` |
| eval cases.jsonl (parser) | `tests/core/test_hermes_eval.py` |
| HTTP `/api/voice/command` | `tests/smoke/test_hermes_leads_smoke.py` |
| Orchestrator | `tests/test_voice_pipeline.py` |

## Исправления в шаге

- `slot_normalize.py` — агенты → `analyst`, алиасы слотов, извлечение company/phone из текста
- `rescue.py` — порядок update/task перед create; слоты delete/list/update
- `fastpath` — list hot/new, delete, create_task, noop «создай два»

## Хвост (не этот пункт)

- **Полный набор интентов** (история, аналитика, фильтры) → PRD_MAP следующий пункт
- **voice_action UI** → отдельный пункт
- **3 LLM eval-кейса** — flaky Groq слоты; опциональный прогон, не блокер смоука
