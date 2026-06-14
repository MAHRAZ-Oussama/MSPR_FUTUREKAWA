# ADR-001 — Choix de la stack technique

**Date** : 2026-06-14
**Statut** : Accepté

## Contexte

FutureKawa nécessite une solution multi-pays robuste, maintenable et évolutive,
avec contraintes terrain (réseau variable, matériel limité) et exigences de traçabilité.

## Décision

### Python + FastAPI (backend)

**Pourquoi** : FastAPI génère l'OpenAPI automatiquement, supporte async natif (essentiel pour MQTT +
HTTP concurrent), et SQLAlchemy async offre un ORM mature. La communauté IoT Python (aiomqtt,
MicroPython) est cohérente avec le reste du stack.

**Alternative rejetée** : Node.js/Express — moins adapté à l'écosystème IoT MicroPython, moins lisible
pour l'équipe data/BI.

### PostgreSQL 16 (base de données)

**Pourquoi** : Requêtes temporelles natives (TIMESTAMPTZ), index B-tree optimal pour FIFO,
ACID strict pour la traçabilité réglementaire. Stable et open-source.

**Alternative rejetée** : TimescaleDB — surqualifié pour le volume actuel, complexité supplémentaire.

### React + Vite + Chart.js (frontend)

**Pourquoi** : React est la norme pour les SPA riches, Vite offre un DX rapide, Chart.js est
léger et parfait pour les séries temporelles température/humidité.

**Alternative rejetée** : Vue.js — bon choix mais React est plus commun pour les équipes mixtes.

### Eclipse Mosquitto 2.x (broker MQTT)

**Pourquoi** : Broker MQTT de référence, Docker officiel, QoS 1 pour la garantie de livraison,
persistance disque native. Léger et éprouvé.

**Alternative rejetée** : RabbitMQ (plugin MQTT) — surqualifié, consomme plus de ressources.

### Architecture Pub/Sub (découplage IoT)

**Pourquoi** : Découple les capteurs du backend. Si le backend redémarre, les messages MQTT sont mis
en file (QoS 1). L'ajout d'un nouveau capteur ne nécessite pas de modifier l'API.

## Conséquences

- Cohérence Python/MicroPython sur toute la stack IoT
- Documentation API automatique (FastAPI OpenAPI)
- Migrations versionées (Alembic)
- Chaque pays peut être déployé indépendamment
