# Guide Utilisateur — FutureKawa

## Prise en main de l'interface Web

### Accéder à l'application

Ouvrir un navigateur et aller sur : **http://[adresse-serveur]:8080**

L'application est organisée en 4 sections accessibles depuis la barre de navigation :

- **Tableau de bord** — Vue globale de tous les pays
- **🇧🇷 Brésil / 🇪🇨 Équateur / 🇨🇴 Colombie** — Détail par pays
- **🔔 Alertes** — Toutes les alertes actives

---

## Tableau de bord (Vue Siège)

Le tableau de bord affiche en temps réel (rafraîchissement toutes les 30 secondes) :

- **Compteurs globaux** : total des lots, conformes, en alerte, périmés, alertes actives
- **Cartes par pays** : état de chaque pays avec ses statistiques de lots

**Indicateurs importants :**
- Un pays affiché **"Hors ligne"** signifie que son backend est momentanément injoignable.
  Les données des autres pays restent disponibles.
- Un bandeau jaune indique les pays en mode dégradé.

---

## Consultation des lots par pays

Cliquer sur un pays (barre de navigation ou carte du tableau de bord).

### Filtrer et trier

La liste est triée par **date de stockage croissante (FIFO)** : les lots les plus anciens
(à expédier en priorité) apparaissent en premier.

Filtres disponibles :
- **Statut** : Tous / Conforme / En alerte / Périmé
- **Entrepôt** : Filtre par entrepôt spécifique

### Lire la liste des lots

| Colonne | Description |
|---------|-------------|
| ID Lot | Identifiant unique du lot |
| Date stockage ↑ | Date d'entrée en entrepôt (tri FIFO) |
| Ancienneté | Nombre de jours depuis le stockage. En rouge si > 365 jours |
| Variété | Type de café (Arabica, Robusta, etc.) |
| Poids (kg) | Poids du lot |
| Statut | CONFORME / EN ALERTE / PÉRIMÉ |

**Signification des statuts :**
- 🟢 **CONFORME** : conditions de stockage dans la plage acceptable
- 🟡 **EN ALERTE** : une ou plusieurs conditions hors tolérance
- 🔴 **PÉRIMÉ** : lot stocké depuis plus de 365 jours

---

## Détail d'un lot et courbes conditions

Cliquer sur **"Voir →"** à droite d'un lot.

La page affiche :
1. **Informations générales** : ID, entrepôt, date de stockage, ancienneté, variété, poids
2. **Courbes température et humidité** : historique depuis le stockage du lot
3. **Statistiques** : min/max/moyenne sur la période

### Lire les courbes

- Ligne **rouge** : température (°C) — axe gauche
- Ligne **bleue** : humidité (%) — axe droit
- Survoler la courbe : les valeurs précises s'affichent
- Si beaucoup de mesures (> 200), les points ne sont pas affichés pour la lisibilité

---

## Alertes et actions attendues

### Page Alertes

Accédez via **🔔 Alertes** dans la navigation. Filtres disponibles :
- Sévérité (CRITICAL / WARNING)
- Type d'alerte
- Pays

### Types d'alertes

| Icône | Type | Cause | Action recommandée |
|-------|------|-------|-------------------|
| 🌡️ | TEMP_OUT_OF_RANGE | Température hors plage | Vérifier le thermomètre, ventilation, isolation |
| 💧 | HUMIDITY_OUT_OF_RANGE | Humidité hors plage | Vérifier humidificateur ou déshumidificateur |
| ⏰ | LOT_EXPIRED | Lot > 365 jours | Planifier l'expédition immédiate ou déclassement |

### Sévérités

- **WARNING** (orange) : surveiller, condition légèrement hors plage
- **CRITICAL** (rouge) : agir immédiatement, risque de déclassement du lot

### Emails d'alerte

Le responsable d'exploitation reçoit un email automatique pour chaque nouvelle alerte.
Le système envoie **au maximum 1 email par type d'alerte par entrepôt toutes les 30 minutes**
pour éviter le flood.

---

## Résolution des problèmes courants

| Problème | Cause probable | Solution |
|----------|---------------|----------|
| Pays "Hors ligne" dans le dashboard | Backend pays indisponible | Vérifier l'état du serveur du pays |
| Courbes vides pour un lot | Capteur IoT non connecté | Vérifier la connexion MQTT et le capteur |
| Beaucoup d'alertes CRITICAL | Panne équipement entrepôt | Intervention technique urgente |
| Lot périmé non expédié | Absence de visibilité FIFO | Utiliser le tri par date ASC, prioriser les lots rouges |

---

## FAQ

**Q : Comment savoir quels lots expédier en priorité ?**
R : La liste des lots est triée par date de stockage croissante (FIFO). Le premier lot affiché
est toujours le plus ancien et doit être expédié en priorité.

**Q : Je ne reçois plus d'emails d'alerte. Que faire ?**
R : Vérifier que votre adresse email est correcte dans le profil d'entrepôt.
Contacter le service informatique si le problème persiste.

**Q : Une alerte est résolue mais reste affichée. Pourquoi ?**
R : Les alertes actives restent visibles jusqu'à résolution manuelle par un opérateur.
Contacter votre responsable pour marquer l'alerte comme résolue.

**Q : Les données affichées sont-elles en temps réel ?**
R : L'interface se rafraîchit automatiquement toutes les 30 secondes.
Les mesures IoT sont collectées toutes les 30 secondes depuis les capteurs.
