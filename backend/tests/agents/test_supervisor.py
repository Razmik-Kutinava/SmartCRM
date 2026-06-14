"""Supervisor — выборочный fanout (Ф2 §2)."""
from agents.supervisor import select_fanout_plan


def test_hermes_subset_create_lead():
    plan = select_fanout_plan(
        "create_lead",
        {"company": "ACME"},
        hermes_agents=["analyst", "marketer"],
    )
    assert plan.parallel_agents == ("analyst", "marketer")
    assert plan.run_strategist is True
    assert plan.source == "hermes"


def test_default_full_analysis():
    plan = select_fanout_plan("run_analysis", {"company": "X"}, hermes_agents=None)
    assert set(plan.parallel_agents) == {
        "analyst", "economist", "marketer", "tech_specialist",
    }
    assert plan.run_strategist is True


def test_ask_economist_single_no_strategist():
    plan = select_fanout_plan("ask_economist", {"question": "выручка"}, None)
    assert plan.parallel_agents == ("economist",)
    assert plan.run_strategist is False
    assert plan.route == "voice_single"


def test_list_leads_analyst_only():
    plan = select_fanout_plan("list_leads", {}, None)
    assert plan.parallel_agents == ("analyst",)
    assert plan.run_strategist is False


def test_hermes_overrides_run_analysis():
    plan = select_fanout_plan(
        "run_analysis",
        {},
        hermes_agents=["analyst", "tech_specialist"],
    )
    assert plan.parallel_agents == ("analyst", "tech_specialist")
    assert plan.source == "hermes"
