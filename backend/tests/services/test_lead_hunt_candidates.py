"""Тесты очереди кандидатов lead hunt."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from services.lead_hunt_candidates import (
    approve_candidate,
    candidate_fingerprint,
    list_candidates,
    process_search_results,
    reject_candidate,
    search_candidates,
)
from services.lead_hunt_config import LeadHuntConfig


def _company(inn: str = "7701234567", name: str = "Тест ООО") -> dict:
    return {"inn": inn, "name": name, "name_short": name, "city": "Москва"}


def test_candidate_fingerprint_inn():
    assert candidate_fingerprint(_company()) == "inn:7701234567"


@pytest.mark.asyncio
async def test_search_candidates_filters_by_threshold(monkeypatch):
    cfg = LeadHuntConfig(min_score_threshold=50, candidates_per_run=3)

    async def _mock_search(portrait, limit=3, **kw):
        return {
            "results": [
                {"inn": "1", "name": "Low", "_portrait_match": 0.2},
                {"inn": "2", "name": "High", "_portrait_match": 0.8},
            ],
            "agent_review": {"companies": []},
            "errors": [],
        }

    monkeypatch.setattr(
        "leadgen.pipeline.search_by_portrait",
        AsyncMock(side_effect=_mock_search),
    )
    icp = {"search_portrait": "B2B IT Москва"}
    out = await search_candidates(icp, cfg)
    assert out["total_raw"] == 2
    assert len(out["candidates"]) == 1
    assert out["candidates"][0]["score"] == 80


@pytest.mark.asyncio
async def test_process_search_results_queues_pending(monkeypatch, tmp_path):
    import services.lead_hunt_config as lhc
    import services.lead_hunt_notifications as lhn

    monkeypatch.setattr(lhc, "STATE_PATH", tmp_path / "state.json")
    monkeypatch.setattr(lhn, "NOTIFICATIONS_PATH", tmp_path / "notif.json")
    cfg = LeadHuntConfig(notify_ops_queue=True, autosave_above_threshold=False)
    candidates = [{"company": _company(), "score": 75}]

    with patch("services.lead_hunt_candidates._push_ops_queue") as push:
        stats = await process_search_results(
            AsyncMock(),
            candidates,
            icp_version=1,
            cfg=cfg,
        )
    assert stats["queued"] == 1
    push.assert_called_once()
    pending = list_candidates(status="pending")
    assert len(pending) == 1
    assert pending[0]["score"] == 75


@pytest.mark.asyncio
async def test_approve_and_reject(monkeypatch, tmp_path):
    import services.lead_hunt_config as lhc

    monkeypatch.setattr(lhc, "STATE_PATH", tmp_path / "state.json")
    cfg = LeadHuntConfig(notify_ops_queue=False)
    db = AsyncMock()
    db.flush = AsyncMock()
    db.refresh = AsyncMock()
    db.commit = AsyncMock()

    fake_lead = type("L", (), {"id": 42})()

    async def _create(company, score, session):
        return 42

    monkeypatch.setattr(
        "services.lead_hunt_candidates._create_lead_from_company",
        AsyncMock(side_effect=_create),
    )
    await process_search_results(
        db,
        [{"company": _company(inn="7709999999"), "score": 60}],
        icp_version=1,
        cfg=cfg,
    )
    cid = list_candidates(status="pending")[0]["id"]
    out = await approve_candidate(cid, db)
    assert out["lead_id"] == 42
    assert list_candidates(status="approved")[0]["lead_id"] == 42

    await process_search_results(
        db,
        [{"company": _company(inn="7708888888"), "score": 55}],
        icp_version=1,
        cfg=cfg,
    )
    cid2 = list_candidates(status="pending")[0]["id"]
    rej = reject_candidate(cid2, note="не подходит")
    assert rej["ok"] is True
    assert list_candidates(status="rejected")[0]["reject_note"] == "не подходит"
