"""
Voice API:
  POST /api/voice/command  — текстовая команда → интент (для тестов)
  POST /api/voice/transcribe — аудио → текст
  WS   /ws/voice           — полный голосовой пайплайн
"""
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse

MAX_AUDIO_BYTES = 10 * 1024 * 1024  # 10 MB
from pydantic import BaseModel

from voice.pipeline import process_audio, process_text

logger = logging.getLogger(__name__)
router = APIRouter()


class TextCommand(BaseModel):
    text: str


@router.post("/api/voice/command")
async def text_command(body: TextCommand):
    """
    Принимает текст → возвращает интент от Hermes.
    Удобно для тестирования без микрофона.
    """
    result = await process_text(body.text)
    return result


@router.post("/api/voice/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    """
    Принимает аудиофайл → возвращает транскрипцию Whisper.
    """
    from voice.whisper import transcribe
    audio_bytes = await file.read(MAX_AUDIO_BYTES + 1)
    if len(audio_bytes) > MAX_AUDIO_BYTES:
        raise HTTPException(413, detail="Файл слишком большой (максимум 10 МБ)")
    transcript = await transcribe(audio_bytes, file.filename or "audio.webm")
    return {"transcript": transcript}


@router.websocket("/ws/voice")
async def voice_websocket(ws: WebSocket):
    """
    WebSocket голосового пайплайна.

    Клиент шлёт:
      - JSON {"type": "text", "text": "..."} — текстовая команда
      - binary bytes — аудио чанк (webm/wav)

    Сервер отвечает JSON событиями:
      {"type": "transcript", "text": "..."}
      {"type": "intent", "intent": "...", "reply": "...", "agents": [...]}
      {"type": "error", "message": "..."}
    """
    await ws.accept()
    logger.info("WebSocket голос: подключение")

    try:
        while True:
            message = await ws.receive()
            # После disconnect нельзя снова вызывать receive — выходим без ошибки
            if message.get("type") == "websocket.disconnect":
                break

            # Текстовая команда (для тестов из браузера)
            if "text" in message:
                data = __import__("json").loads(message["text"])

                if data.get("type") == "text":
                    text = data["text"]
                    page_ctx = data.get("page_context", "")
                    await ws.send_json({"type": "transcript", "text": text})
                    result = await process_text(text, page_context=page_ctx)
                    await ws.send_json({
                        "type": "intent",
                        "intent": result["intent"],
                        "reply": result["reply"],
                        "agents": result.get("agents", []),
                        "slots": result.get("slots", {}),
                        "transcript": result["transcript"],
                        "trace_id": result.get("trace_id"),
                        "agent_result": result.get("agent_result", {}),
                    })

            # Аудио байты
            elif "bytes" in message:
                audio_bytes = message["bytes"]
                if not audio_bytes:
                    continue

                await ws.send_json({"type": "processing", "message": "Распознаю речь..."})

                result = await process_audio(audio_bytes)

                await ws.send_json({"type": "transcript", "text": result["transcript"]})
                await ws.send_json({
                    "type": "intent",
                    "intent": result["intent"],
                    "reply": result["reply"],
                    "agents": result.get("agents", []),
                    "slots": result.get("slots", {}),
                    "transcript": result["transcript"],
                    "trace_id": result.get("trace_id"),
                    "agent_result": result.get("agent_result", {}),
                })

    except WebSocketDisconnect:
        logger.info("WebSocket голос: отключение")
    except RuntimeError as e:
        if "disconnect" in str(e).lower():
            logger.info("WebSocket голос: сессия закрыта клиентом")
        else:
            logger.error(f"WebSocket голос ошибка: {e}")
    except Exception as e:
        logger.error(f"WebSocket голос ошибка: {e}")
        try:
            await ws.send_json({"type": "error", "message": str(e)})
        except Exception:
            pass
