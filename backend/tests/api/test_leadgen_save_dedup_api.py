"""POST /api/leadgen/save — dedup по ИНН."""
from __future__ import annotations

from contextlib import asynccontextmanager
from unittest.mock import patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from leadgen.inn_constants import MOCK_INN_TECHNOSOFT


@pytest.fixture
def leadgen_db(db_engine):
    factory = async_sessionmaker(db_engine, expire_on_commit=False, class_=AsyncSession)

    @asynccontextmanager
    async def fake_session():
        async with factory() as session:
            yield session

    with patch("db.session.get_db_session", fake_session):
        yield factory


@pytest.mark.asyncio
async def test_save_api_created_then_updated(client, leadgen_db):
    card = {
        "company_name": "Dedup API Co",
        "inn": MOCK_INN_TECHNOSOFT,
        "final_score": 55,
        "lpr": {"name": "CEO", "phone": "+79001112233", "email": "ceo@test.ru"},
        "financials": {},
        "tech_stack": {},
    }
    r1 = await client.post("/api/leadgen/save", json={"card": card})
    assert r1.status_code == 200
    d1 = r1.json()
    assert d1["created"] is True

    card["final_score"] = 77
    card["company_name"] = "Dedup API Co v2"
    r2 = await client.post("/api/leadgen/save", json={"card": card})
    assert r2.status_code == 200
    d2 = r2.json()
    assert d2["lead_id"] == d1["lead_id"]
    assert d2["created"] is False
