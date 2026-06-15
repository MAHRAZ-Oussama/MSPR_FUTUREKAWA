# FutureKawa — Système de supervision des entrepôts de café

Architecture distribuée multi-pays (Brésil, Équateur, Colombie) avec monitoring IoT en temps réel.

---

## Prérequis

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installé et **démarré**
- Ports libres : `8000`, `8001`, `8002`, `8003`, `8025`, `8080`, `1025`

---

## Installation et démarrage

```bash
# 1. Cloner ou copier le projet, puis se placer dedans
cd "MSPR FutureKawa"

# 2. Construire et démarrer tous les services (3–5 min au premier lancement)
docker compose up --build
```

> Aucune installation de Python, Node.js ou autre dépendance n'est nécessaire — tout tourne dans Docker.

### Vérifier que tout fonctionne

Dans un second terminal, une fois les services démarrés :

```bash
curl http://localhost:8001/health   # {"status":"ok","country":"BR"}
curl http://localhost:8002/health   # {"status":"ok","country":"EC"}
curl http://localhost:8003/health   # {"status":"ok","country":"CO"}
curl http://localhost:8000/health   # {"status":"ok","service":"central"}
```

---

## URLs d'accès

| Service | URL | Description |
|---------|-----|-------------|
| **Interface Web** | http://localhost:8080 | Application utilisateur |
| Backend central | http://localhost:8000/docs | Swagger UI siège |
| API Brésil | http://localhost:8001/docs | Swagger UI BR |
| API Équateur | http://localhost:8002/docs | Swagger UI EC |
| API Colombie | http://localhost:8003/docs | Swagger UI CO |
| MailHog | http://localhost:8025 | Visualiser les emails d'alerte |

---

## Arrêt

```bash
# Arrêt simple (les données sont conservées)
docker compose down

# Arrêt + suppression des volumes (reset complet des données)
docker compose down -v
```

---

## Logs utiles

```bash
docker compose logs -f api-br          # Logs API Brésil
docker compose logs -f subscriber-br   # Logs subscriber MQTT Brésil
docker compose logs -f simulator-br    # Logs simulateur IoT Brésil
```

---

## Architecture

```
Frontend (React) :8080
    └─► Backend Central (FastAPI) :8000
            ├─► API Brésil :8001   ← PostgreSQL ← MQTT ← Simulateur IoT
            ├─► API Équateur :8002  ← PostgreSQL ← MQTT ← Simulateur IoT
            └─► API Colombie :8003 ← PostgreSQL ← MQTT ← Simulateur IoT
```

Chaque pays dispose de son propre réseau Docker isolé (`br-net`, `ec-net`, `co-net`).
Le backend central agrège les données via `central-net`.

---

## Fonctionnalités

- **Tableau de bord global** : vue consolidée tous pays, rafraîchissement 30s
- **Mode dégradé** : si un backend pays est indisponible, les autres restent accessibles
- **Lots FIFO** : tri par date de stockage croissante, statuts CONFORME / EN_ALERTE / PÉRIMÉ
- **Courbes temps réel** : température et humidité par lot (Chart.js)
- **Alertes intelligentes** : déduplication anti-flood (1 email / 30 min / entrepôt / type)
- **Simulateur IoT** : drift sinusoïdal + bruit gaussien pour déclencher des alertes réalistes

---

## Structure du projet

```
├── backend-pays/      # FastAPI partagé (BR, EC, CO via variable COUNTRY)
├── subscriber/        # Consumer MQTT → PostgreSQL + alerting email
├── simulator/         # Simulateur capteurs DHT22 (ESP32 virtuel)
├── backend-central/   # Agrégateur siège — appels parallèles asyncio
├── frontend/          # React + Vite + Chart.js
├── mosquitto/         # Config broker Eclipse Mosquitto 2.x
└── docker-compose.yml # Orchestration des 18 services
```

---

## Seuils par pays

| Pays     | Temp. cible | Hum. cible | Tolérance T | Tolérance H |
|----------|-------------|------------|-------------|-------------|
| Brésil   | 29°C        | 55%        | ±3°C        | ±2%         |
| Équateur | 31°C        | 60%        | ±3°C        | ±2%         |
| Colombie | 26°C        | 80%        | ±3°C        | ±2%         |

**Sévérité** : WARNING si écart > tolérance, CRITICAL si écart > 1.5× tolérance.
