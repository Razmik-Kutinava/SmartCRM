"""Ops API — настройки CRM (воронка, скоринг)."""
import os

from fastapi import APIRouter, HTTPException

from .schemas import CrmSettingsUpdate

router = APIRouter()


@router.get("/crm-settings")
async def get_crm_settings_endpoint():
    """Тюнинг CRM: этапы воронки, пороги, Битрикс (без секрета)."""
    from core import crm_settings_store

    settings = crm_settings_store.load_settings()
    bx = (os.getenv("BITRIX24_WEBHOOK_URL") or "").strip()
    masked = None
    if bx:
        masked = bx[:36] + "…" + bx[-10:] if len(bx) > 50 else bx[:24] + "…"
    return {
        "settings": settings,
        "bitrix_webhook_configured": bool(bx),
        "bitrix_webhook_masked": masked,
    }


@router.put("/crm-settings")
async def put_crm_settings_endpoint(body: CrmSettingsUpdate):
    from core import crm_settings_store

    data = body.model_dump(exclude_none=True)
    if not data:
        raise HTTPException(400, detail="Нет полей для сохранения")
    try:
        saved = crm_settings_store.save_settings(data)
    except ValueError as e:
        raise HTTPException(400, detail=str(e))
    return {"ok": True, "settings": saved}
