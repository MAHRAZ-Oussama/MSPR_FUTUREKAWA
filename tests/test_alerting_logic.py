"""
Tests isolés de la logique d'alerting backend-pays (O1 péremption, O2 statut).

SQLite en mémoire, aucune dépendance SMTP/MQTT. Couvre :
- création (et dédup) de l'alerte LOT_EXPIRED ;
- envoi d'email au responsable (fonction patchée) ;
- bascule CONFORME <-> EN_ALERTE selon les alertes conditions actives.
"""
import os
import sys
from datetime import date, timedelta

import pytest
import pytest_asyncio

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("COUNTRY", "BR")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../backend-pays"))

from sqlalchemy.pool import StaticPool
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

import alerting
from models import Base, Warehouse, Lot, Alert


@pytest_asyncio.fixture
async def db():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with SessionLocal() as session:
        session.add(Warehouse(
            id=1, code="BR-WH-001", country="BR",
            manager_email="resp@futurekawa.com",
            target_temp_c=29, target_humidity=55, tolerance_temp=3, tolerance_hum=2,
        ))
        await session.commit()
        yield session
    await engine.dispose()


async def _add_lot(db, lot_id, days_old, status="CONFORME", wh=1):
    db.add(Lot(
        id=lot_id, warehouse_id=wh,
        storage_date=date.today() - timedelta(days=days_old), status=status,
    ))
    await db.commit()


@pytest.mark.asyncio
async def test_O1_expired_lot_creates_alert(db):
    await _add_lot(db, "OLD", 400)
    new = await alerting.check_expired_lots(db, notify=False)
    assert len(new) == 1
    assert new[0].alert_type == "LOT_EXPIRED"
    assert new[0].lot_id == "OLD"
    lot = (await db.execute(Lot.__table__.select())).first()
    assert lot.status == "PERIME"


@pytest.mark.asyncio
async def test_O1_recent_lot_no_alert(db):
    await _add_lot(db, "FRESH", 30)
    new = await alerting.check_expired_lots(db, notify=False)
    assert new == []


@pytest.mark.asyncio
async def test_O1_no_duplicate_expired_alert(db):
    await _add_lot(db, "OLD", 400)
    await alerting.check_expired_lots(db, notify=False)
    new = await alerting.check_expired_lots(db, notify=False)  # 2e passage
    assert new == []
    count = len((await db.execute(Alert.__table__.select())).all())
    assert count == 1


@pytest.mark.asyncio
async def test_O1_email_sent_to_manager(db, monkeypatch):
    sent = []

    async def fake_send(to, subject, body):
        sent.append((to, subject))
        return True

    monkeypatch.setattr(alerting, "send_alert_email", fake_send)
    await _add_lot(db, "OLD", 400)
    await alerting.check_expired_lots(db, notify=True)
    assert sent and sent[0][0] == "resp@futurekawa.com"
    alert = (await db.execute(Alert.__table__.select())).first()
    assert alert.email_sent is True


@pytest.mark.asyncio
async def test_O2_lot_becomes_en_alerte_on_active_condition_alert(db):
    await _add_lot(db, "L1", 30)
    db.add(Alert(warehouse_id=1, alert_type="TEMP_OUT_OF_RANGE", severity="CRITICAL"))
    await db.commit()
    await alerting.sync_lot_alert_status(db)
    lot = (await db.execute(Lot.__table__.select())).first()
    assert lot.status == "EN_ALERTE"


@pytest.mark.asyncio
async def test_O2_reverts_to_conforme_when_resolved(db):
    await _add_lot(db, "L1", 30, status="EN_ALERTE")
    # aucune alerte active -> doit revenir CONFORME
    await alerting.sync_lot_alert_status(db)
    lot = (await db.execute(Lot.__table__.select())).first()
    assert lot.status == "CONFORME"


@pytest.mark.asyncio
async def test_O2_perime_takes_precedence(db):
    """Un lot PERIME ne doit jamais être repassé EN_ALERTE."""
    await _add_lot(db, "L1", 400, status="PERIME")
    db.add(Alert(warehouse_id=1, alert_type="HUMIDITY_OUT_OF_RANGE", severity="WARNING"))
    await db.commit()
    await alerting.sync_lot_alert_status(db)
    lot = (await db.execute(Lot.__table__.select())).first()
    assert lot.status == "PERIME"
