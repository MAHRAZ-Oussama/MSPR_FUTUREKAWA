# Plan de Tests — FutureKawa

## 1. Stratégie de tests

### Niveaux de test

| Niveau | Outil | Périmètre | Automatisé |
|--------|-------|-----------|-----------|
| Unitaires | pytest | Logique pure : sévérité, hystérésis, bornes physiques | ✅ CI Jenkins (sans Docker) |
| Application isolée | pytest + httpx ASGITransport + SQLite | Routes API pays, péremption, statut, clé API | ✅ CI Jenkins (sans Docker) |
| Intégration | pytest + httpx | API pays & centrale sur stack Docker réelle | ✅ CI Jenkins (stack live) |
| End-to-end | pytest + paho-mqtt | Cycle IoT complet MQTT → BDD → alerte | ✅ CI Jenkins (stack live) |
| UI | Manuel (scénario) | Interface Web (navigateur) | ❌ Manuel |

### Données de test
- Tests isolés : SQLite **en mémoire** (`StaticPool`), aucune dépendance externe
- Tests intégration/e2e : stack Docker (`docker compose up`)
- Données seed déterministes (fixtures pytest) ; MailHog pour capturer les emails SMTP

---

## 2. Cas de tests unitaires

### 2.1 Calcul de sévérité (subscriber)

| ID | Entrée | Résultat attendu | Critère |
|----|--------|-----------------|---------|
| UT-01 | deviation=2.0, tolerance=3.0 | `None` (pas d'alerte) | deviation ≤ tolerance |
| UT-02 | deviation=3.5, tolerance=3.0 | `WARNING` | tolerance < deviation ≤ 1.5×tolerance |
| UT-03 | deviation=5.0, tolerance=3.0 | `CRITICAL` | deviation > 1.5×tolerance |
| UT-04 | deviation=3.0, tolerance=3.0 | `None` | strictement égal = pas d'alerte |
| UT-05 | deviation=4.5, tolerance=3.0 | `WARNING` | exactement 1.5× = WARNING |
| UT-06 | deviation=4.6, tolerance=3.0 | `CRITICAL` | dépasse 1.5× = CRITICAL |

### 2.1bis Plage physique & hystérésis (subscriber)

| ID | Entrée | Résultat attendu | Critère |
|----|--------|-----------------|---------|
| UT-07 | `is_plausible(29, 55)` | `True` | mesure réaliste acceptée |
| UT-08 | `is_plausible(250, 55)` / `(29, 120)` | `False` | hors bornes physiques → rejetée |
| UT-09 | `is_plausible(None, 55)` | `False` | valeur manquante rejetée |
| UT-10 | `should_clear(2.0, 3.0)` | `True` | retour franc (≤0,8×tol) → auto-résolution |
| UT-11 | `should_clear(2.5, 3.0)` | `False` | bande morte → on maintient l'alerte |

### 2.2 Logique FIFO (lots)

| ID | Scénario | Résultat attendu |
|----|----------|-----------------|
| UT-20 | 3 lots avec dates 2024-01, 2023-06, 2024-06 | Ordre : 2023-06, 2024-01, 2024-06 |
| UT-21 | Lot stocké il y a 366 jours | Statut = PERIME |
| UT-22 | Lot stocké il y a 364 jours | Statut = CONFORME |

### 2.3 Tests d'application & d'alerting ISOLÉS (SQLite, sans Docker)

Exécutés en CI sans stack live, via `httpx ASGITransport` + SQLite mémoire.

| ID | Fichier | Scénario | Résultat attendu |
|----|---------|----------|-----------------|
| AP-01 | `test_app_backend_pays` | `GET /lots/` | tri FIFO, statut PERIME auto |
| AP-02 | `test_app_backend_pays` | `POST /lots/` sans `API_KEY` défini | 201 (ouvert) |
| AP-03 | `test_app_backend_pays` | `POST /lots/` avec `API_KEY` défini, sans clé | 401 |
| AP-04 | `test_app_backend_pays` | `POST /lots/` avec bonne clé | 201 |
| AL-01 | `test_alerting_logic` | lot > 365 j → `check_expired_lots` | 1 alerte `LOT_EXPIRED`, statut PERIME |
| AL-02 | `test_alerting_logic` | 2e passage | aucune alerte en double |
| AL-03 | `test_alerting_logic` | `notify=True` | email envoyé au responsable, `email_sent=True` |
| AL-04 | `test_alerting_logic` | alerte conditions active | lots de l'entrepôt → `EN_ALERTE` |
| AL-05 | `test_alerting_logic` | plus d'alerte active | `EN_ALERTE` → `CONFORME` ; `PERIME` conservé |
| SB-01 | `test_subscriber_logic` | mesure aberrante (T=250) | ni persistée ni alertée (A3) |
| SB-02 | `test_subscriber_logic` | CRITICAL puis retour franc | alerte créée puis auto-résolue (A1) |
| SB-03 | `test_subscriber_logic` | retour en bande morte | alerte maintenue active |

---

## 3. Cas de tests d'intégration API

### 3.1 Backend pays — `/warehouses`

| ID | Méthode | Route | Résultat attendu | Critère de réussite |
|----|---------|-------|-----------------|-------------------|
| IT-01 | GET | `/warehouses/` | HTTP 200, liste ≥ 1 entrepôt | JSON array |
| IT-02 | GET | `/warehouses/1` | HTTP 200, objet warehouse | `code` présent |
| IT-03 | GET | `/warehouses/999` | HTTP 404 | `detail` dans réponse |

### 3.2 Backend pays — `/lots`

| ID | Méthode | Route | Résultat attendu | Critère de réussite |
|----|---------|-------|-----------------|-------------------|
| IT-10 | GET | `/lots/` | HTTP 200, triés par `storage_date` ASC | Premier = plus ancien |
| IT-11 | GET | `/lots/?status=CONFORME` | HTTP 200, uniquement CONFORME | Filtre actif |
| IT-12 | GET | `/lots/?status=PERIME` | HTTP 200, uniquement PERIME | Filtre actif |
| IT-13 | POST | `/lots/` | HTTP 201, lot créé | ID retourné |
| IT-14 | GET | `/lots/INCONNU` | HTTP 404 | `detail` dans réponse |

### 3.3 Backend pays — `/alerts`

| ID | Méthode | Route | Résultat attendu |
|----|---------|-------|-----------------|
| IT-20 | GET | `/alerts/` | HTTP 200, liste (vide ou remplie) |
| IT-21 | GET | `/alerts/?active_only=true` | HTTP 200, uniquement `resolved_at = null` |
| IT-22 | POST | `/alerts/1/resolve` | HTTP 200, `resolved_at` non null |

### 3.4 Backend pays — `/measurements`

| ID | Méthode | Route | Résultat attendu |
|----|---------|-------|-----------------|
| IT-30 | GET | `/measurements/?warehouse_id=1&limit=10` | HTTP 200, ≤ 10 mesures, ordre chronologique |

### 3.5 Backend central — Agrégation

| ID | Scénario | Résultat attendu |
|----|----------|-----------------|
| IT-40 | GET `/dashboard/summary` (3 pays up) | HTTP 200, `degraded_countries = []` |
| IT-41 | GET `/dashboard/summary` (1 pays down) | HTTP 200, `degraded_countries = ["XX"]` |
| IT-42 | GET `/countries/BR/lots` | HTTP 200, liste lots BR |
| IT-43 | GET `/countries/ZZ/lots` | HTTP 404 |
| IT-44 | GET `/alerts` | HTTP 200, alertes de tous pays avec champ `country` |

---

## 4. Tests end-to-end (scénario complet)

### E2E-01 — Cycle complet IoT → Alerte

| Étape | Action | Résultat attendu |
|-------|--------|-----------------|
| 1 | Simulateur publie T=38°C (écart = 9°C, CRITICAL) | Message MQTT reçu par broker |
| 2 | Subscriber consomme le message | Mesure insérée en BDD |
| 3 | Calcul de sévérité | Alerte CRITICAL créée |
| 4 | Email envoyé via MailHog | `email_sent = true` en BDD |
| 5 | GET `/alerts/?active_only=true` | Alerte visible via API |
| 6 | Anti-flood : 2e message 5 min après | Pas de nouvelle alerte créée |
| 7 | POST `/alerts/1/resolve` | `resolved_at` renseigné |
| 8 | 3e message après résolution | Nouvelle alerte créée |

### E2E-02 — Lot périmé

| Étape | Action | Résultat attendu |
|-------|--------|-----------------|
| 1 | Créer lot avec `storage_date` = -366 jours | Statut = CONFORME à la création |
| 2 | GET `/lots/` | Statut automatiquement mis à PERIME |
| 3 | GET `/dashboard/summary` | `lots_perimes` incrémenté |

---

## 5. Tests UI (manuels)

| ID | Scénario | Étapes | Résultat attendu |
|----|----------|--------|-----------------|
| UI-01 | Affichage dashboard | Ouvrir http://localhost:8080/dashboard | Compteurs visibles, 3 cartes pays |
| UI-02 | Navigation pays | Cliquer "🇧🇷 Brésil" | Liste lots triés FIFO |
| UI-03 | Détail lot | Cliquer "Voir →" sur un lot | Courbes T/H visibles |
| UI-04 | Filtre statut | Sélectionner "Périmé" | Seuls lots PERIME affichés |
| UI-05 | Mode dégradé | Stopper `api-br` | Bandeau jaune, compteurs partiels |
| UI-06 | Page alertes | Cliquer "🔔 Alertes" | Liste alertes avec sévérité colorée |
| UI-07 | Rafraîchissement | Attendre 30s | Données mises à jour automatiquement |

---

## 6. Gestion des anomalies

| Anomalie | Constat | Correction | Re-test |
|----------|---------|-----------|---------|
| API retourne 500 | Log uvicorn + traceback | Corriger handler / rollback BDD | Re-lancer IT correspondant |
| Email non reçu | `email_sent = false` en BDD | Vérifier config SMTP_HOST / SMTP_PORT | E2E-01 étape 4 |
| Dashboard vide | `degraded_countries` non vide | Vérifier health des APIs pays | IT-40 |
| Courbes vides | 0 mesures retournées | Vérifier simulator logs + MQTT topic | E2E-01 étapes 1–2 |
| FIFO non respecté | Lot récent en 1er | Vérifier `ORDER BY storage_date ASC` | IT-10 |
