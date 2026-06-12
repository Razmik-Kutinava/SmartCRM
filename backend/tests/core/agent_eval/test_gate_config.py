from core.agent_eval.gate_config import gate_label


def test_gate_label_pass_warn_fail():
    assert gate_label(85.0, 85) == "pass"
    assert gate_label(80.0, 85) == "warn"
    assert gate_label(69.0, 75) == "fail"
