# §7 Тендеры + голос — acceptance (Ф2)

## Scope

Агентский анализ документации, голосовые команды, связь тендера с лидом.

## Команда

```powershell
cd backend
python -m pytest tests/api/test_tenders_section7.py tests/agents/scenarios/test_tender_evaluation.py tests/smoke/test_voice_layer_ui.py tests/test_tender_sources.py -q
```

## Закрыто

| PRD_MAP | Что |
|---------|-----|
| Агентский анализ документации | `POST /api/tenders/evaluate` + document_text; UI «Полная оценка»; `/analyze` tender/tech |
| Голосовые команды | `evaluate_tender` modal; `search_tenders`/`list_tenders` navigate + voice context |
| Связь лида со сделкой | `linked_lead_id`; `link-lead` / `create-lead`; `tenderLink` на карточке лида |

## API

- `POST /api/tenders/evaluate` — fanout tech∥economist→strategist
- `POST /api/tenders/saved/{id}/link-lead` — `{ lead_id }`
- `POST /api/tenders/saved/{id}/create-lead`

## UI

- `/tenders` — голосовой контекст, полная оценка, привязка/создание лида
- `/leads/{id}` — блок `tenderLink`

## Связь с Ф2 §2

Сценарий `evaluate_tender` — [`SCENARIO_TENDER_EVALUATION_ACCEPTANCE.md`](../../phase2/agents/SCENARIO_TENDER_EVALUATION_ACCEPTANCE.md)
