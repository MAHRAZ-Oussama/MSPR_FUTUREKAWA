from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from config import settings

DATABASE_URL = settings.database_url

# Le pool dimensionné (pool_size/max_overflow) n'a de sens que pour un vrai
# SGBD réseau (PostgreSQL). SQLite — utilisé en tests isolés — impose un
# StaticPool qui rejette ces paramètres, donc on ne les passe que hors SQLite.
_engine_kwargs: dict = {"echo": False}
if not DATABASE_URL.startswith("sqlite"):
    _engine_kwargs.update(pool_size=10, max_overflow=20)

engine = create_async_engine(DATABASE_URL, **_engine_kwargs)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
