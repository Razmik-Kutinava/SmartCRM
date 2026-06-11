"""
REST API для лидов — сборка роутера из подмодулей.

Порядок регистрации важен: bitrix и engagement до /{lead_id}.
"""
from fastapi import APIRouter

from . import analytics_routes, bitrix_routes, crud, engagement

router = APIRouter(prefix="/api/leads", tags=["leads"])

router.include_router(bitrix_routes.router)
router.get("/analytics/summary")(analytics_routes.analytics_summary)
router.get("/analytics/export")(analytics_routes.analytics_export)
router.include_router(engagement.router)

router.get("")(crud.list_leads)
router.post("", status_code=201)(crud.create_lead)
router.get("/{lead_id}")(crud.get_lead)
router.get("/{lead_id}/email")(crud.get_lead_email)
router.patch("/{lead_id}")(crud.update_lead)
router.delete("/{lead_id}", status_code=204)(crud.delete_lead)
