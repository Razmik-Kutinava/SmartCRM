"""Ops API — авто-суфлёр Стратега (правки промптов по слабым ответам)."""
import logging

from fastapi import APIRouter, HTTPException

from .schemas import StrategistApplyBody, StrategistSuggestBody

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/strategist/suggest-prompts")
async def strategist_suggest_prompts(body: StrategistSuggestBody = StrategistSuggestBody()):
    """Собрать слабые сигналы и предложить правки промптов (без автоприменения)."""
    from core.strategist_suggester import gather_weak_signals, suggest_prompt_fixes

    signals = await gather_weak_signals(
        max_traces=body.max_hermes_traces,
        max_runs=body.max_agent_runs,
        max_gate=body.max_gate_failures,
    )
    return await suggest_prompt_fixes(signals, max_suggestions=body.max_suggestions)


@router.post("/strategist/apply-suggestion")
async def strategist_apply_suggestion(body: StrategistApplyBody):
    """Апрув оператора: дописать блок в промпт агента или Hermes."""
    append = (body.prompt_append or "").strip()
    if len(append) < 20:
        raise HTTPException(400, detail="prompt_append слишком короткий")

    agent_id = body.agent_id.strip()
    if agent_id == "hermes":
        from core.hermes import get_system_prompt
        from core.hermes_prompt_store import save_override

        current = get_system_prompt()
        new_text = current.rstrip() + "\n\n# Strategist suggester\n" + append
        vid = save_override(new_text, note="strategist_suggester")
        return {"ok": True, "agent_id": "hermes", "version_id": vid, "chars": len(new_text)}

    from .agents_routes import AGENT_IDS, agent_prompt_path, get_effective_prompt

    if agent_id not in AGENT_IDS:
        raise HTTPException(404, detail=f"Агент '{agent_id}' не найден")

    current, _ = get_effective_prompt(agent_id)
    new_text = current.rstrip() + "\n\n# Strategist suggester\n" + append
    if len(new_text) < 50:
        raise HTTPException(400, detail="Итоговый промпт слишком короткий")

    from core.agent_prompt_versions import save_version

    path = agent_prompt_path(agent_id)
    old = path.read_text(encoding="utf-8").strip() if path.exists() else ""
    if old and old != new_text:
        save_version(agent_id, old, note="before_strategist_apply")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(new_text, encoding="utf-8")
    vid = save_version(agent_id, new_text, note="strategist_suggester")
    logger.info("Strategist suggester: применён промпт %s (%s симв.)", agent_id, len(new_text))
    return {"ok": True, "agent_id": agent_id, "version_id": vid, "chars": len(new_text)}
