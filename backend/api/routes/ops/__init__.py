"""
Ops API — дашборд качества голосового пайплайна.
Сборка роутера из подмодулей; URL /api/ops/* без изменений.
"""
from fastapi import APIRouter

from . import (
    agents_routes,
    crm_routes,
    dashboard_routes,
    eval_gate_routes,
    eval_routes,
    hermes_routes,
    logs_routes,
    traces_routes,
    voice_routes,
)

router = APIRouter(prefix="/api/ops", tags=["ops"])

router.include_router(traces_routes.router)
router.include_router(dashboard_routes.router)
router.include_router(hermes_routes.router)
router.include_router(voice_routes.router)
router.include_router(eval_routes.router)
router.include_router(eval_gate_routes.router)
router.include_router(agents_routes.router)
router.include_router(logs_routes.router)
router.include_router(crm_routes.router)
