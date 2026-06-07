"""Hermes — Groq и Ollama провайдеры."""
import httpx

from . import config


async def groq_chat(messages: list[dict]) -> str:
    """Groq API для быстрого парсинга интентов."""
    from groq import AsyncGroq

    client = AsyncGroq(api_key=config.GROQ_API_KEY)
    response = await client.chat.completions.create(
        model=config.GROQ_HERMES_MODEL,
        messages=messages,
        temperature=0.1,
        max_tokens=config.HERMES_MAX_TOKENS,
        response_format={"type": "json_object"},
    )
    try:
        from core.stats import track_llm

        usage = response.usage
        if usage:
            track_llm("groq", prompt_tokens=usage.prompt_tokens, completion_tokens=usage.completion_tokens)
    except Exception:
        pass
    return response.choices[0].message.content


async def ollama_preload(model: str, num_ctx: int, timeout_sec: float | None = None) -> None:
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": "ping"}],
        "stream": False,
        "format": "json",
        "keep_alive": config.HERMES_OLLAMA_KEEP_ALIVE,
        "options": {
            "temperature": 0.0,
            "num_ctx": num_ctx,
        },
    }
    if config.HERMES_ENABLE_GPU_OFFLOAD:
        payload["options"]["num_gpu"] = config.HERMES_OLLAMA_NUM_GPU
        payload["options"]["num_thread"] = config.HERMES_OLLAMA_NUM_THREAD
    timeout = timeout_sec if timeout_sec is not None else config.HERMES_OLLAMA_TIMEOUT_SEC
    async with httpx.AsyncClient(timeout=timeout) as client:
        await client.post(f"{config.OLLAMA_HOST}/api/chat", json=payload)


async def ollama_chat(
    messages: list[dict],
    model: str,
    num_ctx: int,
    timeout_sec: float | None = None,
) -> str:
    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
        "format": "json",
        "keep_alive": config.HERMES_OLLAMA_KEEP_ALIVE,
        "options": {
            "temperature": 0.1,
            "num_ctx": num_ctx,
            "num_predict": config.HERMES_OLLAMA_NUM_PREDICT,
        },
    }
    if config.HERMES_ENABLE_GPU_OFFLOAD:
        payload["options"]["num_gpu"] = config.HERMES_OLLAMA_NUM_GPU
        payload["options"]["num_thread"] = config.HERMES_OLLAMA_NUM_THREAD
    timeout = timeout_sec if timeout_sec is not None else config.HERMES_OLLAMA_TIMEOUT_SEC
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(f"{config.OLLAMA_HOST}/api/chat", json=payload)
        response.raise_for_status()
        return response.json()["message"]["content"]
