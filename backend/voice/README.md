# Voice — голосовой ввод

Аудио → текст → Hermes → агенты. Эндпоинт: `api/routes/voice.py`.

| Файл | За что |
|------|--------|
| `pipeline.py` | `process_text` / `process_audio`: связка Whisper + Hermes + orchestrator |
| `voice_action.py` | Сборка пакета `voice_action` (modal / navigate / filter / approve) для WS; `open_lead` → `/leads/{id}` или payload `ref=last` |
| `synthesis.py` | Синтез fanout → блок `payload.synthesis` для modal |
| `lead_context.py` | История лида (audit/comments/comms) для `lead_history` |
| `enrich_context.py` | Preview enrich-lead для `enrich_lead` (апрув перед PATCH) |
| `approval_followup.py` | Ф3: парсинг «да» / «нет» / «короче» (backend mirror фронта) |
| `revise_draft.py` | Ф3: сокращение черновика письма через LLM |
| `rag_context.py` | Ответ из RAG (Chroma) для `ask_rag` |
| `whisper.py` | Распознавание речи (Groq Whisper / локально) |
| `audio_preprocess.py` | Нормализация аудио перед Whisper |

Настройки: `core/voice_settings.py`, `data/whisper_settings.json`.

Смоук: `python scripts/smoke_whisper_stt.py` · Ф2 modules: `python scripts/smoke_hermes_modules.py` (`HERMES_MODULES_ACCEPTANCE.md`).
