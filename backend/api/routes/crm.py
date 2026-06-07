"""
Публичная конфигурация CRM для UI (воронка, пороги приоритета / CRM Points).
Без секретов; те же данные, что в Ops → CRM, но через лёгкий эндпоинт.
"""
from fastapi import APIRouter

from core import crm_settings_store

router = APIRouter(prefix="/api/crm", tags=["crm"])


@router.get("/config")
async def get_crm_public_config():
    s = crm_settings_store.load_settings()
    return {
        "stages": s.get("stages") or [],
        "priority_thresholds": s.get("priority_thresholds") or {},
        "score_range": s.get("score_range") or {"min": 0, "max": 100},
        "default_new_lead_score": s.get("default_new_lead_score", 50),
        "managerSetsScore": s.get("manager_sets_score", True),
        "agentsMayUpdateScore": s.get("agents_may_update_score", False),
        "scoringAdvisoryEnabled": s.get("scoring_advisory_enabled", True),
        "stageTransitionRules": s.get("stage_transition_rules") or [],
    }
