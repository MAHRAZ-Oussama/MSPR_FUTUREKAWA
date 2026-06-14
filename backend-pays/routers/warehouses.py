from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import get_db
from models import Warehouse
from schemas import WarehouseOut

router = APIRouter(prefix="/warehouses", tags=["warehouses"])


@router.get("/", response_model=list[WarehouseOut])
async def list_warehouses(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Warehouse))
    return result.scalars().all()


@router.get("/{warehouse_id}", response_model=WarehouseOut)
async def get_warehouse(warehouse_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Warehouse).where(Warehouse.id == warehouse_id))
    wh = result.scalar_one_or_none()
    if not wh:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Entrepôt non trouvé")
    return wh
