# voice_action UI — acceptance (2026-06-08)

## Scope (PRD_MAP п.3)

Модалка / навигация / фильтр / апрув по контракту `ARCHITECTURE.md#контракт-voice_action`.

## Команды

```powershell
cd backend; python -m pytest tests/voice/test_voice_action.py tests/api/test_voice_action_ws.py -q
cd backend; python scripts/smoke_voice_action.py
```

## Что сделано

| Зона | Файлы |
|------|--------|
| Сборка пакета | `backend/voice/voice_action.py` |
| Pipeline + WS | `voice/pipeline.py`, `api/routes/voice.py` → события `intent` + `voice_action` |
| Фронт диспетчер | `frontend/src/lib/voice/voiceAction.js` |
| Оверлеи | `frontend/src/components/VoiceActionHost.svelte` |
| Layout WS | `frontend/src/routes/+layout.svelte` |
| Фильтр списка | `voiceLeadFilter` store → `leads/list/+page.svelte` |
| Апрув delete | `delete_lead` только после подтверждения в модалке |

## Поведение `ui`

| ui | Действие |
|----|----------|
| `navigate` | `goto(route)` |
| `filter` | store фильтров + `/leads/list` |
| `modal` | оверлей (анализ, черновик письма, send → `/email`) |
| `approve` | блокирующее подтверждение (delete) |

## Хвост (не этот пункт)

- Полные интенты (история, аналитика) — PRD_MAP п.4
- E2E смоук микрофон → UI — п.5
- Hermes `ui_action` для всех модулей — Фаза 2
