"""Backward-compat: from core.qa_agent import … → core.qa package."""
from core.qa import (  # noqa: F401
    Hypothesis,
    HypothesisRegistry,
    QAAgent,
    dispatch_tool,
    get_current_kpis,
    min_sample_size,
    z_test_proportions,
)

__all__ = [
    "QAAgent",
    "HypothesisRegistry",
    "Hypothesis",
    "get_current_kpis",
    "dispatch_tool",
    "z_test_proportions",
    "min_sample_size",
]
