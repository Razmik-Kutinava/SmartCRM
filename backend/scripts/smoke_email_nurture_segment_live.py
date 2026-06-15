#!/usr/bin/env python3
"""Live nurture segment: узкий сегмент → batch start-segment (без mass process-due)."""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND.parent
PRODUCT = "SmartCRM Product Rollout"
# Узкий фильтр — только тестовые лиды из smoke nurture
SEGMENT = {"stage": "Новый", "min_score": 70, "search": "Nurture Live"}


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
    if not key:
        print("FAIL: SMARTCRM_API_KEY", file=sys.stderr)
        return 1

    out: dict = {"segment": SEGMENT, "product": PRODUCT}
    accs = _api(base, key, "GET", "/api/email/accounts")
    me = next((a for a in accs if "me@" in (a.get("username") or "").lower()), accs[0])
    out["account"] = me["username"]

    preview = _api(
        base,
        key,
        "POST",
        "/api/email/campaigns/segment-preview",
        {"segment": SEGMENT},
    )
    out["segment_preview"] = preview
    lead_count = int(preview.get("count") or preview.get("leadCount") or 0)
    if lead_count < 1:
        print(json.dumps(out, ensure_ascii=False, indent=2))
        print("FAIL: сегмент пуст — сначала smoke_email_nurture_live.py", file=sys.stderr)
        return 1

    # пауза активных цепочек у лидов сегмента (чтобы start-segment не skipped)
    chains_before = _api(base, key, "GET", "/api/email/nurture/chains")
    paused = 0
    for ch in chains_before:
        if ch.get("status") == "active":
            name = (ch.get("name") or "").lower()
            if "nurture live" in name:
                _api(base, key, "POST", f"/api/email/nurture/{ch['id']}/pause")
                paused += 1
    out["paused_chains"] = paused

    try:
        batch = _api(
            base,
            key,
            "POST",
            "/api/email/nurture/start-segment",
            {
                "account_id": me["id"],
                "segment": SEGMENT,
                "product_name": PRODUCT,
                "limit": 5,
            },
        )
    except urllib.error.HTTPError as e:
        out["start_segment_error"] = e.read().decode()[:300]
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 1

    out["start_segment"] = {
        "started": batch.get("started"),
        "skipped": batch.get("skipped"),
        "chain_ids": [c.get("id") for c in (batch.get("chains") or [])],
    }

    chains_after = _api(base, key, "GET", "/api/email/nurture/chains")
    active_nurture = [
        c for c in chains_after
        if c.get("status") == "active" and "nurture live" in (c.get("name") or "").lower()
    ]
    out["active_nurture_chains"] = len(active_nurture)

    started = int(batch.get("started") or 0)
    ok = started >= 1 and out["active_nurture_chains"] >= 1

    print(json.dumps(out, ensure_ascii=False, indent=2))
    if ok:
        print(f"OK: segment batch started={started}, active_chains={out['active_nurture_chains']}")
        return 0
    print("FAIL: start-segment не запустил цепочки", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
