import os

from core.agent_eval.gate import _apply_gate_cpu_profile
from core.agent_eval.gate_config import gate_label


def test_gate_cpu_profile_sets_fast_defaults(monkeypatch):
    monkeypatch.delenv("GATE_CPU_PROFILE", raising=False)
    monkeypatch.delenv("GATE_AGENT_MODEL", raising=False)
    monkeypatch.delenv("HERMES_OLLAMA_TIMEOUT_SEC", raising=False)
    # setdefault не перебивает уже заданный TOTAL — чистим оба ключа
    monkeypatch.delenv("HERMES_OLLAMA_TOTAL_TIMEOUT_SEC", raising=False)
    _apply_gate_cpu_profile()
    assert os.environ["GATE_AGENT_MODEL"] == "qwen2.5:3b"
    assert os.environ["HERMES_OLLAMA_TOTAL_TIMEOUT_SEC"] == "6"


def test_gate_label_pass_warn_fail():
    assert gate_label(85.0, 85) == "pass"
    assert gate_label(80.0, 85) == "warn"
    assert gate_label(79.0, 85) == "fail"
