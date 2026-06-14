"""
Fixtures partagées pour tous les tests.
Utilise une base SQLite en mémoire pour les tests unitaires rapides.
"""
import os
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

# Base SQLite en mémoire pour les tests (pas besoin de PostgreSQL)
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

os.environ["DATABASE_URL"] = TEST_DATABASE_URL
os.environ["COUNTRY"] = "BR"
os.environ["SMTP_HOST"] = "localhost"
os.environ["SMTP_PORT"] = "1025"


@pytest_asyncio.fixture(scope="function")
async def db_session():
    from sqlalchemy.ext.asyncio import create_async_engine
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)

    # Import ici pour que les env vars soient définies avant
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../backend-pays"))
    from database import Base
    from models import Warehouse, Lot, Measurement, Alert

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with SessionLocal() as session:
        yield session

    await engine.dispose()
