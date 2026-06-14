"""
Simulateur de capteurs IoT DHT22 (ESP32 virtuel).
Publie des mesures MQTT toutes les 30 secondes avec dérive périodique
pour déclencher des alertes réalistes.
"""
import asyncio
import json
import logging
import math
import os
import random
import time

import aiomqtt

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

COUNTRY    = os.getenv("COUNTRY", "BR")
MQTT_HOST  = os.getenv("MQTT_HOST", "mosquitto")
MQTT_PORT  = int(os.getenv("MQTT_PORT", "1883"))
INTERVAL   = int(os.getenv("INTERVAL_S", "30"))

# Profils par pays : (cible_temp, cible_hum, tolerance_temp, tolerance_hum)
COUNTRY_PROFILE = {
    "BR": (29.0, 55.0, 3.0, 2.0),
    "EC": (31.0, 60.0, 3.0, 2.0),
    "CO": (26.0, 80.0, 3.0, 2.0),
}

WAREHOUSES = {
    "BR": ["BR-WH-001", "BR-WH-002"],
    "EC": ["EC-WH-001", "EC-WH-002"],
    "CO": ["CO-WH-001", "CO-WH-002"],
}


class SensorSimulator:
    """Simule un capteur DHT22 avec drift sinusoïdal et anomalies ponctuelles."""

    def __init__(self, warehouse_code: str, target_t: float, target_h: float,
                 tol_t: float, tol_h: float):
        self.code = warehouse_code
        self.target_t = target_t
        self.target_h = target_h
        self.tol_t = tol_t
        self.tol_h = tol_h
        self.start_time = time.time()
        # Décalage aléatoire par entrepôt pour diversifier les séries
        self.phase = random.uniform(0, 2 * math.pi)

    def read(self) -> dict:
        elapsed = time.time() - self.start_time
        # Drift sinusoïdal lent (période ~20 min) ± 2× tolérance
        drift_t = math.sin(elapsed / 1200 + self.phase) * self.tol_t * 2
        drift_h = math.cos(elapsed / 900 + self.phase) * self.tol_h * 2
        # Bruit capteur gaussien
        noise_t = random.gauss(0, 0.3)
        noise_h = random.gauss(0, 0.5)
        temp = round(self.target_t + drift_t + noise_t, 1)
        hum  = round(self.target_h + drift_h + noise_h, 1)
        # Clamp à des valeurs physiquement plausibles
        temp = max(10.0, min(50.0, temp))
        hum  = max(10.0, min(99.0, hum))
        return {"temperature_c": temp, "humidity_pct": hum}


async def publish_forever(client: aiomqtt.Client, sensors: list[SensorSimulator]):
    while True:
        for sensor in sensors:
            data = sensor.read()
            topic = f"futurekawa/{COUNTRY}/warehouse/{sensor.code}/measurement"
            payload = json.dumps(data)
            await client.publish(topic, payload, qos=1)
            log.info("[%s] Publié → T=%.1f°C H=%.1f%%", sensor.code,
                     data["temperature_c"], data["humidity_pct"])
        await asyncio.sleep(INTERVAL)


async def main():
    profile = COUNTRY_PROFILE.get(COUNTRY, COUNTRY_PROFILE["BR"])
    wh_codes = WAREHOUSES.get(COUNTRY, WAREHOUSES["BR"])
    sensors = [
        SensorSimulator(code, *profile) for code in wh_codes
    ]
    log.info("Simulateur démarré — pays=%s entrepôts=%s intervalle=%ds",
             COUNTRY, wh_codes, INTERVAL)
    reconnect_delay = 5
    while True:
        try:
            async with aiomqtt.Client(MQTT_HOST, MQTT_PORT) as client:
                reconnect_delay = 5
                await publish_forever(client, sensors)
        except aiomqtt.MqttError as exc:
            log.error("MQTT déconnecté : %s — reconnexion dans %ds", exc, reconnect_delay)
            await asyncio.sleep(reconnect_delay)
            reconnect_delay = min(reconnect_delay * 2, 60)


if __name__ == "__main__":
    asyncio.run(main())
