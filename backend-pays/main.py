import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config import settings
from database import get_db, AsyncSessionLocal
from models import Lot, Alert, Warehouse
from schemas import DashboardStats, WarehouseOut
from routers import warehouses, lots, measurements, alerts
from seed import seed
from alerting import mark_expired_lots, sync_lot_alert_status, run_periodic_checks

log = logging.getLogger("api")
COUNTRY = settings.country


@asynccontextmanager
async def lifespan(app: FastAPI):
    await seed()
    # Vérification immédiate au démarrage, puis périodique (O3).
    await run_periodic_checks(AsyncSessionLocal)
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        run_periodic_checks,
        "interval",
        minutes=settings.check_interval_minutes,
        args=[AsyncSessionLocal],
        id="periodic_checks",
        max_instances=1,
        coalesce=True,
    )
    scheduler.start()
    log.info("Scheduler démarré — vérifications toutes les %d min",
             settings.check_interval_minutes)
    try:
        yield
    finally:
        scheduler.shutdown(wait=False)


app = FastAPI(
    title=f"FutureKawa API — {COUNTRY}",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(warehouses.router)
app.include_router(lots.router)
app.include_router(measurements.router)
app.include_router(alerts.router)


@app.get("/health")
async def health():
    return {"status": "ok", "country": COUNTRY}


@app.get("/dashboard/summary", response_model=DashboardStats)
async def dashboard_summary(db: AsyncSession = Depends(get_db)):
    await mark_expired_lots(db)
    await sync_lot_alert_status(db)

    total = (await db.execute(func.count(Lot.id).select())).scalar() or 0
    conformes = (await db.execute(
        select(func.count(Lot.id)).where(Lot.status == "CONFORME")
    )).scalar() or 0
    en_alerte = (await db.execute(
        select(func.count(Lot.id)).where(Lot.status == "EN_ALERTE")
    )).scalar() or 0
    perimes = (await db.execute(
        select(func.count(Lot.id)).where(Lot.status == "PERIME")
    )).scalar() or 0
    active_alerts = (await db.execute(
        select(func.count(Alert.id)).where(Alert.resolved_at.is_(None))
    )).scalar() or 0

    wh_result = await db.execute(select(Warehouse))
    warehouse_list = wh_result.scalars().all()

    return DashboardStats(
        country=COUNTRY,
        total_lots=total,
        lots_conformes=conformes,
        lots_en_alerte=en_alerte,
        lots_perimes=perimes,
        active_alerts=active_alerts,
        warehouses=[WarehouseOut.model_validate(w) for w in warehouse_list],
    )
