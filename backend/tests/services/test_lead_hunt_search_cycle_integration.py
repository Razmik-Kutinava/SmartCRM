"""Integration: lead hunt search cycle (моки Checko/Serper/pipeline/fanout)."""
from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from db.models import Lead
from services.lead_hunt_config import LeadHuntConfig
from services.lead_hunt_search_cycle import aggregate_score, run_search_cycle


def _co(inn: str, name: str, match: float = 0.7) -> dict:
    return {"inn": inn, "name": name, "name_short": name, "_portrait_match": match}


@pytest.mark.asyncio
async def test_run_search_cycle_dedup_and_fanout(db_session, monkeypatch):
    lead = Lead(company="Existing Co", inn="7700000001", stage="Новый")
    db_session.add(lead)
    await db_session.commit()

    async def _portrait(portrait, limit=3, **kw):
        return {
            "results": [
                _co("7700000001", "Existing Co"),
                _co("7700000002", "New Co A", 0.85),
                _co("7700000003", "New Co B", 0.9),
            ],
            "agent_review": {"companies": []},
            "errors": [],
        }

    async def _pipeline(inn="", company_name="", **kw):
        return {"final_score": 72, "company_name": company_name, "inn": inn}

    async def _fanout(state, agent_ids):
        state = dict(state)
        state["fanout_parallel"] = True
        state["fanout_agent_count"] = 3
        state["analyst_output"] = {"score": 80, "summary": "ok"}
        state["marketer_output"] = {"score": 75, "summary": "hook"}
        state["economist_output"] = {"deal_probability_pct": 70, "summary": "fin"}
        return state

    monkeypatch.setattr("leadgen.pipeline.search_by_portrait", AsyncMock(side_effect=_portrait))
    monkeypatch.setattr("leadgen.pipeline.run_pipeline", AsyncMock(side_effect=_pipeline))
    monkeypatch.setattr("agents.fanout_parallel.run_parallel_fanout", AsyncMock(side_effect=_fanout))

    cfg = LeadHuntConfig(
        candidates_per_run=2,
        min_score_threshold=50,
        use_prospect_fallback=False,
        agent_fanout_enabled=True,
    )
    icp = {"search_portrait": "B2B IT", "portrait_text": "B2B IT", "industry": "IT", "city": "Москва"}
    out = await run_search_cycle(icp, cfg, db_session)

    assert out["dedup_db"] == 1
    assert out["total_raw"] == 3
    assert len(out["candidates"]) == 2
    assert out["candidates"][0]["agent_fanout"]["fanout_agent_count"] == 3
    assert out["candidates"][0]["score"] >= 50


@pytest.mark.asyncio
async def test_run_search_cycle_prospect_fallback(monkeypatch, db_session):
    async def _portrait(portrait, limit=3, **kw):
        return {"results": [], "agent_review": {}, "errors": []}

    async def _prospect(icp, industry="", city="", count=10):
        return {
            "companies": [
                {"name": "Prospect LLC", "fit_score": 88, "url": "https://p.ru", "snippet": "x"},
            ],
            "queries_used": ["q1"],
            "providers_used": ["serper"],
        }

    async def _pipeline(**kw):
        return {"final_score": 65}

    async def _fanout(state, agent_ids):
        s = dict(state)
        s["analyst_output"] = {"score": 60}
        s["marketer_output"] = {"score": 60}
        s["economist_output"] = {"deal_probability_pct": 60}
        return s

    monkeypatch.setattr("leadgen.pipeline.search_by_portrait", AsyncMock(side_effect=_portrait))
    monkeypatch.setattr("rag.search.prospect_companies", AsyncMock(side_effect=_prospect))
    monkeypatch.setattr("leadgen.pipeline.run_pipeline", AsyncMock(side_effect=_pipeline))
    monkeypatch.setattr("agents.fanout_parallel.run_parallel_fanout", AsyncMock(side_effect=_fanout))

    cfg = LeadHuntConfig(min_score_threshold=40, use_prospect_fallback=True, agent_fanout_enabled=True)
    out = await run_search_cycle({"search_portrait": "ритейл"}, cfg, db_session)
    assert "prospect" in out["search_sources"]
    assert len(out["candidates"]) == 1
    assert out["candidates"][0]["search_source"] == "prospect"


def test_aggregate_score_blends_sources():
    score = aggregate_score(
        portrait_score=60,
        pipeline_score=70,
        fanout={
            "analyst_output": {"score": 80},
            "marketer_output": {"score": 70},
            "economist_output": {"deal_probability_pct": 90},
        },
    )
    assert score == 74


@pytest.mark.asyncio
async def test_search_cycle_skips_low_score(db_session, monkeypatch):
    monkeypatch.setattr(
        "leadgen.pipeline.search_by_portrait",
        AsyncMock(
            return_value={
                "results": [_co("7701000001", "Low Co", 0.1)],
                "agent_review": {},
                "errors": [],
            }
        ),
    )
    monkeypatch.setattr("leadgen.pipeline.run_pipeline", AsyncMock(return_value={"final_score": 20}))
    monkeypatch.setattr(
        "agents.fanout_parallel.run_parallel_fanout",
        AsyncMock(return_value={"analyst_output": {"score": 15}}),
    )
    cfg = LeadHuntConfig(min_score_threshold=50, use_prospect_fallback=False, agent_fanout_enabled=True)
    out = await run_search_cycle({"search_portrait": "x"}, cfg, db_session)
    assert out["candidates"] == []
