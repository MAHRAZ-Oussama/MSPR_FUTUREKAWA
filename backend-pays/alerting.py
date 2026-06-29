"""
Logique d'alerting côté backend-pays : péremption des lots (O1) et
synchronisation du statut métier des lots (O2).

Ces fonctions sont appelées périodiquement par le scheduler (O3) et, pour la
mise à jour de statut, de façon paresseuse à la lecture des lots. Elles sont
idempotentes et testables sur SQLite (aucune dépendance MQTT).
"""
import logging
from datetime import date, datetime, timedelta, timezone
from email.mime.text import MIMEText

import aiosmtplib
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from models import Lot, Alert, Warehouse

log = logging.getLogger("alerting")

LOT_EXPIRED = "LOT_EXPIRED"
CONDITION_ALERT_TYPES = ("TEMP_OUT_OF_RANGE", "HUMIDITY_OUT_OF_RANGE")


# ── Envoi d'email ────────────────────────────────────────────────────────────
async def send_alert_email(to: str, subject: str, body: str) -> bool:
    """Envoie un email d'alerte. Renvoie True si l'envoi a réussi.

    Les erreurs SMTP sont journalisées mais n'interrompent jamais le traitement
    (l'alerte reste en base avec email_sent=False).
    """
    try:
        msg = MIMEText(body, "plain", "utf-8")
        msg["Subject"] = subject
        msg["From"] = settings.alert_sender
        msg["To"] = to
        await aiosmtplib.send(msg, hostname=settings.smtp_host, port=settings.smtp_port)
        log.info("Email envoyé à %s : %s", to, subject)
        return True
    except Exception as exc:  # pragma: no cover - dépend de l'infra SMTP
        log.error("Échec envoi email à %s : %s", to, exc)
        return False


# ── O1 : péremption des lots (> EXPIRY_DAYS) + email ──────────────────────────
async def mark_expired_lots(db: AsyncSession) -> int:
    """Passe à PERIME tout lot dont la date de stockage dépasse EXPIRY_DAYS.

    PERIME est prioritaire sur EN_ALERTE et CONFORME. Ne crée PAS d'alerte ni
    d'email (utilisé sur le chemin de lecture rapide). Renvoie le nb de lignes.
    """
    cutoff = date.today() - timedelta(days=settings.expiry_days)
    result = await db.execute(
        update(Lot)
        .where(Lot.storage_date <= cutoff, Lot.status != "PERIME")
        .values(status="PERIME")
    )
    await db.commit()
    return result.rowcount or 0


async def check_expired_lots(db: AsyncSession, *, notify: bool = True) -> list[Alert]:
    """Vérifie la péremption et lève une alerte LOT_EXPIRED (1 par lot, dédup).

    1. marque PERIME les lots trop anciens ;
    2. pour chaque lot périmé SANS alerte LOT_EXPIRED existante, crée l'alerte
       et (si notify) envoie un email au responsable de l'entrepôt.

    La détection se base sur l'absence d'alerte LOT_EXPIRED (et non sur la
    transition de statut), donc reste correcte même si le statut a déjà été
    passé à PERIME par le chemin de lecture paresseux.
    """
    await mark_expired_lots(db)
    cutoff = date.today() - timedelta(days=settings.expiry_days)

    already = await db.execute(
        select(Alert.lot_id).where(Alert.alert_type == LOT_EXPIRED, Alert.lot_id.is_not(None))
    )
    alerted_lot_ids = {row[0] for row in already.all()}

    expired = await db.execute(
        select(Lot).where(Lot.storage_date <= cutoff)
    )
    new_alerts: list[Alert] = []
    for lot in expired.scalars().all():
        if lot.id in alerted_lot_ids:
            continue
        age_days = (date.today() - lot.storage_date).days
        alert = Alert(
            warehouse_id=lot.warehouse_id,
            lot_id=lot.id,
            alert_type=LOT_EXPIRED,
            severity="WARNING",
            message=f"Lot {lot.id} périmé : stocké depuis {age_days} jours "
                    f"(> {settings.expiry_days} j). Expédition à proscrire.",
        )
        db.add(alert)
        await db.flush()
        new_alerts.append(alert)
    await db.commit()

    if notify:
        for alert in new_alerts:
            await _notify_expired(db, alert)
    return new_alerts


async def _notify_expired(db: AsyncSession, alert: Alert) -> None:
    wh = (await db.execute(
        select(Warehouse).where(Warehouse.id == alert.warehouse_id)
    )).scalar_one_or_none()
    if not wh or not wh.manager_email:
        return
    subject = f"[FutureKawa] Lot périmé — {alert.lot_id} ({settings.country})"
    body = (
        f"Pays : {settings.country}\n"
        f"Entrepôt : {wh.code}\n"
        f"Lot : {alert.lot_id}\n"
        f"{alert.message}\n"
        f"Action attendue : retirer le lot de la rotation FIFO et le déclasser.\n"
        f"Horodatage : {datetime.now(timezone.utc).isoformat()}\n"
    )
    if await send_alert_email(wh.manager_email, subject, body):
        await db.execute(update(Alert).where(Alert.id == alert.id).values(email_sent=True))
        await db.commit()


# ── O2 : synchronisation du statut métier des lots ───────────────────────────
async def sync_lot_alert_status(db: AsyncSession) -> None:
    """Reflète l'état des conditions de stockage sur le statut des lots.

    - Un lot dont l'entrepôt a une alerte conditions (T°/H) ACTIVE passe
      EN_ALERTE (sauf s'il est PERIME : la péremption est prioritaire).
    - Quand l'entrepôt n'a plus d'alerte active, ses lots EN_ALERTE
      redeviennent CONFORME.
    """
    active = await db.execute(
        select(Alert.warehouse_id)
        .where(
            Alert.alert_type.in_(CONDITION_ALERT_TYPES),
            Alert.resolved_at.is_(None),
        )
        .distinct()
    )
    alerted_wh = {row[0] for row in active.all()}

    if alerted_wh:
        # CONFORME -> EN_ALERTE pour les entrepôts en alerte conditions
        await db.execute(
            update(Lot)
            .where(Lot.warehouse_id.in_(alerted_wh), Lot.status == "CONFORME")
            .values(status="EN_ALERTE")
        )
    # EN_ALERTE -> CONFORME pour les entrepôts sans alerte active
    revert = update(Lot).where(Lot.status == "EN_ALERTE")
    if alerted_wh:
        revert = revert.where(Lot.warehouse_id.not_in(alerted_wh))
    await db.execute(revert.values(status="CONFORME"))
    await db.commit()


# ── O3 : point d'entrée des vérifications périodiques ─────────────────────────
async def run_periodic_checks(session_factory) -> None:
    """Exécute péremption + synchronisation de statut dans une session dédiée."""
    async with session_factory() as db:
        try:
            new = await check_expired_lots(db, notify=True)
            await sync_lot_alert_status(db)
            if new:
                log.info("Vérification périodique : %d nouveau(x) lot(s) périmé(s)", len(new))
        except Exception as exc:  # pragma: no cover - robustesse scheduler
            log.error("Erreur vérification périodique : %s", exc)
