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


async def init_db():
    """Создаём таблицы при старте, если их нет."""
    from db.models.lead import Lead  # noqa: F401
    from db.models.task import Task  # noqa: F401
    from db.models.email import EmailAccount, EmailThread, EmailMessage, EmailCampaign  # noqa: F401
    from db.models.eval_scenario import EvalScenario  # noqa: F401
    from db.models.training_dataset import TrainingDataset, TrainingRecord  # noqa: F401
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
