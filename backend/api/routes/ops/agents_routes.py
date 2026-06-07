"""Ops API — промпты и тест-запуск агентов."""
import logging
import time
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException

from .schemas import AgentPromptBody, AgentRunBody

logger = logging.getLogger(__name__)
router = APIRouter()

AGENT_IDS = ["analyst", "strategist", "economist", "marketer", "tech_specialist"]


def _backend_data_dir() -> Path:
    return Path(__file__).resolve().parents[3] / "data"


def agent_prompt_path(agent_id: str) -> Path:
    data_dir = _backend_data_dir()
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir / f"agent_prompt_{agent_id}.txt"


def get_builtin_prompt(agent_id: str) -> str:
    if agent_id == "analyst":
        from agents.analyst import ANALYST_SYSTEM_PROMPT
        return ANALYST_SYSTEM_PROMPT
    if agent_id == "strategist":
        from agents.strategist import STRATEGIST_SYSTEM_PROMPT
        return STRATEGIST_SYSTEM_PROMPT
    if agent_id == "economist":
        from agents.economist import ECONOMIST_SYSTEM_PROMPT
        return ECONOMIST_SYSTEM_PROMPT
    if agent_id == "marketer":
        from agents.marketer import MARKETER_SYSTEM_PROMPT
        return MARKETER_SYSTEM_PROMPT
    if agent_id == "tech_specialist":
        from agents.tech_specialist import TECH_SPECIALIST_SYSTEM_PROMPT
        return TECH_SPECIALIST_SYSTEM_PROMPT
    return ""


def get_effective_prompt(agent_id: str) -> tuple[str, str]:
    """Возвращает (промпт, source: 'builtin'|'override')."""
    path = agent_prompt_path(agent_id)
    if path.exists():
        try:
            text = path.read_text(encoding="utf-8").strip()
            if text:
                return text, "override"
        except OSError:
            pass
    builtin = get_builtin_prompt(agent_id)
    return builtin, "builtin"


@router.get("/agents")
async def get_agents_list():
    """Список агентов с кратким статусом."""
    result = []
    for agent_id in AGENT_IDS:
        prompt, source = get_effective_prompt(agent_id)
        implemented = bool(prompt)
        result.append({
            "id": agent_id,
            "source": source,
            "implemented": implemented,
            "prompt_chars": len(prompt),
            "prompt_preview": prompt[:120] if prompt else "",
        })
    return {"agents": result}


@router.get("/agents/{agent_id}/prompt")
async def get_agent_prompt(agent_id: str):
    """Текущий промпт агента (встроенный или override)."""
    if agent_id not in AGENT_IDS:
        raise HTTPException(404, detail=f"Агент '{agent_id}' не найден")
    prompt, source = get_effective_prompt(agent_id)
    return {
        "agent_id": agent_id,
        "prompt": prompt,
        "source": source,
        "chars": len(prompt),
    }


@router.put("/agents/{agent_id}/prompt")
async def put_agent_prompt(agent_id: str, body: AgentPromptBody):
    """Сохранить override промпта агента в backend/data/agent_prompt_{id}.txt"""
    if agent_id not in AGENT_IDS:
        raise HTTPException(404, detail=f"Агент '{agent_id}' не найден")
    text = body.prompt.strip()
    if len(text) < 50:
        raise HTTPException(400, detail="Промпт слишком короткий (минимум 50 символов)")
    path = agent_prompt_path(agent_id)
    path.write_text(text, encoding="utf-8")
    logger.info("Промпт агента %s сохранён (%s симв.)", agent_id, len(text))
    return {"ok": True, "agent_id": agent_id, "chars": len(text), "source": "override"}


@router.delete("/agents/{agent_id}/prompt")
async def delete_agent_prompt(agent_id: str):
    """Удалить override → возврат к встроенному промпту."""
    if agent_id not in AGENT_IDS:
        raise HTTPException(404, detail=f"Агент '{agent_id}' не найден")
    path = agent_prompt_path(agent_id)
    cleared = False
    if path.exists():
        path.unlink()
        cleared = True
    prompt, source = get_effective_prompt(agent_id)
    return {"ok": True, "cleared": cleared, "source": source, "chars": len(prompt)}


@router.post("/agents/{agent_id}/run")
async def run_agent(agent_id: str, body: AgentRunBody):
    """Тест-запуск одного агента вручную."""
    if agent_id not in AGENT_IDS:
        raise HTTPException(404, detail=f"Агент '{agent_id}' не найден")
    if not get_builtin_prompt(agent_id) and not agent_prompt_path(agent_id).exists():
        raise HTTPException(501, detail=f"Агент '{agent_id}' ещё не реализован")

    from agents.base import make_initial_state
    from agents.tools import read_lead_by_id
    from rag.retrieve import attach_rag_to_slots

    slots = dict(body.slots or {})
    intent = body.intent
    transcript = (body.transcript or "").strip()

    if body.lead_id is not None:
        lead = await read_lead_by_id(body.lead_id)
        if not lead:
            raise HTTPException(404, detail="Лид не найден")
        intent = "analyze_lead"
        slots = {**slots, **lead}
        if body.instruction.strip():
            slots["instruction"] = body.instruction.strip()
        if not transcript and body.instruction.strip():
            transcript = body.instruction.strip()

    slots = await attach_rag_to_slots(slots, transcript)
    state = make_initial_state(
        intent=intent,
        slots=slots,
        transcript=transcript,
    )
    state["slots"] = {**slots, "reply": ""}

    t0 = time.monotonic()
    try:
        if agent_id == "analyst":
            from agents import analyst
            result_state = await analyst.run(state)
            output = result_state.get("analyst_output")
        elif agent_id == "strategist":
            from agents import strategist
            result_state = await strategist.run(state)
            output = result_state.get("strategist_output")
        elif agent_id == "economist":
            from agents import economist
            result_state = await economist.run(state)
            output = result_state.get("economist_output")
        elif agent_id == "marketer":
            from agents import marketer
            result_state = await marketer.run(state)
            output = result_state.get("marketer_output")
        elif agent_id == "tech_specialist":
            from agents import tech_specialist
            result_state = await tech_specialist.run(state)
            output = result_state.get("tech_output")
        else:
            raise HTTPException(501, detail=f"Агент '{agent_id}' ещё не реализован")
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Тест-запуск агента %s ошибка: %s", agent_id, e)
        raise HTTPException(500, detail="Внутренняя ошибка агента. Подробности в логах.")

    elapsed_ms = round((time.monotonic() - t0) * 1000)
    return {
        "ok": True,
        "agent_id": agent_id,
        "intent": intent,
        "output": output,
        "elapsed_ms": elapsed_ms,
    }
