"""Этап B: массовая кампания по сегменту."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from starlette.testclient import TestClient

from db.models import EmailAccount, Lead
from main import app
from services.email_campaign_personalize import render_campaign_text
from services.lead_segment_query import lead_matches_segment

import core.auth as auth_module

_TEST_KEY = "pytest-smartcrm-key"


def test_render_campaign_placeholders():
    lead = Lead(company="Acme", contact="Ivan", email="i@acme.ru")
    body = render_campaign_text(
        "{{greeting}} {{company}} — {{product}}\n{{sender}}",
        lead,
        product="PT VM",
        sender_name="Иван",
        sender_email="ib@test.ru",
    )
    assert "Acme" in body
    assert "Ivan" in body
    assert "PT VM" in body
    assert "ib@test.ru" in body


def test_segment_filters_industry_city_search():
    lead = Lead(company="Bank X", industry="Финансы", city="Москва", stage="Новый", score=60, email="a@b.ru")
    assert lead_matches_segment(lead, {"industry": "финан", "city": "моск", "min_score": 50})
    assert not lead_matches_segment(lead, {"industry": "ритейл"})


@pytest.mark.asyncio
async def test_preview_manual_segment(db_session):
    from services.email_campaign_llm import preview_segment_campaign

    db_session.add_all(
        [
            Lead(company="A", contact="C1", email="a@a.ru", stage="Новый", score=80, industry="IT", city="Москва"),
            Lead(company="B", contact="C2", email="b@b.ru", stage="Новый", score=70, industry="IT", city="СПб"),
        ]
    )
    await db_session.commit()
    r = await preview_segment_campaign(
        db_session,
        segment={"stage": "Новый", "min_score": 50},
        product_name="PT VM",
        theme_mode="manual",
        subject_template="{{company}} — {{product}}",
        body_template="{{greeting}} {{company}}",
    )
    assert r["count"] == 2
    assert len(r["examples"]) >= 2
    assert "A" in r["examples"][0]["subject"]


@pytest.mark.asyncio
async def test_campaign_preview_llm_api(db_session):
    auth_module.API_KEY = _TEST_KEY
    lead = Lead(company="Zeta", contact="Ann", email="z@z.ru", stage="New", score=90)
    db_session.add(lead)
    await db_session.commit()

    fake = {
        "subject_template": "{{company}} — {{product}}",
        "body_template": "{{greeting}}\n{{sender}}",
        "examples": [{"company": "Zeta", "subject": "Zeta — PT", "body": "Hi"}],
        "summary": "ok",
    }
    with patch(
        "services.email_campaign_llm.preview_segment_campaign",
        AsyncMock(
            return_value={
                "count": 1,
                "leadIds": [lead.id],
                "subject_template": fake["subject_template"],
                "body_template": fake["body_template"],
                "examples": fake["examples"],
                "marketer": {"summary": "ok"},
                "has_rag": False,
                "segment": {"min_score": 0},
            }
        ),
    ):
        with TestClient(app) as tc:
            r = tc.post(
                "/api/email/campaigns/preview-llm",
                headers={"X-API-Key": _TEST_KEY},
                json={"segment": {"min_score": 0}, "product_name": "PT VM", "theme_mode": "marketer"},
            )
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["count"] >= 1
    assert data["subject_template"]
    assert data["examples"]


@pytest.mark.asyncio
async def test_campaign_test_send_api(client, db_engine):
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    sf = async_sessionmaker(db_engine, expire_on_commit=False, class_=AsyncSession)
    async with sf() as s:
        acc = EmailAccount(name="T", username="me@test.ru", password="x", imap_server="i", smtp_server="s")
        s.add(acc)
        await s.commit()
        await s.refresh(acc)
        aid = acc.id

    with patch("services.email_smtp.send_email_via_smtp", new=AsyncMock()):
        r = await client.post(
            "/api/email/campaigns/test-send",
            json={
                "account_id": aid,
                "to_email": "ib@agneko.com",
                "subject": "Test",
                "body": "Body",
            },
        )
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
