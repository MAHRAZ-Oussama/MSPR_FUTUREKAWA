from datetime import date, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from database import get_db
from models import Lot, Warehouse
from schemas import LotOut, LotCreate

router = APIRouter(prefix="/lots", tags=["lots"])

EXPIRY_DAYS = 365


@router.get("/", response_model=list[LotOut])
async def list_lots(
    status: str | None = Query(None),
    warehouse_id: int | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    await _update_expired_lots(db)
    stmt = select(Lot).order_by(Lot.storage_date.asc())
    if status:
        stmt = stmt.where(Lot.status == status)
    if warehouse_id:
        stmt = stmt.where(Lot.warehouse_id == warehouse_id)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/{lot_id}", response_model=LotOut)
async def get_lot(lot_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Lot).where(Lot.id == lot_id))
    lot = result.scalar_one_or_none()
    if not lot:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Lot non trouvé")
    return lot


@router.post("/", response_model=LotOut, status_code=201)
async def create_lot(payload: LotCreate, db: AsyncSession = Depends(get_db)):
    lot = Lot(**payload.model_dump())
    db.add(lot)
    await db.commit()
    await db.refresh(lot)
    return lot


async def _update_expired_lots(db: AsyncSession):
    cutoff = date.today() - timedelta(days=EXPIRY_DAYS)
    await db.execute(
        update(Lot)
        .where(Lot.storage_date <= cutoff, Lot.status != "EN_ALERTE")
        .values(status="PERIME")
    )
    await db.commit()
