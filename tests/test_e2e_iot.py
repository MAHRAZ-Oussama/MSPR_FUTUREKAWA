"""
Tests end-to-end : cycle IoT complet (simulateur → MQTT → BDD → alerte).
Couvre E2E-01 et E2E-02 du plan de tests.

Pré-requis : docker compose up (stack complète lancée)
Lancer : pytest tests/test_e2e_iot.py -v -s
"""
import time
import json
import pytest
import httpx

try:
    import paho.mqtt.client as mqtt
    PAHO_AVAILABLE = True
except ImportError:
    PAHO_AVAILABLE = False

BASE_BR = "http://localhost:8001"
MQTT_HOST = "localhost"
MQTT_PORT = 1883


def publish_measurement(temp: float, hum: float, warehouse: str = "BR-WH-001"):
    """Publie une mesure MQTT directement depuis le test."""
    if not PAHO_AVAILABLE:
        pytest.skip("paho-mqtt non installé — installer avec: pip install paho-mqtt")
    client = mqtt.Client()
    client.connect(MQTT_HOST, MQTT_PORT, 60)
    topic = f"futurekawa/BR/warehouse/{warehouse}/measurement"
    payload = json.dumps({"temperature_c": temp, "humidity_pct": hum})
    client.publish(topic, payload, qos=1)
    client.disconnect()


class TestE2E_IoT:
    """E2E-01 : cycle complet mesure → alerte."""

    @pytest.mark.skipif(not PAHO_AVAILABLE, reason="paho-mqtt requis")
    def test_E2E01_measurement_persisted(self):
        """Une mesure publiée en MQTT apparaît dans l'API."""
        api = httpx.Client(base_url=BASE_BR, timeout=10)

        # Compter mesures avant
        before = api.get("/measurements/?warehouse_id=1&limit=1000").json()
        count_before = len(before)

        # Publier mesure normale
        publish_measurement(29.0, 55.0)
        time.sleep(3)  # Laisser le subscriber traiter

        after = api.get("/measurements/?warehouse_id=1&limit=1000").json()
        assert len(after) > count_before, "Mesure non persistée en BDD"

    @pytest.mark.skipif(not PAHO_AVAILABLE, reason="paho-mqtt requis")
    def test_E2E01_critical_alert_created(self):
        """Mesure hors plage CRITICAL → alerte créée en BDD."""
        api = httpx.Client(base_url=BASE_BR, timeout=10)

        # Résoudre toutes les alertes actives existantes
        alerts = api.get("/alerts/?active_only=true").json()
        for a in alerts:
            api.post(f"/alerts/{a['id']}/resolve")

        # Publier température CRITICAL (écart = 9°C >> 1.5×3 = 4.5°C)
        publish_measurement(38.0, 55.0)
        time.sleep(5)

        alerts_after = api.get("/alerts/?active_only=true").json()
        temp_alerts = [a for a in alerts_after if a["alert_type"] == "TEMP_OUT_OF_RANGE"]
        assert len(temp_alerts) >= 1
        assert temp_alerts[0]["severity"] == "CRITICAL"

    @pytest.mark.skipif(not PAHO_AVAILABLE, reason="paho-mqtt requis")
    def test_E2E01_antiflood_no_duplicate(self):
        """2 messages critiques en < 30 min → 1 seule alerte."""
        api = httpx.Client(base_url=BASE_BR, timeout=10)

        # S'assurer d'une alerte active TEMP
        alerts_before = [
            a for a in api.get("/alerts/?active_only=true").json()
            if a["alert_type"] == "TEMP_OUT_OF_RANGE"
        ]
        if not alerts_before:
            publish_measurement(38.0, 55.0)
            time.sleep(5)

        alerts_before = [
            a for a in api.get("/alerts/?active_only=true").json()
            if a["alert_type"] == "TEMP_OUT_OF_RANGE"
        ]
        count_before = len(alerts_before)

        # 2e message critique (anti-flood doit bloquer)
        publish_measurement(39.0, 55.0)
        time.sleep(5)

        alerts_after = [
            a for a in api.get("/alerts/?active_only=true").json()
            if a["alert_type"] == "TEMP_OUT_OF_RANGE"
        ]
        assert len(alerts_after) == count_before, "Anti-flood défaillant : doublon créé"

    def test_E2E01_resolve_alert(self):
        """POST /alerts/{id}/resolve → resolved_at renseigné."""
        api = httpx.Client(base_url=BASE_BR, timeout=10)
        alerts = api.get("/alerts/?active_only=true").json()
        if not alerts:
            pytest.skip("Aucune alerte active à résoudre")
        alert_id = alerts[0]["id"]
        r = api.post(f"/alerts/{alert_id}/resolve")
        assert r.status_code == 200
        assert r.json()["resolved_at"] is not None


class TestE2E_LotExpiry:
    """E2E-02 : lot périmé → statut automatique."""

    def test_E2E02_expired_lot_status(self):
        """Lot stocké > 365 jours → statut PERIME automatiquement."""
        import datetime
        api = httpx.Client(base_url=BASE_BR, timeout=10)

        old_date = (datetime.date.today() - datetime.timedelta(days=400)).isoformat()
        lot_id = "BR-LOT-EXPIRE-TEST"

        # Créer lot avec date ancienne
        api.post("/lots/", json={
            "id": lot_id,
            "warehouse_id": 1,
            "storage_date": old_date,
            "variete": "Test",
            "poids_kg": 100.0,
        })

        # Récupérer la liste (déclenche la MAJ statuts)
        lots = api.get("/lots/").json()
        lot = next((l for l in lots if l["id"] == lot_id), None)

        if lot:
            assert lot["status"] == "PERIME", f"Attendu PERIME, obtenu {lot['status']}"
