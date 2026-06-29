"""
Logique métier pure de l'alerting (sans dépendance MQTT/SQL).

Isolée ici pour être testable unitairement sans installer aiomqtt,
sqlalchemy ou asyncpg. Réutilisée par le subscriber et les tests CI.
"""

# Plages physiques plausibles d'un capteur DHT22 (cf. documentation-iot.md §6).
# Toute valeur en dehors est considérée comme une lecture capteur aberrante.
TEMP_BOUNDS = (-10.0, 60.0)   # °C
HUMIDITY_BOUNDS = (0.0, 100.0)  # %

# Hystérésis : on déclenche l'alerte au-delà de la tolérance, mais on ne la
# clôt que lorsque la mesure revient nettement dans la plage (≤ 0.8×tolérance).
# Cette bande morte évite le « flapping » (alerte créée/résolue en boucle) quand
# une valeur oscille juste autour du seuil.
HYSTERESIS_CLEAR_FACTOR = 0.8


def compute_severity(deviation: float, tolerance: float) -> str | None:
    """Renvoie la sévérité d'une dérive par rapport à une tolérance.

    - deviation <= tolerance              -> None     (dans la plage acceptable)
    - tolerance < deviation <= 1.5×tol    -> WARNING
    - deviation > 1.5×tolerance           -> CRITICAL
    """
    if deviation <= tolerance:
        return None
    if deviation <= 1.5 * tolerance:
        return "WARNING"
    return "CRITICAL"


def should_clear(deviation: float, tolerance: float,
                 clear_factor: float = HYSTERESIS_CLEAR_FACTOR) -> bool:
    """Indique si une alerte conditions doit être auto-résolue (hystérésis).

    True seulement si la mesure est revenue franchement dans la plage
    (déviation ≤ clear_factor × tolérance), pas juste sous le seuil de
    déclenchement — sinon l'alerte oscillerait.
    """
    return deviation <= tolerance * clear_factor


def is_plausible(temperature_c: float | None, humidity_pct: float | None) -> bool:
    """Valide qu'une mesure capteur est dans des bornes physiques réalistes.

    Protège la base et l'alerting des valeurs aberrantes d'un DHT22 défaillant
    (mitigation documentée dans le plan de risques IoT).
    """
    if temperature_c is None or humidity_pct is None:
        return False
    t_min, t_max = TEMP_BOUNDS
    h_min, h_max = HUMIDITY_BOUNDS
    return (t_min <= temperature_c <= t_max) and (h_min <= humidity_pct <= h_max)
