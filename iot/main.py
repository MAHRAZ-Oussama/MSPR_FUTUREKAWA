"""
FutureKawa — Firmware capteur IoT (MicroPython / ESP32 + DHT22)

Lit la température et l'humidité d'un DHT22 et publie les mesures sur le broker
MQTT local du pays. Conçu pour des entrepôts à réseau instable :
- reconnexion Wi-Fi / MQTT avec backoff exponentiel ;
- buffer local borné si le broker est injoignable ;
- rejet des lectures aberrantes (capteur défaillant).

Topic   : futurekawa/{COUNTRY}/warehouse/{WAREHOUSE}/measurement
Payload : {"temperature_c": <float>, "humidity_pct": <float>}

Identique au contrat consommé par le subscriber serveur — le simulateur Python
(`simulator/`) produit exactement le même flux pour la démo sans matériel.

Déploiement : voir iot/README.md. Renseigner config.py (copié de config.example.py).
"""
import time

import dht
import machine
import network
import ujson
from umqtt.simple import MQTTClient

try:
    import config  # config.py local, non versionné (cf. config.example.py)
except ImportError:  # valeurs de repli pour un premier flash/démo
    class config:  # type: ignore
        WIFI_SSID = "FutureKawa-WH"
        WIFI_PASSWORD = "changeme"
        MQTT_BROKER = "192.168.1.10"
        MQTT_PORT = 1883
        COUNTRY = "BR"
        WAREHOUSE = "BR-WH-001"
        SENSOR_PIN = 4
        INTERVAL_S = 30

TOPIC = "futurekawa/{}/warehouse/{}/measurement".format(config.COUNTRY, config.WAREHOUSE)
CLIENT_ID = "esp32-{}".format(config.WAREHOUSE)

MAX_BUFFER = 100            # ~50 min de données à 30 s d'intervalle
BACKOFF_MAX = 60           # plafond du backoff (s)

# Bornes physiques plausibles du DHT22 (cf. documentation-iot.md §6).
TEMP_MIN, TEMP_MAX = -10.0, 60.0
HUM_MIN, HUM_MAX = 0.0, 100.0

sensor = dht.DHT22(machine.Pin(config.SENSOR_PIN))
_buffer = []


def is_plausible(temp, hum):
    return (temp is not None and hum is not None
            and TEMP_MIN <= temp <= TEMP_MAX
            and HUM_MIN <= hum <= HUM_MAX)


def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        wlan.connect(config.WIFI_SSID, config.WIFI_PASSWORD)
        for _ in range(20):
            if wlan.isconnected():
                break
            time.sleep(1)
    if wlan.isconnected():
        print("Wi-Fi OK:", wlan.ifconfig())
        return True
    print("Wi-Fi indisponible")
    return False


def connect_mqtt(retries=5):
    delay = 5
    for attempt in range(retries):
        try:
            client = MQTTClient(CLIENT_ID, config.MQTT_BROKER, config.MQTT_PORT, keepalive=60)
            client.connect()
            print("MQTT connecté à", config.MQTT_BROKER)
            return client
        except Exception as exc:
            print("MQTT tentative {} échouée: {}".format(attempt + 1, exc))
            time.sleep(delay)
            delay = min(delay * 2, BACKOFF_MAX)
    return None


def read_sensor():
    sensor.measure()
    temp = sensor.temperature()
    hum = sensor.humidity()
    if not is_plausible(temp, hum):
        print("Lecture capteur rejetée:", temp, hum)
        return None
    return ujson.dumps({"temperature_c": temp, "humidity_pct": hum})


def flush_buffer(client):
    """Tente d'écouler le buffer local (FIFO) une fois la connexion rétablie."""
    while _buffer:
        try:
            client.publish(TOPIC, _buffer[0], qos=1)
            _buffer.pop(0)
        except Exception:
            break


def main():
    connect_wifi()
    client = connect_mqtt()
    delay = 5

    while True:
        try:
            payload = read_sensor()
            if payload is None:
                time.sleep(config.INTERVAL_S)
                continue

            if client:
                flush_buffer(client)
                client.publish(TOPIC, payload, qos=1)
                print("Publié:", payload)
                delay = 5
            else:
                if len(_buffer) < MAX_BUFFER:
                    _buffer.append(payload)
                else:
                    print("Buffer plein, mesure perdue")
                if not connect_wifi():
                    pass
                client = connect_mqtt()

        except Exception as exc:
            print("Erreur cycle:", exc)
            client = None
            time.sleep(delay)
            delay = min(delay * 2, BACKOFF_MAX)

        time.sleep(config.INTERVAL_S)


if __name__ == "__main__":
    main()
