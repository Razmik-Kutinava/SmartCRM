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
    from core.agent_prompt_versions import save_version

    if path.exists():
        try:
            old = path.read_text(encoding="utf-8").strip()
            if old and old != text:
                save_version(agent_id, old, note="before_save")
        except OSError:
            pass
    path.write_text(text, encoding="utf-8")
    version_id = save_version(agent_id, text, note="save")
    logger.info("Промпт агента %s сохранён (%s симв.)", agent_id, len(text))
    return {
        "ok": True,
        "agent_id": agent_id,
        "chars": len(text),
        "source": "override",
        "version_id": version_id,
    }


@router.delete("/agents/{agent_id}/prompt")
async def delete_agent_prompt(agent_id: str):
    """Удалить override → возврат к встроенному промпту."""
    if agent_id not in AGENT_IDS:
        raise HTTPException(404, detail=f"Агент '{agent_id}' не найден")
    path = agent_prompt_path(agent_id)
    from core.agent_prompt_versions import save_version

    cleared = False
    if path.exists():
        try:
            old = path.read_text(encoding="utf-8").strip()
            if old:
                save_version(agent_id, old, note="before_reset")
        except OSError:
            pass
        path.unlink()
        cleared = True
    prompt, source = get_effective_prompt(agent_id)
    return {"ok": True, "cleared": cleared, "source": source, "chars": len(prompt)}


@router.get("/agents/{agent_id}/prompt/versions")
async def list_agent_prompt_versions(agent_id: str):
    """Список сохранённых версий промпта (новые сверху)."""
    if agent_id not in AGENT_IDS:
        raise HTTPException(404, detail=f"Агент '{agent_id}' не найден")
    from core.agent_prompt_versions import list_versions

    return {"agent_id": agent_id, "versions": list_versions(agent_id)}


@router.get("/agents/{agent_id}/prompt/versions/compare")
async def compare_agent_prompt_versions(
    agent_id: str,
    left: str,
    right: str,
):
    """Сравнение двух версий: id (v000001), current, builtin."""
    if agent_id not in AGENT_IDS:
        raise HTTPException(404, detail=f"Агент '{agent_id}' не найден")
    from core.agent_prompt_versions import compare_texts, get_version_text

    def resolve(ref: str) -> tuple[str, str]:
        if ref == "current":
            text, src = get_effective_prompt(agent_id)
            return text, f"current ({src})"
        if ref == "builtin":
            return get_builtin_prompt(agent_id), "builtin"
        text = get_version_text(agent_id, ref)
        if text is None:
            raise HTTPException(404, detail=f"Версия {ref} не найдена")
        return text, ref

    left_text, left_label = resolve(left)
    right_text, right_label = resolve(right)
    cmp_out = compare_texts(left_text, right_text, left_label=left_label, right_label=right_label)
    return {
        "agent_id": agent_id,
        "left": left,
        "right": right,
        **cmp_out,
    }


@router.get("/agents/{agent_id}/prompt/versions/{version_id}")
async def get_agent_prompt_version(agent_id: str, version_id: str):
    if agent_id not in AGENT_IDS:
        raise HTTPException(404, detail=f"Агент '{agent_id}' не найден")
    from core.agent_prompt_versions import get_version_text

    text = get_version_text(agent_id, version_id)
    if text is None:
        raise HTTPException(404, detail=f"Версия {version_id} не найдена")
    return {"agent_id": agent_id, "version_id": version_id, "prompt": text, "chars": len(text)}


@router.post("/agents/{agent_id}/prompt/versions/{version_id}/restore")
async def restore_agent_prompt_version(agent_id: str, version_id: str):
    """Откат override к выбранной версии."""
    if agent_id not in AGENT_IDS:
        raise HTTPException(404, detail=f"Агент '{agent_id}' не найден")
    from core.agent_prompt_versions import get_version_text, save_version

    text = get_version_text(agent_id, version_id)
    if text is None:
        raise HTTPException(404, detail=f"Версия {version_id} не найдена")
    path = agent_prompt_path(agent_id)
    if path.exists():
        try:
            cur = path.read_text(encoding="utf-8").strip()
            if cur and cur != text.strip():
                save_version(agent_id, cur, note="before_restore")
        except OSError:
            pass
    path.write_text(text.strip(), encoding="utf-8")
    new_vid = save_version(agent_id, text.strip(), note=f"restore:{version_id}")
    return {
        "ok": True,
        "agent_id": agent_id,
        "restored_from": version_id,
        "version_id": new_vid,
        "chars": len(text.strip()),
        "source": "override",
    }


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
    rag_ingest = None
    if output and isinstance(output, dict):
        from rag.dialogue_facts import dialogue_auto_enabled, ingest_dialogue_facts

        rag_ingest = await ingest_dialogue_facts(
            agent_id,
            output,
            transcript=transcript,
            slots=slots,
            dry_run=not dialogue_auto_enabled(),
        )
    return {
        "ok": True,
        "agent_id": agent_id,
        "intent": intent,
        "output": output,
        "slots": slots,
        "elapsed_ms": elapsed_ms,
        "rag_ingest": rag_ingest,
    }
