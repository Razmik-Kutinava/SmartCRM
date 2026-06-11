"""API baseline Ops `/ops` — read-эндпоинты и редактирование промптов."""
import pytest

from tests.lib.test_ops_route_manifest import OPS_API_READ_SMOKE

_MIN_PROMPT = "x" * 50


@pytest.mark.asyncio
@pytest.mark.parametrize("path", OPS_API_READ_SMOKE)
async def test_ops_read_endpoints(client, path):
    r = await client.get(path)
    assert r.status_code == 200, f"{path}: {r.status_code} {r.text[:200]}"


@pytest.mark.asyncio
async def test_ops_overview_shape(client):
    body = (await client.get("/api/ops/overview")).json()
    assert "pipeline" in body
    assert "stats" in body
    assert "queue" in body


@pytest.mark.asyncio
async def test_ops_agents_list_five(client):
    agents = (await client.get("/api/ops/agents")).json()["agents"]
    assert len(agents) == 5
    ids = {a["id"] for a in agents}
    assert "analyst" in ids and "strategist" in ids


@pytest.mark.asyncio
async def test_ops_agent_prompt_put_roundtrip(client):
    path = "/api/ops/agents/marketer/prompt"
    original = (await client.get(path)).json()
    custom = _MIN_PROMPT + "\n# ops baseline test override"
    put = await client.put(path, json={"prompt": custom})
    assert put.status_code == 200
    assert (await client.get(path)).json()["source"] == "override"
    if original.get("source") == "override":
        await client.put(path, json={"prompt": original["prompt"]})
    else:
        await client.delete(path)


@pytest.mark.asyncio
async def test_ops_crm_settings_roundtrip(client, monkeypatch, tmp_path):
    from core import crm_settings_store

    fake = tmp_path / "crm_settings.json"
    monkeypatch.setattr(crm_settings_store, "_FILE", fake)
    get_r = await client.get("/api/ops/crm-settings")
    assert get_r.status_code == 200
    settings = get_r.json()["settings"]
    put_r = await client.put("/api/ops/crm-settings", json=settings)
    assert put_r.status_code == 200
