#!/usr/bin/env python3
"""Live POST /api/email/sync — обновить письма без повторного connect."""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND.parent
DEFAULT_API = "http://127.0.0.1:8000"


def _load_env() -> None:
    try:
        from dotenv import load_dotenv

        load_dotenv(BACKEND / ".env")
        load_dotenv(REPO_ROOT / ".env", override=True)
        front_env = REPO_ROOT / "frontend" / ".env"
        if front_env.is_file():
            load_dotenv(front_env, override=False)
    except ImportError:
        pass


def _api_key() -> str:
    return (os.getenv("SMARTCRM_API_KEY") or os.getenv("PUBLIC_SMARTCRM_API_KEY") or "").strip()


def main() -> int:
    _load_env()
    base = (os.getenv("SMARTCRM_API_URL") or DEFAULT_API).rstrip("/")
    key = _api_key()
    if not key:
        print("FAIL: нет SMARTCRM_API_KEY", file=sys.stderr)
        return 1
    req = urllib.request.Request(
        f"{base}/api/email/sync",
        method="POST",
        headers={"X-API-Key": key, "Content-Type": "application/json"},
        data=b"{}",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            body = json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        print(f"FAIL HTTP {e.code}: {e.read().decode()}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"FAIL: {e}", file=sys.stderr)
        return 1
    print(json.dumps(body, ensure_ascii=False, indent=2))
    imported = body.get("imported", 0)
    print(f"OK: imported={imported} total_fetched={body.get('total', 0)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
