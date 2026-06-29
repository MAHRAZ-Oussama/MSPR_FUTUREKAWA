from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from database import get_db
from models import Alert
from schemas import AlertOut
from security import require_api_key

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("/", response_model=list[AlertOut])
async def list_alerts(
    active_only: bool = Query(False),
    severity: str | None = Query(None),
    alert_type: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Alert).order_by(Alert.created_at.desc())
    if active_only:
        stmt = stmt.where(Alert.resolved_at.is_(None))
    if severity:
        stmt = stmt.where(Alert.severity == severity)
    if alert_type:
        stmt = stmt.where(Alert.alert_type == alert_type)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("/{alert_id}/resolve", response_model=AlertOut)
async def resolve_alert(
    alert_id: int,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_api_key),
):
    await db.execute(
        update(Alert)
        .where(Alert.id == alert_id)
        .values(resolved_at=datetime.now(timezone.utc))
    )
    await db.commit()
    result = await db.execute(select(Alert).where(Alert.id == alert_id))
    return result.scalar_one()
