# Hermes modules — acceptance (Ф2 Voice Layer §1)

## Scope

`module` + `intent` + `ui_action` для модулей **email, search, analytics, agents, RAG** (лиды — Ф1).

## Команда

```powershell
cd backend; python scripts/smoke_hermes_modules.py
```

## Матрица (rescue + контракт)

| module | intent | ui_action | route |
|--------|--------|-----------|-------|
| email | list_emails | navigate | `/email` |
| email | write_email | modal | `/email` |
| email | send_email | approve | `/email` |
| search | search_web | navigate | `/search` |
| analytics | analytics_funnel | navigate | `/leads/analytics` |
| analytics | analytics_score | filter | `/leads/list` |
| agents | ask_economist | modal | — |
| rag | ask_rag | modal | `/search` |
| rag | save_to_rag | approve | `/search` |

## Файлы

| Зона | Путь |
|------|------|
| Контракт | `core/hermes/module_contract.py` |
| Промпт | `core/hermes/prompts_data.py` |
| Rescue | `core/hermes/rescue.py` |
| RAG voice | `voice/rag_context.py` |
| voice_action | `voice/voice_action.py` |
| Pipeline | `voice/pipeline.py` |
| Тесты | `tests/core/test_hermes_modules.py`, `tests/voice/test_rag_context.py` |

## Хвост (BACKLOG)

- LLM eval-кейсы для analytics/RAG (не только rescue)
- UI: чтение `payload.period` / `minScore` на `/leads/analytics` и списке
- Live send_email после approve
