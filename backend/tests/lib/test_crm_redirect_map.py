"""Зеркало frontend/src/lib/leads/crmRedirectMap.js."""

CRM_REDIRECT_STATUS = 308

CRM_STATIC_REDIRECTS = {
    "/crm": "/leads/list",
    "/crm/list": "/leads/list",
    "/crm/funnel": "/leads/funnel",
    "/crm/calendar": "/leads/calendar",
    "/crm/tasks": "/leads/tasks",
    "/crm/focus": "/leads/focus",
    "/crm/analytics": "/leads/analytics",
}


def crm_lead_id_redirect(lead_id: str | int) -> str:
    return f"/leads/{lead_id}"


def crm_campaign_redirect(campaign_id: str | int) -> str:
    return f"/leads/campaign/{campaign_id}"


def test_crm_static_redirects_308_targets():
    assert CRM_REDIRECT_STATUS == 308
    assert len(CRM_STATIC_REDIRECTS) == 7
    for src, dst in CRM_STATIC_REDIRECTS.items():
        assert src.startswith("/crm")
        assert dst.startswith("/leads")


def test_crm_lead_id_redirect():
    assert crm_lead_id_redirect(42) == "/leads/42"
    assert crm_lead_id_redirect("abc") == "/leads/abc"


def test_crm_campaign_redirect():
    assert crm_campaign_redirect(7) == "/leads/campaign/7"
