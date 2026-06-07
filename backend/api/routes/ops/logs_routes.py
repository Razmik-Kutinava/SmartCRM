"""Ops API — кольцевой буфер логов."""
from typing import Optional

from fastapi import APIRouter, Query

router = APIRouter()


@router.get("/logs")
async def get_ops_logs(
    limit: int = Query(200, ge=1, le=500),
    level: Optional[str] = Query(None, description="INFO, WARNING, ERROR или пусто = все"),
    q: str = Query("", description="Поиск по тексту"),
):
    """Кольцевой буфер: HTTP-запросы + сообщения логгера (WARNING+)."""
    from core.ops_log_buffer import get_entries

    return {"items": get_entries(limit=limit, level=level, q=q)}


@router.delete("/logs")
async def clear_ops_logs():
    from core.ops_log_buffer import clear

    clear()
    return {"ok": True}
