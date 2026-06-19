"""ICP для автономного lead hunt: won-лиды + аналитика + Стратег."""
from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from agents.scenarios.similar_context import build_portrait_from_won, load_won_leads_db
from core import crm_settings_store
from core.analytics_metrics import compute_funnel_by_source, lead_amount_rub
from db.models import Lead
from services.lead_hunt_config import load_state, save_state

logger = logging.getLogger(__name__)

_ICP_STRATEGIST_PROMPT = """Ты — стратег B2B-продаж SmartCRM.
По статистике выигранных сделок сформулируй идеальный профиль клиента (ICP) для поиска новых лидов.

Верни ТОЛЬКО JSON:
{
  "portrait_text": "1–2 предложения на русском — кому искать",
  "city": "город или регион или пустая строка",
  "industry": "отрасль или пустая строка",
  "company_size": "микро|малый|средний|крупный|любой",
  "keywords": ["до 5 ключевых слов"],
  "priority_sources": ["до 3 лучших каналов лидов"]
}"""


def _top_counter(leads: list[dict[str, Any]], field: str) -> str:
    counts: dict[str, int] = {}
    for lead in leads:
        val = (lead.get(field) or "").strip()
        if not val or val == "—":
            continue
        counts[val] = counts.get(val, 0) + 1
    if not counts:
        return ""
    return max(counts, key=counts.get)


def _avg_won_deal(leads: list[dict[str, Any]]) -> int | None:
    amounts = [lead_amount_rub(l) for l in leads]
    nums = [a for a in amounts if a is not None]
    if not nums:
        return None
    return round(sum(nums) / len(nums))


def build_icp_from_won(
    won_leads: list[dict[str, Any]],
    all_leads: list[dict[str, Any]],
    *,
    stages: list[str] | None = None,
) -> dict[str, Any]:
    """Базовый ICP: портрет won + воронка по источнику."""
    sts = stages or crm_settings_store.load_settings().get("stages") or []
    funnel = compute_funnel_by_source(all_leads, sts)
    ranked_sources = sorted(
        funnel,
        key=lambda row: (-float(row.get("conversionPct") or 0), -int(row.get("total") or 0)),
    )
    top_sources = ranked_sources[:3]
    return {
        "won_count": len(won_leads),
        "base_portrait": build_portrait_from_won(won_leads),
        "signals": {
            "top_industry": _top_counter(won_leads, "industry"),
            "top_city": _top_counter(won_leads, "city"),
            "avg_deal_rub": _avg_won_deal(won_leads),
            "top_source": top_sources[0]["source"] if top_sources else "",
        },
        "funnel_by_source": funnel[:5],
        "priority_sources": [row["source"] for row in top_sources if row.get("source")],
    }


async def load_leads_for_icp(db: AsyncSession, *, won_limit: int) -> tuple[list[dict], list[dict]]:
    result = await db.execute(select(Lead).order_by(Lead.created_at.desc()).limit(2000))
    all_leads = [row.to_dict() for row in result.scalars().all()]
    won = await load_won_leads_db(db, limit=won_limit)
    return won, all_leads


def _heuristic_strategist_icp(base: dict[str, Any]) -> dict[str, Any]:
    sig = base.get("signals") or {}
    keywords: list[str] = []
    for key in ("top_industry", "top_city", "top_source"):
        val = (sig.get(key) or "").strip()
        if val:
            keywords.append(val)
    return {
        "portrait_text": base.get("base_portrait") or "B2B компании среднего сегмента",
        "city": sig.get("top_city") or "",
        "industry": sig.get("top_industry") or "",
        "company_size": "любой",
        "keywords": keywords[:5],
        "priority_sources": list(base.get("priority_sources") or [])[:3],
        "strategist_mode": "heuristic",
    }


def _parse_json_safe(raw: str) -> dict[str, Any]:
    text = (raw or "").strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    try:
        data = json.loads(text)
        return data if isinstance(data, dict) else {}
    except json.JSONDecodeError:
        return {}


async def strategist_enrich_icp(base: dict[str, Any]) -> dict[str, Any]:
    """Один LLM-вызов Стратега; при ошибке — эвристика."""
    from core.llm import chat

    user = json.dumps(
        {
            "base_portrait": base.get("base_portrait"),
            "signals": base.get("signals"),
            "priority_sources": base.get("priority_sources"),
            "funnel_by_source": base.get("funnel_by_source"),
        },
        ensure_ascii=False,
    )
    try:
        raw = await chat(
            [
                {"role": "system", "content": _ICP_STRATEGIST_PROMPT},
                {"role": "user", "content": user},
            ],
            temperature=0.3,
            max_tokens=600,
            json_mode=True,
        )
        parsed = _parse_json_safe(raw)
        if not parsed.get("portrait_text"):
            return _heuristic_strategist_icp(base)
        parsed["strategist_mode"] = "llm"
        return parsed
    except Exception as e:
        logger.warning("strategist_enrich_icp: %s", e)
        out = _heuristic_strategist_icp(base)
        out["strategist_error"] = str(e)
        return out


def merge_icp(base: dict[str, Any], strategist: dict[str, Any]) -> dict[str, Any]:
    portrait = (strategist.get("portrait_text") or base.get("base_portrait") or "").strip()
    return {
        **base,
        "portrait_text": portrait,
        "search_portrait": portrait,
        "city": strategist.get("city") or (base.get("signals") or {}).get("top_city") or "",
        "industry": strategist.get("industry") or (base.get("signals") or {}).get("top_industry") or "",
        "company_size": strategist.get("company_size") or "любой",
        "keywords": list(strategist.get("keywords") or [])[:5],
        "priority_sources": list(
            strategist.get("priority_sources") or base.get("priority_sources") or []
        )[:3],
        "strategist": strategist,
    }


def persist_icp_version(icp: dict[str, Any]) -> dict[str, Any]:
    state = load_state()
    block = state.get("icp") or {}
    version = int(block.get("current_version") or 0) + 1
    entry = {
        **icp,
        "version": version,
        "built_at": datetime.now(timezone.utc).isoformat(),
    }
    versions = [entry, *(block.get("versions") or [])][:20]
    state["icp"] = {"current": entry, "current_version": version, "versions": versions}
    save_state(state)
    return entry


def load_latest_icp() -> dict[str, Any] | None:
    state = load_state()
    current = (state.get("icp") or {}).get("current")
    return current if isinstance(current, dict) else None


async def build_and_persist_icp(db: AsyncSession, *, won_limit: int) -> dict[str, Any]:
    won, all_leads = await load_leads_for_icp(db, won_limit=won_limit)
    base = build_icp_from_won(won, all_leads)
    strategist = await strategist_enrich_icp(base)
    merged = merge_icp(base, strategist)
    return persist_icp_version(merged)
