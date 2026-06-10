"""Dedup по ИНН при сохранении карточки лидогена в CRM."""
from __future__ import annotations

from contextlib import asynccontextmanager
from unittest.mock import patch

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from db.models import Lead
from leadgen.inn_constants import MOCK_INN_TECHNOSOFT
from leadgen.pipeline.persist import _save_to_crm


def _card(*, score: int, company: str = "ООО Тест") -> dict:
    return {
        "company_name": company,
        "inn": MOCK_INN_TECHNOSOFT,
        "final_score": score,
        "lpr": {"name": "Директор", "phone": "+79000000000", "email": "a@b.ru"},
        "financials": {"revenue": 100_000_000},
        "tech_stack": {"maturity": "high"},
    }


@pytest.fixture
def db_session_factory(db_engine):
    return async_sessionmaker(db_engine, expire_on_commit=False, class_=AsyncSession)


@pytest.fixture
def fake_get_db(db_session_factory):
    @asynccontextmanager
    async def _fake():
        async with db_session_factory() as session:
            yield session

    return _fake


@pytest.mark.asyncio
async def test_save_dedup_updates_same_lead(db_session_factory, fake_get_db):
    with patch("db.session.get_db_session", fake_get_db):
        card1 = _card(score=74, company="Первая версия")
        id1 = await _save_to_crm(card1)
        assert id1 is not None
        assert card1.get("crm_lead_created") is True

        card2 = _card(score=88, company="Обновлённая версия")
        id2 = await _save_to_crm(card2)
        assert id2 == id1
        assert card2.get("crm_lead_created") is False

    async with db_session_factory() as session:
        count = await session.scalar(
            select(func.count()).select_from(Lead).where(Lead.inn == MOCK_INN_TECHNOSOFT)
        )
        assert count == 1
        lead = await session.get(Lead, id1)
        assert lead.company == "Обновлённая версия"
        assert lead.score == 88
        assert lead.stage == "Новый"


@pytest.mark.asyncio
async def test_save_without_inn_creates_two_leads(db_session_factory, fake_get_db):
    with patch("db.session.get_db_session", fake_get_db):
        c1 = _card(score=50)
        c1.pop("inn")
        id1 = await _save_to_crm(c1)

        c2 = _card(score=60)
        c2.pop("inn")
        id2 = await _save_to_crm(c2)

    assert id1 is not None and id2 is not None
    assert id1 != id2


@pytest.mark.asyncio
async def test_save_dedup_preserves_stage(db_session_factory, fake_get_db):
    with patch("db.session.get_db_session", fake_get_db):
        id1 = await _save_to_crm(_card(score=40))

    async with db_session_factory() as session:
        lead = await session.get(Lead, id1)
        lead.stage = "Переговоры"
        await session.commit()

    with patch("db.session.get_db_session", fake_get_db):
        await _save_to_crm(_card(score=90))

    async with db_session_factory() as session:
        lead = await session.get(Lead, id1)
        assert lead.stage == "Переговоры"
        assert lead.score == 90
