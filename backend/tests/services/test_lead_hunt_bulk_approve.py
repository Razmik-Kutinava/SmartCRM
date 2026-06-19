"""Тесты bulk approve lead hunt."""
from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from services.lead_hunt_candidates import approve_candidates_above_score


@pytest.mark.asyncio
async def test_approve_candidates_above_score(monkeypatch, tmp_path):
    import services.lead_hunt_config as lhc

    monkeypatch.setattr(lhc, "STATE_PATH", tmp_path / "state.json")
    lhc.save_state(
        {
            "candidates": [
                {
                    "id": "lh-high",
                    "status": "pending",
                    "score": 80,
                    "company": {"inn": "7701111111", "name": "High Co"},
                },
                {
                    "id": "lh-low",
                    "status": "pending",
                    "score": 50,
                    "company": {"inn": "7702222222", "name": "Low Co"},
                },
            ]
        }
    )
    db = AsyncMock()

    async def _approve(cid, session, **kwargs):
        return {"ok": True, "lead_id": 10 if cid == "lh-high" else 11, "candidate_id": cid}

    monkeypatch.setattr(
        "services.lead_hunt_candidates.approve_candidate",
        AsyncMock(side_effect=_approve),
    )
    out = await approve_candidates_above_score(db, min_score=70)
    assert out["approved_count"] == 1
    assert out["approved"][0]["candidate_id"] == "lh-high"
