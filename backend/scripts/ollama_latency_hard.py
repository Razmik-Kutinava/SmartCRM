"""Один раз: сложный промпт к локальному Ollama, замер времени."""
from __future__ import annotations

import json
import time
import urllib.request


def bench(model: str, prompt: str, num_predict: int = 96, num_ctx: int = 2048) -> dict:
    url = "http://localhost:11434/api/generate"
    payload = json.dumps(
        {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {"num_predict": num_predict, "temperature": 0.1, "num_ctx": num_ctx},
            "keep_alive": "5m",
        }
    ).encode()
    t0 = time.perf_counter()
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as r:
        body = r.read()
    elapsed_ms = (time.perf_counter() - t0) * 1000
    d = json.loads(body)
    ev = d.get("eval_duration") or 0
    ec = d.get("eval_count") or 0
    tps = (ec / (ev / 1e9)) if ev else None
    return {
        "model": model,
        "elapsed_ms": round(elapsed_ms, 1),
        "eval_duration_s": round(ev / 1e9, 2) if ev else None,
        "eval_count": ec,
        "tokens_per_s": round(tps, 1) if tps else None,
        "response_chars": len(d.get("response") or ""),
    }


def main() -> None:
    prompt = (
        "Ты роутер CRM. По русской фразе верни ТОЛЬКО валидный JSON без пояснений:\n"
        '{"intent":"...","agents":[],"slots":{},"parallel":false,"reply":"..."}\n\n'
        "Фраза пользователя:\n"
        "Найди компанию ООО Ромашка в Москве, покажи горячих лидов за неделю "
        "и добавь задачу позвонить директору завтра утром, тон письма дружелюбный.\n"
    )
    # 96 токенов — как HERMES_OLLAMA_NUM_PREDICT; на CPU 256 может занимать много минут.
    for model in ("qwen2.5:0.5b", "qwen2.5:3b"):
        try:
            print(json.dumps(bench(model, prompt, num_predict=96), ensure_ascii=False), flush=True)
        except Exception as e:
            print(json.dumps({"model": model, "error": type(e).__name__, "msg": str(e)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
