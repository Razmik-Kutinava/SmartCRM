"""API эффективности агентов по трейсам."""
from unittest.mock import patch

import pytest


@pytest.mark.asyncio
async def test_ops_agent_analytics_api(client):
    sample = [
        {
            "id": "t1",
            "ts": 1_700_000_000,
            "intent": "analyze_lead",
            "agents": ["analyst"],
            "feedback": "good",
            "duration_ms": 200,
        },
        {
            "id": "t2",
            "ts": 1_700_000_100,
            "intent": "analyze_lead",
            "agents": ["analyst"],
            "feedback": "bad",
            "duration_ms": 300,
        },
    ]
    with patch("api.routes.ops.analytics_routes.traces.get_all_traces", return_value=sample):
        r = await client.get("/api/ops/analytics/agents?period_days=0")
    assert r.status_code == 200
    body = r.json()
    assert body["totalTraces"] == 2
    analyst = next(a for a in body["agents"] if a["id"] == "analyst")
    assert analyst["invocations"] == 2
    assert analyst["good"] == 1
    assert analyst["bad"] == 1
    assert body["improveLinks"]["traces"] == "/ops/intents/traces"
