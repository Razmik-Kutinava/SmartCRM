# Voice — голосовой ввод

Аудио → текст → Hermes → агенты. Эндпоинт: `api/routes/voice.py`.

| Файл | За что |
|------|--------|
| `pipeline.py` | `process_text` / `process_audio`: связка Whisper + Hermes + orchestrator |
| `whisper.py` | Распознавание речи (Groq Whisper / локально) |
| `audio_preprocess.py` | Нормализация аудио перед Whisper |

Настройки: `core/voice_settings.py`, `data/whisper_settings.json`.
