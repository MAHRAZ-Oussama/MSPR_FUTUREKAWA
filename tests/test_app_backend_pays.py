"""
Tests d'application ISOLÉS du backend-pays.

Aucune dépendance externe : base SQLite en mémoire + httpx ASGITransport
(pas de PostgreSQL, pas de Docker, pas de MQTT). Exécutables en CI.

Lancer : pytest tests/test_app_backend_pays.py -v
"""
import os
import sys
from datetime import date, timedelta

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

# Configuration d'environnement AVANT import de l'app (DB SQLite mémoire)
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["COUNTRY"] = "BR"
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../backend-pays"))


@pytest_asyncio.fixture
async def client():
    """App FastAPI sur base SQLite mémoire, schéma créé + 1 entrepôt seedé."""
    import database
    import models  # noqa: F401  (enregistre les tables sur Base.metadata)

    # Moteur SQLite mémoire partagé pour toute la session de test.
    # StaticPool = une seule connexion réutilisée -> la base ":memory:" persiste
    # entre les sessions (sinon chaque session repartirait sur une base vide).
    from sqlalchemy.pool import StaticPool
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    database.engine = engine
    database.AsyncSessionLocal = SessionLocal

    from models import Base, Warehouse
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with SessionLocal() as db:
        db.add(Warehouse(
            id=1, code="BR-WH-001", country="BR",
            manager_email="resp@futurekawa.com",
            target_temp_c=29, target_humidity=55,
            tolerance_temp=3, tolerance_hum=2,
        ))
        await db.commit()

    # Importer l'app après avoir patché la DB ; neutraliser le seed() du lifespan
    import main
    async def _noop_seed():
        return None
    main.seed = _noop_seed

    transport = ASGITransport(app=main.app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    await engine.dispose()


@pytest.mark.asyncio
async def test_health(client):
    r = await client.get("/health")
    assert r.status_code == 200
    assert r.json()["country"] == "BR"


@pytest.mark.asyncio
async def test_list_warehouses(client):
    r = await client.get("/warehouses/")
    assert r.status_code == 200
    assert len(r.json()) == 1


@pytest.mark.asyncio
async def test_warehouse_not_found(client):
    r = await client.get("/warehouses/9999")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_create_and_get_lot(client):
    payload = {
        "id": "BR-LOT-APP-1", "warehouse_id": 1,
        "storage_date": "2025-01-15", "variete": "Arabica", "poids_kg": 250.0,
    }
    r = await client.post("/lots/", json=payload)
    assert r.status_code == 201
    assert r.json()["status"] == "CONFORME"

    r = await client.get("/lots/BR-LOT-APP-1")
    assert r.status_code == 200
    assert r.json()["id"] == "BR-LOT-APP-1"


@pytest.mark.asyncio
async def test_lots_fifo_order(client):
    """Les lots doivent être triés par storage_date ASC (FIFO)."""
    for lot_id, days in [("OLD", 300), ("MID", 100), ("NEW", 10)]:
        d = (date.today() - timedelta(days=days)).isoformat()
        await client.post("/lots/", json={"id": lot_id, "warehouse_id": 1, "storage_date": d})
    r = await client.get("/lots/")
    ids = [lot["id"] for lot in r.json()]
    assert ids.index("OLD") < ids.index("MID") < ids.index("NEW")


@pytest.mark.asyncio
async def test_expired_lot_becomes_perime(client):
    """Un lot > 365 j passe automatiquement PERIME à la lecture."""
    old = (date.today() - timedelta(days=400)).isoformat()
    await client.post("/lots/", json={"id": "EXP", "warehouse_id": 1, "storage_date": old})
    r = await client.get("/lots/")
    lot = next(lot for lot in r.json() if lot["id"] == "EXP")
    assert lot["status"] == "PERIME"


@pytest.mark.asyncio
async def test_lot_not_found(client):
    r = await client.get("/lots/DOES-NOT-EXIST")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_dashboard_summary_shape(client):
    r = await client.get("/dashboard/summary")
    assert r.status_code == 200
    data = r.json()
    for key in ("country", "total_lots", "lots_conformes",
                "lots_en_alerte", "lots_perimes", "active_alerts", "warehouses"):
        assert key in data


@pytest.mark.asyncio
async def test_B4_api_key_open_by_default(client):
    """API_KEY non défini -> écriture ouverte (comportement démo)."""
    r = await client.post("/lots/", json={
        "id": "OPEN-1", "warehouse_id": 1, "storage_date": "2025-06-01",
    })
    assert r.status_code == 201


@pytest.mark.asyncio
async def test_B4_api_key_enforced_when_set(client, monkeypatch):
    """API_KEY défini -> 401 sans clé, 201 avec la bonne clé."""
    import config
    monkeypatch.setattr(config.settings, "api_key", "s3cret")

    r = await client.post("/lots/", json={
        "id": "PROT-1", "warehouse_id": 1, "storage_date": "2025-06-01",
    })
    assert r.status_code == 401

    r = await client.post(
        "/lots/",
        json={"id": "PROT-2", "warehouse_id": 1, "storage_date": "2025-06-01"},
        headers={"X-API-Key": "s3cret"},
    )
    assert r.status_code == 201
