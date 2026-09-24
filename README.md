# Zero-Trust OT Lab — AtlantIndustries

> TP guidé et **déployable** pour le Chapitre 4 — *Zero-Trust & cybersécurité industrielle OT*
> (M2 BLOC 2 — Architecture & Cybersécurité).

Ce dépôt transforme le TP « papier » en **projet réel** : deux environnements
conteneurisés que les étudiants démarrent, attaquent, puis sécurisent. La
segmentation n'est pas simulée dans du texte — ce sont de **vrais réseaux
Docker isolés**, et la passerelle est un **vrai PEP/PDP** (NIST SP 800-207)
dont chaque règle est rattachée à l'un des cinq principes du cours.

---

## Le pitch pédagogique

| Mode | Fichier | Ce que l'étudiant observe |
|------|---------|---------------------------|
| **Réseau plat** (château-fort) | `docker-compose.legacy.yml` | Un poste IT compromis atteint **directement** l'automate → la vanne s'ouvre. Échec de sécurité. |
| **Zero-Trust** (segmenté) | `docker-compose.yml` | La même attaque est **bloquée deux fois** : par la segmentation réseau, puis par la politique du PEP. |

Le contraste entre les deux commandes `make legacy-attack` / `make attack`
est le cœur du TP.

---

## Architecture (mode Zero-Trust)

```
        it_zone                dmz            ot_supervision      ot_terrain
   ┌──────────────┐                                                          
   │  attacker    │─────┐                                                    
   │ (poste IT    │     │                                                    
   │  compromis)  │     ▼                                                    
   └──────────────┘  ┌─────────────────────────────────────────────────┐   
                     │              gateway  (PEP + PDP)                │   
                     │  authentifie · évalue la politique · journalise │   
                     └───────┬─────────────────────────┬───────────────┘   
                             │                          │                   
                             ▼                          ▼                   
                       ┌───────────┐              ┌───────────┐             
                       │   scada   │              │    plc    │             
                       │ (niveau 3)│              │(niveau 1) │             
                       └───────────┘              └───────────┘             
```

Chaque réseau Docker est une **zone** ; la passerelle est le **seul conduit**.
`attacker` ne partage aucun réseau avec `plc`/`scada` : il *doit* passer par le
PEP, où la politique l'arrête. Détail complet dans [`docs/00-architecture.md`](docs/00-architecture.md).

---

## Démarrage rapide

### Prérequis
- Docker + Docker Compose v2 (`docker compose version`)
- (Optionnel, pour les tests unitaires hors Docker) Python 3.11+ et `pytest`

### 1. Le monde d'avant : réseau plat
```bash
make legacy-up          # démarre scada + plc sur un réseau unique
make legacy-attack      # l'attaquant ouvre la vanne DIRECTEMENT
make legacy-down
```

### 2. Le monde d'après : Zero-Trust
```bash
make up                 # démarre les 4 zones + la passerelle PEP/PDP
make attack             # la même attaque est bloquée
make logs               # observe les décisions du PDP (journal JSON)
make down
```

### 3. Les vues graphiques (mode Zero-Trust démarré)

La passerelle sert **deux pages web** (le lab doit tourner : `make up`) :

**a) Schéma d'architecture animé — http://localhost:8088/**

Le **plan du réseau** (postes, serveur mail, ERP/AD, passerelle, SCADA,
historian, IHM, automate, vanne) disposé selon les **niveaux de Purdue**. On
**lance l'attaque** et on regarde la **trame du pirate se propager de nœud en
nœud** : hameçonnage → poste IT compromis → tentative directe stoppée par un
**mur de segmentation** → passage par la passerelle → **DENY** du PDP. Un
bouton bascule entre **Réseau plat** (l'attaque va jusqu'à ouvrir la vanne) et
**Zero-Trust** (elle est bloquée). Boutons *Lancer / Étape suivante / Rejouer*.
Sous le schéma, un **terminal d'attaque interactif** (bac à sable pédagogique)
permet à l'étudiant de **jouer l'attaque lui-même**, branché sur la **vraie
passerelle** — chaque commande déclenche une **vraie décision du PDP** et le
schéma réagit en direct. Il suit les commentaires : `mission`, `scan`, `whoami`,
puis tente `open valve`. À chaque refus, le motif indique **quel principe
Zero-Trust** l'a bloqué et un **indice** guide l'**escalade** (changer de rôle
`use`, de zone `set zone`, de posture `set posture`) jusqu'à comprendre ce qu'il
faut réunir pour réussir. Il **récupère du butin réel** : télémétrie des
capteurs (`read sensors`), métriques (`read metrics`), état du procédé — tandis
que les données d'ingénierie (recettes, programme automate) restent, elles,
**protégées** (aucun rôle ne les obtient via le conduit).

> **Données réelles.** L'automate simule un vrai procédé (cuve, température,
> pression, débit) qui **évolue dans le temps** et **réagit aux commandes** :
> capteurs `LT-101 / TT-102 / PT-103 / FT-104`, alarmes de sécurité, ouverture
> de vanne qui provoque une chute de pression et un déversement, etc.

Cette page nécessite seulement la passerelle (et l'automate/SCADA pour les
données live du terminal) : idéale pour une démo ou une soutenance.

**b) Tableau de bord live — http://localhost:8088/live**

Branché sur le **vrai lab**. Il s'actualise toutes les 2 s et montre, couche
par couche : le **statut de chaque équipement**, les **données exposées**, le
**contrôle qui a bloqué**, l'**état live** (vanne, métriques SCADA) et le
**journal ALLOW / DENY** du PEP en temps réel. Lancez `make attack` dans un
terminal et regardez la pile se remplir.

> Les deux pages sont servies **par la passerelle** : elles n'existent qu'en
> mode Zero-Trust. Pour le contraste « réseau plat » côté conteneurs,
> `make legacy-attack` montre dans la **console** la vanne réellement ouverte
> (aucune passerelle pour arbitrer) — et la page (a) le rejoue visuellement via
> son bouton *Réseau plat*.

### 4. Vérifier la politique sans Docker
```bash
make test               # 7 tests unitaires sur le moteur de décision
```

### Tester la passerelle à la main (mode Zero-Trust démarré)
```bash
# Opérateur OT légitime depuis la supervision -> ALLOW
curl -s localhost:8088/command \
  -H "Authorization: Bearer tok-operator-ot" \
  -H "X-Source-Zone: ot_supervision" \
  -H "X-Device-Posture: managed" \
  -H "Content-Type: application/json" \
  -d '{"target":"plc","action":"OPEN_VALVE"}' | jq

# Jeton IT volé -> DENY (moindre privilège)
curl -s localhost:8088/command \
  -H "Authorization: Bearer tok-admin-it" \
  -H "X-Source-Zone: it" \
  -H "X-Device-Posture: unmanaged" \
  -H "Content-Type: application/json" \
  -d '{"target":"plc","action":"OPEN_VALVE"}' | jq
```

---

## Structure du dépôt

```
zero-trust-ot-lab/
├── README.md
├── Makefile                      # raccourcis : up / attack / test / logs ...
├── docker-compose.yml            # mode ZERO-TRUST (4 zones segmentées)
├── docker-compose.legacy.yml     # mode RÉSEAU PLAT (vulnérable)
├── .env.example
├── docs/
│   ├── 00-architecture.md        # zones/conduits, mapping Purdue, flux PEP/PDP
│   ├── 01-enonce-tp.md           # énoncé étudiant (à distribuer)
│   ├── 02-corrige.md             # corrigé formateur
│   └── 03-guide-terminal-debutant.md  # pentest guidé pas-à-pas (débutants)
├── services/
│   ├── gateway/                  # PEP + PDP
│   │   ├── policies.py           #   moteur de décision (pur, testé)
│   │   ├── identities.py         #   IAM simulé (jetons + TTL)
│   │   └── app.py                #   API HTTP (FastAPI)
│   ├── scada/                    # supervision niveau 3
│   └── plc/                      # automate niveau 1 (la « vanne »)
├── attacker/                     # scénario de mouvement latéral IT→OT
└── tests/                        # pytest sur le moteur de politique
```

---

## Correspondance avec le cours

| Notion du Chapitre 4 | Où elle vit dans le projet |
|----------------------|----------------------------|
| Modèle de Purdue (niveaux 0-5) | réseaux Docker `it_zone` / `dmz` / `ot_supervision` / `ot_terrain` |
| DMZ industrielle / zones et conduits | topologie réseau ; la passerelle est le conduit unique |
| PEP / PDP (NIST SP 800-207) | `services/gateway/app.py` + `policies.py` |
| Vérifier explicitement | authentification du jeton (`identities.py`) + posture appareil |
| Moindre privilège | matrice `RBAC` dans `policies.py` |
| Supposer la compromission | refus des commandes procédé venant de la zone IT |
| Vérifier en continu | TTL du jeton + journal d'audit JSON |
| Convergence IT/OT | scénario `attacker/attack.py` |

> ⚠️ **Cadre d'usage** : environnement de laboratoire à but pédagogique.
> Les « attaques » sont de simples requêtes HTTP vers des services simulés,
> les jetons sont en clair : à n'utiliser que dans ce lab isolé.
