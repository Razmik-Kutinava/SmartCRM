#!/usr/bin/env python3
"""Live LLM nurture: лид из CRM → маркетолог → 3 письма MaxPatrol VM → ib@."""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND.parent
PRODUCT = "Positive Technologies MaxPatrol VM"


def _load_env() -> None:
    from dotenv import load_dotenv

    load_dotenv(BACKEND / ".env")
    load_dotenv(REPO_ROOT / ".env", override=True)


def _api(base: str, key: str, method: str, path: str, body: dict | None = None) -> dict:
    headers = {"X-API-Key": key, "Content-Type": "application/json"}
    data = json.dumps(body, ensure_ascii=False).encode("utf-8") if body is not None else None
    req = urllib.request.Request(f"{base}{path}", data=data, method=method, headers=headers)
    with urllib.request.urlopen(req, timeout=300) as resp:
        return json.loads(resp.read().decode())


def main() -> int:
    _load_env()
    base = (os.getenv("SMARTCRM_API_URL") or "http://127.0.0.1:8000").rstrip("/")
    key = (os.getenv("SMARTCRM_API_KEY") or os.getenv("PUBLIC_SMARTCRM_API_KEY") or "").strip()
    client_email = (os.getenv("NURTURE_TEST_CLIENT_EMAIL") or os.getenv("EMAIL_ACCOUNT_2_USER") or "").strip()
    if not key or not client_email:
        print("FAIL: SMARTCRM_API_KEY или NURTURE_TEST_CLIENT_EMAIL", file=sys.stderr)
        return 1

    accs = _api(base, key, "GET", "/api/email/accounts")
    me = next((a for a in accs if "me@" in (a.get("username") or "").lower()), accs[0])

    body = {
        "account_id": me["id"],
        "product_name": PRODUCT,
        "email_count": 3,
        "sender_name": "Иван Б.",
        "sender_email": "ib@agneko.com",
        "client_email": client_email,
        "send_now": True,
    }

    try:
        result = _api(base, key, "POST", "/api/email/nurture/start-llm", body)
    except urllib.error.HTTPError as e:
        print(f"FAIL start-llm: {e.read().decode()[:500]}", file=sys.stderr)
        return 1

    due = result.get("process_due") or {}
    emails_sent = int(due.get("emails_sent") or 0)
    lead = result.get("lead") or {}
    chain = result.get("chain") or {}
    marketer = result.get("marketer") or {}

    out = {
        "lead_id": lead.get("id"),
        "company": lead.get("company"),
        "industry": lead.get("industry"),
        "client_email": client_email,
        "chain_id": chain.get("id"),
        "steps_total": chain.get("stepsTotal"),
        "steps_sent": chain.get("stepsSent"),
        "emails_sent": emails_sent,
        "buyer_profile": marketer.get("buyer_profile"),
        "attack_surface": marketer.get("attack_surface"),
        "product_fit": marketer.get("product_fit"),
        "llm_emails": result.get("llm_emails"),
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))

    ok = emails_sent >= 3 and chain.get("stepsSent", 0) >= 3
    if ok:
        print("OK: LLM nurture 3 emails sent")
        return 0
    if emails_sent >= 1:
        print("WARN: partial send", file=sys.stderr)
        return 0
    print("FAIL: no emails sent", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
