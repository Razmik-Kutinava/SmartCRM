"""Ops API — обзор, очередь, история, снимки."""
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException

from core import ops_store, traces

from .schemas import BaselineBody, ResolveQueueBody, SnapshotBody

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/overview")
async def get_overview():
    """Сводка для дашборда: этапы пайплайна, здоровье LLM, очередь решений (кратко)."""
    from core.llm import health_check

    ops_store.recompute_queue_and_suggestions(update_queue=False)
    q = ops_store.load_queue()
    open_items = [x for x in q if x.get("status") == "open"]
    by_sev = {"critical": 0, "medium": 0, "low": 0}
    for x in open_items:
        s = x.get("severity", "low")
        if s in by_sev:
            by_sev[s] += 1

    try:
        llm_h = await health_check()
    except Exception as e:
        llm_h = {"groq": False, "ollama": False, "active": "none", "error": str(e)[:200]}

    llm_ok = bool(llm_h.get("groq") or llm_h.get("ollama"))
    stats = traces.get_stats()

    pipeline = [
        {"id": "stt", "name": "Whisper (STT)", "status": "ok", "hint": "Аудио → текст"},
        {"id": "hermes", "name": "Hermes (интенты)", "status": "ok", "hint": "Текст → JSON интента"},
        {"id": "graph", "name": "LangGraph", "status": "ok", "hint": "Агенты и инструменты"},
        {"id": "db", "name": "PostgreSQL / Redis", "status": "ok", "hint": "Данные и кэш"},
    ]
    if stats.get("errors", 0) > 0:
        pipeline[1]["status"] = "warn"
        pipeline[1]["hint"] = f"Есть ошибки в трейсах: {stats['errors']}"
    if not llm_ok:
        pipeline[1]["status"] = "error"
        pipeline[1]["hint"] = "Нет доступного LLM (Groq и Ollama недоступны)"

    return {
        "pipeline": pipeline,
        "llm": llm_h,
        "stats": stats,
        "queue": {
            "open_total": len(open_items),
            "by_severity": by_sev,
            "preview": sorted(
                open_items,
                key=lambda x: {"critical": 0, "medium": 1, "low": 2}.get(x.get("severity"), 3),
            )[:5],
        },
    }


@router.get("/queue")
async def get_queue():
    """Очередь задач для оператора (критичность + статус)."""
    items = ops_store.load_queue()
    open_items = [x for x in items if x.get("status") == "open"]
    open_items.sort(
        key=lambda x: (
            {"critical": 0, "medium": 1, "low": 2}.get(x.get("severity"), 3),
            -x.get("created_ts", 0),
        ),
    )
    return {"items": items, "open": open_items}


@router.post("/queue/{item_id}/resolve")
async def resolve_queue_item(item_id: str, body: ResolveQueueBody):
    if body.status not in ("done", "dismissed"):
        raise HTTPException(400, detail="status должен быть 'done' или 'dismissed'")
    ok = ops_store.resolve_queue_item(item_id, body.status, body.note)
    if not ok:
        raise HTTPException(404, detail="Запись не найдена")
    return {"ok": True, "id": item_id}


@router.post("/recompute")
async def post_recompute():
    """Пересчитать авто-очередь и сигналы по текущим трейсам."""
    data = ops_store.recompute_queue_and_suggestions(update_queue=True)
    return data


@router.get("/insights")
async def get_insights():
    """Предложения системы (эвристики) без перезаписи очереди."""
    return ops_store.generate_insights_only()


@router.get("/history")
async def get_history():
    """Снимки метрик и сравнение с базовой линией."""
    return ops_store.history_comparison()


@router.post("/snapshot")
async def post_snapshot(body: SnapshotBody = SnapshotBody()):
    """Зафиксировать текущую статистику трейсов как снимок + текущий промпт."""
    from core.hermes import get_system_prompt
    from core.hermes_prompt_store import get_prompt_source

    stats = traces.get_stats()
    prompt_text = get_system_prompt()
    entry = ops_store.append_snapshot(
        stats,
        source="manual",
        label=body.label,
        prompt_text=prompt_text,
        prompt_source=get_prompt_source(),
    )
    return {"ok": True, "snapshot": entry}


@router.post("/baseline")
async def post_baseline(body: BaselineBody):
    """Установить линию «было» по id снимка."""
    ok = ops_store.set_baseline_snapshot_id(body.snapshot_id)
    if not ok:
        raise HTTPException(404, detail="Снимок с таким id не найден")
    return {"ok": True, "baseline": ops_store.get_baseline()}
