"""API аудита изменений полей лида."""
import pytest


@pytest.mark.asyncio
async def test_lead_audit_not_found(client):
    r = await client.get("/api/leads/999999/audit")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_patch_creates_field_audit(client):
    create_r = await client.post("/api/leads", json={"company": "До патча"})
    lead_id = create_r.json()["id"]

    patch_r = await client.patch(
        f"/api/leads/{lead_id}",
        json={"company": "После патча", "city": "Москва"},
        headers={"x-actor-name": "Anna"},
    )
    assert patch_r.status_code == 200

    audit_r = await client.get(f"/api/leads/{lead_id}/audit")
    assert audit_r.status_code == 200
    rows = audit_r.json()
    fields = {row["field"] for row in rows}
    assert "company" in fields
    assert "city" in fields
    company_row = next(r for r in rows if r["field"] == "company")
    assert company_row["oldValue"] == "До патча"
    assert company_row["newValue"] == "После патча"
    assert company_row["actor"] == "Anna"
    assert company_row["eventType"] == "field_change"


@pytest.mark.asyncio
async def test_patch_same_value_no_extra_audit(client):
    create_r = await client.post("/api/leads", json={"company": "Stable"})
    lead_id = create_r.json()["id"]

    await client.patch(f"/api/leads/{lead_id}", json={"score": 10})
    audit1 = await client.get(f"/api/leads/{lead_id}/audit")
    count1 = len(audit1.json())

    await client.patch(f"/api/leads/{lead_id}", json={"score": 10})
    audit2 = await client.get(f"/api/leads/{lead_id}/audit")
    assert len(audit2.json()) == count1


@pytest.mark.asyncio
async def test_audit_newest_first(client):
    create_r = await client.post("/api/leads", json={"company": "Order audit"})
    lead_id = create_r.json()["id"]

    await client.patch(f"/api/leads/{lead_id}", json={"city": "A"})
    await client.patch(f"/api/leads/{lead_id}", json={"city": "B"})

    rows = (await client.get(f"/api/leads/{lead_id}/audit")).json()
    city_rows = [r for r in rows if r["field"] == "city"]
    assert len(city_rows) >= 2
    assert city_rows[0]["newValue"] == "B"
    assert city_rows[1]["newValue"] == "A"


@pytest.mark.asyncio
async def test_audit_amount_rub_change(client):
    create_r = await client.post("/api/leads", json={"company": "Money audit"})
    lead_id = create_r.json()["id"]

    await client.patch(f"/api/leads/{lead_id}", json={"amountRub": 50000})
    rows = (await client.get(f"/api/leads/{lead_id}/audit")).json()
    amount_rows = [r for r in rows if r["field"] == "amount_rub"]
    assert len(amount_rows) >= 1
    assert "50000" in amount_rows[0]["newValue"]
