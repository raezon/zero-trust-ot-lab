# Guide du terminal d'attaque — pour débutants en cybersécurité

> **À qui s'adresse ce guide ?** À toi, si tu n'as jamais fait de « pentest »
> (test d'intrusion) et que les mots *PLC, SCADA, Zero-Trust, PDP* ne te disent
> rien encore. On explique tout, pas à pas, sans rien supposer.

> ⚠️ **Cadre légal et éthique.** Tout se passe dans un **laboratoire simulé et
> isolé**, fourni pour apprendre. Les « attaques » sont de simples messages
> envoyés à des programmes qui *imitent* une usine. **Ne réutilise jamais ces
> techniques sur un système réel sans autorisation écrite** : c'est un délit.

---

## 1. L'histoire (le scénario)

Une entreprise, *AtlantIndustries*, fabrique des tubes en PVC. Son usine est
pilotée par des **automates** (des petits ordinateurs industriels qui ouvrent
des vannes, chauffent des cuves…).

Tu joues le rôle d'un **attaquant**. Tu as piégé un employé du service
informatique, **j.durand**, avec un e-mail d'hameçonnage. Tu contrôles
maintenant son ordinateur de bureau et tu as volé son **jeton d'accès** (une
sorte de badge numérique).

**Ta mission** : partir de ce poste bureautique et essayer d'atteindre l'usine
pour **ouvrir une vanne** (provoquer un incident physique) et **voler des
données**.

**Ce que tu vas découvrir** : dans une architecture *Zero-Trust*, ton badge
volé ne suffit pas. À chaque tentative, un « garde » invisible te bloque et te
dit pourquoi. C'est toute la démonstration.

---

## 2. Le vocabulaire minimum (glossaire)

| Mot | En clair |
|-----|----------|
| **OT** (*Operational Technology*) | l'informatique **industrielle** : ce qui pilote des machines physiques. |
| **IT** (*Information Technology*) | l'informatique **de bureau** : e-mails, ERP, PC des employés. |
| **PLC / automate** | le petit ordinateur qui commande la **vanne**, la pompe… (niveau « terrain »). |
| **SCADA** | l'écran de **supervision** : il affiche les mesures de l'usine. |
| **Capteur** | un appareil qui mesure une grandeur physique (température, pression…). |
| **Zone** | un morceau **cloisonné** du réseau (IT, usine…). On ne passe pas de l'une à l'autre librement. |
| **Modèle de Purdue** | la façon standard de ranger une usine en **niveaux** (0 = machines, 5 = Internet). |
| **Jeton / token** | ton **badge numérique** d'identité. Ici, `tok-admin-it`, `tok-operator-ot`… |
| **Rôle (RBAC)** | ce que ton badge a le **droit** de faire (lire ? commander ?). |
| **Posture de l'appareil** | l'état de l'ordinateur : `managed` (géré/sécurisé par l'entreprise) ou `unmanaged` (inconnu, non maîtrisé). |
| **Passerelle / PEP / PDP** | le **garde** unique par lequel toute demande doit passer. Il **décide** (PDP) et **applique** (PEP). |
| **ALLOW / DENY** | la décision du garde : **autorisé** / **refusé**. |
| **Zero-Trust** | le principe « **ne jamais faire confiance par défaut, vérifier à chaque fois** ». |

---

## 3. Avant de commencer

1. **Démarre le laboratoire** (dans un terminal de ton ordinateur, pas celui du navigateur) :
   ```bash
   cd zero-trust-ot-lab
   make up
   ```
2. **Ouvre la page** dans ton navigateur : <http://localhost:8088/>
3. Si tu avais déjà la page ouverte, **recharge sans cache** : `Ctrl + Shift + R`.
4. **Connecte-toi** : un écran te demande ton **nom, e-mail et groupe**. Ce n'est
   pas un mot de passe — c'est juste pour **enregistrer ta progression et ta
   note**, qui seront transmises au formateur. Remplis puis clique
   *« Commencer l'exercice »*.

Une fois connecté, un bandeau en haut affiche ta **note (sur 100)** et une barre
de progression qui montent quand tu réussis les objectifs. Le bouton
**« Objectifs »** liste tout ce que tu dois accomplir ; **« Soumettre ma note »**
envoie ton résultat quand tu as terminé.

Tu vois aussi :
- **en haut**, le **schéma de l'usine** (les ordinateurs, la passerelle, l'automate, la vanne), rangés par niveaux ;
- **en bas**, une **zone noire** : c'est **le terminal**. C'est là que tu tapes.

---

## 4. Comment utiliser les terminaux

Tu as **deux terminaux côte à côte** — les **mêmes commandes** dans deux mondes
différents :

- **① RÉSEAU PLAT** (bordure rouge) : le « château-fort ». Aucune sécurité :
  **tout réussit**. Tape `open valve` → la vanne s'ouvre ; `export recipes` →
  tu voles les recettes ; `read program` → tu voles le programme de l'automate.
  C'est le monde à **éviter**. Il te montre l'ampleur des dégâts sans Zero-Trust.
- **② ZERO-TRUST** (bordure verte) : la même attaque, mais un **garde**
  (la passerelle) vérifie **tout**. C'est ici que se fait **l'exercice noté**.

> Le bouton **Réseau plat / Zero-Trust** en haut de page **met en avant** le
> terminal correspondant (l'autre s'estompe).

**Pour utiliser un terminal :** clique dans sa zone noire, tape une commande,
appuie sur **Entrée**. La réponse s'affiche au-dessus.

Astuces :
- Flèches **↑ / ↓** = retrouver les commandes déjà tapées.
- `clear` = nettoyer l'écran. `reset` = repartir de zéro (terminal Zero-Trust).
- Les commandes s'écrivent **en minuscules**, exactement comme indiqué.
- Avant chaque action, une ligne **ℹ bleue** t'explique **ce que fait** la commande.

> Les couleurs t'aident : **vert** = autorisé, **rouge** = refusé, **bleu ℹ** =
> explication, **jaune 🔐** = MFA, **violet #** = indice, **rose** = butin volé.

### La MFA (authentification forte) dans le terminal Zero-Trust

Quand tu endosses un compte industriel (`use tok-operator-ot`), le système
exige une **MFA** — un **deuxième facteur** en plus du mot de passe, comme un
code d'application sur ton téléphone. Le terminal affiche un code de démo :
tape `mfa 135790` pour le valider. **Sans MFA validée, aucune action n'est
acceptée** — c'est le principe « vérifier explicitement ». (En vrai, ce code
change toutes les 30 secondes et n'est pas volable avec le simple mot de passe.)

---

## 5. Le parcours guidé (fais-le dans l'ordre)

Recopie chaque commande, appuie sur Entrée, **lis la réponse**, puis passe à la
suivante. À chaque étape on explique **ce qui se passe** et **pourquoi**.

### Étape 0 — Prendre ses repères

```
help
```
→ Affiche la liste des commandes.

```
mission
```
→ Rappelle ton objectif.

```
tokens
```
→ Montre les **badges** que tu as trouvés sur le poste de j.durand. Tu commences
avec `tok-admin-it` (un compte **informatique**, pas industriel).

### Étape 1 — Reconnaître le terrain

```
whoami
```
→ Interroge le service d'identité : *qui suis-je avec ce badge ?*
Réponse attendue : utilisateur **j.durand**, rôle **admin_it**. C'est un compte
IT : puissant côté bureau, mais **pas** prévu pour l'usine.

```
scan
```
→ Tu sondes le réseau depuis le poste. Résultat clé :
- la **passerelle** est joignable ;
- l'**automate** et le **SCADA** sont **INJOIGNABLES en direct**.

**Pourquoi c'est important ?** C'est la **1ʳᵉ défense : la segmentation**. Depuis
le réseau bureautique, l'usine « n'existe pas ». Tu ne peux pas l'attaquer
directement : tu es **obligé de passer par la passerelle** (le garde).

### Étape 2 — Tenter l'attaque physique (et échouer)

```
open valve
```
→ Tu demandes au garde d'ouvrir la vanne. Réponse :

> **DENY · Moindre privilège** — Le rôle 'admin_it' n'est pas autorisé à
> exécuter 'OPEN_VALVE'.

**Traduction :** ton badge IT a peut-être des droits au bureau, mais **aucun
droit d'agir sur l'usine**. C'est le principe du **moindre privilège** : chacun
n'a que ce dont il a besoin.

### Étape 3 — Escalader (voler un meilleur badge)

L'indice (en violet) t'a soufflé d'essayer un compte OT. Fais-le :

```
use tok-operator-ot
```
→ Le compte industriel exige une **MFA** (authentification forte). Le terminal
affiche un code de démo. Valide-le :

```
mfa 135790
```
→ **✓ MFA validée.** Sans elle, aucune action n'est acceptée : c'est un
**deuxième facteur** en plus du badge, difficile à voler. Maintenant réessaie :

```
open valve
```
→ Nouvelle réponse :

> **DENY · Supposer la compromission** — Commande procédé interdite depuis la
> zone 'it'.

**Traduction :** même avec le bon rôle **et** la MFA, une commande vers l'usine
**ne peut pas venir du réseau bureautique**. Le système *suppose que le poste IT
est compromis* (c'est ton cas !) et refuse.

### Étape 4 — Changer de zone

```
set zone ot_supervision
open valve
```
→ Réponse :

> **DENY · Vérifier explicitement** — Posture de l'appareil 'unmanaged'
> insuffisante.

**Traduction :** tu prétends venir de la salle de contrôle, mais ton ordinateur
n'est **pas reconnu comme géré/sécurisé** (`unmanaged`). Pour une action
sensible, il faut un poste **maîtrisé**.

### Étape 5 — Réunir toutes les conditions

```
set posture managed
open valve
```
→ Enfin :

> **ALLOW** — La vanne V-101 est ouverte.

Sur le schéma, l'automate et la vanne **passent au rouge**. Tu as réussi.

**La grande leçon :** l'attaque n'a marché que lorsque tu as réuni **les quatre
conditions à la fois** : bon **jeton** (valide, non expiré) + bon **rôle** + bonne
**zone** + bonne **posture**. Rate **une seule** → refus. C'est ça, le
Zero-Trust : on vérifie **tout, à chaque fois**. Un simple mot de passe volé ne
donne plus les clés du royaume.

### Étape 6 — Voir ce qu'on peut voler

```
read sensors
```
→ Tu récupères la **télémétrie réelle** des capteurs (`LT-101` niveau, `TT-102`
température, `PT-103` pression, `FT-104` débit). Ces valeurs **changent** à
chaque lecture : le procédé est simulé « en vrai ».

```
read metrics
```
→ Les mesures côté supervision (SCADA).

```
export recipes
```
→ Tu tentes de voler les **recettes de fabrication** (secret industriel) :

> **DENY** — donnée d'ingénierie : aucun rôle ne peut la lire via la passerelle.

**Traduction :** certaines données très sensibles ne passent **jamais** par le
conduit distant. Même en ayant tout escaladé, tu ne les obtiens pas à distance.
Le Zero-Trust protège aussi la **propriété intellectuelle**.

---

## 6. À toi de jouer — mini-défis

Essaie de deviner le résultat **avant** de taper, puis vérifie :

1. `reset` puis `use tok-expire` puis `whoami` — que se passe-t-il ? *(indice : ce badge est périmé)*
2. `stop line` une fois que tu es autorisé — quel dégât provoques-tu ?
3. `set setpoint 95` — regarde les alarmes apparaître (`read state`).
4. Reviens en arrière : `close valve`, `start line`, `reset` — remets l'usine en état.
5. Avec le badge `tok-maintenance`, que peux-tu lire ? Que ne peux-tu **pas** faire ?

---

## 7. Toutes les commandes (aide-mémoire)

| Commande | Effet |
|----------|-------|
| `help` | liste des commandes |
| `mission` | rappel du scénario |
| `tokens` | badges volés disponibles |
| `whoami` | identité de ton badge actuel |
| `scan` | sonde le réseau (montre la segmentation) |
| `use <jeton>` | endosser un badge (`tok-admin-it`, `tok-operator-ot`, `tok-maintenance`, `tok-expire`) |
| `mfa <code>` | valider l'authentification forte (démo : `mfa 135790`) |
| `set zone <zone>` | `it`, `dmz`, `ot_supervision`, `ot_terrain` |
| `set posture <p>` | `managed` ou `unmanaged` |
| `read sensors` | lire les capteurs de l'automate |
| `read metrics` | lire les mesures du SCADA |
| `read state` | lire l'état complet du procédé |
| `read program` | tenter de lire le programme de l'automate |
| `export recipes` | tenter de voler les recettes |
| `read topology` | tenter de lire le plan du réseau OT |
| `open valve` / `close valve` | ouvrir / fermer la vanne V-101 |
| `stop line` / `start line` | arrêter / redémarrer la production |
| `set setpoint <C>` | changer la consigne de chauffe (ex. `set setpoint 90`) |
| `status` | rappel de ta session (jeton, zone, posture) |
| `clear` | effacer l'écran |
| `reset` | recommencer à zéro |

---

## 8. Ce qu'il faut retenir (débriefing)

- **Le mot de passe volé ne suffit plus.** En Zero-Trust, on vérifie *l'identité,
  le rôle, la zone et l'état de l'appareil* — à **chaque** demande.
- **Deux barrières valent mieux qu'une** : la **segmentation réseau** (l'usine est
  injoignable en direct) *puis* la **politique** du garde (PEP/PDP).
- **Le moindre privilège limite les dégâts** : un compte n'a que ses droits
  stricts. Un compte IT ne commande pas une vanne.
- **« Supposer la compromission »** : on part du principe qu'un poste peut être
  piraté, donc on ne lui fait pas confiance juste parce qu'il est « à
  l'intérieur ».
- **Journalisation** : chaque décision (ALLOW/DENY) est tracée — c'est la matière
  première de la détection. Vois-la sur le tableau de bord <http://localhost:8088/live>.

> Les cinq principes correspondent, dans le code, au fichier
> `services/gateway/policies.py`. Va y jeter un œil : tu reconnaîtras chaque
> refus que tu as provoqué.
