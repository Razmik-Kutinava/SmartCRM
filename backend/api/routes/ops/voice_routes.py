"""Ops API — настройки Whisper STT."""
from fastapi import APIRouter

from .schemas import WhisperSettingsBody

router = APIRouter()


@router.get("/voice/whisper")
async def get_whisper_settings():
    """Текущие настройки STT: эффективные значения и дефолты из .env."""
    from core import voice_settings

    return voice_settings.get_settings_for_api()


@router.put("/voice/whisper")
async def put_whisper_settings(body: WhisperSettingsBody):
    """Сохранить настройки Whisper; дальше transcribe и WS используют их без перезапуска."""
    from core import voice_settings

    saved = voice_settings.save_settings(body.model_dump(by_alias=True))
    return {"ok": True, "effective": saved}


@router.delete("/voice/whisper")
async def delete_whisper_settings():
    """Сброс файла настроек — снова только переменные окружения."""
    from core import voice_settings

    cleared = voice_settings.clear_settings_file()
    return {"ok": True, "cleared": cleared, "effective": voice_settings.get_resolved_whisper_params()}


@router.get("/voice/history")
async def voice_command_history(limit: int = 40):
    """Ф3: последние голосовые/текстовые команды (из traces)."""
    from core import traces

    rows = traces.get_traces(limit=min(max(limit, 1), 100))
    return {
        "items": [
            {
                "id": t.get("id"),
                "text": t.get("text"),
                "intent": t.get("intent"),
                "reply": t.get("reply"),
                "source": t.get("source"),
                "duration_ms": t.get("duration_ms"),
                "model": t.get("model"),
                "feedback": t.get("feedback"),
                "error": t.get("error"),
                "ts": t.get("ts"),
            }
            for t in rows
        ],
        "total": len(rows),
    }
