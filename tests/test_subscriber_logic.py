"""
Tests isolés de la logique DB du subscriber : rejet des mesures aberrantes (A3)
et auto-résolution des alertes par hystérésis (A1).

SQLite en mémoire ; l'email est neutralisé (monkeypatch). Aucun broker requis.
"""
import os
import sys
from datetime import datetime, timezone

import pytest
import pytest_asyncio

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("COUNTRY", "BR")
os.environ.setdefault("SMTP_HOST", "localhost")
os.environ.setdefault("SMTP_PORT", "1025")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../subscriber"))

from sqlalchemy.pool import StaticPool
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import select, func

import subscriber as sub


@pytest_asyncio.fixture
async def patched(monkeypatch):
    """Bascule le subscriber sur une base SQLite mémoire + email neutralisé."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with engine.begin() as conn:
        await conn.run_sync(sub.Base.metadata.create_all)
    async with SessionLocal() as db:
        db.add(sub.Warehouse(
            id=1, code="BR-WH-001", country="BR",
            manager_email="resp@futurekawa.com",
            target_temp_c=29, target_humidity=55, tolerance_temp=3, tolerance_hum=2,
        ))
        await db.commit()
    monkeypatch.setattr(sub, "SessionLocal", SessionLocal)

    async def _noop_email(*a, **k):
        return None
    monkeypatch.setattr(sub, "send_alert_email", _noop_email)

    yield SessionLocal
    await engine.dispose()


async def _count(SessionLocal, model):
    async with SessionLocal() as db:
        return (await db.execute(select(func.count()).select_from(model))).scalar()


@pytest.mark.asyncio
async def test_A3_aberrant_measurement_rejected(patched):
    """Mesure physiquement impossible → ni persistée ni alertée."""
    await sub.process_measurement("BR-WH-001", {"temperature_c": 250.0, "humidity_pct": 55.0})
    assert await _count(patched, sub.Measurement) == 0
    assert await _count(patched, sub.Alert) == 0


@pytest.mark.asyncio
async def test_normal_measurement_persisted(patched):
    await sub.process_measurement("BR-WH-001", {"temperature_c": 29.0, "humidity_pct": 55.0})
    assert await _count(patched, sub.Measurement) == 1


@pytest.mark.asyncio
async def test_A1_alert_raised_then_auto_resolved(patched):
    """Mesure CRITICAL → alerte ; retour franc à la normale → auto-résolution."""
    # Hors plage (T=38, écart 9°C >> 1.5×3) -> alerte créée et active
    await sub.process_measurement("BR-WH-001", {"temperature_c": 38.0, "humidity_pct": 55.0})
    async with patched() as db:
        active = (await db.execute(
            select(func.count()).select_from(sub.Alert).where(sub.Alert.resolved_at.is_(None))
        )).scalar()
    assert active == 1

    # Retour franc dans la plage (T=29 cible) -> hystérésis -> résolution
    await sub.process_measurement("BR-WH-001", {"temperature_c": 29.0, "humidity_pct": 55.0})
    async with patched() as db:
        still_active = (await db.execute(
            select(func.count()).select_from(sub.Alert).where(sub.Alert.resolved_at.is_(None))
        )).scalar()
    assert still_active == 0


@pytest.mark.asyncio
async def test_A1_dead_band_does_not_resolve(patched):
    """Dans la bande morte (légèrement sous le seuil) l'alerte reste active."""
    await sub.process_measurement("BR-WH-001", {"temperature_c": 38.0, "humidity_pct": 55.0})
    # Écart 2.5°C : 0.8×3=2.4 < 2.5 ≤ 3 -> bande morte -> NE clôt PAS
    await sub.process_measurement("BR-WH-001", {"temperature_c": 31.5, "humidity_pct": 55.0})
    async with patched() as db:
        active = (await db.execute(
            select(func.count()).select_from(sub.Alert).where(sub.Alert.resolved_at.is_(None))
        )).scalar()
    assert active == 1
