from datetime import date, datetime, timezone
from decimal import Decimal
from sqlalchemy import String, Integer, ForeignKey, Date, DECIMAL, Text, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base

_TZ = DateTime(timezone=True)


def _utcnow() -> datetime:
    """Horodatage UTC timezone-aware (remplace datetime.utcnow() déprécié)."""
    return datetime.now(timezone.utc)


class Warehouse(Base):
    __tablename__ = "warehouses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    country: Mapped[str] = mapped_column(String(2), nullable=False)
    manager_email: Mapped[str | None] = mapped_column(String(150))
    target_temp_c: Mapped[Decimal | None] = mapped_column(DECIMAL(4, 1))
    target_humidity: Mapped[Decimal | None] = mapped_column(DECIMAL(4, 1))
    tolerance_temp: Mapped[Decimal | None] = mapped_column(DECIMAL(3, 1))
    tolerance_hum: Mapped[Decimal | None] = mapped_column(DECIMAL(3, 1))

    lots: Mapped[list["Lot"]] = relationship("Lot", back_populates="warehouse")
    measurements: Mapped[list["Measurement"]] = relationship("Measurement", back_populates="warehouse")
    alerts: Mapped[list["Alert"]] = relationship("Alert", back_populates="warehouse")


class Lot(Base):
    __tablename__ = "lots"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    warehouse_id: Mapped[int] = mapped_column(Integer, ForeignKey("warehouses.id"))
    storage_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="CONFORME")
    variete: Mapped[str | None] = mapped_column(String(50))
    poids_kg: Mapped[Decimal | None] = mapped_column(DECIMAL(8, 2))

    warehouse: Mapped["Warehouse"] = relationship("Warehouse", back_populates="lots")
    alerts: Mapped[list["Alert"]] = relationship("Alert", back_populates="lot")


class Measurement(Base):
    __tablename__ = "measurements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    warehouse_id: Mapped[int] = mapped_column(Integer, ForeignKey("warehouses.id"))
    measured_at: Mapped[datetime] = mapped_column(_TZ, default=_utcnow)
    temperature_c: Mapped[Decimal | None] = mapped_column(DECIMAL(4, 1))
    humidity_pct: Mapped[Decimal | None] = mapped_column(DECIMAL(4, 1))

    warehouse: Mapped["Warehouse"] = relationship("Warehouse", back_populates="measurements")


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    warehouse_id: Mapped[int] = mapped_column(Integer, ForeignKey("warehouses.id"))
    lot_id: Mapped[str | None] = mapped_column(String(50), ForeignKey("lots.id"))
    alert_type: Mapped[str] = mapped_column(String(30), nullable=False)
    severity: Mapped[str] = mapped_column(String(10), nullable=False)
    message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(_TZ, default=_utcnow)
    resolved_at: Mapped[datetime | None] = mapped_column(_TZ)
    email_sent: Mapped[bool] = mapped_column(Boolean, default=False)

    warehouse: Mapped["Warehouse"] = relationship("Warehouse", back_populates="alerts")
    lot: Mapped["Lot | None"] = relationship("Lot", back_populates="alerts")
