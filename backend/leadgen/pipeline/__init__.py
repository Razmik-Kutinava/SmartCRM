"""Leadgen pipeline — публичный API и re-export для тестов."""
from .cluster import run_cluster
from .gather import _build_agent_context, _gather_all_data, _run_leadgen_agents
from .persist import _save_to_crm
from .portrait_cache import (
    _portrait_review_cache_get,
    _portrait_review_cache_key,
    _portrait_review_cache_put,
)
from .portrait_helpers import (
    _build_portrait_seed_queries,
    _build_reference_profile,
    _dedup_companies,
    _extract_company_from_portrait,
    _fallback_portrait_candidates_from_web,
    _fill_missing_portrait_fields,
    _match_portrait,
    _merge_criteria_with_reference,
    _normalize_portrait_criteria,
    _parse_portrait_criteria,
    _portrait_workability_verdict,
    _score_reference_similarity,
)
from .run_pipeline import run_pipeline
from .score_card import _build_lead_card, _compute_final_score
from .search_by_portrait import _portrait_fit_analysis, search_by_portrait
from .utils import (
    _build_connections,
    _dedup_list,
    _extract_contacts_from_web,
    _extract_domain,
    _extract_employees_from_text,
    _extract_revenue_from_text,
    _fmt_money,
    _parse_json_safe,
    _render_script,
    _safe,
)

__all__ = [
    "run_pipeline",
    "run_cluster",
    "search_by_portrait",
    "_save_to_crm",
]
