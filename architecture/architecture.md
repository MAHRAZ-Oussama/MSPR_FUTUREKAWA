# FutureKawa — Dossier d'Architecture

## 1. Vue d'ensemble

FutureKawa déploie une **architecture distribuée** dans laquelle chaque pays (Brésil, Équateur,
Colombie) dispose d'un backend autonome, et un backend central (siège) agrège les données via REST.

```
┌────────────────────────────────────────────────────────────────────────┐
│                          SIÈGE (central)                               │
│   ┌──────────────┐    ┌─────────────────┐                             │
│   │   Frontend   │◄───│ Backend Central │◄──────────────┐             │
│   │  React/Nginx │    │   FastAPI :8000  │               │             │
│   │    :8080     │    └─────────────────┘               │             │
│   └──────────────┘                                       │             │
│                              │ HTTP REST                 │             │
└──────────────────────────────┼───────────────────────────┘             │
                               │                                          │
          ┌────────────────────┼──────────────────────┐                  │
          │                    │                       │                  │
   ┌──────▼──────┐    ┌───────▼──────┐    ┌──────────▼──────┐          │
   │   BRÉSIL    │    │   ÉQUATEUR   │    │    COLOMBIE      │          │
   │             │    │              │    │                  │          │
   │ [IoT/Sim]   │    │  [IoT/Sim]   │    │   [IoT/Sim]      │          │
   │     ↓ MQTT  │    │    ↓ MQTT    │    │     ↓ MQTT       │          │
   │ [Mosquitto] │    │ [Mosquitto]  │    │  [Mosquitto]     │          │
   │     ↓       │    │      ↓       │    │      ↓           │          │
   │ [Subscriber]│    │ [Subscriber] │    │  [Subscriber]    │          │
   │     ↓       │    │      ↓       │    │      ↓           │          │
   │ [PostgreSQL] │    │ [PostgreSQL]│    │  [PostgreSQL]    │          │
   │     ↑       │    │      ↑       │    │      ↑           │          │
   │ [API :8001] │    │ [API :8002]  │    │  [API :8003]     │          │
   │ [Alerting]  │    │  [Alerting]  │    │  [Alerting]      │          │
   └─────────────┘    └──────────────┘    └──────────────────┘          │
```

## 2. Composants par pays

| Composant | Rôle | Technologie |
|-----------|------|-------------|
| IoT / Simulateur | Lecture capteur DHT22, publication MQTT | MicroPython ESP32 / Python |
| Mosquitto | Broker MQTT local, découplage IoT | Eclipse Mosquitto 2.x |
| Subscriber | Consomme MQTT → INSERT PostgreSQL + alerte | Python asyncio + aiomqtt |
| PostgreSQL | Persistance locale des lots et mesures | PostgreSQL 16 |
| API FastAPI | REST : lots, mesures, alertes, warehouses | Python FastAPI 0.110 |
| Alerting cron | Vérification quotidienne lots périmés | APScheduler + aiosmtplib |
| MailHog | SMTP de développement | MailHog |

## 3. Flux de données

### Flux IoT → Backend pays

1. ESP32/simulateur lit le DHT22 toutes les **30 secondes**
2. Publication JSON MQTT sur `futurekawa/{PAYS}/warehouse/{CODE}/measurement` (QoS 1)
3. Subscriber Python consomme et INSERT dans `measurements`
4. Évaluation des seuils → création alerte si dérive
5. Envoi email SMTP si alerte non dédupliquée

### Flux Frontend ← Backend Central ← Backends Pays

1. Frontend appelle `/dashboard/summary` ou `/countries/{code}/lots`
2. Backend central agrège en parallèle (`asyncio.gather`) vers les APIs pays
3. Si un pays est indisponible : réponse partielle, champ `degraded_countries`
4. Frontend affiche les données disponibles avec indicateur de mode dégradé

## 4. Modèle de données

### `warehouses` — Entrepôts
| Colonne | Type | Description |
|---------|------|-------------|
| id | SERIAL PK | |
| code | VARCHAR(20) UNIQUE | Ex : BR-WH-001 |
| country | VARCHAR(2) | BR / EC / CO |
| manager_email | VARCHAR(150) | Email du responsable |
| target_temp_c | DECIMAL(4,1) | Température cible (°C) |
| target_humidity | DECIMAL(4,1) | Humidité cible (%) |
| tolerance_temp | DECIMAL(3,1) | Tolérance température |
| tolerance_hum | DECIMAL(3,1) | Tolérance humidité |

### `lots` — Lots de café
| Colonne | Type | Description |
|---------|------|-------------|
| id | VARCHAR(50) PK | Id unique (ex : BR-LOT-2024-001) |
| warehouse_id | INT FK | Entrepôt de stockage |
| storage_date | DATE | Date d'entrée en entrepôt (FIFO) |
| status | VARCHAR(20) | CONFORME / EN_ALERTE / PERIME |

**Index FIFO** : `idx_lots_storage_date` sur `storage_date ASC`

### `measurements` — Mesures IoT
| Colonne | Type | Description |
|---------|------|-------------|
| id | BIGSERIAL PK | |
| warehouse_id | INT FK | |
| measured_at | TIMESTAMPTZ | Horodatage UTC |
| temperature_c | DECIMAL(4,1) | |
| humidity_pct | DECIMAL(4,1) | |

**Index** : `idx_measurements_wh_time` sur `(warehouse_id, measured_at DESC)`

### `alerts` — Alertes
| Colonne | Type | Description |
|---------|------|-------------|
| alert_type | VARCHAR(30) | TEMP_OUT_OF_RANGE / HUMIDITY_OUT_OF_RANGE / LOT_EXPIRED |
| severity | VARCHAR(10) | WARNING / CRITICAL |
| email_sent | BOOLEAN | Anti-flood : un email par alerte non résolue |
| resolved_at | TIMESTAMPTZ | NULL = alerte active |

## 5. Seuils et règles d'alerting

| Pays | Temp. cible | Hum. cible | Tolérance T | Tolérance H |
|------|-------------|------------|-------------|-------------|
| Brésil | 29°C | 55% | ±3°C | ±2% |
| Équateur | 31°C | 60% | ±3°C | ±2% |
| Colombie | 26°C | 80% | ±3°C | ±2% |

**Calcul de sévérité** :
- Écart ≤ tolérance → Aucune alerte
- Tolérance < écart ≤ 1.5× tolérance → WARNING
- Écart > 1.5× tolérance → CRITICAL

**Anti-flood** : fenêtre glissante de 30 min par (type, entrepôt).

## 6. Robustesse et tolérance aux pannes

- **Backend pays autonome** : fonctionne sans le siège (données locales suffisantes)
- **Mode dégradé siège** : si un pays est indisponible, les autres restent accessibles
- **Reconnexion MQTT** : backoff exponentiel (5s → 60s max)
- **Buffer local IoT** : 100 mesures stockées en cas de déconnexion MQTT
- **Pool de connexions PostgreSQL** : pool_size=10, max_overflow=20
- **Healthchecks Docker** : tous les services critiques disposent d'un healthcheck

## 7. Sécurité (recommandations production)

- Remplacer `allow_anonymous true` dans Mosquitto par authentification par certificats
- Variables d'environnement pour tous les secrets (pas de valeurs en dur)
- HTTPS via reverse proxy (Nginx + Let's Encrypt) en production
- Authentification JWT sur les APIs FastAPI (à ajouter en phase 2)
- Réseaux Docker isolés par pays (`br-net`, `ec-net`, `co-net`)
