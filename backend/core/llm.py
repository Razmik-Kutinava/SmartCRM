"""
LLM клиент: Groq (primary) → Ollama/Qwen (fallback)
Автоматически переключается при исчерпании токенов Groq или ошибке.
"""
import os
import time
import logging
import httpx
from groq import AsyncGroq, RateLimitError, APIStatusError

logger = logging.getLogger(__name__)

def _env(name: str, default: str = "") -> str:
    return os.getenv(name, default)


def _groq_key() -> str:
    return _env("GROQ_API_KEY", "")


def _groq_model() -> str:
    return _env("GROQ_MODEL", "llama-3.1-8b-instant")


def _ollama_host() -> str:
    return _env("OLLAMA_HOST", "http://localhost:11434")


def _ollama_model() -> str:
    return _env("OLLAMA_MODEL", "llama3.2:latest")


# Совместимость: модули, которые импортируют константы напрямую.
GROQ_API_KEY = _groq_key()
GROQ_MODEL = _groq_model()
OLLAMA_HOST = _ollama_host()
OLLAMA_MODEL = _ollama_model()

_groq_client: AsyncGroq | None = None
_groq_available = bool(_groq_key())
_groq_retry_after: float = 0.0  # timestamp когда снова пробовать Groq


def _get_groq_client() -> AsyncGroq | None:
    """Ленивая фабрика. Перечитывает ключ из env при первом вызове."""
    global _groq_client
    if _groq_client is None:
        key = _groq_key()
        if not key:
            return None
        _groq_client = AsyncGroq(api_key=key)
    return _groq_client


async def chat(
    messages: list[dict],
    model: str = "auto",
    temperature: float = 0.7,
    max_tokens: int = 2048,
    json_mode: bool = False,
) -> str:
    """
    Основной метод чата. model="auto" → Groq если доступен, иначе Ollama.
    Возвращает строку с ответом LLM.
    """
    global _groq_available, _groq_retry_after

    if model == "auto":
        # Восстанавливаем Groq после паузы (rate limit обычно снимается за 30–60 сек)
        if not _groq_available and time.monotonic() > _groq_retry_after:
            _groq_available = True
            logger.info("Groq: повторная попытка после паузы")
        if _groq_available and _get_groq_client() is not None:
            try:
                return await _groq_chat(messages, temperature, max_tokens, json_mode)
            except Exception as e:
                logger.warning(f"Groq недоступен ({type(e).__name__}: {e}), переключаемся на Ollama")
                _groq_available = False
                # Rate limit — пробуем снова через 60 сек, остальное — через 30 сек
                pause = 60.0 if isinstance(e, RateLimitError) else 30.0
                _groq_retry_after = time.monotonic() + pause
        return await _ollama_chat(messages, temperature, max_tokens, json_mode)

    elif model == "groq":
        return await _groq_chat(messages, temperature, max_tokens, json_mode)

    elif model == "ollama":
        return await _ollama_chat(messages, temperature, max_tokens, json_mode)

    raise ValueError(f"Неизвестная модель: {model}")


async def _groq_chat(
    messages: list[dict],
    temperature: float,
    max_tokens: int,
    json_mode: bool,
) -> str:
    client = _get_groq_client()
    if client is None:
        raise RuntimeError("GROQ_API_KEY не задан")
    kwargs = dict(
        model=_groq_model(),
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}

    response = await client.chat.completions.create(**kwargs)
    # message.content может быть None (tool_calls без текста) — защищаемся от TypeError в len()
    result = response.choices[0].message.content or ""
    # Трекинг токенов
    try:
        from core.stats import track_llm
        usage = response.usage
        if usage:
            track_llm("groq", prompt_tokens=usage.prompt_tokens,
                      completion_tokens=usage.completion_tokens)
    except Exception:
        pass
    logger.info(f"Groq ответил ({len(result)} символов)")
    return result


async def _ollama_chat(
    messages: list[dict],
    temperature: float,
    max_tokens: int,
    json_mode: bool,
) -> str:
    payload = {
        "model": _ollama_model(),
        "messages": messages,
        "stream": False,
        "options": {
            "temperature": temperature,
            "num_predict": max_tokens,
        },
    }
    if json_mode:
        payload["format"] = "json"

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{_ollama_host()}/api/chat",
            json=payload,
        )
        response.raise_for_status()
        data = response.json()
        result = (data.get("message") or {}).get("content") or ""
        try:
            from core.stats import track_llm
            # Ollama не возвращает точные токены — считаем символы / 4
            est = len(result) // 4
            track_llm("ollama", prompt_tokens=0, completion_tokens=est)
        except Exception:
            pass
        logger.info(f"Ollama ответил ({len(result)} символов)")
        return result


async def health_check() -> dict:
    """
    Проверка доступности LLM провайдеров.
    Не делает реальный chat-вызов на Groq, чтобы /health/llm нельзя было
    использовать для сжигания платных токенов через DoS.
    """
    status = {"groq": False, "ollama": False, "active": "none"}

    if _groq_key():
        # Groq не имеет дешёвой ping-ручки в SDK. Считаем доступным, если есть ключ
        # и мы недавно не получали ошибок (см. _groq_available).
        status["groq"] = bool(_groq_available)
        if status["groq"]:
            status["active"] = "groq"

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get(f"{_ollama_host()}/api/tags")
            if r.status_code == 200:
                status["ollama"] = True
                if status["active"] == "none":
                    status["active"] = "ollama"
    except Exception:
        pass

    return status
