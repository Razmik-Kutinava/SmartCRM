"""Smoke-тесты Dr. QA (без LLM и subprocess)."""
from core.qa.stats import min_sample_size, z_test_proportions
from core.qa.registry import HypothesisRegistry
from core.qa_agent import QAAgent, HypothesisRegistry as HRShim


def test_z_test_proportions_significant():
    r = z_test_proportions(0.8, 0.9, 100, 100)
    assert "p_value" in r
    assert r.get("significant") is True


def test_min_sample_size_positive():
    n = min_sample_size(0.8, mde=0.05)
    assert n >= 30


def test_qa_import_shim():
    assert HRShim is HypothesisRegistry
    agent = QAAgent()
    assert agent.registry is not None
    agent.reset()
    assert len(agent.history) == 1
