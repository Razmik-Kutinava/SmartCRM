"""Hermes — системные промпты и выбор активного профиля."""
from core.hermes_prompt_profiles import build_profile
from core.hermes_prompt_store import get_active_system_prompt

from . import config
from .prompts_data import COMPACT_SYSTEM_PROMPT, SYSTEM_PROMPT


def get_system_prompt() -> str:
    """Активный системный промпт (встроенный или из backend/data/hermes_system_prompt.txt)."""
    profile_prompt = build_profile(config.HERMES_PROMPT_PROFILE)
    if profile_prompt:
        return profile_prompt
    base_prompt = COMPACT_SYSTEM_PROMPT if config.HERMES_PROMPT_MODE == "compact" else SYSTEM_PROMPT
    if config.HERMES_PROMPT_MODE == "compact":
        return base_prompt
    return get_active_system_prompt(base_prompt)
