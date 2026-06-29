from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import get_db
from models import Lot
from schemas import LotOut, LotCreate
from alerting import mark_expired_lots, sync_lot_alert_status
from security import require_api_key

router = APIRouter(prefix="/lots", tags=["lots"])


@router.get("/", response_model=list[LotOut])
async def list_lots(
    status: str | None = Query(None),
    warehouse_id: int | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    await mark_expired_lots(db)
    await sync_lot_alert_status(db)
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
async def create_lot(
    payload: LotCreate,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_api_key),
):
    lot = Lot(**payload.model_dump())
    db.add(lot)
    await db.commit()
    await db.refresh(lot)
    return lot
