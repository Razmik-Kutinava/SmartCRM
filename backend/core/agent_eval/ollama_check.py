"""Проверка Ollama перед live quality gate."""
from __future__ import annotations

import os
from typing import Any

import httpx

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
HERMES_MODEL = os.getenv("HERMES_MODEL", "hermes3:latest")


async def check_ollama_ready(model: str | None = None) -> dict[str, Any]:
    """Возвращает статус; raises RuntimeError если Ollama недоступен или модели нет."""
    want = model or HERMES_MODEL
    base = want.split(":")[0]
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(f"{OLLAMA_HOST}/api/tags")
            r.raise_for_status()
            tags = r.json().get("models") or []
    except Exception as e:
        raise RuntimeError(
            f"Ollama недоступен на {OLLAMA_HOST}: {e}. Запустите: ollama serve"
        ) from e

    names = [m.get("name", "") for m in tags]
    found = any(n == want or n.startswith(f"{base}:") for n in names)
    if not found:
        raise RuntimeError(
            f"Модель {want!r} не найдена в Ollama. Установите: ollama pull {want}"
        )
    return {"host": OLLAMA_HOST, "model": want, "available_models": names}


async def warmup_ollama(model: str | None = None) -> None:
    """Прогрев модели (первый запрос на CPU может быть очень долгим)."""
    want = model or HERMES_MODEL
    timeout = float(os.getenv("EVAL_OLLAMA_TIMEOUT", "300"))
    payload = {
        "model": want,
        "messages": [{"role": "user", "content": "ping"}],
        "stream": False,
    }
    async with httpx.AsyncClient(timeout=timeout) as client:
        r = await client.post(f"{OLLAMA_HOST}/api/chat", json=payload)
        r.raise_for_status()
