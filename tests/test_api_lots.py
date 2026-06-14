"""
Tests d'intégration API : routes /lots et /warehouses.
Couvre IT-10 à IT-14 du plan de tests.

Pré-requis : docker compose up (backends pays lancés)
Lancer : pytest tests/test_api_lots.py -v
"""
import pytest
import httpx

BASE_BR = "http://localhost:8001"
BASE_EC = "http://localhost:8002"
BASE_CO = "http://localhost:8003"


@pytest.fixture(scope="module")
def client():
    return httpx.Client(base_url=BASE_BR, timeout=10)


class TestWarehouses:
    """IT-01 à IT-03 : routes entrepôts."""

    def test_IT01_list_warehouses(self, client):
        """GET /warehouses/ → HTTP 200, liste non vide."""
        r = client.get("/warehouses/")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_IT02_get_warehouse_by_id(self, client):
        """GET /warehouses/1 → HTTP 200, objet valide."""
        r = client.get("/warehouses/1")
        assert r.status_code == 200
        data = r.json()
        assert "code" in data
        assert "country" in data

    def test_IT03_get_warehouse_not_found(self, client):
        """GET /warehouses/9999 → HTTP 404."""
        r = client.get("/warehouses/9999")
        assert r.status_code == 404


class TestLots:
    """IT-10 à IT-14 : routes lots."""

    def test_IT10_lots_sorted_fifo(self, client):
        """GET /lots/ → triés par date de stockage ASC (FIFO)."""
        r = client.get("/lots/")
        assert r.status_code == 200
        lots = r.json()
        if len(lots) >= 2:
            dates = [lot["storage_date"] for lot in lots]
            assert dates == sorted(dates), "Lots non triés en ordre FIFO"

    def test_IT11_filter_conforme(self, client):
        """GET /lots/?status=CONFORME → uniquement CONFORME."""
        r = client.get("/lots/?status=CONFORME")
        assert r.status_code == 200
        for lot in r.json():
            assert lot["status"] == "CONFORME"

    def test_IT12_filter_perime(self, client):
        """GET /lots/?status=PERIME → uniquement PERIME."""
        r = client.get("/lots/?status=PERIME")
        assert r.status_code == 200
        for lot in r.json():
            assert lot["status"] == "PERIME"

    def test_IT13_create_lot(self, client):
        """POST /lots/ → HTTP 201, lot créé avec ID retourné."""
        payload = {
            "id": "BR-LOT-TEST-999",
            "warehouse_id": 1,
            "storage_date": "2024-01-15",
            "variete": "Arabica",
            "poids_kg": 250.0,
        }
        r = client.post("/lots/", json=payload)
        assert r.status_code == 201
        data = r.json()
        assert data["id"] == "BR-LOT-TEST-999"
        assert data["status"] == "CONFORME"

    def test_IT14_get_lot_not_found(self, client):
        """GET /lots/INCONNU → HTTP 404."""
        r = client.get("/lots/INCONNU-LOT-9999")
        assert r.status_code == 404


class TestAlerts:
    """IT-20 à IT-22 : routes alertes."""

    def test_IT20_list_alerts(self, client):
        """GET /alerts/ → HTTP 200, liste."""
        r = client.get("/alerts/")
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_IT21_filter_active_alerts(self, client):
        """GET /alerts/?active_only=true → uniquement resolved_at = null."""
        r = client.get("/alerts/?active_only=true")
        assert r.status_code == 200
        for alert in r.json():
            assert alert["resolved_at"] is None


class TestMeasurements:
    """IT-30 : routes mesures."""

    def test_IT30_list_measurements(self, client):
        """GET /measurements/?warehouse_id=1&limit=10 → HTTP 200, ≤ 10 résultats."""
        r = client.get("/measurements/?warehouse_id=1&limit=10")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        assert len(data) <= 10


class TestHealth:
    """Sanity checks."""

    def test_health_br(self):
        r = httpx.get(f"{BASE_BR}/health", timeout=5)
        assert r.status_code == 200
        assert r.json()["country"] == "BR"

    def test_health_ec(self):
        r = httpx.get(f"{BASE_EC}/health", timeout=5)
        assert r.status_code == 200
        assert r.json()["country"] == "EC"

    def test_health_co(self):
        r = httpx.get(f"{BASE_CO}/health", timeout=5)
        assert r.status_code == 200
        assert r.json()["country"] == "CO"
