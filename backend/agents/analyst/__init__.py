"""Агент-аналитик — CRM-анализ лидов и скоринг."""
from .analyze import analyze as _analyze
from .prompts_data import ANALYST_SYSTEM_PROMPT
from .runner import run

__all__ = ["run", "ANALYST_SYSTEM_PROMPT", "_analyze"]
