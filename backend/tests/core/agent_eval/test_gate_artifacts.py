import json

from core.agent_eval.gate_artifacts import latest_gate_path, load_latest_gate


def test_load_latest_gate_empty(tmp_path, monkeypatch):
    monkeypatch.setattr("core.agent_eval.gate_artifacts.ARTIFACTS_DIR", tmp_path)
    assert latest_gate_path() is None
    assert load_latest_gate() == (None, None)


def test_load_latest_gate_found(tmp_path, monkeypatch):
    monkeypatch.setattr("core.agent_eval.gate_artifacts.ARTIFACTS_DIR", tmp_path)
    p = tmp_path / "agents_gate_20260101_120000.json"
    p.write_text(json.dumps({"overall_gate": "fail", "agents": {}}), encoding="utf-8")
    path, data = load_latest_gate()
    assert path == p
    assert data["overall_gate"] == "fail"


def test_load_previous_gate(tmp_path, monkeypatch):
    from core.agent_eval.gate_artifacts import load_previous_gate

    monkeypatch.setattr("core.agent_eval.gate_artifacts.ARTIFACTS_DIR", tmp_path)
    old = tmp_path / "agents_gate_20260101_100000.json"
    new = tmp_path / "agents_gate_20260101_120000.json"
    old.write_text("{}", encoding="utf-8")
    new.write_text('{"overall_gate": "pass"}', encoding="utf-8")
    path, data = load_previous_gate()
    assert path == old
