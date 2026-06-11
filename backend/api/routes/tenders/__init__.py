"""Tenders API — сборка роутера."""
from fastapi import APIRouter

from . import (
    analyze_routes,
    classifiers_routes,
    detail_routes,
    document_routes,
    plans_routes,
    saved_routes,
    search_routes,
)
from .helpers import (
    _estimate_relevance,
    _normalize_item_for_ui,
    _parse_any_date,
    _passes_local_filters,
    _query_hits,
    _tokenize_query,
)

router = APIRouter(prefix="/api/tenders", tags=["tenders"])

router.include_router(search_routes.router)
router.include_router(saved_routes.router)
router.include_router(analyze_routes.router)
router.include_router(document_routes.router)
router.include_router(plans_routes.router)
router.include_router(classifiers_routes.router)
router.include_router(detail_routes.router)

__all__ = [
    "router",
    "_parse_any_date",
    "_tokenize_query",
    "_query_hits",
    "_estimate_relevance",
    "_passes_local_filters",
    "_normalize_item_for_ui",
]
