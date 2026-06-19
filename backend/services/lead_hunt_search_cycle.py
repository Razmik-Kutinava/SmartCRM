"""Lead hunt — цикл поиска: ICP → portrait/prospect → pipeline → fanout агентов."""
from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Lead
from leadgen.pipeline.portrait_helpers import _dedup_companies
from leadgen.pipeline.persist_autosave import portrait_fit_score
from services.lead_hunt_config import LeadHuntConfig

logger = logging.getLogger(__name__)

LEAD_HUNT_FANOUT_AGENTS = ("analyst", "marketer", "economist")


def _prospect_to_company(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": row.get("name") or "",
        "name_short": row.get("name") or "",
        "inn": (row.get("inn") or "").strip(),
        "_prospect_fit_score": int(row.get("fit_score") or 0),
        "_prospect_url": row.get("url") or "",
        "_search_source": "prospect",
    }


async def _load_db_dedup_keys(db: AsyncSession) -> tuple[set[str], set[str]]:
    result = await db.execute(select(Lead.inn, Lead.company))
    inns: set[str] = set()
    names: set[str] = set()
    for inn, company in result.all():
        if inn and str(inn).strip():
            inns.add(str(inn).strip())
        name = (company or "").strip()
        if name and name != "—":
            names.add(name.lower())
    return inns, names


def _company_in_db(company: dict[str, Any], inns: set[str], names: set[str]) -> bool:
    inn = (company.get("inn") or "").strip()
    if inn and inn in inns:
        return True
    name = (company.get("name") or company.get("name_short") or "").strip().lower()
    return bool(name and name in names)


async def discover_companies(icp: dict[str, Any], cfg: LeadHuntConfig) -> dict[str, Any]:
    portrait = (icp.get("search_portrait") or icp.get("portrait_text") or "").strip()
    if not portrait:
        return {"companies": [], "errors": ["empty_portrait"], "sources": []}

    from leadgen.pipeline import search_by_portrait

    errors: list[str] = []
    sources: list[str] = []
    limit = min(cfg.candidates_per_run, 5)
    portrait_res = await search_by_portrait(portrait, limit=limit, save_to_crm=False)
    pool = list(portrait_res.get("results") or [])
    if pool:
        sources.append("portrait")
    errors.extend(portrait_res.get("errors") or [])

    if cfg.use_prospect_fallback and len(pool) < limit:
        from rag.search import prospect_companies

        prospect = await prospect_companies(
            icp=portrait,
            industry=(icp.get("industry") or ""),
            city=(icp.get("city") or ""),
            count=limit * 2,
        )
        for row in prospect.get("companies") or []:
            pool.append(_prospect_to_company(row))
        if prospect.get("companies"):
            sources.append("prospect")
        errors.extend(prospect.get("errors") or [])

    for c in pool:
        if not c.get("_search_source"):
            c["_search_source"] = "portrait"
    return {
        "companies": _dedup_companies(pool),
        "errors": errors,
        "sources": sources,
        "portrait_review": portrait_res.get("agent_review") or {},
    }


async def _pipeline_light_score(company: dict[str, Any]) -> tuple[int | None, dict[str, Any]]:
    inn = (company.get("inn") or "").strip()
    name = (company.get("name") or company.get("name_short") or "").strip()
    if not inn and not name:
        return None, {}
    from leadgen.pipeline import run_pipeline

    try:
        card = await run_pipeline(
            inn=inn,
            company_name=name,
            save_to_crm=False,
            deep_analysis=False,
        )
        return int(card.get("final_score") or 0), card
    except Exception as e:
        logger.warning("lead_hunt pipeline light: %s", e)
        return None, {"error": str(e)}


async def fanout_agents(company: dict[str, Any], icp: dict[str, Any]) -> dict[str, Any]:
    from agents.base import make_initial_state
    from agents.fanout_parallel import run_parallel_fanout

    name = (company.get("name") or company.get("name_short") or "").strip()
    inn = (company.get("inn") or "").strip()
    slots = {
        "inn": inn,
        "company_name": name,
        "company": name,
        "note": f"Lead hunt · ICP: {(icp.get('portrait_text') or '')[:180]}",
    }
    state = make_initial_state("generate_lead", slots, "")
    state = await run_parallel_fanout(state, list(LEAD_HUNT_FANOUT_AGENTS))
    return {
        "fanout_parallel": bool(state.get("fanout_parallel")),
        "fanout_agent_count": int(state.get("fanout_agent_count") or 0),
        "analyst_output": state.get("analyst_output"),
        "marketer_output": state.get("marketer_output"),
        "economist_output": state.get("economist_output"),
    }


def aggregate_score(
    *,
    portrait_score: int,
    pipeline_score: int | None,
    fanout: dict[str, Any] | None,
) -> int:
    parts = [portrait_score]
    if pipeline_score is not None:
        parts.append(pipeline_score)
    for key in ("analyst_output", "marketer_output"):
        out = (fanout or {}).get(key) or {}
        if out.get("score") is not None:
            parts.append(int(out["score"]))
    econ = (fanout or {}).get("economist_output") or {}
    if econ.get("deal_probability_pct") is not None:
        parts.append(int(econ["deal_probability_pct"]))
    return round(sum(parts) / len(parts))


async def run_search_cycle(
    icp: dict[str, Any],
    cfg: LeadHuntConfig,
    db: AsyncSession,
) -> dict[str, Any]:
    """Полный цикл: discover → dedup БД → pipeline → fanout → скор."""
    discovered = await discover_companies(icp, cfg)
    review = discovered.get("portrait_review") or {}
    inns, names = await _load_db_dedup_keys(db)
    enriched: list[dict[str, Any]] = []
    dedup_db = 0

    for company in discovered["companies"]:
        if _company_in_db(company, inns, names):
            dedup_db += 1
            continue
        portrait_score = portrait_fit_score(company, review)
        if company.get("_prospect_fit_score"):
            portrait_score = max(portrait_score, int(company["_prospect_fit_score"]))

        pipeline_score, pipeline_card = await _pipeline_light_score(company)
        fanout: dict[str, Any] = {}
        if cfg.agent_fanout_enabled:
            fanout = await fanout_agents(company, icp)

        score = aggregate_score(
            portrait_score=portrait_score,
            pipeline_score=pipeline_score,
            fanout=fanout,
        )
        if score < cfg.min_score_threshold:
            continue
        enriched.append(
            {
                "company": company,
                "score": score,
                "portrait_score": portrait_score,
                "pipeline_score": pipeline_score,
                "pipeline_card": pipeline_card,
                "agent_fanout": fanout,
                "search_source": company.get("_search_source") or "portrait",
            }
        )
        if len(enriched) >= cfg.candidates_per_run:
            break

    return {
        "candidates": enriched,
        "errors": discovered.get("errors") or [],
        "total_raw": len(discovered.get("companies") or []),
        "dedup_db": dedup_db,
        "search_sources": discovered.get("sources") or [],
    }
