"""
Tests unitaires : calcul de sévérité des alertes.
Couvre les cas UT-01 à UT-06 du plan de tests.

Lancer : pytest tests/test_unit_severity.py -v
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../subscriber"))

from subscriber import compute_severity


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
