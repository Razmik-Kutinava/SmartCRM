"""API POST /api/ops/hermes/prompt/ab-traces."""
from unittest.mock import AsyncMock, patch

import pytest

_MIN = "y" * 80


@pytest.mark.asyncio
async def test_ab_traces_api_ok(client):
    fake = {
        "ok": True,
        "cases_count": 2,
        "cases_with_expected": 1,
        "delta": {"accuracy_pp": 50, "fixes": 1, "regressions": 0},
        "baseline": {"accuracy_pct": 0},
        "variant": {"accuracy_pct": 50},
        "per_case": [],
    }
    with patch(
        "core.prompt_ab_traces.run_prompt_ab_on_traces",
        new_callable=AsyncMock,
        return_value=fake,
    ):
        r = await client.post(
            "/api/ops/hermes/prompt/ab-traces",
            json={"variant_prompt": _MIN, "max_bad_traces": 5, "models": ["hermes3"]},
        )
    assert r.status_code == 200
    assert r.json()["cases_count"] == 2


@pytest.mark.asyncio
async def test_ab_traces_api_no_traces(client):
    with patch(
        "core.prompt_ab_traces.run_prompt_ab_on_traces",
        new_callable=AsyncMock,
        return_value={"ok": False, "error": "no_bad_traces", "message": "нет"},
    ):
        r = await client.post(
            "/api/ops/hermes/prompt/ab-traces",
            json={"variant_prompt": _MIN},
        )
    assert r.status_code == 400
