"""
Voice Pipeline: аудио → Whisper → Hermes → агенты (LangGraph) → ответ.
Логирует каждый проход в traces.
"""
import time
import logging
from voice.whisper import transcribe
from voice.voice_action import build_voice_action
from core.hermes import parse_intent
from core import traces

logger = logging.getLogger(__name__)


async def process_audio(audio_bytes: bytes, filename: str = "audio.webm") -> dict:
    """
    Полный пайплайн обработки голосовой команды.
    Возвращает dict с transcript, intent, reply и agent_result.
    """
    transcript = await transcribe(audio_bytes, filename)

    if not transcript:
        return {
            "transcript": "",
            "intent": "noop",
            "reply": "Не удалось распознать речь. Попробуйте ещё раз.",
            "agents": [],
            "slots": {},
        }

    return await _run_pipeline(transcript, source="audio")


async def process_text(text: str, page_context: str = "") -> dict:
    """
    Обработка текстовой команды (для тестирования без микрофона).
    page_context — строка вида "Страница: Лиды" для уточнения контекста.
    """
    return await _run_pipeline(text, source="text", page_context=page_context)


async def _run_pipeline(text: str, source: str, page_context: str = "") -> dict:
    """Шаги 2–4: Hermes → трейс → агенты."""
    trace = traces.new_trace(text, source=source)
    t0 = time.monotonic()

    # Если клиент передал контекст страницы — включаем в текст для Hermes
    hermes_text = text
    if page_context:
        hermes_text = f"{page_context}\n{text}"

    # Шаг 2: Текст → интент (Hermes)
    try:
        intent_data = await parse_intent(hermes_text)
        duration_ms = (time.monotonic() - t0) * 1000
        model = intent_data.pop("_model", "groq/llama-3.1-8b-instant")
        traces.finish_trace(trace, intent_data, model=model, duration_ms=duration_ms)
    except Exception as e:
        traces.error_trace(trace, str(e))
        return {
            "transcript": text,
            "trace_id": trace["id"],
            "intent": "noop",
            "agents": [],
            "slots": {},
            "parallel": False,
            "reply": f"Ошибка разбора команды: {e}",
        }

    intent = intent_data.get("intent", "noop")
    slots = intent_data.get("slots", {})
    base_reply = intent_data.get("reply", "")

    # Шаг 3: Агенты (только для лидовых интентов, чтобы не тормозить остальные)
    agent_result: dict = {}
    final_reply = base_reply

    try:
        if intent == "lead_history":
            from voice.lead_context import fetch_lead_history

            agent_result = await fetch_lead_history(slots)
            if agent_result.get("final_reply"):
                final_reply = agent_result["final_reply"]
            lid = agent_result.get("lead_id")
            if lid is not None:
                slots = {**slots, "lead_id": lid}
        else:
            from agents.orchestrator import run_agents

            agent_result = await run_agents(
                intent=intent,
                slots={**slots, "reply": base_reply},
                transcript=text,
                trace_id=trace["id"],
            )
            if agent_result.get("agents_ran") and agent_result.get("final_reply"):
                final_reply = agent_result["final_reply"]
    except Exception as e:
        logger.warning("Оркестратор ошибка (пайплайн продолжается): %s", e)
        agent_result = {"agents_ran": False, "error": str(e)}

    agents = intent_data.get("agents", [])
    voice_action = build_voice_action(
        intent=intent,
        slots=slots,
        reply=final_reply,
        agents=agents,
        agent_result=agent_result,
        ui_action=intent_data.get("ui_action"),
        trace_id=trace["id"],
    )

    return {
        "transcript": text,
        "trace_id": trace["id"],
        "intent": intent,
        "agents": agents,
        "slots": slots,
        "parallel": intent_data.get("parallel", False),
        "reply": final_reply,
        "agent_result": agent_result,
        "voice_action": voice_action,
    }
