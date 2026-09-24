# Déployer le lab gratuitement (permanent)

Le lab local (`make up`) utilise 4 réseaux Docker segmentés. Pour un hébergement
**gratuit en ligne**, on regroupe les 3 services dans **un seul conteneur** via le
`Dockerfile` à la racine : seule la passerelle est exposée, PLC et SCADA restent
en interne (`127.0.0.1`). L'expérience web (schéma animé, 2 terminaux, dashboard,
LMS) fonctionne à l'identique.

> ⚠️ Sur les offres gratuites, le **stockage est éphémère** : les notes des
> étudiants (`lab_data`) sont réinitialisées à chaque redéploiement/veille. Parfait
> pour une démo ; pour une vraie session notée, garde le lab en local ou branche
> une base externe.

---

## Option 1 — Hugging Face Spaces (recommandé : gratuit, sans carte)

1. Crée un compte sur <https://huggingface.co> → **New Space**.
2. **SDK : Docker** (Blank). Nom au choix, visibilité *Public*.
3. Dans l'onglet **Files** du Space, ajoute **tout le contenu du repo**
   (glisser-déposer, ou `git push` vers le remote du Space).
   Le `Dockerfile` à la racine sera utilisé automatiquement.
4. Édite le `README.md` du Space pour qu'il commence par cet en-tête (nécessaire à HF) :
   ```
   ---
   title: Zero-Trust OT Lab
   emoji: 🛡️
   colorFrom: green
   colorTo: blue
   sdk: docker
   app_port: 7860
   pinned: false
   ---
   ```
5. Le Space se construit puis démarre. URL permanente du type
   `https://<toi>-zero-trust-ot-lab.hf.space`.

> Le Space se met en veille après 48 h sans visite et se réveille au premier accès.

---

## Option 2 — Render (gratuit, URL permanente)

1. Pousse le repo sur **GitHub** (voir les commandes git plus bas).
2. Sur <https://render.com> → **New > Blueprint** → connecte le repo.
   Render lit `render.yaml` et construit le `Dockerfile`.
   *(Ou : New > Web Service > Docker, sans blueprint.)*
3. Plan **Free**. Déploiement auto à chaque `git push`.
4. URL type `https://zero-trust-ot-lab.onrender.com`.

> Le service gratuit s'endort après 15 min d'inactivité (démarrage à froid ~1 min).

---

## Option 3 — Fly.io / Google Cloud Run (quota gratuit, carte requise)

Le même `Dockerfile` convient. Ces plateformes injectent la variable `PORT`,
respectée par `deploy/start.sh`. Elles « scale to zero » (démarrage à froid).

---

## Activer l'e-mail des notes (optionnel, toutes plateformes)

Ajoute ces variables d'environnement dans le tableau de bord de la plateforme
(ne les mets JAMAIS dans le code) — pour Gmail, un **mot de passe d'application** :

```
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=ton.adresse@gmail.com
SMTP_PASS=mot_de_passe_application
REPORT_TO=amardjebabla10@gmail.com
```

Sans ces variables, le formateur récupère les notes via
`https://<ton-url>/lab/report.csv?code=prof`.

---

## Pousser sur GitHub (prérequis pour Render)

```
cd zero-trust-ot-lab
git init && git add -A
git commit -m "Zero-Trust OT lab + déploiement conteneur unique"
git branch -M main
git remote add origin https://github.com/<toi>/zero-trust-ot-lab.git
git push -u origin main
```

> Vérifie que `.env` (secrets SMTP) est bien ignoré par git — seul `.env.example`
> doit être versionné.
