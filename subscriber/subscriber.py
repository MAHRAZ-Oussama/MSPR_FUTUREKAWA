"""
MQTT subscriber : consomme les mesures IoT, les persiste en base,
et déclenche les alertes avec déduplication anti-flood (fenêtre 30 min).
"""
import asyncio
import json
import logging
import os
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import aiomqtt
import aiosmtplib
from email.mime.text import MIMEText
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import Column, Integer, String, DECIMAL, Boolean, Text, DateTime

TIMESTAMPTZ = DateTime(timezone=True)
from sqlalchemy.orm import DeclarativeBase

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

# ── Configuration ────────────────────────────────────────────────────────────
COUNTRY     = os.getenv("COUNTRY", "BR")
MQTT_HOST   = os.getenv("MQTT_HOST", "mosquitto")
MQTT_PORT   = int(os.getenv("MQTT_PORT", "1883"))
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://futurekawa:futurekawa@postgres:5432/futurekawa")
SMTP_HOST   = os.getenv("SMTP_HOST", "mailhog")
SMTP_PORT   = int(os.getenv("SMTP_PORT", "1025"))
TOPIC       = f"futurekawa/{COUNTRY}/warehouse/+/measurement"
FLOOD_WINDOW = timedelta(minutes=30)

# ── ORM minimal (réutilise le même schéma que le backend) ────────────────────
class Base(DeclarativeBase):
    pass


class Warehouse(Base):
    __tablename__ = "warehouses"
    id            = Column(Integer, primary_key=True)
    code          = Column(String(20))
    country       = Column(String(2))
    manager_email = Column(String(150))
    target_temp_c = Column(DECIMAL(4, 1))
    target_humidity = Column(DECIMAL(4, 1))
    tolerance_temp  = Column(DECIMAL(3, 1))
    tolerance_hum   = Column(DECIMAL(3, 1))


class Lot(Base):
    __tablename__ = "lots"
    id           = Column(String(50), primary_key=True)
    warehouse_id = Column(Integer)
    storage_date = Column(DECIMAL)  # used only for querying lots in alert
    status       = Column(String(20))


class Measurement(Base):
    __tablename__ = "measurements"
    id           = Column(Integer, primary_key=True, autoincrement=True)
    warehouse_id = Column(Integer)
    measured_at  = Column(TIMESTAMPTZ, default=lambda: datetime.now(timezone.utc))
    temperature_c = Column(DECIMAL(4, 1))
    humidity_pct  = Column(DECIMAL(4, 1))


class Alert(Base):
    __tablename__ = "alerts"
    id           = Column(Integer, primary_key=True, autoincrement=True)
    warehouse_id = Column(Integer)
    lot_id       = Column(String(50))
    alert_type   = Column(String(30))
    severity     = Column(String(10))
    message      = Column(Text)
    created_at   = Column(TIMESTAMPTZ, default=lambda: datetime.now(timezone.utc))
    resolved_at  = Column(TIMESTAMPTZ)
    email_sent   = Column(Boolean, default=False)


engine = create_async_engine(DATABASE_URL, echo=False)
SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


# ── Calcul de sévérité ───────────────────────────────────────────────────────
def compute_severity(deviation: float, tolerance: float) -> str | None:
    if deviation <= tolerance:
        return None
    if deviation <= 1.5 * tolerance:
        return "WARNING"
    return "CRITICAL"


# ── Déduplication anti-flood ─────────────────────────────────────────────────
async def is_duplicate(db: AsyncSession, warehouse_id: int, alert_type: str) -> bool:
    cutoff = datetime.now(timezone.utc) - FLOOD_WINDOW
    result = await db.execute(
        select(Alert).where(
            Alert.warehouse_id == warehouse_id,
            Alert.alert_type == alert_type,
            Alert.resolved_at.is_(None),
            Alert.created_at >= cutoff,
        )
    )
    return result.scalar_one_or_none() is not None


# ── Envoi email ──────────────────────────────────────────────────────────────
async def send_alert_email(to: str, subject: str, body: str, alert_id: int, db: AsyncSession):
    try:
        msg = MIMEText(body, "plain", "utf-8")
        msg["Subject"] = subject
        msg["From"]    = "alertes@futurekawa.com"
        msg["To"]      = to
        await aiosmtplib.send(msg, hostname=SMTP_HOST, port=SMTP_PORT)
        await db.execute(
            update(Alert).where(Alert.id == alert_id).values(email_sent=True)
        )
        await db.commit()
        log.info("Email envoyé à %s : %s", to, subject)
    except Exception as exc:
        log.error("Échec envoi email : %s", exc)


# ── Traitement d'une mesure ──────────────────────────────────────────────────
async def process_measurement(warehouse_code: str, payload: dict):
    temp = payload.get("temperature_c")
    hum  = payload.get("humidity_pct")
    if temp is None or hum is None:
        log.warning("Payload incomplet : %s", payload)
        return

    async with SessionLocal() as db:
        wh_result = await db.execute(
            select(Warehouse).where(Warehouse.code == warehouse_code)
        )
        wh = wh_result.scalar_one_or_none()
        if not wh:
            log.warning("Entrepôt inconnu : %s", warehouse_code)
            return

        m = Measurement(
            warehouse_id=wh.id,
            measured_at=datetime.now(timezone.utc),
            temperature_c=Decimal(str(temp)),
            humidity_pct=Decimal(str(hum)),
        )
        db.add(m)
        await db.commit()
        log.info("[%s] T=%.1f°C H=%.1f%%", warehouse_code, temp, hum)

        target_t = float(wh.target_temp_c or 25)
        target_h = float(wh.target_humidity or 60)
        tol_t    = float(wh.tolerance_temp or 3)
        tol_h    = float(wh.tolerance_hum or 2)

        checks = [
            ("TEMP_OUT_OF_RANGE",     abs(temp - target_t), tol_t,
             f"Température {temp}°C hors plage (cible {target_t}°C ±{tol_t}°C)"),
            ("HUMIDITY_OUT_OF_RANGE", abs(hum - target_h), tol_h,
             f"Humidité {hum}% hors plage (cible {target_h}% ±{tol_h}%)"),
        ]

        for alert_type, deviation, tolerance, msg_text in checks:
            severity = compute_severity(deviation, tolerance)
            if not severity:
                continue
            if await is_duplicate(db, wh.id, alert_type):
                log.debug("Anti-flood : alerte %s déjà active pour %s", alert_type, warehouse_code)
                continue

            alert = Alert(
                warehouse_id=wh.id,
                alert_type=alert_type,
                severity=severity,
                message=msg_text,
            )
            db.add(alert)
            await db.commit()
            await db.refresh(alert)
            log.warning("[ALERTE %s] %s — %s", severity, warehouse_code, msg_text)

            if wh.manager_email:
                subject = f"[FutureKawa {severity}] {alert_type} — {warehouse_code}"
                body = (
                    f"Entrepôt : {warehouse_code} ({COUNTRY})\n"
                    f"Type : {alert_type}\n"
                    f"Sévérité : {severity}\n"
                    f"Détail : {msg_text}\n"
                    f"Horodatage : {datetime.now(timezone.utc).isoformat()}\n"
                )
                await send_alert_email(wh.manager_email, subject, body, alert.id, db)


# ── Boucle MQTT principale ───────────────────────────────────────────────────
async def main():
    log.info("Subscriber démarré — pays=%s topic=%s", COUNTRY, TOPIC)
    reconnect_delay = 5
    while True:
        try:
            async with aiomqtt.Client(MQTT_HOST, MQTT_PORT) as client:
                reconnect_delay = 5
                await client.subscribe(TOPIC, qos=1)
                log.info("Abonné au topic %s", TOPIC)
                async with client.messages() as messages:
                    async for message in messages:
                        try:
                            topic_parts = str(message.topic).split("/")
                            # futurekawa/{COUNTRY}/warehouse/{CODE}/measurement
                            if len(topic_parts) >= 4:
                                warehouse_code = topic_parts[3]
                                data = json.loads(message.payload)
                                await process_measurement(warehouse_code, data)
                        except Exception as exc:
                            log.error("Erreur traitement message : %s", exc)
        except aiomqtt.MqttError as exc:
            log.error("MQTT déconnecté : %s — reconnexion dans %ds", exc, reconnect_delay)
            await asyncio.sleep(reconnect_delay)
            reconnect_delay = min(reconnect_delay * 2, 60)
        except Exception as exc:
            log.error("Erreur inattendue : %s", exc)
            await asyncio.sleep(reconnect_delay)


if __name__ == "__main__":
    asyncio.run(main())
