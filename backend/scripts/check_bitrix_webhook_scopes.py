"""Проверка scope входящего вебхука Битрикс24 (crm, user, task)."""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND.parent
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
        probe_webhook_scopes,
        scope_label,
        webhook_setup_hint,
    )
    from integrations.bitrix24 import webhook_base

    if not webhook_base():
        print("BITRIX24_WEBHOOK_URL не задан в .env")
        return 1

    report = await probe_webhook_scopes()
    print("Bitrix24 webhook scopes:")
    for scope in REQUIRED_WEBHOOK_SCOPES:
        row = report.get(scope, {})
        status = row.get("status", "?")
        detail = row.get("detail", "")
        print(f"  {scope_label(scope)}: {status}")
        if status != "ok" and detail:
            print(f"    {detail[:240]}")

    missing = missing_scopes(report)
    if missing:
        print()
        print(webhook_setup_hint(missing=missing))
        return 1

    print()
    print("OK: crm + user + task")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
