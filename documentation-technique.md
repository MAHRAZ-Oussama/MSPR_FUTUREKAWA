# Documentation Technique Complète — FutureKawa
**Version** : 1.0.0 | **Date** : Juin 2026 | **Statut** : Prototype avancé (MSPR)

---

## Table des matières

1. [Vue d'ensemble du projet](#1-vue-densemble-du-projet)
2. [Architecture globale](#2-architecture-globale)
3. [Structure des fichiers](#3-structure-des-fichiers)
4. [Base de données — Modèle de données](#4-base-de-données--modèle-de-données)
5. [Backend pays](#5-backend-pays)
6. [Subscriber MQTT](#6-subscriber-mqtt)
7. [Simulateur IoT](#7-simulateur-iot)
8. [Backend central (siège)](#8-backend-central-siège)
9. [Frontend Web](#9-frontend-web)
10. [Configuration Mosquitto](#10-configuration-mosquitto)
11. [Orchestration Docker Compose](#11-orchestration-docker-compose)
12. [Module IoT — ESP32 + DHT22](#12-module-iot--esp32--dht22)
13. [Tests](#13-tests)
14. [Pipeline CI/CD Jenkins](#14-pipeline-cicd-jenkins)
15. [Variables d'environnement](#15-variables-denvironnement)
16. [Guide de démarrage](#16-guide-de-démarrage)
17. [API Reference](#17-api-reference)
18. [Règles métier implémentées](#18-règles-métier-implémentées)

---

## 1. Vue d'ensemble du projet

FutureKawa est une solution applicative distribuée de supervision des entrepôts de café vert,
déployée dans 3 pays d'Amérique du Sud : **Brésil**, **Équateur** et **Colombie**.

### Objectifs remplis

| Objectif | Implémentation |
|----------|---------------|
| Suivi des lots par pays et entrepôt | API REST `/lots/` avec statuts CONFORME / EN_ALERTE / PÉRIMÉ |
| Traçabilité FIFO | Tri par `storage_date ASC`, index PostgreSQL dédié |
| Surveillance IoT température/humidité | Simulateur ESP32 virtuel → MQTT → PostgreSQL |
| Alertes automatiques | Subscriber Python avec anti-flood 30 min + emails SMTP |
| Architecture distribuée pays ↔ siège | 3 backends pays autonomes + 1 backend central agrégateur |
| Mode dégradé | Si un pays est indisponible, les autres restent accessibles |
| Interface Web | React + Vite + Chart.js (dashboard, lots, courbes, alertes) |
| Conteneurisation | Docker Compose — 18 services orchestrés |
| CI/CD | Jenkinsfile (build → tests → lint → packaging) |
| Tests | Pytest — unitaires, intégration, end-to-end |

---

## 2. Architecture globale

```
┌───────────────────────────────────────────────────────────────────┐
│                        SIÈGE (central)                             │
│  ┌────────────────┐    ┌──────────────────────────────────────┐   │
│  │  Frontend React│◄───│     Backend Central (FastAPI :8000)  │   │
│  │   Nginx :8080  │    │  asyncio.gather() → appels parallèles│   │
│  └────────────────┘    └──────────────────────────────────────┘   │
│                                     │ HTTP REST (timeout 10s)      │
└─────────────────────────────────────┼─────────────────────────────┘
                                      │
          ┌───────────────────────────┼──────────────────────┐
          │                           │                       │
   ┌──────▼──────┐           ┌────────▼─────┐      ┌────────▼──────┐
   │   BRÉSIL    │           │   ÉQUATEUR   │      │   COLOMBIE    │
   │  br-net     │           │   ec-net     │      │   co-net      │
   │             │           │              │      │               │
   │ simulator   │           │  simulator   │      │  simulator    │
   │    ↓ MQTT   │           │   ↓ MQTT     │      │   ↓ MQTT      │
   │ mosquitto   │           │  mosquitto   │      │  mosquitto    │
   │    ↓        │           │    ↓         │      │    ↓          │
   │ subscriber  │           │  subscriber  │      │  subscriber   │
   │    ↓ SQL    │           │    ↓ SQL     │      │    ↓ SQL      │
   │ postgres-br │           │  postgres-ec │      │  postgres-co  │
   │    ↑        │           │    ↑         │      │    ↑          │
   │ api-br:8001 │           │ api-ec:8002  │      │ api-co:8003   │
   │    +alerting│           │   +alerting  │      │   +alerting   │
   └─────────────┘           └──────────────┘      └───────────────┘
          │                           │                       │
          └───────────────────────────┴───────────────────────┘
                             central-net
```

### Principe d'isolation réseau

Chaque pays dispose de son propre réseau Docker isolé (`br-net`, `ec-net`, `co-net`).
Le backend central communique avec chaque API pays via le réseau `central-net`.
Le frontend est sur `central-net` et appelle le backend central uniquement.

---

## 3. Structure des fichiers

```
MSPR FutureKawa/
│
├── docker-compose.yml              # Orchestration 18 services
├── Jenkinsfile                     # Pipeline CI/CD Jenkins
├── README.md                       # Guide de démarrage rapide
├── .gitignore
│
├── backend-pays/                   # API FastAPI partagée (BR, EC, CO)
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py                     # Application FastAPI + seed + dashboard
│   ├── database.py                 # Connexion SQLAlchemy async
│   ├── models.py                   # ORM : Warehouse, Lot, Measurement, Alert
│   ├── schemas.py                  # Pydantic schemas I/O
│   ├── seed.py                     # Données initiales par pays
│   ├── init-db/init.sql            # Schéma SQL + index
│   └── routers/
│       ├── warehouses.py           # GET /warehouses/
│       ├── lots.py                 # GET/POST /lots/ + FIFO + expiry
│       ├── measurements.py         # GET /measurements/
│       └── alerts.py               # GET /alerts/ + POST /{id}/resolve
│
├── subscriber/                     # Consumer MQTT → PostgreSQL
│   ├── Dockerfile
│   ├── requirements.txt
│   └── subscriber.py               # aiomqtt + alerting + anti-flood + email
│
├── simulator/                      # Capteurs IoT virtuels (DHT22)
│   ├── Dockerfile
│   ├── requirements.txt
│   └── simulator.py                # Drift sinusoïdal + bruit gaussien
│
├── backend-central/                # Agrégateur siège
│   ├── Dockerfile
│   ├── requirements.txt
│   └── main.py                     # Routes consolidées + mode dégradé
│
├── frontend/                       # Interface Web React
│   ├── Dockerfile                  # Build multi-stage → Nginx
│   ├── nginx.conf                  # Reverse proxy /api → backend-central
│   ├── package.json                # React 18 + Vite + Chart.js
│   ├── vite.config.js
│   ├── index.html
│   └── src/
│       ├── main.jsx
│       ├── App.jsx                 # Routeur React
│       ├── api.js                  # Fonctions fetch vers /api/*
│       ├── components/
│       │   ├── NavBar.jsx
│       │   ├── StatusBadge.jsx     # Badge coloré CONFORME/EN_ALERTE/PERIME
│       │   └── Spinner.jsx
│       └── pages/
│           ├── Dashboard.jsx       # Vue globale siège
│           ├── CountryPage.jsx     # Lots FIFO par pays
│           ├── LotDetail.jsx       # Courbes T°/H% + stats
│           └── AlertsPage.jsx      # Alertes filtrables
│
├── mosquitto/
│   └── mosquitto.conf              # Broker MQTT (QoS 1, persistence)
│
├── tests/
│   ├── pytest.ini
│   ├── conftest.py
│   ├── requirements-test.txt
│   ├── test_unit_severity.py       # UT-01 à UT-06 : calcul sévérité
│   ├── test_api_lots.py            # IT-01 à IT-30 : API pays
│   ├── test_api_central.py         # IT-40 à IT-44 : API centrale
│   └── test_e2e_iot.py             # E2E-01, E2E-02 : cycle IoT complet
│
├── architecture/
│   ├── architecture.md             # Architecture globale + flux
│   ├── documentation-iot.md        # Câblage ESP32, topics MQTT, reconnexion
│   ├── plan-tests.md               # Stratégie + cas de test détaillés
│   ├── schema-automatisation-phase2.md
│   └── questionnaire-phase2.md
│
├── adr/
│   ├── ADR-001-stack-technique.md  # Justification Python/FastAPI/PostgreSQL/React
│   ├── ADR-002-architecture-distribuee.md
│   └── ADR-003-alerting-anti-flood.md
│
└── user-guide/
    └── guide-utilisateur.md        # Documentation métier
```

---

## 4. Base de données — Modèle de données

### Schéma SQL (`backend-pays/init-db/init.sql`)

```sql
-- Entrepôts
CREATE TABLE warehouses (
    id              SERIAL PRIMARY KEY,
    code            VARCHAR(20) UNIQUE NOT NULL,   -- ex: BR-WH-001
    country         VARCHAR(2)  NOT NULL,           -- BR / EC / CO
    manager_email   VARCHAR(150),
    target_temp_c   DECIMAL(4,1),                  -- Température cible
    target_humidity DECIMAL(4,1),                  -- Humidité cible
    tolerance_temp  DECIMAL(3,1),                  -- Tolérance ±°C
    tolerance_hum   DECIMAL(3,1)                   -- Tolérance ±%
);

-- Lots de café
CREATE TABLE lots (
    id           VARCHAR(50) PRIMARY KEY,           -- ex: BR-LOT-2024-001
    warehouse_id INT REFERENCES warehouses(id),
    storage_date DATE NOT NULL,                    -- Date entrée FIFO
    status       VARCHAR(20) DEFAULT 'CONFORME',   -- CONFORME/EN_ALERTE/PERIME
    variete      VARCHAR(50),                      -- Arabica, Robusta…
    poids_kg     DECIMAL(8,2)
);
CREATE INDEX idx_lots_storage_date ON lots(storage_date ASC);

-- Mesures IoT
CREATE TABLE measurements (
    id            BIGSERIAL PRIMARY KEY,
    warehouse_id  INT REFERENCES warehouses(id),
    measured_at   TIMESTAMPTZ DEFAULT NOW(),
    temperature_c DECIMAL(4,1),
    humidity_pct  DECIMAL(4,1)
);
CREATE INDEX idx_measurements_wh_time ON measurements(warehouse_id, measured_at DESC);

-- Alertes
CREATE TABLE alerts (
    id           SERIAL PRIMARY KEY,
    warehouse_id INT REFERENCES warehouses(id),
    lot_id       VARCHAR(50) REFERENCES lots(id),
    alert_type   VARCHAR(30) NOT NULL,             -- TEMP_OUT_OF_RANGE / HUMIDITY_OUT_OF_RANGE / LOT_EXPIRED
    severity     VARCHAR(10) NOT NULL,             -- WARNING / CRITICAL
    message      TEXT,
    created_at   TIMESTAMPTZ DEFAULT NOW(),
    resolved_at  TIMESTAMPTZ,                      -- NULL = alerte active
    email_sent   BOOLEAN DEFAULT FALSE
);
```

### Données initiales par pays (`backend-pays/seed.py`)

Au démarrage, le backend crée automatiquement les entrepôts et 10 lots de démonstration :

| Pays | Entrepôts | Cible T°C | Cible H% | Tolérance |
|------|-----------|-----------|----------|-----------|
| BR | BR-WH-001, BR-WH-002 | 29°C | 55% | ±3°C / ±2% |
| EC | EC-WH-001, EC-WH-002 | 31°C | 60% | ±3°C / ±2% |
| CO | CO-WH-001, CO-WH-002 | 26°C | 80% | ±3°C / ±2% |

Les lots de seed ont des dates aléatoires entre J-10 et J-400, avec calcul automatique
du statut PERIME si ancienneté > 365 jours.

---

## 5. Backend pays

**Fichiers** : `backend-pays/` | **Port interne** : 8000 | **Ports exposés** : 8001 (BR), 8002 (EC), 8003 (CO)

### `database.py` — Connexion asynchrone

```python
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://...")
engine = create_async_engine(DATABASE_URL, pool_size=10, max_overflow=20)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession)
```

- Pool de connexions : 10 connexions + 20 overflow
- Session injectée via `Depends(get_db)` dans chaque route

### `models.py` — ORM SQLAlchemy

4 modèles mappés sur les tables SQL :
- `Warehouse` — entrepôts avec seuils et emails
- `Lot` — lots avec statut et date FIFO
- `Measurement` — mesures IoT horodatées UTC
- `Alert` — alertes avec déduplication et email_sent

### `main.py` — Application FastAPI

**Lifespan** : exécute `seed()` au démarrage (crée tables + données initiales).

**Route `/dashboard/summary`** : avant de compter, met à jour automatiquement
les lots expirés (> 365 jours) via UPDATE SQL en une seule requête.

### `routers/lots.py` — Gestion FIFO + expiry

```python
# Mise à jour automatique des lots expirés
cutoff = date.today() - timedelta(days=365)
await db.execute(
    update(Lot)
    .where(Lot.storage_date <= cutoff, Lot.status != "EN_ALERTE")
    .values(status="PERIME")
)

# Tri FIFO systématique
stmt = select(Lot).order_by(Lot.storage_date.asc())
```

**Note** : les lots EN_ALERTE ne sont **pas** automatiquement mis en PERIME
(ils requièrent une action humaine de résolution d'abord).

### `routers/measurements.py` — Historique par lot

La route `/measurements/?lot_id=XX` retrouve l'entrepôt du lot puis filtre
les mesures depuis la date de stockage du lot :

```python
stmt = stmt.where(
    Measurement.warehouse_id == lot.warehouse_id,
    Measurement.measured_at >= lot.storage_date,
)
```

Les résultats sont retournés en ordre **chronologique** (inversement de DESC puis reversed).

---

## 6. Subscriber MQTT

**Fichier** : `subscriber/subscriber.py`

### Flux de traitement

```
Message MQTT reçu
       ↓
Parsing topic → extraction code entrepôt
       ↓
Lookup entrepôt en BDD (code → Warehouse)
       ↓
INSERT Measurement
       ↓
Calcul dérive temperature : |T_mesurée - T_cible|
Calcul dérive humidité    : |H_mesurée - H_cible|
       ↓
Pour chaque dérive > 0 :
    compute_severity(deviation, tolerance) → None / WARNING / CRITICAL
       ↓
Si severity non None :
    is_duplicate(warehouse_id, alert_type, fenêtre 30min) ?
    → OUI : silencieux (anti-flood)
    → NON : INSERT Alert + envoi email SMTP
```

### Calcul de sévérité

```python
def compute_severity(deviation: float, tolerance: float) -> str | None:
    if deviation <= tolerance:          return None       # dans la plage
    if deviation <= 1.5 * tolerance:    return "WARNING"  # dérive modérée
    return "CRITICAL"                                     # dérive sévère
```

### Anti-flood (déduplication)

```python
FLOOD_WINDOW = timedelta(minutes=30)

async def is_duplicate(db, warehouse_id, alert_type) -> bool:
    cutoff = datetime.now(timezone.utc) - FLOOD_WINDOW
    result = await db.execute(
        select(Alert).where(
            Alert.warehouse_id == warehouse_id,
            Alert.alert_type == alert_type,
            Alert.resolved_at.is_(None),      # alerte encore active
            Alert.created_at >= cutoff,        # dans la fenêtre 30min
        )
    )
    return result.scalar_one_or_none() is not None
```

**Effet** : maximum **1 email** par type d'alerte par entrepôt toutes les 30 minutes.
La déduplication est en base (pas en mémoire) pour survivre aux redémarrages.

### Reconnexion MQTT (backoff exponentiel)

```python
reconnect_delay = 5
while True:
    try:
        async with aiomqtt.Client(MQTT_HOST, MQTT_PORT) as client:
            reconnect_delay = 5          # reset au succès
            await client.subscribe(TOPIC, qos=1)
            async for message in client.messages:
                await process_measurement(...)
    except aiomqtt.MqttError:
        await asyncio.sleep(reconnect_delay)
        reconnect_delay = min(reconnect_delay * 2, 60)   # 5s → 10s → 20s → 40s → 60s
```

---

## 7. Simulateur IoT

**Fichier** : `simulator/simulator.py`

Simule des capteurs DHT22 embarqués sur ESP32 avec un comportement réaliste.

### Modèle de simulation

```python
class SensorSimulator:
    def read(self) -> dict:
        elapsed = time.time() - self.start_time
        # Drift sinusoïdal lent (période ~20 min) sur ±2× tolérance
        drift_t = math.sin(elapsed / 1200 + self.phase) * self.tol_t * 2
        drift_h = math.cos(elapsed / 900  + self.phase) * self.tol_h * 2
        # Bruit capteur gaussien (σ=0.3°C, σ=0.5%)
        noise_t = random.gauss(0, 0.3)
        noise_h = random.gauss(0, 0.5)
        temp = round(self.target_t + drift_t + noise_t, 1)
        hum  = round(self.target_h + drift_h + noise_h, 1)
        return {"temperature_c": temp, "humidity_pct": hum}
```

**Comportement** : la dérive sinusoïdale (amplitude = 2× tolérance) garantit que
le simulateur sort régulièrement de la zone acceptable et déclenche des alertes WARNING
puis CRITICAL, permettant de tester l'ensemble du système.

**Chaque entrepôt** a une phase de démarrage aléatoire (`random.uniform(0, 2π)`),
produisant des séries temporelles diversifiées.

### Topic MQTT publié

```
futurekawa/{COUNTRY}/warehouse/{CODE}/measurement
```

Payload JSON : `{"temperature_c": 29.4, "humidity_pct": 57.1}`
Fréquence : toutes les 30 secondes (configurable via `INTERVAL_S`)
QoS : 1 (at least once)

---

## 8. Backend central (siège)

**Fichier** : `backend-central/main.py` | **Port** : 8000

### Appels parallèles avec mode dégradé

```python
async def fetch(client, country, path) -> tuple[str, Any, bool]:
    try:
        resp = await client.get(COUNTRY_URLS[country] + path, timeout=TIMEOUT)
        resp.raise_for_status()
        return country, resp.json(), False   # succès
    except Exception:
        return country, None, True           # échec → mode dégradé

# Dashboard : appels simultanés vers les 3 pays
tasks = [fetch(client, c, "/dashboard/summary") for c in COUNTRY_URLS]
results = await asyncio.gather(*tasks)
```

Si un pays retourne une erreur (réseau, timeout, 5xx), il est ajouté à
`degraded_countries` et les données des autres pays restent disponibles.

### Routes exposées

| Méthode | Route | Description |
|---------|-------|-------------|
| GET | `/health` | Sanity check |
| GET | `/dashboard/summary` | Consolidation globale tous pays |
| GET | `/countries/{country}/lots` | Lots d'un pays (proxy + filtres) |
| GET | `/countries/{country}/lots/{lot_id}` | Détail lot + mesures |
| GET | `/countries/{country}/warehouses` | Entrepôts d'un pays |
| GET | `/alerts` | Alertes consolidées tous pays |
| POST | `/countries/{country}/alerts/{id}/resolve` | Résolution alerte |

### Enrichissement des alertes

Le backend central ajoute le champ `country` à chaque alerte remontée des backends pays,
permettant au frontend de filtrer et d'afficher le pays d'origine.

---

## 9. Frontend Web

**Fichiers** : `frontend/src/` | **Port** : 8080

### Pages

#### `Dashboard.jsx` — Vue siège
- Rafraîchissement automatique toutes les 30 secondes (`setInterval`)
- 5 compteurs globaux : lots totaux, conformes, en alerte, périmés, alertes actives
- 3 cartes pays cliquables (navigables vers la page pays)
- Bandeau dégradé si un pays est indisponible
- Indicateur "dernière MAJ" en temps réel

#### `CountryPage.jsx` — Lots par pays
- Tableau trié FIFO (date de stockage ASC)
- Filtres : statut (CONFORME / EN_ALERTE / PÉRIMÉ) + entrepôt
- Colonne "Ancienneté" en rouge si > 365 jours
- Navigation vers le détail d'un lot
- Rafraîchissement 30 secondes

#### `LotDetail.jsx` — Détail lot + graphes
- Informations générales du lot (ID, entrepôt, date, ancienneté, variété, poids, statut)
- Statistiques min/moy/max sur toute la période
- Graphe dual-axe via Chart.js :
  - Axe gauche rouge : température (°C)
  - Axe droit bleu : humidité (%)
  - Points masqués si > 200 mesures (lisibilité)
  - Tooltip interactif sur survol

#### `AlertsPage.jsx` — Alertes
- Filtres : sévérité (CRITICAL/WARNING) + type d'alerte + pays + actives uniquement
- Icônes par type : 🌡️ TEMP, 💧 HUMIDITY, ⏰ LOT_EXPIRED
- Bouton "Résoudre" pour marquer une alerte résolue
- Bandeau dégradé si pays indisponibles

### Proxy Nginx (`nginx.conf`)

```nginx
location /api/ {
    proxy_pass http://backend-central:8000/;
}
```

Toutes les requêtes `/api/*` du frontend sont proxifiées vers le backend central.
Le frontend ne connaît pas les URLs des backends pays (isolation propre).

### Client API (`api.js`)

```javascript
const BASE = "/api";
export const getDashboard        = () => fetchJSON("/dashboard/summary");
export const getCountryLots      = (country, params) => fetchJSON(`/countries/${country}/lots?${qs}`);
export const getLotDetail        = (country, lotId)  => fetchJSON(`/countries/${country}/lots/${lotId}`);
export const getCountryWarehouses = (country)        => fetchJSON(`/countries/${country}/warehouses`);
export const getAlerts           = (params)          => fetchJSON(`/alerts?${qs}`);
export const resolveAlert        = (country, alertId) => fetch(`/api/countries/${country}/alerts/${alertId}/resolve`, { method: "POST" });
```

---

## 10. Configuration Mosquitto

**Fichier** : `mosquitto/mosquitto.conf`

```
listener 1883
allow_anonymous true          # Production : remplacer par certificats mTLS
persistence true              # QoS 1 : messages survivent aux redémarrages
persistence_location /mosquitto/data/
log_dest stdout
max_queued_messages 1000      # Buffer 1000 messages si subscriber lent
```

**Un broker par pays** (mosquitto-br, mosquitto-ec, mosquitto-co) sur le réseau isolé
du pays correspondant. Le siège n'a pas accès direct aux brokers pays.

---

## 11. Orchestration Docker Compose

**Fichier** : `docker-compose.yml` — **18 services** au total.

### Services par catégorie

| Catégorie | Services | Réseau(x) |
|-----------|---------|-----------|
| Bases de données | postgres-br, postgres-ec, postgres-co | br-net / ec-net / co-net |
| Brokers MQTT | mosquitto-br, mosquitto-ec, mosquitto-co | br-net / ec-net / co-net |
| APIs pays | api-br (:8001), api-ec (:8002), api-co (:8003) | pays-net + central-net |
| Subscribers | subscriber-br, subscriber-ec, subscriber-co | br-net / ec-net / co-net |
| Simulateurs | simulator-br, simulator-ec, simulator-co | br-net / ec-net / co-net |
| Siège | backend-central (:8000), frontend (:8080) | central-net |
| Email dev | mailhog (:8025 web, :1025 SMTP) | tous réseaux |

### Healthchecks

```yaml
# PostgreSQL
healthcheck:
  test: ["CMD-SHELL", "pg_isready -U futurekawa"]
  interval: 10s
  retries: 5

# API pays
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
  interval: 15s
  start_period: 30s
```

Le backend central attend que les 3 APIs pays soient `healthy` avant de démarrer
(`condition: service_healthy`).

### Volumes persistants

```yaml
volumes:
  pgdata-br:    # Données PostgreSQL Brésil
  pgdata-ec:    # Données PostgreSQL Équateur
  pgdata-co:    # Données PostgreSQL Colombie
  mqdata-br:    # Persistance MQTT Brésil (QoS 1)
  mqdata-ec:
  mqdata-co:
```

---

## 12. Module IoT — ESP32 + DHT22

### Schéma de câblage

```
ESP32 (WROOM-32)                DHT22
┌───────────────┐               ┌─────────────┐
│          3.3V │──────────────►│ Pin 1 (VCC) │
│               │         ┌────►│             │
│          GND  │──────────┤   │ Pin 4 (GND) │◄──── GND
│               │          │   │             │
│         GPIO4 │◄─────────┘   │ Pin 2 DATA  │
│               │   [10kΩ]     └─────────────┘
└───────────────┘
(résistance pull-up entre DATA et 3.3V — obligatoire)
```

### Code MicroPython (ESP32 physique)

Le fichier `architecture/documentation-iot.md` contient le code complet `main.py`
MicroPython avec :
- Connexion Wi-Fi avec retry
- Publication MQTT QoS 1 toutes les 30 secondes
- Buffer local 100 mesures en cas de déconnexion
- Backoff exponentiel (5s → 60s max)

### Topics MQTT

| Topic | Direction | QoS | Payload |
|-------|-----------|-----|---------|
| `futurekawa/{PAYS}/warehouse/{CODE}/measurement` | IoT → Broker | 1 | `{"temperature_c": 29.4, "humidity_pct": 54.8}` |

---

## 13. Tests

### Lancement rapide

```bash
# Tests unitaires (sans Docker, rapide)
cd "/Users/mahraz/Desktop/MSPR FutureKawa"
pip install pytest aiomqtt aiosmtplib sqlalchemy asyncpg aiosqlite
pytest tests/test_unit_severity.py -v

# Tests d'intégration (nécessite docker compose up)
pytest tests/test_api_lots.py tests/test_api_central.py -v

# Tests end-to-end (nécessite paho-mqtt + stack complète)
pip install paho-mqtt
pytest tests/test_e2e_iot.py -v -s

# Tous les tests
pytest tests/ -v
```

### Couverture des tests

#### Tests unitaires — `test_unit_severity.py`

| Test | Cas | Résultat attendu |
|------|-----|-----------------|
| UT-01 | deviation=2.0, tolerance=3.0 | None |
| UT-02 | deviation=3.5, tolerance=3.0 | WARNING |
| UT-03 | deviation=5.0, tolerance=3.0 | CRITICAL |
| UT-04 | deviation=3.0, tolerance=3.0 | None (égalité = pas d'alerte) |
| UT-05 | deviation=4.5, tolerance=3.0 | WARNING (exactement 1.5×) |
| UT-06 | deviation=4.51, tolerance=3.0 | CRITICAL |
| UT-07 | deviation=0.0 | None |
| UT-08 | deviation=20.0 | CRITICAL |
| UT-09 | deviation=1.0, tolerance=0.5 | CRITICAL |

#### Tests d'intégration API — `test_api_lots.py`

Routes testées : `/warehouses/`, `/lots/`, `/alerts/`, `/measurements/`, `/health`

Cas notables :
- Vérification du tri FIFO (dates ASC)
- Filtre par statut (CONFORME, PERIME)
- Création de lot (POST)
- 404 sur ressource inexistante
- Health check des 3 APIs pays

#### Tests d'intégration centrale — `test_api_central.py`

Routes testées : `/health`, `/dashboard/summary`, `/countries/{country}/lots`, `/alerts`

Cas notables :
- `total_lots` = somme exacte des lots de chaque pays
- Champ `country` présent dans chaque alerte agrégée
- Pays inconnu → 404
- Mesures incluses dans le détail d'un lot

#### Tests end-to-end — `test_e2e_iot.py`

| Test | Scénario |
|------|----------|
| E2E-01a | Mesure publiée en MQTT → persiste en BDD |
| E2E-01b | T=38°C (CRITICAL) → alerte créée |
| E2E-01c | 2e message en < 30 min → anti-flood (pas de doublon) |
| E2E-01d | POST resolve → resolved_at renseigné |
| E2E-02 | Lot avec storage_date J-400 → statut PERIME automatique |

---

## 14. Pipeline CI/CD Jenkins

**Fichier** : `Jenkinsfile`

### Stages

```
Checkout
    ↓
Build images Docker (--no-cache)
    ↓
Tests unitaires (conteneur Python éphémère)
    ↓
Démarrage stack de test (postgres + mosquitto + apis + subscribers + central)
    ↓
Tests d'intégration API (conteneur Python dans les réseaux Docker CI)
    ↓
Vérification qualité — ruff (linting Python, ignore E501)
    ↓
Build Frontend (conteneur Node 20 → npm ci && npm run build)
    ↓
Packaging artefacts (images Docker + dist frontend archivés)
    ↓
[post] Nettoyage stack (docker compose down -v)
```

### Configuration Jenkins requise

- Docker installé sur l'agent Jenkins
- Permission d'exécuter `docker` et `docker compose`
- Plugin JUnit pour publication des rapports XML

### Commande de déclenchement manuel

```bash
# Depuis le répertoire du projet
docker compose -p futurekawa-ci build
docker compose -p futurekawa-ci up -d
# Puis lancer les tests...
docker compose -p futurekawa-ci down -v
```

---

## 15. Variables d'environnement

### Backend pays (`api-br`, `api-ec`, `api-co`)

| Variable | Valeur exemple | Description |
|----------|---------------|-------------|
| `COUNTRY` | `BR` / `EC` / `CO` | Code pays (détermine le seed et les labels) |
| `DATABASE_URL` | `postgresql+asyncpg://futurekawa:futurekawa@postgres-br:5432/futurekawa` | URL connexion PostgreSQL async |

### Subscriber (`subscriber-br`, etc.)

| Variable | Valeur exemple | Description |
|----------|---------------|-------------|
| `COUNTRY` | `BR` | Code pays (filtre les alertes) |
| `MQTT_HOST` | `mosquitto-br` | Nom du broker MQTT |
| `MQTT_PORT` | `1883` | Port MQTT |
| `DATABASE_URL` | (idem API) | Même base que l'API du pays |
| `SMTP_HOST` | `mailhog` | Serveur SMTP |
| `SMTP_PORT` | `1025` | Port SMTP |

### Simulateur (`simulator-br`, etc.)

| Variable | Valeur exemple | Description |
|----------|---------------|-------------|
| `COUNTRY` | `BR` | Détermine les entrepôts à simuler |
| `MQTT_HOST` | `mosquitto-br` | Broker MQTT cible |
| `INTERVAL_S` | `30` | Fréquence de publication (secondes) |

### Backend central

| Variable | Valeur exemple | Description |
|----------|---------------|-------------|
| `URL_BR` | `http://api-br:8000` | URL API Brésil |
| `URL_EC` | `http://api-ec:8000` | URL API Équateur |
| `URL_CO` | `http://api-co:8000` | URL API Colombie |

---

## 16. Guide de démarrage

### Prérequis

- Docker Desktop installé et démarré
- Ports disponibles : 8000, 8001, 8002, 8003, 8025, 8080, 1025

### Démarrage complet

```bash
cd "/Users/mahraz/Desktop/MSPR FutureKawa"
docker compose up --build
```

Le premier démarrage prend 3–5 minutes (téléchargement des images, build des images,
initialisation des bases, seed des données).

### Vérification

```bash
# Sanity checks
curl http://localhost:8001/health   # {"status":"ok","country":"BR"}
curl http://localhost:8002/health   # {"status":"ok","country":"EC"}
curl http://localhost:8003/health   # {"status":"ok","country":"CO"}
curl http://localhost:8000/health   # {"status":"ok","service":"central"}
```

### URLs d'accès

| Service | URL | Description |
|---------|-----|-------------|
| Interface Web | http://localhost:8080 | Application utilisateur |
| Backend central | http://localhost:8000/docs | Swagger UI siège |
| API Brésil | http://localhost:8001/docs | Swagger UI BR |
| API Équateur | http://localhost:8002/docs | Swagger UI EC |
| API Colombie | http://localhost:8003/docs | Swagger UI CO |
| MailHog | http://localhost:8025 | Visualiser les emails d'alerte |

### Arrêt

```bash
docker compose down           # Arrêt, volumes conservés
docker compose down -v        # Arrêt + suppression des volumes (reset complet)
```

### Voir les logs d'un service

```bash
docker compose logs -f subscriber-br    # Logs subscriber Brésil
docker compose logs -f simulator-br     # Logs simulateur Brésil
docker compose logs -f api-br           # Logs API Brésil
```

---

## 17. API Reference

### Backend pays (répété pour BR :8001, EC :8002, CO :8003)

#### `GET /health`
```json
{"status": "ok", "country": "BR"}
```

#### `GET /warehouses/`
```json
[
  {
    "id": 1, "code": "BR-WH-001", "country": "BR",
    "manager_email": "responsable.br1@futurekawa.com",
    "target_temp_c": "29.0", "target_humidity": "55.0",
    "tolerance_temp": "3.0", "tolerance_hum": "2.0"
  }
]
```

#### `GET /lots/?status=CONFORME&warehouse_id=1`
Résultats triés par `storage_date ASC` (FIFO).
```json
[
  {
    "id": "BR-LOT-2024-001", "warehouse_id": 1,
    "storage_date": "2024-03-15", "status": "CONFORME",
    "variete": "Arabica", "poids_kg": "320.50"
  }
]
```

#### `POST /lots/`
```json
// Corps
{"id": "BR-LOT-2024-999", "warehouse_id": 1, "storage_date": "2024-06-01",
 "variete": "Robusta", "poids_kg": 150.0}
// Réponse 201
{"id": "BR-LOT-2024-999", "status": "CONFORME", ...}
```

#### `GET /measurements/?warehouse_id=1&limit=200`
Retournés en ordre chronologique (ASC).
```json
[
  {"id": 1, "warehouse_id": 1, "measured_at": "2026-06-15T10:00:00Z",
   "temperature_c": "29.2", "humidity_pct": "54.8"}
]
```

#### `GET /alerts/?active_only=true&severity=CRITICAL`
```json
[
  {"id": 1, "warehouse_id": 1, "lot_id": null,
   "alert_type": "TEMP_OUT_OF_RANGE", "severity": "CRITICAL",
   "message": "Température 38.0°C hors plage (cible 29.0°C ±3.0°C)",
   "created_at": "2026-06-15T10:05:00Z", "resolved_at": null, "email_sent": true}
]
```

#### `POST /alerts/{id}/resolve`
```json
// Réponse
{"id": 1, ..., "resolved_at": "2026-06-15T11:00:00Z"}
```

#### `GET /dashboard/summary`
```json
{
  "country": "BR",
  "total_lots": 10, "lots_conformes": 7, "lots_en_alerte": 1, "lots_perimes": 2,
  "active_alerts": 3,
  "warehouses": [...]
}
```

### Backend central (:8000)

#### `GET /dashboard/summary`
```json
{
  "total_lots": 30, "lots_conformes": 21, "lots_en_alerte": 3, "lots_perimes": 6,
  "active_alerts": 9,
  "degraded_countries": [],
  "countries": [
    {"country": "BR", "total_lots": 10, ...},
    {"country": "EC", "total_lots": 10, ...},
    {"country": "CO", "total_lots": 10, ...}
  ]
}
```

#### `GET /alerts`
```json
{
  "alerts": [
    {"id": 1, "country": "BR", "alert_type": "TEMP_OUT_OF_RANGE", "severity": "CRITICAL", ...}
  ],
  "degraded_countries": []
}
```

---

## 18. Règles métier implémentées

### Seuils par pays

| Pays | T° cible | H% cible | Tol. T° | Tol. H% |
|------|----------|----------|---------|---------|
| Brésil (BR) | 29°C | 55% | ±3°C | ±2% |
| Équateur (EC) | 31°C | 60% | ±3°C | ±2% |
| Colombie (CO) | 26°C | 80% | ±3°C | ±2% |

### Calcul de sévérité

| Condition | Sévérité |
|-----------|---------|
| `écart ≤ tolérance` | Aucune alerte |
| `tolérance < écart ≤ 1.5 × tolérance` | WARNING |
| `écart > 1.5 × tolérance` | CRITICAL |

La frontière est stricte (`>`, pas `≥`) : un écart exactement égal à la tolérance
n'est **pas** une alerte.

### Péremption des lots

Un lot est automatiquement basculé en `PERIME` si `storage_date ≤ date_aujourd'hui - 365 jours`.
Cette mise à jour se fait lors de chaque appel à `GET /lots/` et `GET /dashboard/summary`.
**Exception** : les lots `EN_ALERTE` ne sont pas automatiquement mis en PERIME.

### Anti-flood alertes

- Fenêtre glissante de **30 minutes** par triplet `(alert_type, warehouse_id, résolu=False)`
- Déduplication stockée en base PostgreSQL (résiste aux redémarrages)
- Résolution manuelle via `POST /alerts/{id}/resolve` remet le compteur à zéro

### Distribution FIFO

Tous les appels `GET /lots/` retournent les lots triés par `storage_date ASC`.
Le premier lot de la liste est toujours **le plus ancien** et doit être expédié en priorité.

---

*Documentation générée le 15 juin 2026 — FutureKawa MSPR — EPSI RNCP35584 Bloc 4*
