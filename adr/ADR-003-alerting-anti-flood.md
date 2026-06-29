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
- **CRITICAL** : écart > 1.5× tolérance

La frontière est stricte (`>`, pas `>=`) pour favoriser le WARNING sur les cas limites.

## Auto-résolution par hystérésis (révision)

Une alerte conditions est **auto-résolue** dès qu'une mesure revient
franchement dans la plage (écart ≤ 0,8 × tolérance). La bande morte entre
0,8 × tolérance et la tolérance empêche le « flapping » (alerte créée/résolue en
boucle quand une valeur oscille autour du seuil). Inspiré de l'hystérésis du
projet de référence, mais implémenté de façon idiomatique côté subscriber
(`severity.should_clear` + `resolve_active_alerts`).

## Alerte de péremption `LOT_EXPIRED` (révision)

Un lot stocké depuis plus de 365 jours (`EXPIRY_DAYS`) lève une alerte
`LOT_EXPIRED` (sévérité WARNING) **une seule fois par lot** et déclenche un email
au responsable de l'entrepôt. Portée par le backend-pays (`alerting.py`) via un
scheduler APScheduler (`CHECK_INTERVAL_MINUTES`, défaut 5 min) + au démarrage +
à la lecture des lots. Le statut du lot passe `PERIME` (prioritaire sur tout).

## Statut métier des lots

Un lot dont l'entrepôt a une alerte conditions active passe `EN_ALERTE` ;
il revient `CONFORME` à la résolution (`alerting.sync_lot_alert_status`).

## Conséquences

- Maximum 1 email par type d'alerte par entrepôt toutes les 30 minutes
- Les alertes non résolues s'accumulent en base (audit trail)
- La résolution est **automatique** (hystérésis) ou manuelle (`POST /alerts/{id}/resolve`)
- `email_sent = true` sur l'alerte après envoi réussi (rejeu possible en cas d'échec SMTP)
