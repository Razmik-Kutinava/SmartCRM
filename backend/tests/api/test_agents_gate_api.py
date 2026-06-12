"""API POST /api/ops/eval/agents-gate."""
from unittest.mock import AsyncMock, patch

import pytest


@pytest.mark.asyncio
async def test_agents_gate_status_ready(client):
    with patch(
        "api.routes.ops.eval_routes.check_ollama_ready",
        new_callable=AsyncMock,
        return_value={"host": "http://localhost:11434", "model": "hermes3:latest", "available_models": []},
    ):
        r = await client.get("/api/ops/eval/agents-gate/status")
    assert r.status_code == 200
    assert r.json()["ready"] is True


@pytest.mark.asyncio
async def test_agents_gate_run_mocked(client):
    fake = {
        "generated_at": "2026-01-01T00:00:00+00:00",
        "ollama": {"model": "hermes3:latest"},
        "agents": {"hermes": {"summary": {"gate": "pass"}}},
        "overall_gate": "pass",
    }
    with patch(
        "api.routes.ops.eval_gate_routes.run_agents_quality_gate",
        new_callable=AsyncMock,
        return_value=fake,
    ), patch("api.routes.ops.eval_gate_routes.save_gate_artifact", return_value="/tmp/x.json"):
        r = await client.post("/api/ops/eval/agents-gate", json={"hermes_limit": 1, "save_artifact": False})
    assert r.status_code == 200
    assert r.json()["overall_gate"] == "pass"


@pytest.mark.asyncio
async def test_agents_gate_ollama_down_503(client):
    with patch(
        "api.routes.ops.eval_gate_routes.check_ollama_ready",
        new_callable=AsyncMock,
        side_effect=RuntimeError("Ollama недоступен"),
    ):
        r = await client.post("/api/ops/eval/agents-gate", json={})
    assert r.status_code == 503


@pytest.mark.asyncio
async def test_agents_gate_latest_empty(client, monkeypatch):
    monkeypatch.setattr(
        "api.routes.ops.eval_gate_routes.load_latest_gate",
        lambda: (None, None),
    )
    r = await client.get("/api/ops/eval/agents-gate/latest")
    assert r.status_code == 200
    assert r.json()["found"] is False
