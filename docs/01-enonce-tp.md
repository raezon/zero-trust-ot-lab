# TD4 — TP guidé : sécuriser AtlantIndustries en Zero-Trust

**Durée indicative :** 2 h · **Modalité :** binômes · **Rendu :** voir §5

## Mise en situation

AtlantIndustries exploite deux sites (Nantes, Wrocław), un SCADA Wonderware et
≈250 capteurs/automates par site. Un poste bureautique a été compromis par
hameçonnage. Vous allez démontrer, puis corriger, le chemin qui mène de ce
poste IT jusqu'à l'ouverture d'une **vanne** sur le procédé physique.

## Objectifs

À l'issue du TP, vous saurez :
- montrer expérimentalement le **mouvement latéral** IT → OT sur un réseau plat ;
- expliquer en quoi la **segmentation** puis le **Zero-Trust** le neutralisent ;
- lire une politique PEP/PDP et la relier aux **cinq principes** du chapitre.

## Prérequis
- Docker + Docker Compose v2 installés (`docker compose version`).
- Avoir relu : modèle de Purdue, DMZ industrielle, zones/conduits, PEP/PDP.

---

## Partie 1 — Le monde d'avant (réseau plat)

```bash
make legacy-up
make legacy-attack
```

**Q1.** Observez la sortie de la *Tentative A*. L'attaquant, sur le même réseau
que l'automate, a-t-il réussi à ouvrir la vanne ? Reproduisez le résultat avec
un simple `curl` (indice : `plc` est exposé sur `localhost:8081`).

**Q2.** Expliquez, avec le vocabulaire du cours, pourquoi cette architecture
« château-fort » a échoué. Quel niveau de Purdue a été atteint depuis quel
niveau ?

```bash
make legacy-down
```

---

## Partie 2 — Le monde d'après (Zero-Trust)

```bash
make up
make attack
```

**Q3.** Cette fois, deux tentatives sont jouées.
- *Tentative A* (accès direct au PLC) : quel message obtient l'attaquant ?
  Ouvrez `docker-compose.yml` et expliquez, réseau par réseau, **pourquoi**
  l'automate est injoignable.
- *Tentative B* (via la passerelle, jeton IT volé) : quel code HTTP et quel
  **principe** la passerelle invoque-t-elle pour refuser ?

**Q4.** Consultez le journal d'audit :
```bash
make logs        # (Ctrl-C pour quitter)
```
Relevez une ligne de refus. Quels champs permettraient à une supervision IT/OT
de corréler cet événement avec une alerte côté IT ?

**Q5.** Jouez maintenant un accès **légitime** et montrez qu'il passe :
```bash
curl -s localhost:8088/command \
  -H "Authorization: Bearer tok-operator-ot" \
  -H "X-Source-Zone: ot_supervision" \
  -H "X-Device-Posture: managed" \
  -H "Content-Type: application/json" \
  -d '{"target":"plc","action":"OPEN_VALVE"}'
```
Puis tentez la **même action** avec `X-Source-Zone: it`. Que se passe-t-il, et
quel principe est en jeu ?

---

## Partie 3 — Questions de réflexion

1. **Moindre privilège** — Pourquoi un identifiant IT *valide* ne suffit-il pas
   à commander l'automate ? Où, dans le code, cette décision est-elle prise ?
2. **Microsegmentation** — En quoi les réseaux Docker séparés jouent-ils le rôle
   des « zones et conduits » de l'IEC 62443 ? Qu'apporte cette barrière que la
   politique applicative n'apporte pas, et inversement ?
3. **Authentification continue** — Le jeton `tok-expire` est déjà expiré.
   Testez-le et expliquez ce que « vérifier en continu » change par rapport à
   une authentification uniquement à la connexion.
4. **Compromis sécurité / exploitation** — Le cours insiste : jamais d'IPS en
   coupure sur le niveau 0/1. Comment ce lab respecte-t-il ce principe ? Quel
   serait le risque d'un blocage *actif* directement sur l'automate ?

---

## Partie 4 — Pour aller plus loin (extensions)

- **E1.** Ajoutez un rôle `superviseur` en lecture seule sur le SCADA et écrivez
  un test dans `tests/test_policies.py` qui le vérifie.
- **E2.** Ajoutez une règle « fenêtre horaire » : les commandes procédé ne sont
  autorisées qu'entre 6 h et 22 h (nouveau principe contextuel).
- **E3.** Écrivez un petit script qui lit le journal JSON de la passerelle et
  compte les refus par `principle` : esquisse d'un tableau de bord de détection.

---

## 5. Rendu attendu

- Réponses argumentées Q1→Q5 + les 4 questions de réflexion.
- Les sorties console des deux modes (copie ou capture).
- Un schéma d'architecture cible AtlantIndustries situant chaque composant dans
  le modèle de Purdue et justifiant **chaque conduit** par un principe
  Zero-Trust (cf. mission du TD4).
- (Bonus) une extension parmi E1–E3, avec le test associé qui passe.
