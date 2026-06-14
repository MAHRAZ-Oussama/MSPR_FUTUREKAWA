# Prototype de schéma — Automatisation des entrepôts (Phase 2)

## Principe : Capteurs → Décision → Actionneurs

```
┌─────────────────────────────────────────────────────────────────────┐
│                    ENTREPÔT (local)                                  │
│                                                                      │
│  ┌──────────────┐    MQTT     ┌──────────────────────────────────┐  │
│  │  ESP32/DHT22  │ ──────────► │     Moteur de décision           │  │
│  │  (capteur T/H)│            │     (subscriber Python étendu)    │  │
│  └──────────────┘            │                                   │  │
│                               │  Règle : temp < (cible - tol) ?  │  │
│                               │    → Activer chauffage            │  │
│                               │  Règle : hum < (cible - tol) ?   │  │
│                               │    → Activer humidificateur       │  │
│                               │  Règle : temp > (cible + tol) ?  │  │
│                               │    → Activer ventilation          │  │
│                               │                                   │  │
│                               │  Sécurités :                      │  │
│                               │  - Arrêt urgence si T > 40°C      │  │
│                               │  - Mode manuel prioritaire         │  │
│                               │  - Durée max activation = 2h      │  │
│                               └──────────────────────────────────┘  │
│                                         │                            │
│                                         ▼ MQTT (commandes)           │
│                               ┌──────────────────────────────────┐  │
│                               │       Contrôleur d'actionneurs    │  │
│                               │    (ESP32 dédié ou relais IoT)    │  │
│                               └──────────────────────────────────┘  │
│                                    │         │          │            │
│                            ┌───────▼──┐  ┌──▼──────┐  ┌▼────────┐  │
│                            │Chauffage │  │Humidif. │  │Aération │  │
│                            │(résistance│  │(vaporis.)│  │(ventil.)│  │
│                            │  ou PAC) │  └─────────┘  └─────────┘  │
│                            └──────────┘                             │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  Interface de supervision locale (dashboard entrepôt)         │   │
│  │  - Statut actionneurs (ON/OFF)                                │   │
│  │  - Bouton arrêt d'urgence physique                           │   │
│  │  - Mode manuel / automatique                                  │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
           │ API REST
           ▼
   ┌──────────────────┐
   │  Backend Siège   │
   │  (supervision)   │
   └──────────────────┘
```

## Topics MQTT des commandes (extension phase 2)

| Topic | Direction | Payload | QoS |
|-------|-----------|---------|-----|
| `futurekawa/{PAYS}/warehouse/{CODE}/actuator/heating` | Backend → Contrôleur | `{"state":"ON","duration_s":1800}` | 1 |
| `futurekawa/{PAYS}/warehouse/{CODE}/actuator/humidifier` | Backend → Contrôleur | `{"state":"OFF"}` | 1 |
| `futurekawa/{PAYS}/warehouse/{CODE}/actuator/ventilation` | Backend → Contrôleur | `{"state":"ON","speed":"medium"}` | 1 |
| `futurekawa/{PAYS}/warehouse/{CODE}/actuator/emergency_stop` | Backend → Contrôleur | `{"state":"ON"}` | 2 |
| `futurekawa/{PAYS}/warehouse/{CODE}/actuator/status` | Contrôleur → Backend | `{"heating":"ON","humidifier":"OFF","ventilation":"ON"}` | 1 (retain) |

## Sécurités implémentées

1. **Arrêt d'urgence logique** : si T > 40°C → coupure immédiate du chauffage + ventilation forcée
2. **Durée max d'activation** : chaque actionneur limité à 2h consécutives (évite sur-chauffage)
3. **Priorité mode manuel** : un opérateur peut forcer l'arrêt via bouton physique, overriding l'automatique
4. **Timeout de commande** : si le contrôleur ne reçoit pas de heartbeat backend depuis 10 min → mode sécurisé (arrêt tout)
5. **Double capteur recommandé** : en production, un capteur de secours pour détecter les pannes
6. **Log de toutes les commandes** : traçabilité des activations pour audit

## Intégration avec la solution IoT existante

La phase 2 réutilise :
- Le broker Mosquitto existant (ajout des topics actionneurs)
- La base de données PostgreSQL (ajout table `actuator_events`)
- L'API FastAPI (ajout endpoints `/actuators`)
- Le Frontend (ajout panneau de contrôle des actionneurs)
