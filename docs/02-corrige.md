# Corrigé formateur — TD4 Zero-Trust OT

> Document réservé à l'enseignant. Contient les réponses attendues, les sorties
> de référence et les corrigés des extensions.

## Sorties de référence

### Mode réseau plat (`make legacy-attack`)
La *Tentative A* aboutit : le PLC renvoie `200` et `valve_open: true`, message
« VANNE OUVERTE — procédé physique impacté ». La *Tentative B* échoue seulement
parce qu'aucune passerelle n'existe (`gateway` injoignable), ce qui est normal.

### Mode Zero-Trust (`make attack`)
- *Tentative A* : `httpx` lève une erreur de résolution/connexion → « Automate
  injoignable » → attaque bloquée **au réseau**.
- *Tentative B* : la passerelle répond `403` avec
  `principle: "Moindre privilege"` (le rôle `admin_it` n'a pas `OPEN_VALVE`).

## Réponses

**Q1.** Oui, l'attaquant ouvre la vanne. `curl -s -XPOST localhost:8081/execute
-H 'Content-Type: application/json' -d '{"action":"OPEN_VALVE"}'` renvoie l'état
`valve_open: true`. Sur un réseau plat, rien ne s'y oppose.

**Q2.** Le modèle périmétrique fait confiance à tout ce qui est « à
l'intérieur ». Le poste compromis (niveau 4-5, IT) atteint sans obstacle le
niveau 1 (automate) : c'est le **mouvement latéral**. Aucune DMZ, aucune zone,
aucun conduit contrôlé n'interrompt la propagation.

**Q3.**
- *Tentative A* : message « Automate injoignable ». Dans `docker-compose.yml`,
  `attacker` est sur `it_zone` seulement ; `plc` est sur `ot_terrain`. Sans
  réseau partagé, le nom `plc` n'est pas résolvable → il n'existe aucun conduit
  direct IT→OT. C'est la microsegmentation.
- *Tentative B* : code `403`, principe **« Moindre privilège »**. L'identité est
  authentifiée (jeton IT valide) mais le rôle `admin_it` n'a pas le droit
  `OPEN_VALVE`. (Si l'on donnait un jeton `operator_ot` depuis `it`, ce serait
  le principe **« Supposer la compromission »** — commande refusée hors zone
  OT.)

**Q4.** Une ligne de refus contient `user`, `role`, `action`, `target`,
`source_zone`, `device_posture`, `principle`, `ts`. Pour corréler avec l'IT :
`user`/`role` (même identité qu'un événement d'auth Azure AD), `source_zone`
(origine du flux), `ts` (fenêtre temporelle). C'est exactement la
**corrélation IT↔OT** évoquée en Section 4.

**Q5.** Le premier appel (opérateur OT, zone OT, poste maîtrisé) → `ALLOW`, la
vanne s'ouvre. Le même appel avec `X-Source-Zone: it` → `403`, principe
**« Supposer la compromission »** : une commande procédé ne doit jamais provenir
de la zone IT, même émise par un compte légitime.

## Questions de réflexion

1. **Moindre privilège.** Parce que l'autorisation n'est pas liée au *réseau*
   mais au *rôle*. La décision est prise dans `policies.evaluate()`, règle n°3,
   via la matrice `RBAC`. `admin_it` ne mappe que des lectures. Point clé du
   cours : *segmenter sans revoir les droits d'accès* est une erreur — ici les
   deux sont traités.

2. **Microsegmentation.** Les réseaux Docker = zones ; la passerelle = conduit
   unique et documenté. La barrière **réseau** stoppe *tout* trafic non prévu (y
   compris scans, protocoles non authentifiés comme Modbus) sans exécuter la
   moindre logique applicative. La barrière **applicative** (PDP) apporte la
   granularité : qui, quelle action, dans quel contexte. Les deux sont
   complémentaires — défense en profondeur.

3. **Authentification continue.** `tok-expire` renvoie `403`, principe
   **« Vérifier en continu »**. Une auth « à la connexion seulement » laisserait
   une session compromise valable indéfiniment ; le TTL force une réévaluation.
   Test : `curl` avec `Bearer tok-expire`.

4. **Compromis sécurité / exploitation.** Le lab ne place aucun blocage *en
   coupure* sur l'automate : le PLC n'est jamais interrompu par la sécurité, il
   est seulement *inatteignable* sans décision favorable en amont (en DMZ). Un
   IPS actif en coupure sur le niveau 0/1 pourrait, sur un faux positif,
   interrompre une trame et arrêter un procédé physique en plein cycle — un
   incident de sécurité *physique*, pas un simple incident IT.

## Corrigés des extensions

**E1 — rôle `superviseur` (lecture seule SCADA).**
Dans `policies.py`, ajouter à `RBAC` : `"superviseur": {"READ_METRICS"}`. Test :
```python
def test_superviseur_lecture_seule():
    d = evaluate(req(action="READ_METRICS", target="scada",
                     identity={"user": "s", "role": "superviseur"}))
    assert d.effect is Effect.ALLOW
    d2 = evaluate(req(action="OPEN_VALVE",
                      identity={"user": "s", "role": "superviseur"}))
    assert d2.effect is Effect.DENY
```

**E2 — fenêtre horaire.** Ajouter un champ `hour: int` à `AccessRequest` et,
après la règle 5, une règle : si `action in COMMANDES_PROCEDE and not (6 <= hour
< 22)` → `DENY`, principe « Vérifier explicitement (contexte temporel) ». Côté
`app.py`, dériver l'heure de `time.localtime()`. Discuter en cours : c'est une
règle **contextuelle** typique du Zero-Trust (ABAC).

**E3 — mini tableau de bord.**
```python
import json, sys, collections
c = collections.Counter()
for line in sys.stdin:
    try:
        e = json.loads(line)
        if e.get("effect") == "DENY":
            c[e["principle"]] += 1
    except Exception:
        pass
for principe, n in c.most_common():
    print(f"{n:4d}  {principe}")
```
Usage : `docker compose logs gateway | python dashboard.py`. Ouvre la discussion
sur l'agrégation d'alertes vers une supervision commune IT/OT (Section 4).

## Barème indicatif (/20)
- Partie 1 (démonstration + explication) : 4
- Partie 2 (Zero-Trust, les deux barrières, lecture du 403) : 6
- Journal / corrélation IT↔OT : 2
- Questions de réflexion : 5
- Schéma d'architecture AtlantIndustries justifié : 3
- Bonus extension fonctionnelle + test : +2
