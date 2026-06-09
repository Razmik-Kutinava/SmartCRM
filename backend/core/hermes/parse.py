"""Hermes — оркестрация parse_intent (Groq → Ollama → rescue)."""
import logging
import time

from core.agent_memory import add_observation, lookup_recent_similar

from . import config
from .cache import cache_get, cache_set, fastpath_route
from .json_parse import parse_json
from .prompts import get_system_prompt
from .providers import groq_chat, ollama_chat, ollama_preload
from .rescue import post_verify, rescue_route
from .slot_normalize import normalize_parsed_intent
from .text_utils import choose_num_ctx, choose_provider, compress_context, sanitize_user_text, unique_models

logger = logging.getLogger(__name__)


async def parse_intent(text: str) -> dict:
    """
    Парсит текст команды → возвращает dict с интентом.
    Primary: Groq (быстро). Fallback: Ollama (локально).
    """
    normalized_text = sanitize_user_text(text)
    cached = cache_get(normalized_text)
    if cached:
        cached["_model"] = f"{cached.get('_model', 'cache')}:cache"
        return cached

    fastpath = fastpath_route(normalized_text)
    if fastpath:
        fastpath = normalize_parsed_intent(normalized_text, fastpath)
        cache_set(normalized_text, fastpath)
        if config.HERMES_ENABLE_MEMORY:
            try:
                add_observation("hermes", normalized_text, fastpath.get("intent", ""), fastpath)
            except Exception:
                pass
        return fastpath

    if config.HERMES_ENABLE_MEMORY:
        mem_hit = lookup_recent_similar("hermes", normalized_text)
        if mem_hit and isinstance(mem_hit, dict) and mem_hit.get("intent"):
            mem_hit = dict(mem_hit)
            mem_hit["_model"] = f"{mem_hit.get('_model', 'memory')}:memory"
            cache_set(normalized_text, mem_hit)
            return mem_hit

    provider_order = choose_provider(normalized_text)
    text_for_model = compress_context(normalized_text)

    messages = [
        {"role": "system", "content": get_system_prompt()},
        {"role": "user", "content": text_for_model},
    ]

    async def _try_groq() -> dict | None:
        if not config.GROQ_API_KEY:
            return None
        try:
            result = await groq_chat(messages)
            logger.info(f"Hermes/Groq сырой ответ: {result[:200]}")
            parsed = parse_json(result)
            if parsed:
                parsed = post_verify(normalized_text, parsed)
                logger.info(f"Hermes/Groq разобрал: intent={parsed.get('intent')}")
                parsed["_model"] = config.GROQ_HERMES_MODEL
                cache_set(normalized_text, parsed)
                if config.HERMES_ENABLE_MEMORY:
                    try:
                        add_observation("hermes", normalized_text, parsed.get("intent", ""), parsed)
                    except Exception:
                        pass
                return parsed
        except Exception as e:
            logger.warning(f"Hermes/Groq ошибка: {e}, переключаемся на Ollama")
        return None

    async def _try_ollama() -> dict | None:
        ctx_for_ollama = choose_num_ctx(normalized_text)
        model_chain = [config.HERMES_MODEL, config.HERMES_FALLBACK]
        if config.HERMES_ENABLE_QUANT_MODEL and config.HERMES_MODEL_QUANT:
            model_chain = [config.HERMES_MODEL_QUANT, *model_chain]
        model_chain = unique_models(model_chain)
        deadline = time.monotonic() + max(1.0, config.HERMES_OLLAMA_TOTAL_TIMEOUT_SEC)
        for model in model_chain:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                logger.warning("Hermes/Ollama: исчерпан общий таймаут, прерываем попытки")
                break
            request_timeout = min(config.HERMES_OLLAMA_TIMEOUT_SEC, max(1.0, remaining))
            try:
                if config.HERMES_ENABLE_OLLAMA_PRELOAD and model not in config._preloaded_models:
                    await ollama_preload(model, ctx_for_ollama, timeout_sec=min(5.0, request_timeout))
                    config._preloaded_models.add(model)
                result = await ollama_chat(messages, model, ctx_for_ollama, timeout_sec=request_timeout)
                logger.info(f"Hermes/Ollama ({model}) сырой ответ: {result[:200]}")
                parsed = parse_json(result)
                if parsed:
                    parsed = post_verify(normalized_text, parsed)
                    logger.info(f"Hermes/Ollama ({model}) разобрал: intent={parsed.get('intent')}")
                    parsed["_model"] = model
                    cache_set(normalized_text, parsed)
                    if config.HERMES_ENABLE_MEMORY:
                        try:
                            add_observation("hermes", normalized_text, parsed.get("intent", ""), parsed)
                        except Exception:
                            pass
                    return parsed
                logger.warning(f"Hermes/Ollama ({model}) не смог распарсить JSON из: {result[:100]}")
            except Exception as e:
                logger.warning(f"Hermes/Ollama ({model}) ошибка [{type(e).__name__}]: {e}")
                continue
        return None

    if provider_order == "ollama_first":
        parsed = await _try_ollama()
        if parsed:
            return parsed
        parsed = await _try_groq()
        if parsed:
            return parsed
    else:
        parsed = await _try_groq()
        if parsed:
            return parsed
        parsed = await _try_ollama()
        if parsed:
            return parsed

    rescue = rescue_route(normalized_text)
    if rescue:
        rescue = normalize_parsed_intent(normalized_text, rescue)
        cache_set(normalized_text, rescue)
        if config.HERMES_ENABLE_MEMORY:
            try:
                add_observation("hermes", normalized_text, rescue.get("intent", ""), rescue)
            except Exception:
                pass
        return rescue

    logger.error("Hermes: оба варианта недоступны, возвращаем noop")
    out = {
        "intent": "noop",
        "agents": [],
        "slots": {},
        "parallel": False,
        "reply": "Не удалось распознать команду. Попробуйте ещё раз.",
        "_model": "none",
    }
    if config.HERMES_ENABLE_MEMORY:
        try:
            add_observation("hermes", normalized_text, "noop", out)
        except Exception:
            pass
    return out
