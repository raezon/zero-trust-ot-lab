# 🚀 Déployer sur Oracle Cloud Always Free

Guide complet pour déployer le Zero-Trust OT Lab sur la VM gratuite d'Oracle Cloud.

---

## 📋 Table des matières

1. [Créer un compte Oracle](#créer-un-compte-oracle)
2. [Créer une VM](#créer-une-vm)
3. [Déployer avec le script](#déployer-avec-le-script)
4. [Exposer publiquement](#exposer-publiquement)
5. [Troubleshooting](#troubleshooting)

---

## 🔐 Créer un compte Oracle

### Étape 1: Aller sur Oracle Cloud

1. Va sur: **https://www.oracle.com/cloud/free/**
2. Clique sur **"Start for free"** ou **"Create account"**

### Étape 2: Remplir le formulaire

```
Email: ton-email@example.com
Pays: France
Nom de compte (tenant): mon-ot-lab
```

### Étape 3: Ajouter une carte de crédit

⚠️ **Important**: Oracle demande une carte de crédit pour le Free Tier, **MAIS il n'y a aucun frais**. C'est juste pour vérifier.

- Ajoute ta carte
- Aucune charge ne sera faite (vraiment gratuit)

### Étape 4: Vérifier l'email

- Tu reçois un email de confirmation
- Clique sur le lien pour activer

### Résultat

✅ Accès gratuit illimité à:
- 2 VM (ARM Ampere - 4 cores, 24 GB RAM chacune)
- 200 GB stockage
- Bases de données, etc.

---

## 🖥️ Créer une VM

### Dans le dashboard Oracle Cloud

1. **Aller à:** Compute → Instances
2. **Clique:** "Create instance"

### Configuration recommandée

```
Name:           zero-trust-ot-lab
Image:          Ubuntu 22.04 (LTS) - Canonical
Shape:          Ampere (ARM)       ← GRATUIT
Cores:          4 (suffisant)
RAM:            24 GB              ← Gratuit
Storage:        100 GB
Public IP:      Assign (✓)
```

### SSH Key

Lors de la création:
- **Clique:** "Download SSH key pair"
- **Sauvegarde** le fichier `.key` en local
- C'est ta clé pour te connecter

### Créer l'instance

- Clique **"Create"**
- Attends ~2 min (création)
- Note l'**IP publique** (ex: `158.101.23.45`)

---

## 🚀 Déployer avec le script

### Étape 1: Se connecter à la VM

```bash
# Depuis ton ordi local
chmod 600 /chemin/vers/ta/cle.key
ssh -i /chemin/vers/ta/cle.key ubuntu@158.101.23.45
```

### Étape 2: Télécharger et lancer le script

```bash
# Sur la VM
curl -fsSL https://raw.githubusercontent.com/raezon/zero-trust-ot-lab/main/deploy-oracle.sh | bash
```

Ou manuellement:

```bash
git clone https://github.com/raezon/zero-trust-ot-lab.git
cd zero-trust-ot-lab
chmod +x deploy-oracle.sh
./deploy-oracle.sh
```

### Résultat attendu

```
🚀 Zero-Trust OT Lab — Deployment on Oracle Cloud Always Free
==============================================================

ℹ️ Step 1/5: Updating system packages...
✅ System updated
ℹ️ Step 2/5: Installing Docker...
✅ Docker installed
ℹ️ Step 3/5: Installing Docker Compose and tools...
✅ Tools installed
ℹ️ Step 4/5: Cloning Zero-Trust OT Lab...
✅ Repository cloned
ℹ️ Step 5/5: Starting Docker Compose services...
✅ Services started successfully!

🎉 Deployment Complete!
==============================================================

📊 Dashboard accessible locally:
  http://localhost:8088/dashboard
  http://localhost:8088/

📡 NEXT STEP: Expose with Cloudflare Tunnel
...
```

Le script:
- ✅ Installe Docker
- ✅ Clone ton repo
- ✅ Lance `make up`
- ✅ Installe Cloudflare Tunnel
- ⏱️ Prend ~5-10 min

---

## 🌐 Exposer publiquement avec Cloudflare Tunnel

### Pourquoi?

Sans tunnel, le lab est accessible seulement:
- Sur la VM locale (`http://localhost:8088`)
- Pas depuis Internet

Avec le tunnel:
- ✅ Accessible publiquement
- ✅ HTTPS gratuit (sécurisé)
- ✅ Pas d'ouverture de port

### Lancer le tunnel

Sur la VM, dans un nouveau terminal SSH:

```bash
cloudflared tunnel run --url http://localhost:8088
```

### Résultat

```
Your quick tunnel has been created! Visit it at (it may take a few moments to be ready):

https://abcd-1234-efgh-5678.trycloudflare.com
```

✅ Copie cette URL — c'est ton dashboard public!

### Partager avec les étudiants

```
Envoie-leur:
https://abcd-1234-efgh-5678.trycloudflare.com/dashboard
```

---

## 🔐 Sécuriser l'accès (optionnel)

### Option 1: Cloudflare Access (gratuit jusqu'à 50 users)

Si tu veux limiter l'accès (ex: seulement tes étudiants):

1. Va sur: **https://dash.cloudflare.com/**
2. Applications → Add an application
3. Ajoute des restrictions (email, organisation, etc.)

### Option 2: Token d'authentification

Ajoute dans le `.env`:

```env
DASHBOARD_TOKEN=mon-secret-123
```

Puis les utilisateurs doivent passer le token:
```
https://tunnel.url/dashboard?token=mon-secret-123
```

---

## 🔄 Auto-start (optionnel)

Pour que le lab redémarre automatiquement après un reboot:

```bash
# Sur la VM
sudo cp /tmp/zero-trust-ot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable zero-trust-ot
sudo systemctl start zero-trust-ot

# Vérifier
sudo systemctl status zero-trust-ot
```

---

## 📊 Commandes utiles

```bash
# Vérifier l'état des services
docker compose ps

# Voir les logs en temps réel
docker compose logs -f gateway

# Arrêter tous les services
docker compose down

# Redémarrer les services
docker compose restart

# Lancer une attaque
make attack

# Voir tous les conteneurs
docker ps -a
```

---

## 🆘 Troubleshooting

### ❌ "Permission denied" pour docker

```bash
# Solution
sudo usermod -aG docker $USER
newgrp docker
```

### ❌ "docker-compose: command not found"

```bash
# Solution
sudo apt-get install docker-compose-plugin
```

### ❌ Services ne démarrent pas

```bash
# Vérifier les logs
docker compose logs

# Reconstruire
docker compose down
docker compose up --build -d
```

### ❌ Port 8088 déjà utilisé

```bash
# Changer le port dans docker-compose.yml
# Remplace "8088:8000" par "8089:8000"
# Puis redémarre
docker compose down
docker compose up -d
```

### ❌ Tunnel CloudFlare "connection refused"

- Vérifie que les services tournent: `docker compose ps`
- Attends 30 secondes après `make up`
- Teste localement d'abord: `curl http://localhost:8088/`

---

## 💰 Coûts

| Composant | Coût |
|-----------|------|
| VM Oracle (4 cores, 24GB) | **Gratuit** ∞ |
| Stockage (100 GB) | **Gratuit** |
| Cloudflare Tunnel | **Gratuit** |
| Cloudflare Access | **Gratuit** (50 users) |
| **TOTAL** | **0€** 🎉 |

---

## 📚 Ressources

- [Oracle Cloud Always Free](https://www.oracle.com/cloud/free/)
- [Cloudflare Tunnel Docs](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/)
- [Docker Compose Reference](https://docs.docker.com/compose/compose-file/)

---

## ✨ Résumé

```
1. Créer compte Oracle           → 5 min
2. Créer une VM                   → 2 min
3. Copier la clé SSH             → 1 min
4. SSH sur la VM                  → 1 min
5. Lancer deploy-oracle.sh        → 10 min
6. Lancer cloudflared tunnel      → 30 sec
7. Partager l'URL publique        → 1 min

⏱️ Total: ~20 min

✅ Résultat: Lab public, gratuit, illimité!
```

---

Besoin d'aide? Ouvre une issue sur [GitHub](https://github.com/raezon/zero-trust-ot-lab/issues) 🚀
