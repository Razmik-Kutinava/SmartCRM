"""gate_insights — подсказки для /ops/insights."""
from unittest.mock import patch

from core.agent_eval.gate_insights import gate_insights_block


def test_gate_insights_no_artifact_hint():
    with patch("core.agent_eval.gate_insights.load_latest_gate", return_value=(None, None)):
        block = gate_insights_block()
    assert block["found"] is False
    assert len(block["hints"]) == 1
    assert "eval" in block["hints"][0]["body"].lower()
