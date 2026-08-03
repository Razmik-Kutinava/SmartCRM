"""POST /api/leads/{id}/raw-inbox — сырьё → поля + checko.analyses.raw_inbox."""
from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_raw_inbox_endpoint_fills_lead(client, monkeypatch):
    monkeypatch.setattr(
        "api.routes.leads.raw_inbox_routes.ingest_manual_text",
        lambda *args, **kwargs: {"chunks": 1, "dry_run": False},
    )
    cr = await client.post("/api/leads", json={"company": "Сырьё Тест", "stage": "Новый"})
    assert cr.status_code == 201
    lid = cr.json()["id"]

    r = await client.post(
        f"/api/leads/{lid}/raw-inbox",
        json={
            "text": "ИНН 7707083893\nтел +7 495 123-45-67\nemail sales@syrye.ru\nсайт https://syrye.ru",
            "ingest_rag": True,
        },
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body.get("summary")
    assert body.get("lead", {}).get("inn") == "7707083893"
    assert "sales@syrye.ru" in str(body["lead"].get("email") or "")
    checko = body["lead"].get("checko") or {}
    inbox = (checko.get("analyses") or {}).get("raw_inbox") or {}
    assert inbox.get("chunks")
    assert body.get("rag", {}).get("chunks") == 1


@pytest.mark.asyncio
async def test_raw_inbox_empty_text_400(client):
    cr = await client.post("/api/leads", json={"company": "Empty Raw", "stage": "Новый"})
    lid = cr.json()["id"]
    r = await client.post(f"/api/leads/{lid}/raw-inbox", json={"text": "  "})
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_raw_inbox_not_found(client):
    r = await client.post("/api/leads/999999/raw-inbox", json={"text": "ИНН 7707083893"})
    assert r.status_code == 404
