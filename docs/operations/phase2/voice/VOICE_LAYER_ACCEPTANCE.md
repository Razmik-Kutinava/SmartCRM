# Voice Layer §1 — acceptance (Ф2)

## Scope

Hermes `module` + `intent` + `ui_action` + фронт voice_action (WS, modal, navigate, filter, approve).

## Команда

```powershell
cd backend
.venv\Scripts\python.exe scripts/smoke_voice_layer.py
# или WSL:
.venv-linux/bin/python scripts/smoke_voice_layer.py
```

## Закрыто

| PRD_MAP | Что |
|---------|-----|
| Hermes modules | `module_contract.py`, rescue, промпт, pytest |
| WS voice_action | `+layout.svelte` → `handleVoiceAction` |
| UI modal | `VoiceActionHost.svelte` — агенты, RAG, email |
| UI navigate | goto route + `/search?q=` + analytics context |
| UI filter | `voiceLeadFilter` + minScore на `/leads/list` |
| UI approve | delete_lead, send_email, save_to_rag |

## Eval (без LLM)

`eval/cases_modules.jsonl` + `tests/core/test_hermes_modules_rescue_eval.py`

Live LLM eval analytics/RAG — опционально, `pytest -m live_eval` при Groq/Ollama.

## Хвост

- Полный live Hermes eval всех модулей через LLM (не rescue)
- E2E Playwright всех модулей (SMOKE_UI=1)
