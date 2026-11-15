"""
Voice Pipeline: аудио → Whisper → Hermes → агенты (LangGraph) → ответ.
Логирует каждый проход в traces.
"""
import asyncio
import time
import logging
from voice.whisper import transcribe
from voice.voice_action import build_voice_action
from core.hermes import parse_intent
from core import traces
from core.agent_memory import set_last_lead, get_last_lead, clear_last_lead, set_last_search_candidates, clear_last_search_candidates

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
    module = intent_data.get("module")
    base_reply = intent_data.get("reply", "")
    agents = intent_data.get("agents", [])

    _NAV_ONLY = frozenset({
        "list_emails", "analytics_funnel", "analytics_conversion",
        "analytics_cycle", "analytics_score", "analytics_report",
        "save_to_rag", "list_emails",
        "generate_lead", "find_leads_portrait", "cluster_company",
    })

    # Извлекаем session_id из контекста (если передан в page_context или есть в метаданных)
    session_id = None
    if page_context:
        # page_context может содержать session_id в формате "session_id:xxx"
        import re
        m = re.search(r"session[_\s]*id[:\s]*([a-zA-Z0-9\-_]+)", page_context)
        if m:
            session_id = m.group(1)
    # Fallback: используем trace_id как session_id
    if not session_id:
        session_id = trace["id"]

    # Шаг 3: Агенты / контекстные хэндлеры
    agent_result: dict = {}
    final_reply = base_reply

    try:
        # Обработка голосовой памяти для open_lead
        if intent == "open_lead":
            # Если есть selected_index — выбираем из сохранённых кандидатов
            selected_index = slots.get("selected_index")
            if selected_index is not None:
                memory = get_last_lead(session_id, max_age_sec=60)
                if memory and memory.get("candidates"):
                    candidates = memory["candidates"]
                    if 0 <= selected_index < len(candidates):
                        chosen = candidates[selected_index]
                        slots = {**slots, "lead_id": chosen["id"], "ref": "last"}
                        final_reply = f"Открываю лид №{selected_index + 1}: {chosen.get('company', '')}."
                    else:
                        final_reply = f"Лид №{selected_index + 1} не найден в списке."
                else:
                    final_reply = "Нет сохранённого списка лидов для выбора по номеру."

            # Если нет lead_id и нет selected_index — пробуем взять последний найденный
            elif not slots.get("lead_id") and slots.get("ref") != "last":
                memory = get_last_lead(session_id, max_age_sec=60)
                if memory:
                    slots = {**slots, "lead_id": memory["lead_id"], "ref": "last"}
                    final_reply = f"Открываю последний найденный лид: {memory['company']}."
                else:
                    final_reply = "Не найден лид для открытия. Сначала скажите «найди лид ...»."

        # Очистка памяти при «найди другой лид» / list_leads с флагом сброса
        if intent == "list_leads" and slots.get("_clear_voice_memory"):
            clear_last_lead(session_id)
            clear_last_search_candidates()

        if intent == "lead_history":
            from voice.lead_context import fetch_lead_history

            agent_result = await fetch_lead_history(slots)
            if agent_result.get("final_reply"):
                final_reply = agent_result["final_reply"]
            lid = agent_result.get("lead_id")
            company = agent_result.get("company")
            if lid is not None:
                slots = {**slots, "lead_id": lid}
            # Сохраняем в голосовую память (single lead)
            if lid is not None and company:
                set_last_lead(session_id, lid, company, [{"id": lid, "company": company}])

        # list_leads: если это поисковый запрос — получаем список лидов и сохраняем кандидатов
        elif intent == "list_leads":
            # Если есть query/company — делаем поиск и сохраняем топ-10 кандидатов
            query = slots.get("query") or slots.get("company")
            if query:
                from agents.tools import read_lead_by_company
                candidates = await read_lead_by_company(query, limit=10)
                if candidates:
                    # Сохраняем первый как "последний найденный" и весь список как кандидаты
                    first = candidates[0]
                    set_last_lead(session_id, first["lead_id"], first["company"], candidates)
                    # Список кандидатов для голосового выбора по номеру
                    set_last_search_candidates(candidates)
                    final_reply = f"Найдено {len(candidates)} лид(ов). Первый: {first['company']}. Скажите «открой первый» или номер лида."
                else:
                    final_reply = f"По запросу «{query}» лиды не найдены."
            else:
                # Просто list_leads без поиска — не меняем память
                pass
        elif intent == "ask_rag":
            from voice.rag_context import fetch_rag_answer

            agent_result = await fetch_rag_answer(slots, text)
            if agent_result.get("final_reply"):
                final_reply = agent_result["final_reply"]
        elif intent == "enrich_lead":
            from voice.enrich_context import fetch_enrich_preview

            agent_result = await fetch_enrich_preview(slots)
            if agent_result.get("final_reply"):
                final_reply = agent_result["final_reply"]
            lid = agent_result.get("lead_id")
            if lid is not None:
                slots = {**slots, "lead_id": lid}
        elif intent not in _NAV_ONLY:
            from agents.orchestrator import run_agents

            agent_result = await run_agents(
                intent=intent,
                slots={**slots, "reply": base_reply},
                transcript=text,
                trace_id=trace["id"],
                hermes_agents=agents,
                hermes_parallel=bool(intent_data.get("parallel")),
            )
            if agent_result.get("agents_ran") and agent_result.get("final_reply"):
                final_reply = agent_result["final_reply"]
            if agent_result.get("agents_ran"):
                try:
                    from rag.dialogue_facts import dialogue_auto_enabled, ingest_orchestrator_dialogues

                    if dialogue_auto_enabled():
                        agent_result["rag_dialogue_ingest"] = await ingest_orchestrator_dialogues(
                            agent_result,
                            transcript=text,
                            slots=slots,
                            dry_run=False,
                        )
                except Exception as e:
                    logger.warning("RAG dialogue ingest: %s", e)
    except Exception as e:
        logger.warning("Оркестратор ошибка (пайплайн продолжается): %s", e)
        agent_result = {"agents_ran": False, "error": str(e)}

    voice_action = build_voice_action(
        intent=intent,
        slots=slots,
        reply=final_reply,
        agents=agents,
        agent_result=agent_result,
        ui_action=intent_data.get("ui_action"),
        module=module,
        trace_id=trace["id"],
    )

    return {
        "transcript": text,
        "trace_id": trace["id"],
        "intent": intent,
        "module": module,
        "agents": agents,
        "slots": slots,
        "parallel": intent_data.get("parallel", False),
        "reply": final_reply,
        "agent_result": agent_result,
        "voice_action": voice_action,
    }
