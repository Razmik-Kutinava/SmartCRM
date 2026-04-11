"""
Прогон eval-кейсов через Groq / Ollama — без привязки к FastAPI (переиспользование из ops и scenarios).
"""
from __future__ import annotations

import asyncio
import logging
import os
import time
from typing import Any, Optional

from core.hermes import get_system_prompt, _groq_chat, _parse_json, GROQ_API_KEY, GROQ_HERMES_MODEL

logger = logging.getLogger(__name__)

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
HERMES_MODEL = os.getenv("HERMES_MODEL", "hermes3:latest")
EVAL_OLLAMA_TIMEOUT = float(os.getenv("EVAL_OLLAMA_TIMEOUT", "60"))


async def _ollama_eval(messages: list[dict], model: str, timeout: float) -> str:
    import httpx

    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
        "format": "json",
        "options": {"temperature": 0.1},
    }
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(f"{OLLAMA_HOST}/api/chat", json=payload)
        response.raise_for_status()
        return response.json()["message"]["content"]


async def eval_one_case(text: str, expected: Optional[str], model_name: str) -> dict[str, Any]:
    """Один кейс через одну модель."""
    messages = [
        {"role": "system", "content": get_system_prompt()},
        {"role": "user", "content": text},
    ]
    t0 = time.monotonic()
    try:
        if model_name == "groq":
            if not GROQ_API_KEY:
                return {"error": "GROQ_API_KEY не задан", "duration_ms": 0, "correct": False}
            raw = await _groq_chat(messages)
            parsed = _parse_json(raw)
            actual_model = GROQ_HERMES_MODEL
        elif model_name in ("hermes3", "ollama"):
            ollama_model = HERMES_MODEL if model_name == "hermes3" else os.getenv("OLLAMA_MODEL", "qwen2.5:3b")
            raw = await _ollama_eval(messages, ollama_model, timeout=EVAL_OLLAMA_TIMEOUT)
            parsed = _parse_json(raw)
            actual_model = ollama_model
        else:
            return {"error": f"Неизвестная модель: {model_name}", "duration_ms": 0, "correct": False}

        duration_ms = round((time.monotonic() - t0) * 1000)
        got_intent = parsed.get("intent") if parsed else None
        correct = (got_intent == expected) if expected else None
        return {
            "intent": got_intent,
            "slots": parsed.get("slots", {}) if parsed else {},
            "reply": parsed.get("reply", "") if parsed else "",
            "duration_ms": duration_ms,
            "correct": correct,
            "model": actual_model,
        }

    except Exception as e:
        duration_ms = round((time.monotonic() - t0) * 1000)
        logger.warning("Eval [%s] '%s' → %s: %s", model_name, text[:30], type(e).__name__, e)
        return {
            "error": f"{type(e).__name__}: {str(e)[:150]}",
            "duration_ms": duration_ms,
            "correct": False,
        }


async def run_eval_pipeline(cases: list[dict[str, Any]], models: list[str]) -> dict[str, Any]:
    """
    cases: элементы с ключами text, expected, опционально scenario_id, scenario_title.
    models: подмножество groq, hermes3, ollama.
    """
    groq_models = [m for m in models if m == "groq"]
    local_models = [m for m in models if m != "groq"]

    all_results: dict[str, dict] = {c["text"]: {} for c in cases}

    if groq_models:
        PAUSE = 2.5
        for idx, case in enumerate(cases):
            resp = await eval_one_case(case["text"], case.get("expected"), "groq")
            all_results[case["text"]]["groq"] = resp
            if idx < len(cases) - 1:
                await asyncio.sleep(PAUSE)

    for model_name in local_models:
        for case in cases:
            result = await eval_one_case(case["text"], case.get("expected"), model_name)
            all_results[case["text"]][model_name] = result

    results = [
        {
            "text": c["text"],
            "expected": c.get("expected"),
            "scenario_id": c.get("scenario_id"),
            "scenario_title": c.get("scenario_title"),
            "models": all_results[c["text"]],
        }
        for c in cases
    ]

    summary: dict[str, Any] = {}
    for model_name in models:
        model_results = [r["models"].get(model_name, {}) for r in results]
        total = sum(1 for r, c in zip(model_results, cases) if "error" not in r and c.get("expected"))
        correct = sum(1 for r in model_results if r.get("correct") is True)
        times = [r["duration_ms"] for r in model_results if r.get("duration_ms")]
        avg_ms = round(sum(times) / len(times)) if times else 0
        summary[model_name] = {
            "correct": correct,
            "total": total,
            "accuracy_pct": round(correct / total * 100) if total else 0,
            "avg_ms": avg_ms,
        }

    return {
        "cases_count": len(cases),
        "summary": summary,
        "results": results,
    }
