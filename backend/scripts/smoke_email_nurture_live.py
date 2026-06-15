#!/usr/bin/env python3
"""Live nurture: тестовый лид-клиент → 20 касаний → 1-е письмо с {{company}}."""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND.parent
TEST_COMPANY = "Nurture Live Клиент ООО"
TEST_CONTACT = "Иван Тестов"
PRODUCT = "SmartCRM Product Rollout"


def _load_env() -> None:
    from dotenv import load_dotenv

    load_dotenv(BACKEND / ".env")
    load_dotenv(REPO_ROOT / ".env", override=True)


def _api(base: str, key: str, method: str, path: str, body: dict | None = None) -> dict:
    headers = {"X-API-Key": key, "Content-Type": "application/json"}
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(f"{base}{path}", data=data, method=method, headers=headers)
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read().decode())


def main() -> int:
    _load_env()
    base = (os.getenv("SMARTCRM_API_URL") or "http://127.0.0.1:8000").rstrip("/")
    key = (os.getenv("SMARTCRM_API_KEY") or os.getenv("PUBLIC_SMARTCRM_API_KEY") or "").strip()
    client_email = (os.getenv("NURTURE_TEST_CLIENT_EMAIL") or os.getenv("EMAIL_ACCOUNT_2_USER") or "").strip()
    if not key or not client_email:
        print("FAIL: SMARTCRM_API_KEY или NURTURE_TEST_CLIENT_EMAIL", file=sys.stderr)
        return 1

    out: dict = {"client_email": client_email, "product": PRODUCT}
    accs = _api(base, key, "GET", "/api/email/accounts")
    me = next((a for a in accs if "me@" in (a.get("username") or "").lower()), accs[0])
    out["account"] = me["username"]

    # тестовый лид-клиент
    try:
        lead = _api(
            base,
            key,
            "POST",
            "/api/leads",
            {
                "company": TEST_COMPANY,
                "contact": TEST_CONTACT,
                "email": client_email,
                "stage": "Новый",
                "score": 75,
            },
        )
        lead_id = lead["id"]
        out["lead_id"] = lead_id
    except urllib.error.HTTPError as e:
        print(f"FAIL create lead: {e.read().decode()[:300]}", file=sys.stderr)
        return 1

    # пауза старых цепочек через API если есть
    chains = _api(base, key, "GET", f"/api/email/nurture/chains?lead_id={lead_id}")
    for ch in chains:
        if ch.get("status") == "active":
            _api(base, key, "POST", f"/api/email/nurture/{ch['id']}/pause")

    try:
        start = _api(
            base,
            key,
            "POST",
            "/api/email/nurture/start",
            {
                "lead_id": lead_id,
                "account_id": me["id"],
                "product_name": PRODUCT,
            },
        )
        out["chain_id"] = start["chain"]["id"]
        out["steps_total"] = start["chain"]["stepsTotal"]
    except urllib.error.HTTPError as e:
        out["start_error"] = e.read().decode()[:200]
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 1

    due = _api(base, key, "POST", "/api/email/nurture/process-due")
    out["process_due"] = due

    chains_after = _api(base, key, "GET", f"/api/email/nurture/chains?lead_id={lead_id}")
    if chains_after:
        out["steps_sent"] = chains_after[0].get("stepsSent")

    # персонализация в последнем nurture outbound
    sys.path.insert(0, str(BACKEND))
    import asyncio
    from sqlalchemy import select

    from db.models import EmailMessage
    from db.session import get_db_session

    async def _last_nurture() -> dict | None:
        async with get_db_session() as db:
            row = (
                await db.execute(
                    select(EmailMessage)
                    .where(
                        EmailMessage.lead_id == lead_id,
                        EmailMessage.category == "nurture",
                        EmailMessage.direction == "outbound",
                    )
                    .order_by(EmailMessage.id.desc())
                    .limit(1)
                )
            ).scalars().first()
            if not row:
                return None
            return {"subject": row.subject, "body": (row.body or "")[:200]}

    last = asyncio.run(_last_nurture())
    out["last_nurture"] = last
    ok = bool(due.get("emails_sent", 0) >= 1 and last and TEST_COMPANY in (last.get("subject") or ""))

    print(json.dumps(out, ensure_ascii=False, indent=2))
    if ok:
        print("OK: nurture touch 1 sent with company name")
        return 0
    print("FAIL: nurture email not sent or not personalized", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
