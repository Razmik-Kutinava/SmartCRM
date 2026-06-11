# Whisper STT — acceptance (2026-06-08)

## Что это

Голос с микрофона → **Groq Whisper** → текст на русском → дальше Hermes.  
Эндпоинты: `POST /api/voice/transcribe`, бинарные байты в `WS /ws/voice`.

## Команда

```bash
cd backend && python scripts/smoke_whisper_stt.py
```

Загружает `.env` для опционального **live Groq** (тишина WAV ~0.3 с).

## Покрытие (15 pytest)

| Зона | Файлы |
|------|--------|
| Whisper + preprocess + settings | `tests/voice/test_whisper_stt.py` |
| HTTP transcribe, ops settings, WS text | `tests/smoke/test_whisper_stt_smoke.py` |

## Исправления в шаге

- `POST /api/voice/transcribe` — **503** с текстом, если нет `GROQ_API_KEY`
- `WS /ws/voice` audio — **`error`** вместо «Внутренняя ошибка» при сбое STT

## E2E микрофон (2026-06-11)

- Автомат: `python scripts/smoke_voice_mic_e2e.py` — WS `send_bytes` = путь `sendAudio(blob)`
- Dev UI: `data-testid="voice-simulate-mic"` (кнопка 🎤 sim) + `voice_mic_fixture.wav`
- Док: `VOICE_MIC_E2E_ACCEPTANCE.md`

## DevTools (опционально)

- `/leads/list` — `data-testid="voice-mic-button"` + живая речь (spot-check)

## Хвост (не блокер STT)

- Hermes / интенты / `voice_action` — следующие пункты PRD_MAP
- `health_check()` только проверяет наличие ключа, не ping Groq API
