"""API экспорта баллов и воронки."""
import pytest


@pytest.mark.asyncio
async def test_scoring_export_csv(client):
    await client.post("/api/leads", json={"company": "Score Exp", "stage": "Новый", "score": 70})
    r = await client.get("/api/leads/scoring/export?format=csv")
    assert r.status_code == 200
    text = r.text
    assert "managerScore" in text or "avgManagerScore" in text
    assert "Score Exp" in text or "company" in text


@pytest.mark.asyncio
async def test_scoring_export_xlsx(client):
    r = await client.get("/api/leads/scoring/export?format=xlsx")
    assert r.status_code == 200
    assert r.content[:2] == b"PK"


@pytest.mark.asyncio
async def test_scoring_export_bad_format(client):
    r = await client.get("/api/leads/scoring/export?format=doc")
    assert r.status_code == 400
