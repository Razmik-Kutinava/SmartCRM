"""Автосейв списка компаний (портрет / кластер)."""
from __future__ import annotations

from contextlib import asynccontextmanager
from unittest.mock import patch

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from db.models import Lead
from leadgen.inn_constants import MOCK_INN_TECHNOSOFT
from leadgen.pipeline.persist_autosave import (
    autosave_companies,
    minimal_card_from_company,
    portrait_fit_score,
)


def test_portrait_fit_score_prefers_agent_review():
    company = {"inn": "7701000001", "_portrait_match": 0.4}
    review = {"companies": [{"inn": "7701000001", "fit_score": 72}]}
    assert portrait_fit_score(company, review) == 72


def test_portrait_fit_score_fallback_match():
    company = {"inn": "7701000001", "_portrait_match": 0.82}
    assert portrait_fit_score(company, {}) == 82


@pytest.mark.asyncio
async def test_autosave_companies_skips_below_threshold(db_engine):
    from leadgen.crm_threshold import DEFAULT_CRM_SCORE_THRESHOLD

    factory = async_sessionmaker(db_engine, expire_on_commit=False, class_=AsyncSession)

    @asynccontextmanager
    async def fake_session():
        async with factory() as session:
            yield session

    companies = [
        {"inn": MOCK_INN_TECHNOSOFT, "name": "High", "city": "Москва"},
        {"inn": "7701000099", "name": "Low", "city": "Москва"},
    ]
    with patch("db.session.get_db_session", fake_session):
        saved = await autosave_companies(
            companies,
            save_to_crm=True,
            score_for=lambda c: 80 if c["inn"] == MOCK_INN_TECHNOSOFT else DEFAULT_CRM_SCORE_THRESHOLD - 1,
        )
    assert len(saved) == 1
    assert saved[0]["inn"] == MOCK_INN_TECHNOSOFT


@pytest.mark.asyncio
async def test_autosave_companies_dedup_same_inn(db_engine):
    factory = async_sessionmaker(db_engine, expire_on_commit=False, class_=AsyncSession)

    @asynccontextmanager
    async def fake_session():
        async with factory() as session:
            yield session

    dup = {"inn": MOCK_INN_TECHNOSOFT, "name": "A", "city": "Москва"}
    with patch("db.session.get_db_session", fake_session):
        saved = await autosave_companies(
            [dup, dup],
            save_to_crm=True,
            score_for=lambda _c: 55,
        )
    assert len(saved) == 1

    async with factory() as session:
        count = await session.scalar(
            select(func.count()).select_from(Lead).where(Lead.inn == MOCK_INN_TECHNOSOFT)
        )
        assert count == 1


def test_minimal_card_from_company():
    card = minimal_card_from_company(
        {"inn": "123", "name": "ООО Тест", "director": "Иванов", "city": "СПб"},
        final_score=60,
    )
    assert card["company_name"] == "ООО Тест"
    assert card["final_score"] == 60
    assert card["lpr"]["name"] == "Иванов"
