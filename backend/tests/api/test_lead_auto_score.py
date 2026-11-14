"""Автоскор в шапке: score в API = scoreAdvisory.suggestedScore, ручное — score_manual."""
import pytest


@pytest.mark.asyncio
async def test_get_lead_returns_auto_score(client):
    """GET /api/leads/{id} — score = scoreAdvisory.suggestedScore (автоскор, не ручное поле)."""
    create_r = await client.post(
        "/api/leads",
        json={"company": "Автоскор Тест", "stage": "КП отправлено", "amountRub": 300000},
    )
    assert create_r.status_code == 201
    lead_id = create_r.json()["id"]

    get_r = await client.get(f"/api/leads/{lead_id}")
    assert get_r.status_code == 200
    data = get_r.json()
    advisory = data["scoreAdvisory"]
    assert advisory["suggestedScore"] is not None
    assert data["score"] == advisory["suggestedScore"], (
        f"score {data['score']} != suggestedScore {advisory['suggestedScore']}"
    )


@pytest.mark.asyncio
async def test_score_updates_on_stage_change(client):
    """Смена этапа → автоскор пересчитывается (не ручное поле)."""
    create_r = await client.post("/api/leads", json={"company": "Скор Этап", "stage": "Новый"})
    assert create_r.status_code == 201
    lead_id = create_r.json()["id"]

    r_new = await client.get(f"/api/leads/{lead_id}")
    assert r_new.json()["scoreAdvisory"]["suggestedScore"] == 28  # by_stage["Новый"]

    patch_r = await client.patch(f"/api/leads/{lead_id}", json={"stage": "Выигран"})
    assert patch_r.status_code == 200

    r_win = await client.get(f"/api/leads/{lead_id}")
    data = r_win.json()
    assert data["scoreAdvisory"]["suggestedScore"] == 88  # by_stage["Выигран"]
    assert data["score"] == 88  # автоскор обновился без ручного ввода


@pytest.mark.asyncio
async def test_score_manual_overrides_auto(client):
    """PATCH score → пишем в score_manual; GET отдаёт score = score_manual (ручное переопределение)."""
    create_r = await client.post("/api/leads", json={"company": "Ручной Скор", "stage": "Новый"})
    assert create_r.status_code == 201
    lead_id = create_r.json()["id"]

    patch_r = await client.patch(f"/api/leads/{lead_id}", json={"score": 77})
    assert patch_r.status_code == 200

    get_r = await client.get(f"/api/leads/{lead_id}")
    data = get_r.json()
    assert data["scoreManual"] == 77
    assert data["score"] == 77  # ручное переопределение приоритетнее формулы
    # advisory остаётся своей (для "Новый" = 28), не перезаписывается
    assert data["scoreAdvisory"]["suggestedScore"] == 28
