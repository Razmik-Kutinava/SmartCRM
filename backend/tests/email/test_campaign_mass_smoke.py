"""API smoke: массовая рассылка — сегмент (этап B)."""
from __future__ import annotations

import pytest

from db.models import Lead


@pytest.mark.asyncio
async def test_campaign_mass_smoke_api(client, db_session):
    db_session.add_all(
        [
            Lead(company="Mass A", industry="IT и телеком", email="a@a.ru", score=80),
            Lead(company="Mass B", industry="Финансы", email="b@b.ru", score=70),
        ]
    )
    await db_session.commit()

    ind_r = await client.get("/api/leads/industries")
    assert ind_r.status_code == 200
    items = ind_r.json().get("items") or []
    assert any(x.get("count", 0) > 0 for x in items)

    seg_r = await client.post(
        "/api/email/campaigns/segment-preview",
        json={"segment": {"industries": ["IT и телеком"], "min_score": 0}},
    )
    assert seg_r.status_code == 200, seg_r.text
    assert seg_r.json()["count"] == 1
