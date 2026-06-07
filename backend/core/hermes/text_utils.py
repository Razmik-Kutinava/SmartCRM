"""Hermes — нормализация текста, сжатие контекста, выбор провайдера."""
import re

from . import config


def normalize_text_for_cache(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip().lower())


def compress_context(text: str) -> str:
    if not config.HERMES_ENABLE_CONTEXT_COMPRESS:
        return text
    t = (text or "").strip()
    t = re.sub(r"\s+", " ", t)
    if len(t) <= config.HERMES_COMPRESS_MAX_CHARS:
        return t
    head = t[: int(config.HERMES_COMPRESS_MAX_CHARS * 0.85)]
    tail = t[-int(config.HERMES_COMPRESS_MAX_CHARS * 0.15) :]
    return f"{head} ... {tail}"


def sanitize_user_text(text: str) -> str:
    if not config.HERMES_ENABLE_CONTEXT_HYGIENE:
        return text
    t = (text or "").strip()
    t = re.sub(r"https?://\S+", " ", t)
    t = re.sub(r"[\r\n\t]+", " ", t)
    t = re.sub(r"[!?.]{3,}", ".", t)
    t = re.sub(r"\s{2,}", " ", t)
    return t.strip()


def choose_provider(text: str) -> str:
    if config.HERMES_ROUTING_POLICY != "local_first":
        return "groq_first"
    t = normalize_text_for_cache(text)
    is_short = len(t) <= 120
    low_risk = any(k in t for k in ("покажи", "список", "какие", "сколько", "найди"))
    if is_short and low_risk:
        return "ollama_first"
    return "groq_first"


def choose_num_ctx(text: str) -> int:
    if not config.HERMES_ENABLE_CONTEXT_PROFILE:
        return config.HERMES_OLLAMA_CTX_MEDIUM
    t = normalize_text_for_cache(text)
    if len(t) <= 120:
        chosen = config.HERMES_OLLAMA_CTX_SHORT
    elif len(t) <= 600:
        chosen = config.HERMES_OLLAMA_CTX_MEDIUM
    else:
        chosen = config.HERMES_OLLAMA_CTX_LONG
    if config.HERMES_ENABLE_GPU_OFFLOAD:
        return chosen
    if len(t) <= 80:
        return min(chosen, 1024)
    return min(chosen, 2048)


def unique_models(models: list[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for model in models:
        m = (model or "").strip()
        if not m or m in seen:
            continue
        out.append(m)
        seen.add(m)
    return out
