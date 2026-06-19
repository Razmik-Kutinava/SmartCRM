"""Тесты очереди lead hunt (шаг 4)."""
from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from services.lead_hunt_queue import build_summary, list_queue, to_queue_item


def test_build_summary_from_fanout():
    raw = {
        "company": {"name": "Test Co"},
        "agent_fanout": {
            "analyst_output": {"summary": "Хороший потенциал"},
            "marketer_output": {"hook": "Рост выручки"},
        },
    }
    s = build_summary(raw)
    assert "Аналитик" in s
    assert "Маркетолог" in s


def test_to_queue_item_shape():
    item = to_queue_item(
        {
            "id": "lh-abc",
            "status": "pending",
            "score": 77,
            "company": {"inn": "7701", "name": "Co"},
            "summary": "Кратко",
        }
    )
    assert item["id"] == "lh-abc"
    assert item["company"] == "Co"
    assert item["score"] == 77
    assert item["summary"] == "Кратко"


def test_list_queue_pending(monkeypatch, tmp_path):
    import services.lead_hunt_config as lhc

    monkeypatch.setattr(lhc, "STATE_PATH", tmp_path / "s.json")
    lhc.save_state(
        {
            "candidates": [
                {
                    "id": "lh-q1",
                    "status": "pending",
                    "score": 80,
                    "company": {"name": "Queue Co", "inn": "770999"},
                    "summary": "Тест",
                }
            ]
        }
    )
    items = list_queue(status="pending")
    assert len(items) == 1
    assert items[0]["company"] == "Queue Co"


@pytest.mark.asyncio
async def test_approve_uses_save_to_crm(monkeypatch, tmp_path):
    import services.lead_hunt_config as lhc
    from services.lead_hunt_candidates import approve_candidate

    monkeypatch.setattr(lhc, "STATE_PATH", tmp_path / "s.json")
    lhc.save_state(
        {
            "candidates": [
                {
                    "id": "lh-ap1",
                    "status": "pending",
                    "score": 70,
                    "company": {"name": "Appr Co", "inn": "770888"},
                    "pipeline_card": {"company_name": "Appr Co", "final_score": 70},
                }
            ]
        }
    )
    db = AsyncMock()
    db.flush = AsyncMock()
    db.refresh = AsyncMock()
    db.commit = AsyncMock()

    monkeypatch.setattr(
        "services.lead_hunt_candidates.save_candidate_to_crm",
        AsyncMock(return_value=55),
    )
    monkeypatch.setattr(
        "services.lead_hunt_candidates._maybe_start_nurture",
        AsyncMock(return_value=None),
    )
    out = await approve_candidate("lh-ap1", db, start_nurture=False)
    assert out["lead_id"] == 55
