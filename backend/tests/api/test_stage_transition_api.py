"""API правил переходов стадий."""
import pytest


@pytest.mark.asyncio
async def test_crm_config_exposes_stage_transition_rules(client, monkeypatch):
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
    r = await client.get("/api/crm/config")
    assert r.status_code == 200
    rules = r.json().get("stageTransitionRules") or []
    assert len(rules) == 1
    assert rules[0]["to_stage"] == "Выигран"


@pytest.mark.asyncio
async def test_stage_transition_same_patch_satisfies_rule(client, monkeypatch):
    from core import crm_settings_store

    monkeypatch.setattr(
        crm_settings_store,
        "load_settings",
        lambda: {
            "stages": ["Новый", "Выигран"],
            "stage_transition_rules": [
                {"to_stage": "Выигран", "require_non_empty": ["email", "company"]},
            ],
        },
    )
    create_r = await client.post(
        "/api/leads",
        json={"company": "—", "email": "—"},
    )
    lead_id = create_r.json()["id"]

    patch_r = await client.patch(
        f"/api/leads/{lead_id}",
        json={"stage": "Выигран", "email": "win@corp.ru", "company": "Corp"},
    )
    assert patch_r.status_code == 200
    assert patch_r.json()["stage"] == "Выигран"


@pytest.mark.asyncio
async def test_ops_crm_settings_save_rules(client, monkeypatch, tmp_path):
    from core import crm_settings_store

    fake_file = tmp_path / "crm_settings.json"
    monkeypatch.setattr(crm_settings_store, "_FILE", fake_file)

    put_r = await client.put(
        "/api/ops/crm-settings",
        json={
            "stages": ["Новый", "Выигран"],
            "stage_transition_rules": [
                {"to_stage": "Выигран", "require_non_empty": ["phone"], "junk": True},
                {"to_stage": "", "require_non_empty": ["email"]},
            ],
        },
    )
    assert put_r.status_code == 200
    saved = put_r.json()["settings"]["stage_transition_rules"]
    assert len(saved) == 1
    assert saved[0]["to_stage"] == "Выигран"
    assert saved[0]["require_non_empty"] == ["phone"]

    create_r = await client.post("/api/leads", json={"company": "Ops rules", "phone": "—"})
    lead_id = create_r.json()["id"]
    block_r = await client.patch(f"/api/leads/{lead_id}", json={"stage": "Выигран"})
    assert block_r.status_code == 400
    assert block_r.json()["detail"]["code"] == "stage_transition_blocked"
