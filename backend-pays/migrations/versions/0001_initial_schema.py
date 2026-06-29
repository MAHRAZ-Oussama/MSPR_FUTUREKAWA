"""Schéma initial FutureKawa (warehouses, lots, measurements, alerts)

Revision ID: 0001
Revises:
Create Date: 2026-06-28
"""
from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "warehouses",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(20), nullable=False, unique=True),
        sa.Column("country", sa.String(2), nullable=False),
        sa.Column("manager_email", sa.String(150)),
        sa.Column("target_temp_c", sa.Numeric(4, 1)),
        sa.Column("target_humidity", sa.Numeric(4, 1)),
        sa.Column("tolerance_temp", sa.Numeric(3, 1)),
        sa.Column("tolerance_hum", sa.Numeric(3, 1)),
    )

    op.create_table(
        "lots",
        sa.Column("id", sa.String(50), primary_key=True),
        sa.Column("warehouse_id", sa.Integer(), sa.ForeignKey("warehouses.id")),
        sa.Column("storage_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(20), server_default="CONFORME"),
        sa.Column("variete", sa.String(50)),
        sa.Column("poids_kg", sa.Numeric(8, 2)),
    )
    op.create_index("idx_lots_storage_date", "lots", ["storage_date"])

    op.create_table(
        "measurements",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("warehouse_id", sa.Integer(), sa.ForeignKey("warehouses.id")),
        sa.Column("measured_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("temperature_c", sa.Numeric(4, 1)),
        sa.Column("humidity_pct", sa.Numeric(4, 1)),
    )
    op.create_index("idx_measurements_wh_time", "measurements", ["warehouse_id", "measured_at"])

    op.create_table(
        "alerts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("warehouse_id", sa.Integer(), sa.ForeignKey("warehouses.id")),
        sa.Column("lot_id", sa.String(50), sa.ForeignKey("lots.id")),
        sa.Column("alert_type", sa.String(30), nullable=False),
        sa.Column("severity", sa.String(10), nullable=False),
        sa.Column("message", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("resolved_at", sa.DateTime(timezone=True)),
        sa.Column("email_sent", sa.Boolean(), server_default=sa.false()),
    )
    op.create_index("idx_alerts_active", "alerts", ["warehouse_id", "alert_type", "resolved_at"])


def downgrade() -> None:
    op.drop_table("alerts")
    op.drop_table("measurements")
    op.drop_index("idx_lots_storage_date", table_name="lots")
    op.drop_table("lots")
    op.drop_table("warehouses")
