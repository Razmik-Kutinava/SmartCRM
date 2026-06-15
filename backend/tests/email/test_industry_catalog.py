"""Этап D: справочник отраслей и фильтр verified."""
from __future__ import annotations

import pytest

from db.models import Lead
from services.industry_catalog import (
    FIXED_INDUSTRIES,
    is_industry_empty,
    list_industry_catalog,
    segment_industry_stats,
)
from services.lead_segment_query import lead_matches_segment


def test_is_industry_empty():
    assert is_industry_empty(None)
    assert is_industry_empty("")
    assert is_industry_empty("—")
    assert not is_industry_empty("IT")


@pytest.mark.asyncio
async def test_list_industry_catalog_merges_fixed_and_crm(db_session):
    db_session.add(Lead(company="A", industry="Кастомная отрасль", email="a@a.ru"))
    db_session.add(Lead(company="B", industry="—", email="b@b.ru"))
    await db_session.commit()

    catalog = await list_industry_catalog(db_session)
    assert "Кастомная отрасль" in catalog
    assert FIXED_INDUSTRIES[0] in catalog
    assert catalog == sorted(catalog, key=lambda x: x.casefold())


@pytest.mark.asyncio
async def test_segment_industry_stats(db_session):
    db_session.add_all(
        [
            Lead(company="A", industry="IT", email="a@a.ru"),
            Lead(company="B", industry="—", email="b@b.ru"),
        ]
    )
    await db_session.commit()
    from sqlalchemy import select

    rows = (await db_session.execute(select(Lead))).scalars().all()
    ids = [r.id for r in rows]

    stats = await segment_industry_stats(db_session, ids)
    assert stats["total"] == 2
    assert stats["withoutIndustry"] == 1


def test_segment_filter_industry_verified():
    verified = Lead(company="V", industry="IT", industry_verified=True, email="v@v.ru")
    raw = Lead(company="R", industry="IT", industry_verified=False, email="r@r.ru")
    seg = {"industry": "it", "industry_verified": True}
    assert lead_matches_segment(verified, seg)
    assert not lead_matches_segment(raw, seg)


@pytest.mark.asyncio
async def test_leads_industries_api(client, db_session):
    db_session.add(Lead(company="CRM Co", industry="Уникальная", email="u@u.ru"))
    await db_session.commit()

    r = await client.get("/api/leads/industries")
    assert r.status_code == 200, r.text
    data = r.json()
    assert "industries" in data
    assert "items" in data
    assert "Уникальная" in data["industries"]
    assert "IT и телеком" in data["industries"]
    row = next((x for x in data["items"] if x["name"] == "Уникальная"), None)
    assert row and row["count"] == 1


@pytest.mark.asyncio
async def test_industry_catalog_with_counts(db_session):
    from services.industry_catalog import industry_catalog_with_counts

    db_session.add_all(
        [
            Lead(company="A", industry="IT и телеком", email="a@a.ru"),
            Lead(company="B", industry="—", email="b@b.ru"),
        ]
    )
    await db_session.commit()
    data = await industry_catalog_with_counts(db_session)
    assert data["withoutIndustryCount"] == 1
    it_row = next(x for x in data["items"] if x["name"] == "IT и телеком")
    assert it_row["count"] == 1


@pytest.mark.asyncio
async def test_patch_industry_verified(client):
    create_r = await client.post("/api/leads", json={"company": "Verify Co", "industry": "Финансы"})
    assert create_r.status_code == 201
    lead_id = create_r.json()["id"]

    patch_r = await client.patch(
        f"/api/leads/{lead_id}",
        json={"industryVerified": True},
    )
    assert patch_r.status_code == 200
    assert patch_r.json().get("industryVerified") is True


@pytest.mark.asyncio
async def test_campaign_segment_preview_multi_industry(client, db_session):
    db_session.add_all(
        [
            Lead(company="It Co", industry="IT и телеком", email="it@it.ru", score=80),
            Lead(company="Fin Co", industry="Финансы", email="fin@fin.ru", score=80),
            Lead(company="Other", industry="Ритейл", email="r@r.ru", score=80),
        ]
    )
    await db_session.commit()

    r = await client.post(
        "/api/email/campaigns/segment-preview",
        json={"segment": {"industries": ["IT и телеком", "Финансы"], "min_score": 0}},
    )
    assert r.status_code == 200, r.text
    assert r.json()["count"] == 2


@pytest.mark.asyncio
async def test_campaign_segment_preview_without_industry(client, db_session):
    db_session.add_all(
        [
            Lead(company="Ok", industry="IT", email="ok@ok.ru", score=80),
            Lead(company="NoInd", industry="—", email="no@no.ru", score=80),
        ]
    )
    await db_session.commit()

    r = await client.post(
        "/api/email/campaigns/segment-preview",
        json={"segment": {"min_score": 0}},
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["count"] == 2
    assert data["withoutIndustry"] == 1
