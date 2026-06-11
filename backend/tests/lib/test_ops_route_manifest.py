"""Зеркало навигации Ops UI (frontend/src/routes/ops/+layout.svelte)."""

OPS_MAIN_NAV = [
    "/ops",
    "/ops/intents",
    "/ops/voice",
    "/ops/agents",
    "/ops/email-agents",
    "/ops/search",
    "/ops/queue",
    "/ops/stats",
    "/ops/insights",
    "/ops/api-limits",
    "/ops/logs",
    "/ops/crm",
]

OPS_INTENTS_NAV = [
    "/ops/intents/traces",
    "/ops/intents/improve",
    "/ops/intents/import",
    "/ops/intents/eval",
    "/ops/intents/scenarios",
    "/ops/intents/history",
]

OPS_API_READ_SMOKE = [
    "/api/ops/overview",
    "/api/ops/queue",
    "/api/ops/stats",
    "/api/ops/insights",
    "/api/ops/traces?limit=5",
    "/api/ops/logs?limit=5",
    "/api/ops/crm-settings",
    "/api/ops/agents",
    "/api/ops/agents/analyst/prompt",
    "/api/ops/voice/whisper",
    "/api/ops/hermes/prompt",
    "/api/ops/improvement",
    "/api/ops/history",
    "/api/ops/scenarios?limit=10",
    "/api/search/config",
    "/api/search/providers",
    "/api/usage/stats",
]


def test_ops_main_nav_count():
    assert len(OPS_MAIN_NAV) == 12


def test_ops_intents_subnav():
    assert "/ops/intents/improve" in OPS_INTENTS_NAV


def test_ops_api_smoke_paths():
    assert all(p.startswith("/api/") for p in OPS_API_READ_SMOKE)
