"""Проверка Groq: живой ключ + остаток лимитов (rate-limit заголовки).

Запуск: python scripts/check_groq.py
Ключ не печатается — только длина/префикс.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import httpx
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env", override=True)
load_dotenv(ROOT / "backend" / ".env", override=False)

KEY = (os.getenv("GROQ_API_KEY") or "").strip()
MODEL = (os.getenv("GROQ_MODEL") or "llama-3.1-8b-instant").strip()

_LIMIT_HEADERS = (
    "x-ratelimit-limit-requests",
    "x-ratelimit-remaining-requests",
    "x-ratelimit-reset-requests",
    "x-ratelimit-limit-tokens",
    "x-ratelimit-remaining-tokens",
    "x-ratelimit-reset-tokens",
)


def main() -> int:
    print(f"key_set={bool(KEY)} len={len(KEY)} prefix={KEY[:4] + '***' if KEY else '—'}")
    print(f"model={MODEL}")
    if not KEY:
        print("FAIL: GROQ_API_KEY не задан в .env")
        return 1

    headers = {"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"}
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": "Ответь одним словом: ок"}],
        "max_tokens": 8,
        "temperature": 0,
    }
    with httpx.Client(timeout=30.0) as client:
        r = client.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=payload,
        )
        print(f"http={r.status_code}")
        if r.status_code != 200:
            print("FAIL:", r.text[:300])
            return 1

        data = r.json()
        text = (data["choices"][0]["message"]["content"] or "").strip()
        usage = data.get("usage") or {}
        print(f"reply={text[:60]!r}")
        print(
            "usage: prompt={} completion={} total={}".format(
                usage.get("prompt_tokens"),
                usage.get("completion_tokens"),
                usage.get("total_tokens"),
            )
        )
        print("--- лимиты (из заголовков ответа) ---")
        limits = {h: r.headers.get(h) for h in _LIMIT_HEADERS if r.headers.get(h)}
        for k, v in limits.items():
            print(f"{k}: {v}")
        if not limits:
            print("заголовки лимитов не пришли")

        out = ROOT / "backend" / "data" / "artifacts" / "llm" / "groq_check.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(
            json.dumps(
                {"model": MODEL, "http": r.status_code, "usage": usage, "limits": limits},
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        print(f"артефакт: {out}")
    print("OK: Groq отвечает")
    return 0


if __name__ == "__main__":
    sys.exit(main())
