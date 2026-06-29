"""
Tests unitaires : calcul de sévérité des alertes.
Couvre les cas UT-01 à UT-06 du plan de tests.

Lancer : pytest tests/test_unit_severity.py -v
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../subscriber"))

from severity import compute_severity, is_plausible, should_clear


class TestComputeSeverity:
    """UT-01 à UT-06 : règles de sévérité."""

    def test_UT01_no_alert_within_tolerance(self):
        """deviation ≤ tolerance → pas d'alerte."""
        assert compute_severity(2.0, 3.0) is None

    def test_UT02_warning_between_tolerance_and_1_5x(self):
        """tolerance < deviation ≤ 1.5×tolerance → WARNING."""
        assert compute_severity(3.5, 3.0) == "WARNING"

    def test_UT03_critical_above_1_5x_tolerance(self):
        """deviation > 1.5×tolerance → CRITICAL."""
        assert compute_severity(5.0, 3.0) == "CRITICAL"

    def test_UT04_equal_to_tolerance_no_alert(self):
        """Exactement égal à la tolérance → pas d'alerte (strict >)."""
        assert compute_severity(3.0, 3.0) is None

    def test_UT05_exactly_1_5x_is_warning(self):
        """Exactement 1.5× → WARNING (encore dans la zone WARNING)."""
        assert compute_severity(4.5, 3.0) == "WARNING"

    def test_UT06_just_above_1_5x_is_critical(self):
        """Dépasse légèrement 1.5× → CRITICAL."""
        assert compute_severity(4.51, 3.0) == "CRITICAL"

    def test_zero_deviation(self):
        """Pas de dérive → pas d'alerte."""
        assert compute_severity(0.0, 3.0) is None

    def test_large_deviation(self):
        """Très grande dérive → CRITICAL."""
        assert compute_severity(20.0, 3.0) == "CRITICAL"

    def test_small_tolerance(self):
        """Tolérance très petite, faible dérive → CRITICAL."""
        assert compute_severity(1.0, 0.5) == "CRITICAL"


class TestIsPlausible:
    """UT-07 à UT-09 : validation de plage physique des mesures capteur."""

    def test_UT07_normal_measurement_is_plausible(self):
        assert is_plausible(29.0, 55.0) is True

    def test_UT08_out_of_range_temperature_rejected(self):
        """Valeur aberrante (capteur DHT22 défaillant) → rejetée."""
        assert is_plausible(150.0, 55.0) is False
        assert is_plausible(-50.0, 55.0) is False

    def test_UT08_out_of_range_humidity_rejected(self):
        assert is_plausible(29.0, 120.0) is False
        assert is_plausible(29.0, -5.0) is False

    def test_UT09_none_values_rejected(self):
        assert is_plausible(None, 55.0) is False
        assert is_plausible(29.0, None) is False

    def test_boundaries_inclusive(self):
        """Les bornes exactes sont acceptées."""
        assert is_plausible(-10.0, 0.0) is True
        assert is_plausible(60.0, 100.0) is True


class TestShouldClear:
    """Hystérésis : auto-résolution uniquement après franc retour à la normale."""

    def test_clears_well_within_range(self):
        """Déviation nettement sous le seuil (≤ 0.8×tol) → on clôt."""
        assert should_clear(2.0, 3.0) is True   # 2.0 ≤ 2.4

    def test_holds_in_dead_band(self):
        """Déviation dans la bande morte (0.8×tol < dev ≤ tol) → on maintient."""
        assert should_clear(2.5, 3.0) is False  # 2.4 < 2.5 ≤ 3.0

    def test_holds_above_tolerance(self):
        """Toujours hors plage → pas de clôture."""
        assert should_clear(4.0, 3.0) is False

    def test_clears_at_exact_clear_threshold(self):
        assert should_clear(2.4, 3.0) is True   # exactement 0.8×3
