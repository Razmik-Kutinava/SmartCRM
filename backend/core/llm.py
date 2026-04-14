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

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:latest")

_groq_client = AsyncGroq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None
_groq_available = bool(GROQ_API_KEY)
_groq_retry_after: float = 0.0  # timestamp когда снова пробовать Groq


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
    global _groq_available

    if model == "auto":
        global _groq_available, _groq_retry_after
        # Восстанавливаем Groq после паузы (rate limit обычно снимается за 30–60 сек)
        if not _groq_available and time.monotonic() > _groq_retry_after:
            _groq_available = True
            logger.info("Groq: повторная попытка после паузы")
        if _groq_available and _groq_client:
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
    kwargs = dict(
        model=GROQ_MODEL,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}

    response = await _groq_client.chat.completions.create(**kwargs)
    result = response.choices[0].message.content
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
        "model": OLLAMA_MODEL,
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
            f"{OLLAMA_HOST}/api/chat",
            json=payload,
        )
        response.raise_for_status()
        data = response.json()
        result = data["message"]["content"]
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
    """Проверка доступности LLM провайдеров."""
    status = {"groq": False, "ollama": False, "active": "none"}

    if _groq_client:
        try:
            await _groq_chat(
                [{"role": "user", "content": "hi"}],
                temperature=0.1,
                max_tokens=5,
                json_mode=False,
            )
            status["groq"] = True
            status["active"] = "groq"
        except Exception:
            pass

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get(f"{OLLAMA_HOST}/api/tags")
            if r.status_code == 200:
                status["ollama"] = True
                if status["active"] == "none":
                    status["active"] = "ollama"
    except Exception:
        pass

    return status
