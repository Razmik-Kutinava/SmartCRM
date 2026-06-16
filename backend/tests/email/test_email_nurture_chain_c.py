"""Этап C: products_owned и chain_type nurture."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from db.models import Lead
from db.models.email_nurture import EmailNurtureChain
from services.lead_products_owned import normalize_products_owned
from services.email_nurture import start_nurture_chain
from services.email_nurture_llm import build_marketer_slots


def test_normalize_products_owned():
    assert normalize_products_owned(None) == []
    assert normalize_products_owned("A\nB; C") == ["A", "B", "C"]
    assert normalize_products_owned(["X", ""]) == ["X"]


@pytest.mark.asyncio
async def test_patch_products_owned(client):
    create_r = await client.post("/api/leads", json={"company": "Products Co"})
    assert create_r.status_code == 201
    lead_id = create_r.json()["id"]

    patch_r = await client.patch(
        f"/api/leads/{lead_id}",
        json={"productsOwned": ["MaxPatrol VM", "OpManager"]},
    )
    assert patch_r.status_code == 200
    data = patch_r.json()
    assert data.get("productsOwned") == ["MaxPatrol VM", "OpManager"]


@pytest.mark.asyncio
async def test_build_marketer_slots_includes_products(db_session):
    lead = Lead(
        company="Bank",
        industry="IT",
        email="a@b.ru",
        products_owned=["PT VM"],
    )
    db_session.add(lead)
    await db_session.commit()
    await db_session.refresh(lead)

    with patch(
        "services.email_nurture_llm.attach_product_rag",
        AsyncMock(side_effect=lambda s: s),
    ):
        slots = await build_marketer_slots(db_session, lead, product_name="SIEM", chain_type="cross")
    assert slots["products_owned"] == ["PT VM"]
    assert slots["chain_type"] == "cross"


@pytest.mark.asyncio
async def test_start_nurture_chain_chain_type(db_session):
    from db.models import EmailAccount

    lead = Lead(company="Chain Co", email="c@c.ru")
    acc = EmailAccount(name="T", username="t@t.ru", password="x", imap_server="i", smtp_server="s")
    db_session.add_all([lead, acc])
    await db_session.commit()
    await db_session.refresh(lead)
    await db_session.refresh(acc)

    chain = await start_nurture_chain(
        db_session,
        lead_id=lead.id,
        account_id=acc.id,
        plan=[{"day": 0, "subject": "S", "body": "B"}],
        product="OpManager",
        chain_type="upsell",
    )
    assert chain.chain_type == "upsell"
    assert chain.product_name == "OpManager"
    row = await db_session.get(EmailNurtureChain, chain.id)
    assert row is not None
    assert row.chain_type == "upsell"
