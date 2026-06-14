"""POST /api/leads/lookalike-import после voice approve."""
import pytest


@pytest.mark.asyncio
async def test_lookalike_import_creates_leads(client):
    payload = {
        "leads": [
            {"company": "Lookalike Alpha", "city": "Москва", "score": 88, "matched_by": ["similar_city"]},
            {"company": "Lookalike Beta", "industry": "IT", "score": 75},
        ],
    }
    r = await client.post("/api/leads/lookalike-import", json=payload)
    assert r.status_code == 201
    data = r.json()
    assert data["count"] == 2
    assert len(data["created"]) == 2
    assert data["created"][0]["source"] == "lookalike"
    assert data["created"][0]["stage"] == "Новый"


@pytest.mark.asyncio
async def test_lookalike_import_skips_duplicate_company(client):
    await client.post("/api/leads", json={"company": "Dup Co", "stage": "Новый"})
    r = await client.post(
        "/api/leads/lookalike-import",
        json={"leads": [{"company": "Dup Co", "score": 90}]},
    )
    assert r.status_code == 201
    data = r.json()
    assert data["count"] == 0
    assert data["skipped"][0]["reason"] == "duplicate"
