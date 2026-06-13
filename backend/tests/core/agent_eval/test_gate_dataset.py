"""failed_pairs_from_report и bulk импорт."""
from core.agent_eval.gate_dataset import failed_pairs_from_report


def test_failed_pairs_all_agents():
    report = {
        "agents": {
            "hermes": {"results": [{"id": "h1", "passed": False}, {"id": "h2", "passed": True}]},
            "analyst": {"results": [{"id": "a1", "passed": False}]},
        }
    }
    pairs = failed_pairs_from_report(report, "all")
    assert ("hermes", "h1") in pairs
    assert ("analyst", "a1") in pairs
    assert len(pairs) == 2


def test_failed_pairs_single_tab():
    report = {
        "agents": {
            "hermes": {"results": [{"id": "h1", "passed": False}]},
            "analyst": {"results": [{"id": "a1", "passed": False}]},
        }
    }
    pairs = failed_pairs_from_report(report, "hermes")
    assert pairs == [("hermes", "h1")]
