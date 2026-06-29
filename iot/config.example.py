# Copier ce fichier en `config.py` et l'adapter avant de flasher l'ESP32.
# config.py ne doit PAS être versionné (contient le mot de passe Wi-Fi).

WIFI_SSID = "FutureKawa-WH"
WIFI_PASSWORD = "votre_mot_de_passe"

MQTT_BROKER = "192.168.1.10"   # IP du broker Mosquitto local au pays
MQTT_PORT = 1883

COUNTRY = "BR"                  # BR | EC | CO
WAREHOUSE = "BR-WH-001"        # doit exister en base (table warehouses.code)

SENSOR_PIN = 4                 # GPIO relié à la broche DATA du DHT22
INTERVAL_S = 30                # période de publication (s)
