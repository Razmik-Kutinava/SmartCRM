"""Проверка scope входящего вебхука Битрикс24 (crm, user, task) + feature API."""
from __future__ import annotations

import asyncio
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND.parent
REPORT_PATH = BACKEND / "data" / "bitrix_webhook_scope_report.json"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))


def _load_env() -> None:
    try:
        from dotenv import load_dotenv

        load_dotenv(BACKEND / ".env")
        load_dotenv(REPO_ROOT / ".env", override=True)
    except ImportError:
        pass


async def main() -> int:
    _load_env()
    from core.bitrix_webhook_scopes import (
        REQUIRED_WEBHOOK_SCOPES,
        missing_scopes,
        probe_webhook_full,
        scope_label,
        webhook_setup_hint,
    )
    from integrations.bitrix24 import webhook_base

    if not webhook_base():
        print("BITRIX24_WEBHOOK_URL не задан в .env")
        return 1

    full = await probe_webhook_full()
    report = full["scopes"]
    features = full.get("features") or {}

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(
        json.dumps(
            {
                "checked_at": datetime.now(timezone.utc).isoformat(),
                **full,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print("Bitrix24 webhook scopes:")
    for scope in REQUIRED_WEBHOOK_SCOPES:
        row = report.get(scope, {})
        status = row.get("status", "?")
        print(f"  {scope_label(scope)}: {status}")
        if status != "ok" and row.get("detail"):
            print(f"    {row['detail'][:240]}")

    if features:
        print()
        print("Feature API (при scope crm):")
        for key, row in features.items():
            if key == "sample_lead":
                continue
            status = row.get("status", "?")
            mark = "OK" if status == "ok" else status.upper()
            print(f"  {key}: {mark}")

    missing = missing_scopes(report)
    if missing:
        print()
        print(webhook_setup_hint(missing=missing))
        print(f"Report: {REPORT_PATH}")
        return 1

    print()
    print("OK: crm + user + task")
    print(f"Report: {REPORT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
