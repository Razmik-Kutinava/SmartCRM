"""Зеркало frontend/src/lib/leads/leadsRouteManifest.js."""

LEADS_ROOT_REDIRECT = "/leads/list"

LEADS_TAB_ROUTES = [
    "/leads/funnel",
    "/leads/list",
    "/leads/calendar",
    "/leads/tasks",
    "/leads/focus",
    "/leads/analytics",
]

LEADS_STATIC_ROUTES = ["/leads", *LEADS_TAB_ROUTES]


def leads_card_path(lead_id: str | int) -> str:
    return f"/leads/{lead_id}"


def leads_campaign_path(campaign_id: str | int) -> str:
    return f"/leads/campaign/{campaign_id}"


def test_leads_tab_routes_complete():
    assert len(LEADS_TAB_ROUTES) == 6
    assert LEADS_ROOT_REDIRECT in LEADS_TAB_ROUTES
    for path in LEADS_TAB_ROUTES:
        assert path.startswith("/leads/")


def test_leads_dynamic_paths():
    assert leads_card_path(42) == "/leads/42"
    assert leads_campaign_path(7) == "/leads/campaign/7"
