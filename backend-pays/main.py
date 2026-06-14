import os
import asyncio
from contextlib import asynccontextmanager
from datetime import date, timedelta

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update as sa_update

from database import get_db
from models import Lot, Alert, Warehouse
from schemas import DashboardStats, WarehouseOut
from routers import warehouses, lots, measurements, alerts
from seed import seed

COUNTRY = os.getenv("COUNTRY", "BR")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await seed()
    yield


app = FastAPI(
    title=f"FutureKawa API — {COUNTRY}",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
    cutoff = date.today() - timedelta(days=365)
    await db.execute(
        sa_update(Lot)
        .where(Lot.storage_date <= cutoff, Lot.status != "EN_ALERTE")
        .values(status="PERIME")
    )
    await db.commit()

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
