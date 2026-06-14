# FutureKawa — Système de supervision des entrepôts de café

Architecture distribuée multi-pays (Brésil, Équateur, Colombie) avec monitoring IoT en temps réel.

## Démarrage rapide

```bash
docker compose up --build
```

L'application est disponible sur :
- **Frontend** : http://localhost:8080
- **Backend central** : http://localhost:8000
- **API Brésil** : http://localhost:8001/docs
- **API Équateur** : http://localhost:8002/docs
- **API Colombie** : http://localhost:8003/docs
- **MailHog** (emails) : http://localhost:8025

## Architecture

```
Frontend (React) :8080
    └─► Backend Central (FastAPI) :8000
            ├─► API Brésil :8001   ← PostgreSQL ← MQTT ← Simulateur IoT
            ├─► API Équateur :8002  ← PostgreSQL ← MQTT ← Simulateur IoT
            └─► API Colombie :8003 ← PostgreSQL ← MQTT ← Simulateur IoT
```

## Fonctionnalités

- **Tableau de bord global** : vue consolidée tous pays, rafraîchissement 30s
- **Mode dégradé** : si un backend pays est indisponible, les autres restent accessibles
- **Lots FIFO** : tri par date de stockage croissante, statuts CONFORME / EN_ALERTE / PÉRIMÉ
- **Courbes temps réel** : température et humidité par lot (Chart.js)
- **Alertes intelligentes** : déduplication anti-flood (1 email / 30 min / entrepôt / type)
- **Simulateur IoT** : drift sinusoïdal + bruit gaussien pour déclencher des alertes réalistes

## Structure

```
├── backend-pays/      # FastAPI partagé (BR, EC, CO via env COUNTRY)
├── subscriber/        # Consumer MQTT → PostgreSQL + alerting email
├── simulator/         # Simulateur capteurs DHT22 (ESP32 virtuel)
├── backend-central/   # Agrégateur siège — appels parallèles asyncio
├── frontend/          # React + Vite + Chart.js
├── mosquitto/         # Config broker Eclipse Mosquitto 2.x
└── docker-compose.yml # Orchestration complète
```

## Seuils par pays

| Pays     | Temp. cible | Hum. cible | Tolérance T | Tolérance H |
|----------|-------------|------------|-------------|-------------|
| Brésil   | 29°C        | 55%        | ±3°C        | ±2%         |
| Équateur | 31°C        | 60%        | ±3°C        | ±2%         |
| Colombie | 26°C        | 80%        | ±3°C        | ±2%         |

**Sévérité** : WARNING si écart > tolérance, CRITICAL si écart > 1.5× tolérance.
