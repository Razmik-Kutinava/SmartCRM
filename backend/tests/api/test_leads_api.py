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

    get_r = await client.get(f"/api/leads/{lead_id}")
    assert get_r.json()["email"] == "new@test.ru"


@pytest.mark.asyncio
async def test_update_lead_contacts_sets_lpr(client):
    """PATCH contacts → ЛПР в approvals и dealPath."""
    create_r = await client.post("/api/leads", json={"company": "Контакты Тест"})
    lead_id = create_r.json()["id"]
    contacts = [
        {
            "name": "Алексей",
            "role": "lpr",
            "position": "Гендиректор",
            "phones": ["+79001234567"],
            "emails": ["lpr@test.ru"],
            "messengers": ["telegram:@alex"],
        }
    ]
    patch_r = await client.patch(f"/api/leads/{lead_id}", json={"contacts": contacts})
    assert patch_r.status_code == 200
    data = patch_r.json()
    assert data["contact"] == "Алексей"
    assert data["email"] == "lpr@test.ru"
    assert data["approvals"]["lprEstablished"] is True
    qual = next(g for g in data["dealPath"]["groups"] if g["id"] == "qualification")
    lpr_step = next(s for s in qual["steps"] if s["key"] == "lprEstablished")
    assert lpr_step["done"] is True


@pytest.mark.asyncio
async def test_update_lead_amount_rub_camelcase(client):
    """PATCH с amountRub/paidAmountRub (как карточка /leads/{id}) сохраняется в БД."""
    create_r = await client.post("/api/leads", json={"company": "Суммы CRUD"})
    lead_id = create_r.json()["id"]

    patch_r = await client.patch(
        f"/api/leads/{lead_id}",
        json={"amountRub": 125000.5, "paidAmountRub": 50000},
    )
    assert patch_r.status_code == 200
    assert patch_r.json()["amountRub"] == 125000.5
    assert patch_r.json()["paidAmountRub"] == 50000.0

    get_r = await client.get(f"/api/leads/{lead_id}")
    assert get_r.json()["amountRub"] == 125000.5
    assert get_r.json()["paidAmountRub"] == 50000.0


@pytest.mark.asyncio
async def test_update_lead_stage(client):
    """PATCH обновляет этап воронки."""
    create_r = await client.post("/api/leads", json={"company": "Сменить этап"})
    lead_id = create_r.json()["id"]

    patch_r = await client.patch(f"/api/leads/{lead_id}", json={"stage": "Переговоры"})
    assert patch_r.status_code == 200
    assert patch_r.json()["stage"] == "Переговоры"


@pytest.mark.asyncio
async def test_update_lead_stage_blocked(client, monkeypatch):
    """PATCH stage → 400 stage_transition_blocked при правилах CRM."""
    from core import crm_settings_store

    monkeypatch.setattr(
        crm_settings_store,
        "load_settings",
        lambda: {
            "stages": ["Новый", "Выигран"],
            "stage_transition_rules": [
                {"to_stage": "Выигран", "require_non_empty": ["email"]},
            ],
        },
    )
    create_r = await client.post(
        "/api/leads",
        json={"company": "Блок стадии", "email": "—"},
    )
    lead_id = create_r.json()["id"]

    patch_r = await client.patch(f"/api/leads/{lead_id}", json={"stage": "Выигран"})
    assert patch_r.status_code == 400
    detail = patch_r.json()["detail"]
    assert detail["code"] == "stage_transition_blocked"
    assert detail["messages"]


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
async def test_delete_lead_with_nurture_chain(client, db_session):
    """DELETE лида с цепочкой nurture — 204, без FK-ошибки."""
    from datetime import datetime, timezone

    from db.models.email import EmailAccount
    from db.models.email_nurture import EmailNurtureChain, EmailNurtureStep

    create_r = await client.post("/api/leads", json={"company": "Удалить с nurture"})
    assert create_r.status_code == 201
    lead_id = create_r.json()["id"]

    acc = EmailAccount(
        name="test",
        provider="generic",
        username="u@test.ru",
        password="secret",
        imap_server="imap.test",
        smtp_server="smtp.test",
    )
    db_session.add(acc)
    await db_session.flush()
    chain = EmailNurtureChain(lead_id=lead_id, account_id=acc.id)
    db_session.add(chain)
    await db_session.flush()
    db_session.add(
        EmailNurtureStep(
            chain_id=chain.id,
            step_index=1,
            scheduled_at=datetime.now(timezone.utc),
        )
    )
    await db_session.commit()

    del_r = await client.delete(f"/api/leads/{lead_id}")
    assert del_r.status_code == 204

    get_r = await client.get(f"/api/leads/{lead_id}")
    assert get_r.status_code == 404


@pytest.mark.asyncio
async def test_multiple_leads_order(client):
    """Список возвращается по убыванию даты создания (новые сверху)."""
    await client.post("/api/leads", json={"company": "Первый"})
    await client.post("/api/leads", json={"company": "Второй"})
    r = await client.get("/api/leads")
    companies = [l["company"] for l in r.json()]
    assert companies.index("Второй") < companies.index("Первый")


@pytest.mark.asyncio
async def test_list_leads_includes_score_advisory_flags(client):
    """GET /api/leads — лёгкие флаги scoreAdvisory для фильтров списка."""
    create_r = await client.post(
        "/api/leads",
        json={"company": "Флаги advisory", "stage": "Новый", "score": 90},
    )
    assert create_r.status_code == 201

    r = await client.get("/api/leads")
    assert r.status_code == 200
    row = next(l for l in r.json() if l["company"] == "Флаги advisory")
    assert "hasScoreWarnings" in row
    assert "scoreDivergent" in row
    assert "suggestedScore" in row
    assert "scoreDelta" in row
    assert row["scoreDivergent"] is True
