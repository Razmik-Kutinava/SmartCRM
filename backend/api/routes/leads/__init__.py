"""
REST API для лидов — сборка роутера из подмодулей.

Порядок регистрации важен: bitrix и engagement до /{lead_id}.
"""
from fastapi import APIRouter

from . import analytics_routes, amo_routes, bitrix_routes, crud, csv_routes, engagement, export_routes, hubspot_routes, sla_routes

router = APIRouter(prefix="/api/leads", tags=["leads"])

router.include_router(bitrix_routes.router)
router.include_router(amo_routes.router)
router.include_router(hubspot_routes.router)
router.include_router(sla_routes.router)
router.get("/analytics/summary")(analytics_routes.analytics_summary)
router.get("/analytics/export")(analytics_routes.analytics_export)
router.include_router(engagement.router)
router.include_router(csv_routes.router)
router.include_router(export_routes.router)

router.get("")(crud.list_leads)
router.get("/industries")(crud.list_industries)
router.post("", status_code=201)(crud.create_lead)
router.post("/lookalike-import", status_code=201)(crud.import_lookalike_leads)
router.get("/{lead_id}")(crud.get_lead)
router.get("/{lead_id}/email")(crud.get_lead_email)
router.patch("/{lead_id}")(crud.update_lead)
router.delete("/{lead_id}", status_code=204)(crud.delete_lead)
