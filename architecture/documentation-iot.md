# Documentation Technique — Module IoT FutureKawa

## 1. Matériel retenu

| Composant | Référence | Rôle |
|-----------|-----------|------|
| Microcontrôleur | ESP32 (WROOM-32) | Wi-Fi intégré, MicroPython compatible |
| Capteur | DHT22 (AM2302) | Température −40…+80°C ±0,5°C / Humidité 0–100% ±2–5% |
| Alimentation | USB 5V ou batterie LiPo 3,7V + régulateur | Autonomie terrain |
| Breadboard | 400 points | Prototypage |
| Câblage | Jumpers mâle/mâle 20 cm | Connexions |

**Justification du DHT22 vs DHT11** : le DHT22 offre une plage de mesure plus large (−40°C à +80°C)
et une précision supérieure (±0,5°C vs ±2°C), essentielle pour les seuils d'alerte à ±3°C.

---

## 2. Schéma de câblage ESP32 + DHT22

```
ESP32 (WROOM-32)          DHT22
┌─────────────────┐       ┌──────────────┐
│           3.3V  │──────►│ Pin 1 (VCC)  │
│                 │       │              │
│           GND   │──────►│ Pin 4 (GND)  │
│                 │       │              │
│           GPIO4 │◄──────│ Pin 2 (DATA) │
│                 │       │              │
└─────────────────┘       └──────────────┘
                                │
                           [10kΩ pull-up]
                                │
                              3.3V
```

**Notes de câblage :**
- La résistance de pull-up 10 kΩ est **obligatoire** entre DATA et VCC
- GPIO4 est configurable via la variable `SENSOR_PIN` dans le code MicroPython
- Alimentation 3,3V uniquement (le DHT22 supporte aussi 5V mais l'ESP32 est en 3,3V)
- Distance capteur → microcontrôleur : maximum 20 m avec câble blindé

---

## 3. Code MicroPython (ESP32 réel)

> Le firmware est livré comme fichier **flashable autonome** dans
> [`iot/main.py`](../iot/main.py) (config dans `iot/config.example.py`,
> procédure de flash dans `iot/README.md`). L'extrait ci-dessous en présente
> la logique principale.

```python
# main.py — ESP32 + DHT22 + MQTT (MicroPython)
import dht
import machine
import network
import time
import ujson
from umqtt.simple import MQTTClient

# Configuration
WIFI_SSID     = "FutureKawa-WH"
WIFI_PASSWORD = "xxxxxxxx"
MQTT_BROKER   = "192.168.1.10"   # IP du Raspberry Pi / serveur local
MQTT_PORT     = 1883
COUNTRY       = "BR"
WAREHOUSE     = "BR-WH-001"
INTERVAL_S    = 30

TOPIC = f"futurekawa/{COUNTRY}/warehouse/{WAREHOUSE}/measurement"
BUFFER = []   # Buffer local QoS 1 (max 100 mesures)

sensor = dht.DHT22(machine.Pin(4))

def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(WIFI_SSID, WIFI_PASSWORD)
    for _ in range(20):
        if wlan.isconnected():
            print("Wi-Fi connecté :", wlan.ifconfig())
            return True
        time.sleep(1)
    return False

def connect_mqtt(retry=5):
    for attempt in range(retry):
        try:
            client = MQTTClient("esp32-" + WAREHOUSE, MQTT_BROKER, MQTT_PORT)
            client.connect()
            return client
        except Exception as e:
            print(f"MQTT erreur tentative {attempt+1}: {e}")
            time.sleep(min(5 * (2 ** attempt), 60))
    return None

def main():
    connect_wifi()
    client = connect_mqtt()
    delay = 5

    while True:
        try:
            sensor.measure()
            temp = sensor.temperature()
            hum  = sensor.humidity()
            payload = ujson.dumps({"temperature_c": temp, "humidity_pct": hum})

            # Vider le buffer si connexion disponible
            while BUFFER and client:
                client.publish(TOPIC, BUFFER.pop(0), qos=1)

            if client:
                client.publish(TOPIC, payload, qos=1)
                print(f"Publié : {payload}")
                delay = 5
            else:
                if len(BUFFER) < 100:
                    BUFFER.append(payload)
                client = connect_mqtt()

        except Exception as e:
            print("Erreur:", e)
            client = None
            time.sleep(delay)
            delay = min(delay * 2, 60)

        time.sleep(INTERVAL_S)

main()
```

---

## 4. Topics MQTT

| Topic | Direction | Fréquence | QoS | Payload |
|-------|-----------|-----------|-----|---------|
| `futurekawa/{PAYS}/warehouse/{CODE}/measurement` | ESP32 → Broker | 30 s | 1 | `{"temperature_c": 29.4, "humidity_pct": 54.8}` |

**Format payload JSON :**
```json
{
  "temperature_c": 29.4,
  "humidity_pct": 54.8
}
```

**Conventions de nommage :**
- `{PAYS}` : code ISO 2 lettres — `BR`, `EC`, `CO`
- `{CODE}` : code entrepôt — ex. `BR-WH-001`
- Le broker Mosquitto est local à chaque pays (pas de flux inter-pays)

---

## 5. Stratégie de reconnexion et gestion des erreurs

### Côté ESP32 (MicroPython)
| Scénario | Comportement |
|----------|-------------|
| Perte Wi-Fi | Reconnexion toutes les 30 s, backoff exponentiel (5s → 60s max) |
| Perte MQTT | Reconnexion backoff exponentiel (5s → 60s max) |
| Broker injoignable | Buffer local : 100 mesures stockées en RAM |
| Capteur défaillant | Log erreur, pas de publication, retry au cycle suivant |

### Côté Subscriber Python (serveur)
| Scénario | Comportement |
|----------|-------------|
| Déconnexion MQTT | Reconnexion avec backoff exponentiel (5s → 60s) |
| Payload invalide | Log warning, message ignoré, abonnement maintenu |
| Erreur BDD | Log erreur, transaction rollback, message perdu (pas de re-queue) |
| Erreur SMTP | Log erreur, alerte créée en BDD mais `email_sent = false` |

### QoS 1 — Garantie de livraison
Avec QoS 1 (`at least once`), si le subscriber redémarre, les messages MQTT sont re-délivrés
par Mosquitto (persistence activée). Cela peut créer des doublons en base dans des cas rares —
acceptable pour des mesures toutes les 30 s.

---

## 6. Limites et risques identifiés

| Risque | Probabilité | Impact | Mitigation |
|--------|-------------|--------|-----------|
| Capteur DHT22 défaillant (valeurs aberrantes) | Moyen | Haut | Validation plage physique : T ∈ [-10, 60°C], H ∈ [0, 100%] |
| Coupure réseau prolongée (> 100 mesures) | Moyen | Moyen | Buffer 100 pts = 50 min de données. Recommandation : SD card en v2 |
| Interférences Wi-Fi en entrepôt métallique | Élevé | Moyen | Préconiser antenne externe sur ESP32, ou LoRa en phase 2 |
| Condensation sur le capteur (humidité > 90%) | Faible | Faible | Boîtier IP54 recommandé en production |
| Dérive capteur (vieillissement) | Faible | Moyen | Étalonnage annuel recommandé |
