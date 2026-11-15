"""Ф3 Email: FAQ, сегменты, nurture, domain link."""
from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import select
from starlette.testclient import TestClient

from db.models import EmailMessage, EmailThread, Lead
from db.models.agent_email_intent import AgentEmailIntent
from db.models.email_nurture import EmailNurtureChain, EmailNurtureStep
from main import app
from services.email_faq_matcher import match_faq_intent
from services.email_lead_match import email_domain, find_lead_for_email, lead_domain_keys
from services.email_nurture import start_nurture_chain
from services.email_nurture_plan import build_20_touch_plan, personalize_touch
from services.lead_segment_query import lead_matches_segment, resolve_segment_lead_ids

import core.auth as auth_module

_TEST_KEY = "pytest-smartcrm-key"


def test_email_domain_extract():
    assert email_domain("User@Hochland.RU") == "hochland.ru"


def test_lead_domain_keys_website():
    lead = Lead(company="X", email="a@beta.ru", website="https://www.beta.ru/page")
    keys = lead_domain_keys(lead)
    assert "beta.ru" in keys


@pytest.mark.asyncio
async def test_find_lead_by_domain(db_session):
    lead = Lead(company="Hochland", email="—", website="hochland.ru", stage="Новый", score=50)
    db_session.add(lead)
    await db_session.commit()

    found = await find_lead_for_email(
        db_session,
        "Client <buyer@hochland.ru>",
        "",
        "",
    )
    assert found is not None
    assert found.company == "Hochland"


def test_faq_matcher_keywords():
    intent = AgentEmailIntent(
        intent_name="FAQ цены",
        agent_name="marketer",
        trigger_keywords="прайс,стоимость",
        action_template="Ответ",
        auto_send=True,
        is_active=True,
    )
    assert match_faq_intent("Скиньте прайс", [intent]) is intent
    assert match_faq_intent("Договор", [intent]) is None


def test_build_20_touch_plan():
    lead = Lead(company="Acme", contact="Ivan")
    plan = build_20_touch_plan(lead, product="MegaCRM")
    assert len(plan) == 20
    assert plan[0]["channel"] == "email"
    assert "{{company}}" in plan[0]["subject"]
    rendered = personalize_touch(plan[0]["body"], lead, product="MegaCRM")
    assert "Acme" in rendered
    assert "Ivan" in rendered
    assert "MegaCRM" in rendered


@pytest.mark.asyncio
async def test_nurture_process_due_personalized(db_session):
    from db.models import EmailAccount
    from services.email_nurture import process_due_nurture_steps, start_nurture_chain

    acc = EmailAccount(
        name="t", username="me@test.ru", password="x", imap_server="i", smtp_server="s"
    )
    db_session.add(acc)
    await db_session.flush()
    lead = Lead(company="BetaCorp", contact="Anna", email="client@betacorp.ru", score=60)
    db_session.add(lead)
    await db_session.commit()

    await start_nurture_chain(
        db_session, lead_id=lead.id, account_id=acc.id, product="NewProduct"
    )
    await db_session.commit()

    from unittest.mock import AsyncMock, patch

    with patch("services.email_smtp.send_email_via_smtp", AsyncMock()) as mock_send:
        stats = await process_due_nurture_steps(db_session)
        await db_session.commit()

    assert stats["emails_sent"] == 1
    args = mock_send.call_args[0]
    assert "BetaCorp" in args[1]
    assert "Anna" in args[2]
    assert "NewProduct" in args[2]


def test_lead_matches_segment_stage():
    lead = Lead(company="A", stage="Новый", score=80, email="a@x.ru")
    assert lead_matches_segment(lead, {"stage": "Новый"})
    assert not lead_matches_segment(lead, {"stage": "Выигран"})


@pytest.mark.asyncio
async def test_resolve_segment_lead_ids(db_session):
    db_session.add(Lead(company="Hot", stage="Новый", score=90, email="hot@co.ru"))
    db_session.add(Lead(company="Cold", stage="Проигран", score=10, email="—"))
    await db_session.commit()
    ids = await resolve_segment_lead_ids(db_session, {"stage": "Новый", "min_score": 50})
    assert len(ids) == 1


@pytest.mark.asyncio
async def test_start_nurture_chain(db_session):
    from db.models import EmailAccount

    acc = EmailAccount(
        name="t", username="t@test.ru", password="x", imap_server="i", smtp_server="s"
    )
    db_session.add(acc)
    await db_session.flush()
    lead = Lead(company="NurtureCo", email="n@nurture.ru", score=60)
    db_session.add(lead)
    await db_session.commit()

    chain = await start_nurture_chain(db_session, lead_id=lead.id, account_id=acc.id)
    steps = (
        await db_session.execute(select(EmailNurtureStep).where(EmailNurtureStep.chain_id == chain.id))
    ).scalars().all()
    assert chain.steps_total == 20
    assert len(steps) == 20


def test_segment_preview_api():
    auth_module._API_KEY = _TEST_KEY
    with patch(
        "api.routes.email.resolve_segment_lead_ids",
        AsyncMock(return_value=[1, 2, 3]),
    ):
        with TestClient(app) as tc:
            r = tc.post(
                "/api/email/campaigns/segment-preview",
                json={"segment": {"stage": "Новый", "min_score": 50}},
                headers={"X-API-Key": _TEST_KEY},
            )
    assert r.status_code == 200
    assert r.json()["count"] == 3


def test_f3_ui_contracts():
    from pathlib import Path
    repo = Path(__file__).resolve().parents[3]
    ops = (repo / "frontend/src/routes/ops/email/+page.svelte").read_text(encoding="utf-8")
    assert "nurture-chains-table" in ops
    agents = (repo / "frontend/src/routes/ops/email-agents/+page.svelte").read_text(encoding="utf-8")
    assert "faq-auto-send" in agents


@pytest.mark.asyncio
async def test_build_lead_match_index(db_session):
    from services.email_lead_match import build_lead_match_index

    db_session.add(Lead(company="DomCo", email="sales@domco.ru", website="https://domco.ru"))
    await db_session.commit()
    idx = await build_lead_match_index(db_session)
    assert idx.get("sales@domco.ru")
    assert idx.get("domco.ru")


@pytest.mark.asyncio
async def test_relink_orphans_api(client, db_session):
    from db.models import EmailAccount
    from services.email_lead_match import relink_orphan_threads

    acc = EmailAccount(
        name="t", username="t@test.ru", password="x", imap_server="i", smtp_server="s"
    )
    db_session.add(acc)
    lead = Lead(company="RelinkCo", email="buyer@relinkco.ru", website="relinkco.ru")
    db_session.add(lead)
    await db_session.flush()
    thread = EmailThread(account_id=acc.id, subject="Hi", thread_key="Hi")
    db_session.add(thread)
    await db_session.flush()
    db_session.add(
        EmailMessage(
            account_id=acc.id,
            thread_id=thread.id,
            message_id="r1",
            subject="Hi",
            sender="buyer@relinkco.ru",
            direction="inbound",
            sent_at=datetime.now(timezone.utc),
        )
    )
    await db_session.commit()

    stats = await relink_orphan_threads(db_session, limit=10)
    assert stats["threads_linked"] == 1


@pytest.mark.asyncio
async def test_faq_autoreply_mocked(db_session, monkeypatch):
    from db.models import EmailAccount
    from services.email_faq_autoreply import try_faq_autoreply

    # .env может выключить FAQ (EMAIL_FAQ_AUTOREPLY=0) — для юнит-теста включаем
    monkeypatch.setenv("EMAIL_FAQ_AUTOREPLY", "1")

    acc = EmailAccount(
        name="t", username="me@corp.ru", password="x", imap_server="i", smtp_server="s"
    )
    db_session.add(acc)
    await db_session.flush()
    thread = EmailThread(account_id=acc.id, subject="Q", thread_key="Q")
    db_session.add(thread)
    await db_session.flush()
    inbound = EmailMessage(
        account_id=acc.id,
        thread_id=thread.id,
        message_id="in-1",
        subject="Прайс",
        sender="client@clientco.ru",
        body="Пришлите прайс",
        direction="inbound",
        sent_at=datetime.now(timezone.utc),
    )
    db_session.add(inbound)
    await db_session.flush()

    intent = AgentEmailIntent(
        agent_name="marketer",
        intent_name="price",
        trigger_keywords="прайс",
        action_template="Вот прайс",
        auto_send=True,
        reply_subject="Re: прайс",
        is_active=True,
    )
    db_session.add(intent)
    await db_session.commit()

    with patch("services.email_smtp.send_email_via_smtp", AsyncMock()):
        ok = await try_faq_autoreply(db_session, acc, inbound)
    assert ok is True
