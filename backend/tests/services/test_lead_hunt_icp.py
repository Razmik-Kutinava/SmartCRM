"""ICP lead hunt — unit."""
from __future__ import annotations

import pytest

from services.lead_hunt_icp import (
    build_icp_from_won,
    merge_icp,
    persist_icp_version,
    strategist_enrich_icp,
)


def _won(company: str, *, industry="IT", city="Москва", source="email", amount=500_000):
    return {
        "company": company,
        "stage": "Выигран",
        "industry": industry,
        "city": city,
        "source": source,
        "amountRub": amount,
    }


def test_build_icp_from_won_uses_funnel_by_source():
    won = [_won("A"), _won("B", city="Казань")]
    all_leads = won + [
        {"company": "C", "stage": "Новый", "source": "leadgen", "industry": "IT", "city": "Москва"},
        {"company": "D", "stage": "Проигран", "source": "email", "industry": "IT", "city": "Москва"},
    ]
    icp = build_icp_from_won(won, all_leads, stages=["Новый", "Выигран", "Проигран"])
    assert icp["won_count"] == 2
    assert "профиль по 2 выигранным" in icp["base_portrait"]
    assert icp["signals"]["top_industry"] == "IT"
    assert icp["signals"]["top_city"] == "Москва"
    assert icp["funnel_by_source"]
    assert "email" in icp["priority_sources"]


@pytest.mark.asyncio
async def test_strategist_enrich_icp_heuristic_without_llm(monkeypatch):
    async def _fail(*_a, **_k):
        raise RuntimeError("no llm")

    monkeypatch.setattr("core.llm.chat", _fail)
    base = build_icp_from_won([_won("X")], [_won("X")], stages=["Выигран"])
    out = await strategist_enrich_icp(base)
    assert out["strategist_mode"] == "heuristic"
    assert out["portrait_text"]


def test_merge_and_version_icp(monkeypatch, tmp_path):
    import services.lead_hunt_config as lhc

    monkeypatch.setattr(lhc, "STATE_PATH", tmp_path / "state.json")
    base = build_icp_from_won([_won("Co")], [_won("Co")], stages=["Выигран"])
    strat = {
        "portrait_text": "IT в Москве, средний бизнес",
        "city": "Москва",
        "industry": "IT",
        "company_size": "средний",
        "keywords": ["CRM"],
        "priority_sources": ["email"],
        "strategist_mode": "heuristic",
    }
    merged = merge_icp(base, strat)
    v1 = persist_icp_version(merged)
    v2 = persist_icp_version(merged)
    assert v1["version"] == 1
    assert v2["version"] == 2
    state = lhc.load_state()
    assert len(state["icp"]["versions"]) == 2
