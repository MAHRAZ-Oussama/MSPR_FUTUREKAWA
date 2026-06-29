"""Seed initial data per country — called once at startup."""
import asyncio
from datetime import date, timedelta
import random
from sqlalchemy import select
from database import engine, AsyncSessionLocal
from models import Base, Warehouse, Lot
from config import settings

COUNTRY = settings.country

COUNTRY_CONFIG = {
    "BR": {
        "warehouses": [
            {"code": "BR-WH-001", "manager_email": "responsable.br1@futurekawa.com",
             "target_temp_c": 29.0, "target_humidity": 55.0, "tolerance_temp": 3.0, "tolerance_hum": 2.0},
            {"code": "BR-WH-002", "manager_email": "responsable.br2@futurekawa.com",
             "target_temp_c": 29.0, "target_humidity": 55.0, "tolerance_temp": 3.0, "tolerance_hum": 2.0},
        ],
        "lot_prefix": "BR-LOT",
        "varietes": ["Arabica", "Robusta", "Bourbon"],
    },
    "EC": {
        "warehouses": [
            {"code": "EC-WH-001", "manager_email": "responsable.ec1@futurekawa.com",
             "target_temp_c": 31.0, "target_humidity": 60.0, "tolerance_temp": 3.0, "tolerance_hum": 2.0},
            {"code": "EC-WH-002", "manager_email": "responsable.ec2@futurekawa.com",
             "target_temp_c": 31.0, "target_humidity": 60.0, "tolerance_temp": 3.0, "tolerance_hum": 2.0},
        ],
        "lot_prefix": "EC-LOT",
        "varietes": ["Arabica", "Typica", "Caturra"],
    },
    "CO": {
        "warehouses": [
            {"code": "CO-WH-001", "manager_email": "responsable.co1@futurekawa.com",
             "target_temp_c": 26.0, "target_humidity": 80.0, "tolerance_temp": 3.0, "tolerance_hum": 2.0},
            {"code": "CO-WH-002", "manager_email": "responsable.co2@futurekawa.com",
             "target_temp_c": 26.0, "target_humidity": 80.0, "tolerance_temp": 3.0, "tolerance_hum": 2.0},
        ],
        "lot_prefix": "CO-LOT",
        "varietes": ["Supremo", "Excelso", "Arabica"],
    },
}


async def seed():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    config = COUNTRY_CONFIG.get(COUNTRY, COUNTRY_CONFIG["BR"])
    async with AsyncSessionLocal() as db:
        for wh_data in config["warehouses"]:
            existing = await db.execute(
                select(Warehouse).where(Warehouse.code == wh_data["code"])
            )
            if existing.scalar_one_or_none():
                continue
            wh = Warehouse(country=COUNTRY, **wh_data)
            db.add(wh)
        await db.commit()

        warehouses = (await db.execute(select(Warehouse))).scalars().all()
        for i, wh in enumerate(warehouses):
            for j in range(1, 6):
                lot_id = f"{config['lot_prefix']}-2024-{(i * 5 + j):03d}"
                existing_lot = await db.execute(select(Lot).where(Lot.id == lot_id))
                if existing_lot.scalar_one_or_none():
                    continue
                days_ago = random.randint(10, 400)
                storage_date = date.today() - timedelta(days=days_ago)
                status = "PERIME" if days_ago > 365 else "CONFORME"
                lot = Lot(
                    id=lot_id,
                    warehouse_id=wh.id,
                    storage_date=storage_date,
                    status=status,
                    variete=random.choice(config["varietes"]),
                    poids_kg=round(random.uniform(100, 500), 2),
                )
                db.add(lot)
        await db.commit()


if __name__ == "__main__":
    asyncio.run(seed())
