# Module IoT — Firmware ESP32 + DHT22 (MicroPython)

Prototype matériel réel du capteur d'entrepôt. Publie température/humidité sur le
broker MQTT local du pays, avec le **même contrat** que le simulateur logiciel
(`simulator/`) : la stack serveur fonctionne à l'identique avec le capteur réel
ou le simulateur.

- **Topic** : `futurekawa/{COUNTRY}/warehouse/{WAREHOUSE}/measurement`
- **Payload** : `{"temperature_c": 29.4, "humidity_pct": 54.8}`
- **Fréquence** : 30 s (configurable)

> Schéma de câblage détaillé, choix matériel et analyse de risques :
> [`architecture/documentation-iot.md`](../architecture/documentation-iot.md).

## Matériel

| Composant | Référence |
|-----------|-----------|
| Microcontrôleur | ESP32 WROOM-32 (Wi-Fi intégré) |
| Capteur | DHT22 / AM2302 |
| Résistance | pull-up 10 kΩ entre DATA et VCC (**obligatoire**) |

Câblage : `3.3V → VCC`, `GND → GND`, `GPIO4 → DATA` (+ pull-up 10 kΩ DATA↔VCC).

## Fichiers

| Fichier | Rôle |
|---------|------|
| `main.py` | Firmware (lecture capteur, Wi-Fi/MQTT, buffer, reconnexion) |
| `config.example.py` | Modèle de configuration à copier en `config.py` |

## Flash (étapes)

1. **Installer MicroPython** sur l'ESP32 :
   ```bash
   pip install esptool
   esptool.py --port /dev/ttyUSB0 erase_flash
   esptool.py --port /dev/ttyUSB0 write_flash 0x1000 ESP32_GENERIC-*.bin
   ```
2. **Configurer** : copier `config.example.py` en `config.py` et renseigner
   Wi-Fi, IP du broker, `COUNTRY`, `WAREHOUSE`.
3. **Téléverser** le code (avec [mpremote](https://docs.micropython.org/en/latest/reference/mpremote.html)) :
   ```bash
   mpremote connect /dev/ttyUSB0 fs cp config.py :config.py
   mpremote connect /dev/ttyUSB0 fs cp main.py   :main.py
   mpremote connect /dev/ttyUSB0 reset
   ```
4. **Observer** : `mpremote connect /dev/ttyUSB0 repl` → lignes `Publié: {...}`.

## Démo sans matériel

Pas de carte sous la main ? Le service `simulator-*` du `docker-compose.yml`
publie le même flux MQTT — la démo complète tourne sans ESP32.

## Robustesse

- Reconnexion Wi-Fi / MQTT avec backoff exponentiel (5 s → 60 s).
- Buffer local FIFO (100 mesures ≈ 50 min) si le broker est injoignable.
- Rejet des lectures aberrantes du capteur (mêmes bornes physiques que le
  subscriber serveur, `subscriber/severity.py`).
