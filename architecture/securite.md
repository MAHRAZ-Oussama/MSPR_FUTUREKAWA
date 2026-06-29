# Sécurité — FutureKawa

Posture de sécurité du prototype et recommandations pour l'industrialisation.
La démarche est volontairement **proportionnée à un prototype** : on sécurise ce
qui a un sens pour la démo et on documente le durcissement attendu en production.

## 1. Isolation réseau (mesure structurante)

Chaque pays dispose de son propre réseau Docker isolé (`br-net`, `ec-net`,
`co-net`). Les bases, brokers et subscribers d'un pays ne sont **pas** joignables
depuis un autre pays. Seules les API pays sont exposées au `central-net` pour la
consolidation siège. Un incident (ou une compromission) reste cantonné à un pays.

| Composant | Exposition |
|-----------|-----------|
| PostgreSQL pays | réseau pays uniquement (jamais publié) |
| Broker MQTT pays | réseau pays uniquement |
| API pays | réseau pays + central-net |
| Backend central | central-net + port 8000 |
| Frontend | port 8080 (point d'entrée utilisateur) |

## 2. Authentification des écritures (clé API optionnelle)

Les routes d'**écriture** des API pays (`POST /lots/`, `POST /alerts/{id}/resolve`)
acceptent une clé API via l'en-tête `X-API-Key`, contrôlée par
`backend-pays/security.py` :

- `API_KEY` **non défini** (défaut) → routes ouvertes (confort de démo) ;
- `API_KEY` **défini** → toute écriture sans clé valide renvoie `401`.

Le backend central propage automatiquement la clé (`X-API-Key`) sur ses appels
d'écriture lorsqu'elle est configurée, donc la chaîne reste fonctionnelle une fois
la sécurité activée. Les routes de **lecture** restent ouvertes (consultation
terrain/siège), conformément à l'usage métier.

## 3. CORS

`CORS_ORIGINS` (défaut `*`) restreint les origines autorisées, côté API pays et
backend central. En production : `CORS_ORIGINS=https://futurekawa.example`.
Dans l'architecture actuelle, le navigateur ne joint que le frontend (origine
unique, proxy Nginx `/api`), donc la surface CORS réelle est faible.

## 4. MQTT

Le broker est configuré `allow_anonymous true`, **acceptable ici** car il n'est
exposé que sur le réseau privé du pays (jamais publié hors Docker). 

**Recommandé en production** : authentification Mosquitto (`password_file`) +
TLS (port 8883) + ACL par topic (un capteur ne publie que son entrepôt). Le
firmware (`iot/`) et le subscriber peuvent recevoir identifiants/CA sans
changement d'architecture.

## 5. Secrets

- `.env` et `iot/config.py` (mot de passe Wi-Fi) sont exclus du dépôt (`.gitignore`).
- `.env.example` documente les variables sans valeurs sensibles.
- Identifiants PostgreSQL de démo (`futurekawa/futurekawa`) : à remplacer par des
  secrets gérés (Docker secrets / Vault) en production.

## 6. Correspondance OWASP API Security Top 10 (extrait)

| Risque | Statut prototype | Action production |
|--------|------------------|-------------------|
| API2 Broken Authentication | clé API optionnelle sur écritures | activer `API_KEY`, envisager OAuth2/JWT siège |
| API4 Unrestricted Resource Consumption | `limit` plafonné (≤1000) sur `/measurements` | rate-limiting passerelle |
| API7 SSRF / exposition | réseaux isolés, pas d'URL utilisateur | reverse-proxy + WAF |
| API8 Security Misconfiguration | CORS paramétrable, MQTT privé | TLS partout, durcir images |

## 7. Synthèse

| Mesure | Prototype | Production recommandée |
|--------|-----------|------------------------|
| Isolation réseau pays | ✅ | ✅ |
| Clé API écritures | ✅ optionnelle | ✅ activée |
| CORS restreint | ✅ paramétrable | ✅ origine unique |
| MQTT auth + TLS | ❌ (réseau privé) | ✅ |
| Secrets gérés | partiel (.env) | ✅ Vault / Docker secrets |
