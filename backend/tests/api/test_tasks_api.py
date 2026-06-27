"""REST API задач: CRUD, lead_id, SLA-фильтры."""
import pytest


@pytest.mark.asyncio
async def test_task_crud_with_lead_and_sla(client):
    lead_r = await client.post("/api/leads", json={"company": "Задачи ООО"})
    lead_id = lead_r.json()["id"]

    create_r = await client.post(
        "/api/tasks",
        json={
            "title": "Позвонить",
            "lead_id": lead_id,
            "related_lead": "Задачи ООО",
            "sla_due": "18.04.2026",
            "due": "20.04.2026",
        },
    )
    assert create_r.status_code == 201
    task = create_r.json()
    task_id = task["id"]
    assert task["leadId"] == lead_id
    assert task["slaDue"] == "18.04.2026"

    by_lead = await client.get(f"/api/tasks?lead_id={lead_id}")
    assert by_lead.status_code == 200
    assert len(by_lead.json()) >= 1

    patch_r = await client.patch(f"/api/tasks/{task_id}", json={"status": "done", "escalated": True})
    assert patch_r.status_code == 200
    assert patch_r.json()["status"] == "done"
    assert patch_r.json()["escalated"] is True

    del_r = await client.delete(f"/api/tasks/{task_id}")
    assert del_r.status_code == 204


@pytest.mark.asyncio
async def test_tasks_filter_overdue(client):
    create_r = await client.post(
        "/api/tasks",
        json={"title": "Просрочка", "status": "open", "sla_due": "01.01.2020"},
    )
    assert create_r.status_code == 201

    overdue_r = await client.get("/api/tasks?status=overdue")
    assert overdue_r.status_code == 200
    titles = [t["title"] for t in overdue_r.json()]
    assert "Просрочка" in titles


@pytest.mark.asyncio
async def test_tasks_filter_done_and_combined(client):
    await client.post("/api/tasks", json={"title": "Готово", "status": "done", "due": "24.06.2026"})
    await client.post(
        "/api/tasks",
        json={"title": "Сегодня открыта", "status": "open", "due": "24.06.2026"},
    )

    done_r = await client.get("/api/tasks?task_status=done")
    assert done_r.status_code == 200
    assert all(t["status"] == "done" for t in done_r.json())

    combo_r = await client.get("/api/tasks?task_status=open&due=today")
    assert combo_r.status_code == 200
    titles = [t["title"] for t in combo_r.json()]
    assert "Сегодня открыта" in titles
    assert "Готово" not in titles


@pytest.mark.asyncio
async def test_task_intent_create_patch_and_catalog(client):
    catalog_r = await client.get("/api/tasks/intent-catalog")
    assert catalog_r.status_code == 200
    items = catalog_r.json()["items"]
    assert any(i["id"] == "kp_followup" for i in items)

    create_r = await client.post(
        "/api/tasks",
        json={
            "title": "Ответить на КП",
            "task_intent": "kp_followup",
            "note": "Срочно",
        },
    )
    assert create_r.status_code == 201
    task = create_r.json()
    task_id = task["id"]
    assert task["taskIntent"] == "kp_followup"
    assert task["note"] == "Срочно"
    assert "intent:" not in task["note"]

    patch_r = await client.patch(
        f"/api/tasks/{task_id}",
        json={"task_intent": "trial_request"},
    )
    assert patch_r.status_code == 200
    assert patch_r.json()["taskIntent"] == "trial_request"

    await client.delete(f"/api/tasks/{task_id}")
