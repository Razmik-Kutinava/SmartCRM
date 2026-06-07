"""
Hermes — центральный роутер интентов.
Принимает текст команды → возвращает структурированный JSON с интентом.
Primary: Groq API (быстро). Fallback: Ollama (локально).
"""
from . import config
from .config import *  # noqa: F403
from .json_parse import parse_json
from .parse import parse_intent
from .prompts import get_system_prompt
from .prompts_data import COMPACT_SYSTEM_PROMPT, SYSTEM_PROMPT
from .providers import groq_chat, ollama_chat, ollama_preload

# Backward-compat aliases (eval_runner, scripts)
_groq_chat = groq_chat
_ollama_chat = ollama_chat
_ollama_preload = ollama_preload
_parse_json = parse_json
_intent_cache = config._intent_cache
_preloaded_models = config._preloaded_models

__all__ = [
    "parse_intent",
    "get_system_prompt",
    "SYSTEM_PROMPT",
    "COMPACT_SYSTEM_PROMPT",
    "GROQ_API_KEY",
    "GROQ_HERMES_MODEL",
    "_groq_chat",
    "_parse_json",
    "_intent_cache",
    "_preloaded_models",
]
