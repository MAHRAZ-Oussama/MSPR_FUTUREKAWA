from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import get_db
from models import Measurement, Lot
from schemas import MeasurementOut

router = APIRouter(prefix="/measurements", tags=["measurements"])


@router.get("/", response_model=list[MeasurementOut])
async def list_measurements(
    warehouse_id: int | None = Query(None),
    lot_id: str | None = Query(None),
    limit: int = Query(200, le=1000),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Measurement).order_by(Measurement.measured_at.desc()).limit(limit)
    if warehouse_id:
        stmt = stmt.where(Measurement.warehouse_id == warehouse_id)
    elif lot_id:
        lot_result = await db.execute(select(Lot).where(Lot.id == lot_id))
        lot = lot_result.scalar_one_or_none()
        if lot:
            stmt = stmt.where(
                Measurement.warehouse_id == lot.warehouse_id,
                Measurement.measured_at >= lot.storage_date,
            )
    result = await db.execute(stmt)
    rows = result.scalars().all()
    return list(reversed(rows))
