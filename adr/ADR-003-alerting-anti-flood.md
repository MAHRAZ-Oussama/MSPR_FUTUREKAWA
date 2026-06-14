# ADR-003 — Système d'alerting avec déduplication (anti-flood)

**Date** : 2026-06-14
**Statut** : Accepté

## Contexte

Les capteurs IoT publient toutes les 30 secondes. Sans déduplication, une condition
hors-plage persistante génèrerait des centaines d'emails par heure.

## Décision

Déduplication basée sur une **fenêtre glissante de 30 minutes** :
avant de créer une alerte et envoyer un email, on vérifie si une alerte identique
(même `alert_type`, même `warehouse_id`) existe déjà dans la base, non résolue,
déclenchée dans les 30 dernières minutes.

Si oui → silencieux (pas de doublon, pas d'email).

La vérification se fait en base de données (pas en mémoire) pour survivre aux redémarrages.

## Règles de sévérité

- **WARNING** : écart > tolérance ET ≤ 1.5× tolérance
- **CRITICAL** : écart > 1.5× tolérance OU condition persiste > 30 min

La frontière est stricte (`>`, pas `>=`) pour favoriser le WARNING sur les cas limites.

## Conséquences

- Maximum 1 email par type d'alerte par entrepôt toutes les 30 minutes
- Les alertes non résolues s'accumulent en base (audit trail)
- La résolution manuelle (`POST /alerts/{id}/resolve`) remet le compteur à zéro
- `email_sent = true` sur l'alerte après envoi réussi (rejeu possible en cas d'échec SMTP)
