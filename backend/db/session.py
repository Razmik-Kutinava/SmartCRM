"""
Async SQLAlchemy сессия.
DATABASE_URL берётся из .env, например:
  postgresql+asyncpg://smartcrm:smartcrm@127.0.0.1:5432/smartcrm
"""
from __future__ import annotations

import logging
import os
import re

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

logger = logging.getLogger(__name__)

_RAW_DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://smartcrm:smartcrm@127.0.0.1:5432/smartcrm",
)


def normalize_database_url(url: str) -> str:
    """
    На Windows asyncpg часто получает RST на рукопожатии, если хост `localhost`
    резолвится в ::1, а Postgres слушает только IPv4.
    Отключается: DATABASE_FORCE_IPV4=0
    """
    if (os.getenv("DATABASE_FORCE_IPV4", "1") or "").strip().lower() in ("0", "false", "no", "off"):
        return url
    return re.sub(r"@localhost(?=[/:])", "@127.0.0.1", url, count=1, flags=re.IGNORECASE)


DATABASE_URL = normalize_database_url(_RAW_DATABASE_URL)
if DATABASE_URL != _RAW_DATABASE_URL:
    logger.info("DATABASE_URL: хост localhost заменён на 127.0.0.1 (DATABASE_FORCE_IPV4)")

_connect_timeout = float(os.getenv("DATABASE_CONNECT_TIMEOUT", "30"))
_connect_args: dict = {"timeout": _connect_timeout}
_ssl = (os.getenv("DATABASE_SSL", "") or "").strip().lower()
if _ssl in ("0", "false", "disable", "off", "no"):
    _connect_args["ssl"] = False

# pool_pre_ping: перед выдачей из пула проверяем соединение (обрывы TCP / рестарт Postgres / Win 10054).
# pool_recycle: не держим коннект дольше ~4.5 мин — многие прокси/СУБД рвут idle дольше 5–10 мин.
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    future=True,
    pool_pre_ping=True,
    pool_recycle=int(os.getenv("DATABASE_POOL_RECYCLE_SEC", "280")),
    connect_args=_connect_args,
)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with SessionLocal() as session:
        yield session


from contextlib import asynccontextmanager

@asynccontextmanager
async def get_db_session():
    """Context manager для использования вне FastAPI DI (например в pipeline)."""
    async with SessionLocal() as session:
        yield session


async def init_db():
    """Создаём таблицы при старте, если их нет. Применяем лёгкие миграции колонок."""
    from db.models.lead import Lead  # noqa: F401
    from db.models.lead_comment import LeadComment  # noqa: F401
    from db.models.lead_field_audit import LeadFieldAudit  # noqa: F401
    from db.models.lead_communication_log import LeadCommunicationLog  # noqa: F401
    from db.models.agent_email_intent import AgentEmailIntent  # noqa: F401
    from db.models.agent_run_log import AgentRunLog  # noqa: F401
    from db.models.task import Task  # noqa: F401
    from db.models.email import EmailAccount, EmailThread, EmailMessage, EmailCampaign  # noqa: F401
    from db.models.eval_scenario import EvalScenario  # noqa: F401
    from db.models.training_dataset import TrainingDataset, TrainingRecord  # noqa: F401
    from db.models.tender_saved import TenderSaved  # noqa: F401
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # ── лёгкие миграции: добавляем колонки которых может не быть ──
        migrations = [
            "ALTER TABLE email_messages ADD COLUMN IF NOT EXISTS is_archived BOOLEAN DEFAULT FALSE",
            "ALTER TABLE leads ADD COLUMN IF NOT EXISTS inn VARCHAR(20)",
            "ALTER TABLE leads ADD COLUMN IF NOT EXISTS ogrn VARCHAR(20)",
            "ALTER TABLE leads ADD COLUMN IF NOT EXISTS phone VARCHAR(100) DEFAULT '—'",
            "ALTER TABLE leads ADD COLUMN IF NOT EXISTS checko_json TEXT",
            "ALTER TABLE leads ADD COLUMN IF NOT EXISTS tech_json TEXT",
            "ALTER TABLE leads ADD COLUMN IF NOT EXISTS bitrix_lead_id INTEGER",
            "ALTER TABLE leads ADD COLUMN IF NOT EXISTS financials_json TEXT",
            "ALTER TABLE tasks ADD COLUMN IF NOT EXISTS sla_due VARCHAR(120)",
            "ALTER TABLE tasks ADD COLUMN IF NOT EXISTS escalated BOOLEAN DEFAULT FALSE",
            "ALTER TABLE leads ADD COLUMN IF NOT EXISTS amount_rub NUMERIC(14,2)",
            "ALTER TABLE leads ADD COLUMN IF NOT EXISTS paid_amount_rub NUMERIC(14,2)",
            "ALTER TABLE leads ADD COLUMN IF NOT EXISTS approvals JSONB",
            "ALTER TABLE lead_field_audits ADD COLUMN IF NOT EXISTS event_type VARCHAR(64) DEFAULT 'field_change'",
            "ALTER TABLE lead_field_audits ADD COLUMN IF NOT EXISTS metadata JSONB DEFAULT '{}'::jsonb",
        ]
        for sql in migrations:
            try:
                await conn.execute(__import__('sqlalchemy').text(sql))
            except Exception:
                pass  # колонка уже есть или другая СУБД
