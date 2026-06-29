"""Срочно выключить smoke FAQ-интенты (прайс) и показать активные правила."""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND.parent
sys.path.insert(0, str(BACKEND))


def _load_env() -> None:
    from dotenv import load_dotenv

    load_dotenv(BACKEND / ".env")
    load_dotenv(REPO_ROOT / ".env", override=True)


from sqlalchemy import select

from db.models.agent_email_intent import AgentEmailIntent
from db.session import get_db_session, init_db


def _is_smoke_intent(intent: AgentEmailIntent) -> bool:
    name = (intent.intent_name or "").lower()
    kw = (intent.trigger_keywords or "").lower()
    if "smoke" in name or "smoke" in kw:
        return True
    return "live" in name and "faq" in name


async def main() -> int:
    _load_env()
    await init_db()
    disabled: list[int] = []
    async with get_db_session() as db:
        rows = (await db.execute(select(AgentEmailIntent))).scalars().all()
        for intent in rows:
            if intent.is_active and _is_smoke_intent(intent):
                intent.is_active = False
                disabled.append(intent.id)
        if disabled:
            await db.commit()
    print("disabled_ids:", disabled or "none")
    async with get_db_session() as db:
        active = (
            await db.execute(select(AgentEmailIntent).where(AgentEmailIntent.is_active == True))  # noqa: E712
        ).scalars().all()
    print("active_count:", len(active))
    for a in active:
        print(f"  id={a.id} {a.intent_name!r}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
