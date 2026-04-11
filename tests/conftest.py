"""
Общие фикстуры для тестов SmartCRM.
Используем SQLite in-memory вместо PostgreSQL, чтобы тесты не требовали запущенной БД.
"""
import asyncio
import os
import sys
from pathlib import Path

# Добавляем backend в PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

# Подменяем DATABASE_URL до импорта app
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("GROQ_API_KEY", "test")

from db.session import Base, get_db
from main import app


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def db_engine():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    from db.models.lead import Lead  # noqa: F401
    from db.models.eval_scenario import EvalScenario  # noqa: F401
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine):
    SessionLocal = async_sessionmaker(db_engine, expire_on_commit=False, class_=AsyncSession)
    async with SessionLocal() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client(db_engine):
    """HTTPX async клиент с подменённой сессией БД."""
    SessionLocal = async_sessionmaker(db_engine, expire_on_commit=False, class_=AsyncSession)

    async def override_get_db():
        async with SessionLocal() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()
