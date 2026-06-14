# Questionnaire de cadrage — Phase 2 : Automatisation des entrepôts

Destiné à : Direction des Opérations + Responsables d'exploitation
Date cible de l'interview : À planifier

---

## 1. Objectifs métier de l'automatisation

1. Quels sont les 3 principaux problèmes que vous souhaitez résoudre avec l'automatisation ?
2. Quel est le coût estimé des pertes actuelles liées aux mauvaises conditions de stockage ?
3. Avez-vous des objectifs chiffrés (ex : réduire les pertes de X%, atteindre Y% de conformité) ?
4. L'automatisation doit-elle être déployée dans tous les entrepôts simultanément ou par priorité ?

---

## 2. Contraintes de sécurité

5. Qui est responsable légalement en cas de dommages causés par un actionneur automatisé ?
6. Quelles certifications ou normes de sécurité électrique s'appliquent dans chaque pays ?
7. Comment gérer une panne du système de contrôle ? L'entrepôt doit-il rester opérable ?
8. Qui peut déclencher un arrêt d'urgence ? (opérateur local, siège, système automatique)
9. Y a-t-il des risques spécifiques liés aux marchandises (café vert = denrée alimentaire) ?

---

## 3. Limites de l'automatisation acceptables

10. Quelles décisions souhaitez-vous que le système prenne seul vs. toujours superviser ?
    - Activation chauffage : [ ] Automatique  [ ] Confirmation requise
    - Déshumidification : [ ] Automatique  [ ] Confirmation requise
    - Ventilation : [ ] Automatique  [ ] Confirmation requise
11. Y a-t-il des plages horaires où l'automatisation doit être suspendue ?
    (ex : maintenance, nettoyage, chargements)
12. Quel est le temps de réaction maximal acceptable entre la détection d'une dérive et l'action ?

---

## 4. Modalités de maintenance et d'exploitation

13. Qui effectue la maintenance des actionneurs (chauffage, ventilateurs) ? Technicien interne ou prestataire ?
14. Quelle est la procédure en cas de panne d'un actionneur pendant un week-end ?
15. Les opérateurs locaux ont-ils des compétences techniques pour intervenir sur les équipements ?
16. Souhaitez-vous un mode "test" permettant de simuler les commandes avant mise en production ?
17. Comment former les équipes locales à ce nouvel outil ?

---

## 5. Tolérances et modes manuels/automatiques

18. Pour chaque pays, les seuils de déclenchement des actionneurs doivent-ils être différents des seuils d'alerte ?
19. En mode manuel, le système doit-il quand même logger les conditions et alerter ?
20. Après un arrêt d'urgence manuel, le passage en mode automatique doit-il être :
    - [ ] Automatique après X minutes
    - [ ] Manuel par un opérateur
    - [ ] Nécessite validation du siège

---

## 6. Priorités de déploiement

21. Quel entrepôt (pays) prioriser pour le premier déploiement pilote ?
22. Sur quelle durée souhaitez-vous tester en mode "supervision only" avant d'activer les commandes ?
23. Quels critères définissent le succès du pilote pour passer au déploiement complet ?

---

## 7. Risques et scénarios d'incident

24. Que se passe-t-il si le réseau Wi-Fi local tombe pendant qu'un chauffage est actif ?
25. Comment gérer un capteur défaillant qui envoie des valeurs erronées (ex : 0°C ou 99°C) ?
26. Y a-t-il eu des incidents passés liés aux conditions de stockage que nous devons éviter ?
27. Quel est le plan de continuité si le système de contrôle est complètement inopérant ?

---

## Notes de l'interviewer

*(à compléter pendant l'interview)*
