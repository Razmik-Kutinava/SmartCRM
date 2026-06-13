# Voice mic E2E — acceptance (2026-06-11)

## Что закрыто

Путь **микрофон → WS binary audio → Whisper → Hermes → UI** без ручной речи:

| Слой | Как |
|------|-----|
| Backend | `tests/smoke/test_voice_mic_ws_e2e.py` — WS `send_bytes` = тот же контракт, что `sendAudio(blob)` |
| Frontend dev | `data-testid="voice-simulate-mic"` → `sendFixtureAudio()` → `/fixtures/voice_mic_fixture.wav` |
| Ф2 §8 slice | `tests/smoke/test_leadgen_voice_ws.py` — `generate_lead` + navigate `/leadgen` |

## Команда

```bash
cd backend && python scripts/smoke_voice_mic_e2e.py
```

## DevTools (опционально)

1. Backend `:8000` **отвечает** (`GET /api/ops/agents` < 2 с), frontend `npm run dev`
2. `/leads/list` → кнопка **🎤 sim** (только dev)
3. Ожидание: «Обрабатываю…» → transcript → reply (нужен `GROQ_API_KEY` для live STT)
4. Если бэкенд завис — WS `off`, через 8 с ошибка «нет соединения» (не вечный processing)

## Реальный микрофон

Spot-check по желанию: кнопка `data-testid="voice-mic-button"` + живая речь — не блокер CI.

## Связь MAP

- `PRD_MAP` «Голос → лиды» п.1 → ✅
- DoD Ф1 п.5 → ✅
- DoD Ф1 п.6 → ✅ (старт Ф2, очередь 5)
