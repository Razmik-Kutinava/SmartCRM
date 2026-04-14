"""
Async SQLAlchemy сессия.
DATABASE_URL берётся из .env, например:
  postgresql+asyncpg://smartcrm:smartcrm@localhost:5432/smartcrm
"""
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://smartcrm:smartcrm@localhost:5432/smartcrm")

engine = create_async_engine(DATABASE_URL, echo=False, future=True)
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
    from db.models.agent_email_intent import AgentEmailIntent  # noqa: F401
    from db.models.agent_run_log import AgentRunLog  # noqa: F401
    from db.models.task import Task  # noqa: F401
    from db.models.email import EmailAccount, EmailThread, EmailMessage, EmailCampaign  # noqa: F401
    from db.models.eval_scenario import EvalScenario  # noqa: F401
    from db.models.training_dataset import TrainingDataset, TrainingRecord  # noqa: F401
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
        ]
        for sql in migrations:
            try:
                await conn.execute(__import__('sqlalchemy').text(sql))
            except Exception:
                pass  # колонка уже есть или другая СУБД
