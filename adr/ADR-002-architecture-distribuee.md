# ADR-002 — Architecture distribuée pays + siège

**Date** : 2026-06-14
**Statut** : Accepté

## Contexte

FutureKawa opère dans 3 pays avec des conditions réseau variables. Le siège doit
consolider les données sans bloquer les opérations locales si la connexion siège est instable.

## Décision

Architecture à **2 niveaux** :
1. **Backend local par pays** : autonome, traite IoT, persiste localement, gère ses alertes
2. **Backend central** : agrège les données en appelant les APIs pays en parallèle, mode dégradé natif

**Découplage IoT via MQTT** : le subscriber Python est séparé de l'API REST, les deux peuvent
redémarrer indépendamment sans perte de données (QoS 1 = garantie de livraison).

## Alternatives considérées

| Option | Avantages | Inconvénients |
|--------|-----------|---------------|
| Centralisé tout-en-un | Simple | Point de défaillance unique, latence réseau IoT |
| Message bus global (Kafka) | Scalable | Complexité opérationnelle excessive pour 3 pays |
| **Distribué REST (retenu)** | Autonomie locale, couplage faible | Consistance éventuelle |

## Conséquences

- Ajout d'un 4e pays = dupliquer `docker-compose.country.yml` + enregistrer l'URL au siège
- Le siège peut afficher des données partielles si un pays est indisponible (champ `degraded_countries`)
- Les alertes sont émises localement, sans dépendre du siège
- Tolérance aux pannes réseau : les opérations locales continuent sans le siège
