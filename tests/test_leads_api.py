"""
Тесты REST API лидов: GET / POST / PATCH / DELETE.
Проверяем, что данные попадают в БД и переживают перезагрузку (возвращаются через GET).
"""
import pytest


@pytest.mark.asyncio
async def test_list_leads_empty(client):
    """Пустая БД → пустой список."""
    r = await client.get("/api/leads")
    assert r.status_code == 200
    assert r.json() == []


@pytest.mark.asyncio
async def test_create_lead(client):
    """POST создаёт лид с нужными полями и возвращает id."""
    payload = {
        "company": "ООО Ромашка",
        "contact": "Пётр Сергеевич",
        "phone": "+7775631",
        "email": "—",
        "stage": "Новый",
    }
    r = await client.post("/api/leads", json=payload)
    assert r.status_code == 201
    data = r.json()
    assert data["id"] > 0
    assert data["company"] == "ООО Ромашка"
    assert data["contact"] == "Пётр Сергеевич"
    assert data["stage"] == "Новый"


@pytest.mark.asyncio
async def test_lead_persists_after_reload(client):
    """
    Главный баг: лид создан голосом → после 'перезагрузки' (новый GET) лид должен быть в списке.
    """
    await client.post("/api/leads", json={"company": "Персистент Тест"})
    r = await client.get("/api/leads")
    companies = [l["company"] for l in r.json()]
    assert "Персистент Тест" in companies


@pytest.mark.asyncio
async def test_get_lead_by_id(client):
    """GET /api/leads/{id} возвращает нужный лид."""
    create_r = await client.post("/api/leads", json={"company": "Точный поиск"})
    lead_id = create_r.json()["id"]

    r = await client.get(f"/api/leads/{lead_id}")
    assert r.status_code == 200
    assert r.json()["company"] == "Точный поиск"


@pytest.mark.asyncio
async def test_get_lead_not_found(client):
    """GET несуществующего лида → 404."""
    r = await client.get("/api/leads/99999")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_update_lead_email(client):
    """
    PATCH обновляет поле email — голосовая команда «исправь почту» должна сохраниться.
    """
    create_r = await client.post("/api/leads", json={"company": "Обновить почту", "email": "old@test.ru"})
    lead_id = create_r.json()["id"]

    patch_r = await client.patch(f"/api/leads/{lead_id}", json={"email": "new@test.ru"})
    assert patch_r.status_code == 200
    assert patch_r.json()["email"] == "new@test.ru"

    # Проверяем, что изменение сохранилось в БД
    get_r = await client.get(f"/api/leads/{lead_id}")
    assert get_r.json()["email"] == "new@test.ru"


@pytest.mark.asyncio
async def test_update_lead_stage(client):
    """PATCH обновляет этап воронки."""
    create_r = await client.post("/api/leads", json={"company": "Сменить этап"})
    lead_id = create_r.json()["id"]

    patch_r = await client.patch(f"/api/leads/{lead_id}", json={"stage": "Переговоры"})
    assert patch_r.status_code == 200
    assert patch_r.json()["stage"] == "Переговоры"


@pytest.mark.asyncio
async def test_update_lead_not_found(client):
    """PATCH несуществующего → 404."""
    r = await client.patch("/api/leads/99999", json={"stage": "Выигран"})
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_delete_lead(client):
    """DELETE удаляет лид; после — GET возвращает 404."""
    create_r = await client.post("/api/leads", json={"company": "К удалению"})
    lead_id = create_r.json()["id"]

    del_r = await client.delete(f"/api/leads/{lead_id}")
    assert del_r.status_code == 204

    get_r = await client.get(f"/api/leads/{lead_id}")
    assert get_r.status_code == 404


@pytest.mark.asyncio
async def test_delete_lead_not_found(client):
    """DELETE несуществующего → 404."""
    r = await client.delete("/api/leads/99999")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_multiple_leads_order(client):
    """Список возвращается по убыванию даты создания (новые сверху)."""
    await client.post("/api/leads", json={"company": "Первый"})
    await client.post("/api/leads", json={"company": "Второй"})
    r = await client.get("/api/leads")
    companies = [l["company"] for l in r.json()]
    assert companies.index("Второй") < companies.index("Первый")
