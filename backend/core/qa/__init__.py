"""
Dr. QA — Principal Experimentation Engineer.
"""
from .agent import QAAgent
from .experiments import get_current_kpis
from .registry import Hypothesis, HypothesisRegistry
from .stats import min_sample_size, z_test_proportions
from .tools import dispatch_tool, get_registry

__all__ = [
    "QAAgent",
    "HypothesisRegistry",
    "Hypothesis",
    "get_current_kpis",
    "dispatch_tool",
    "z_test_proportions",
    "min_sample_size",
]
