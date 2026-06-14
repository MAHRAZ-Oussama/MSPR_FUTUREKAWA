"""
Tests d'intégration : backend central (siège).
Couvre IT-40 à IT-44 du plan de tests.

Pré-requis : docker compose up (stack complète lancée)
Lancer : pytest tests/test_api_central.py -v
"""
import pytest
import httpx

BASE_CENTRAL = "http://localhost:8000"


@pytest.fixture(scope="module")
def client():
    return httpx.Client(base_url=BASE_CENTRAL, timeout=15)


class TestCentralHealth:
    def test_health(self, client):
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json()["service"] == "central"


class TestDashboardSummary:
    """IT-40 à IT-41 : consolidation dashboard."""

    def test_IT40_dashboard_all_countries_up(self, client):
        """GET /dashboard/summary → HTTP 200, tous pays dans countries."""
        r = client.get("/dashboard/summary")
        assert r.status_code == 200
        data = r.json()
        assert "total_lots" in data
        assert "lots_conformes" in data
        assert "lots_en_alerte" in data
        assert "lots_perimes" in data
        assert "active_alerts" in data
        assert "countries" in data
        assert "degraded_countries" in data

    def test_IT40_total_lots_is_sum_of_countries(self, client):
        """total_lots = somme des lots de chaque pays disponible."""
        r = client.get("/dashboard/summary")
        data = r.json()
        country_sum = sum(c.get("total_lots", 0) for c in data["countries"])
        assert data["total_lots"] == country_sum


class TestCountryRoutes:
    """IT-42 à IT-43 : routes par pays."""

    def test_IT42_get_br_lots(self, client):
        """GET /countries/BR/lots → HTTP 200, liste."""
        r = client.get("/countries/BR/lots")
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_IT42_get_ec_lots(self, client):
        """GET /countries/EC/lots → HTTP 200."""
        r = client.get("/countries/EC/lots")
        assert r.status_code == 200

    def test_IT42_get_co_lots(self, client):
        """GET /countries/CO/lots → HTTP 200."""
        r = client.get("/countries/CO/lots")
        assert r.status_code == 200

    def test_IT43_unknown_country(self, client):
        """GET /countries/ZZ/lots → HTTP 404."""
        r = client.get("/countries/ZZ/lots")
        assert r.status_code == 404

    def test_country_lots_sorted_fifo(self, client):
        """Lots BR triés par date de stockage ASC."""
        r = client.get("/countries/BR/lots")
        lots = r.json()
        if len(lots) >= 2:
            dates = [lot["storage_date"] for lot in lots]
            assert dates == sorted(dates)


class TestAlertsAggregation:
    """IT-44 : agrégation alertes tous pays."""

    def test_IT44_alerts_have_country_field(self, client):
        """GET /alerts → chaque alerte a un champ 'country'."""
        r = client.get("/alerts")
        assert r.status_code == 200
        data = r.json()
        assert "alerts" in data
        for alert in data["alerts"]:
            assert "country" in alert
            assert alert["country"] in ("BR", "EC", "CO")


class TestLotDetail:
    """Test consultation détail lot."""

    def test_lot_detail_includes_measurements(self, client):
        """GET /countries/BR/lots/{id} → champ measurements présent."""
        lots_r = client.get("/countries/BR/lots")
        lots = lots_r.json()
        if not lots:
            pytest.skip("Aucun lot disponible")
        lot_id = lots[0]["id"]
        r = client.get(f"/countries/BR/lots/{lot_id}")
        assert r.status_code == 200
        data = r.json()
        assert "measurements" in data
        assert isinstance(data["measurements"], list)
