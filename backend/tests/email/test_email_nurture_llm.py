"""Тесты LLM nurture (без live LLM)."""
from __future__ import annotations

import pytest

from services.email_nurture_llm import llm_emails_to_plan, pick_nurture_lead
from db.models import Lead


def test_llm_emails_to_plan_live_now():
    llm = {
        "emails": [
            {"step": 1, "day": 0, "subject": "S1", "body": "Body 1"},
            {"step": 2, "day": 3, "subject": "S2", "body": "Body 2"},
            {"step": 3, "day": 6, "subject": "S3", "body": "Body 3"},
        ]
    }
    plan = llm_emails_to_plan(llm, live_all_now=True)
    assert len(plan) == 3
    assert all(s["day"] == 0 for s in plan)
    assert plan[0]["subject"] == "S1"


def test_llm_emails_to_plan_spaced():
    llm = {"emails": [{"day": 6, "subject": "X", "body": "Y"}]}
    plan = llm_emails_to_plan(llm, live_all_now=False)
    assert plan[0]["day"] == 6


def test_build_manual_emails():
    from services.email_nurture_llm import build_manual_emails

    r = build_manual_emails(
        count=2,
        product_name="PT VM",
        company="ООО Тест",
        contact="Иван",
        sender_name="IB",
        sender_email="ib@test.ru",
    )
    assert len(r["emails"]) == 2
    assert "ООО Тест" in r["emails"][0]["subject"]
    assert "Иван" in r["emails"][0]["body"]


@pytest.mark.asyncio
async def test_pick_nurture_lead_skips_test_prefix(db_session):
    db_session.add(
        Lead(company="Nurture Live Test", industry="IT", email="a@b.ru", score=90)
    )
    db_session.add(
        Lead(
            company="Ромашка Банк",
            industry="Финансы",
            email="c@bank.ru",
            description="Региональный банк, ДБО",
            score=80,
        )
    )
    await db_session.commit()
    lead = await pick_nurture_lead(db_session)
    assert lead is not None
    assert "Nurture Live" not in (lead.company or "")
