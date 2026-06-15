#!/usr/bin/env python3
"""Live SMTP send smoke — POST /api/email/send (self-test)."""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND.parent
DEFAULT_API = "http://127.0.0.1:8000"


def _load_env() -> None:
    try:
        from dotenv import load_dotenv

        load_dotenv(BACKEND / ".env")
        load_dotenv(REPO_ROOT / ".env", override=True)
    except ImportError:
        pass


def main() -> int:
    _load_env()
    base = (os.getenv("SMARTCRM_API_URL") or DEFAULT_API).rstrip("/")
    key = (os.getenv("SMARTCRM_API_KEY") or os.getenv("PUBLIC_SMARTCRM_API_KEY") or "").strip()
    if not key:
        print("FAIL: нет SMARTCRM_API_KEY", file=sys.stderr)
        return 1

    # prefer ib@ (connect OK in smoke)
    to_addr = (os.getenv("EMAIL_SMOKE_SEND_TO") or os.getenv("EMAIL_ACCOUNT_2_USER") or "").strip()
    if not to_addr:
        print("FAIL: нет EMAIL_ACCOUNT_2_USER / EMAIL_SMOKE_SEND_TO", file=sys.stderr)
        return 1

    req_accounts = urllib.request.Request(
        f"{base}/api/email/accounts",
        headers={"X-API-Key": key},
    )
    with urllib.request.urlopen(req_accounts, timeout=30) as resp:
        accounts = json.loads(resp.read().decode())
    if not accounts:
        print("FAIL: нет аккаунтов в БД", file=sys.stderr)
        return 1

    account = next((a for a in accounts if to_addr.lower() in (a.get("username") or "").lower()), accounts[0])
    account_id = account["id"]
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    body = {
        "account_id": account_id,
        "to": [to_addr],
        "subject": f"SmartCRM F3 live SMTP smoke {ts}",
        "body": f"Live SMTP smoke OK.\nTimestamp: {ts}\nAccount: {account.get('username')}",
    }
    req = urllib.request.Request(
        f"{base}/api/email/send",
        method="POST",
        headers={"X-API-Key": key, "Content-Type": "application/json"},
        data=json.dumps(body).encode(),
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            out = json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        print(f"FAIL HTTP {e.code}: {e.read().decode()}", file=sys.stderr)
        return 1
    print(json.dumps(out, ensure_ascii=False, indent=2))
    print(f"OK: SMTP send to {to_addr} via account_id={account_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
