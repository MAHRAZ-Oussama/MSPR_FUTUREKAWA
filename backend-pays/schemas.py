from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel


class WarehouseOut(BaseModel):
    id: int
    code: str
    country: str
    manager_email: str | None
    target_temp_c: Decimal | None
    target_humidity: Decimal | None
    tolerance_temp: Decimal | None
    tolerance_hum: Decimal | None

    model_config = {"from_attributes": True}


class LotOut(BaseModel):
    id: str
    warehouse_id: int
    storage_date: date
    status: str
    variete: str | None
    poids_kg: Decimal | None

    model_config = {"from_attributes": True}


class LotCreate(BaseModel):
    id: str
    warehouse_id: int
    storage_date: date
    variete: str | None = None
    poids_kg: Decimal | None = None


class MeasurementOut(BaseModel):
    id: int
    warehouse_id: int
    measured_at: datetime
    temperature_c: Decimal | None
    humidity_pct: Decimal | None

    model_config = {"from_attributes": True}


class AlertOut(BaseModel):
    id: int
    warehouse_id: int
    lot_id: str | None
    alert_type: str
    severity: str
    message: str | None
    created_at: datetime
    resolved_at: datetime | None
    email_sent: bool

    model_config = {"from_attributes": True}


class DashboardStats(BaseModel):
    country: str
    total_lots: int
    lots_conformes: int
    lots_en_alerte: int
    lots_perimes: int
    active_alerts: int
    warehouses: list[WarehouseOut]
