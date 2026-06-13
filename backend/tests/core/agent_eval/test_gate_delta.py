"""Тесты gate_delta — было % → стало %."""
from core.agent_eval.gate_delta import compute_delta_vs_previous


def _report(rates: dict[str, float], overall: str = "fail") -> dict:
    return {
        "generated_at": "2026-01-01T00:00:00+00:00",
        "overall_gate": overall,
        "agents": {
            k: {"summary": {"pass_rate_pct": v, "gate": "fail"}}
            for k, v in rates.items()
        },
    }


def test_delta_no_previous():
    d = compute_delta_vs_previous(_report({"hermes": 80}), None)
    assert d["has_previous"] is False


def test_delta_was_became():
    prev = _report({"hermes": 70, "analyst": 60})
    curr = _report({"hermes": 85, "analyst": 55}, overall="warn")
    d = compute_delta_vs_previous(curr, prev, previous_artifact_name="old.json")
    assert d["has_previous"] is True
    assert d["previous_artifact_name"] == "old.json"
    assert d["agents"]["hermes"]["was_pct"] == 70
    assert d["agents"]["hermes"]["became_pct"] == 85
    assert d["agents"]["hermes"]["delta_pct"] == 15.0
    assert d["agents"]["analyst"]["delta_pct"] == -5.0
    assert d["overall_was"] == "fail"
    assert d["overall_became"] == "warn"
