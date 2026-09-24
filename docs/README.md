# 📚 Documentation — Zero-Trust OT Lab

Bienvenue dans la documentation complète du lab Zero-Trust OT. Choisis ton rôle:

---

## 👨‍🎓 Pour les étudiants

### 📖 [01 - Énoncé du TP](01-enonce-tp.md)
**Tâches et missions à accomplir**

- Objectifs du TP
- Scénario d'attaque
- Missions guidées
- Critères de succès

📌 **Commence ici!**

### 🖥️ [03 - Guide Terminal Débutant](03-guide-terminal-debutant.md)
**Pentest guidé pas-à-pas**

- Commandes de base
- Exemples concrets
- Explication de chaque étape
- Indices et solutions

💡 **Besoin d'aide? C'est ici!**

---

## 👨‍🏫 Pour les formateurs

### 🏗️ [00 - Architecture détaillée](00-architecture.md)
**Topologie réseau, zones, conduits**

- Modèle Purdue (niveaux 0-5)
- Réseaux Docker isolés
- Flux du PEP/PDP
- Mapping NIST SP 800-207

📋 **Compréhension générale du système**

### ✅ 02 - Corrigé complet (Solution)
**Solutions et attentes**

> ⚠️ **Réservé aux formateurs**
> 
> Le corrigé n'est pas disponible publiquement pour éviter les fuites.
> Contacte les auteurs pour l'accès formateur.

- Réponses aux missions
- Explications pédagogiques
- Pièges communs
- Extensions possibles

📧 **Demande l'accès: amardjebabla10@gmail.com**

---

## 🚀 Déploiement

### 📱 [GitHub Codespaces](../README.md#codespaces)
**Zéro installation pour les étudiants**

- Lancer directement depuis GitHub
- Services auto-lancés
- Accès immédiat

### ☁️ [Oracle Cloud Always Free](../DEPLOY-ORACLE.md)
**Démo publique gratuite illimitée**

- Deployment automatisé
- Exposition publique via Cloudflare
- Zéro frais

---

## 📊 Structure de la documentation

```
docs/
├── README.md                        ← Vous êtes ici
├── 00-architecture.md              (formateurs)
├── 01-enonce-tp.md                 (étudiants)
├── 02-corrige.md                   (formateurs)
├── 03-guide-terminal-debutant.md   (étudiants)
└── screenshots/
    ├── architecture.png
    └── dashboard-live.png
```

---

## 🎯 Quick Start par rôle

### Je suis un étudiant
```
1. Lis 01-enonce-tp.md (tâches)
2. Ouvre GitHub Codespaces
3. Fais make up
4. Lance make attack
5. Consulte 03-guide-terminal-debutant.md si besoin
```

### Je suis un formateur
```
1. Lis 00-architecture.md (système)
2. Lis 02-corrige.md (solutions)
3. Deploy sur Oracle Cloud (voir DEPLOY-ORACLE.md)
4. Donne le lien Codespaces/public aux étudiants
5. Consulte les logs et rapports
```

### Je veux déployer
```
1. GitHub Codespaces → README.md#codespaces
2. Oracle Cloud → DEPLOY-ORACLE.md
3. Local Docker → make up
```

---

## 📖 Correspondance cours ↔ Lab

| Chapitre | Concept | Implémentation |
|----------|---------|---|
| 4.1 | Modèle Purdue | Réseaux Docker `it_zone`, `ot_supervision`, `ot_terrain` |
| 4.2 | Zones & conduits | Topologie réseau; passerelle = seul conduit |
| 4.3 | PEP/PDP | `services/gateway/` + `policies.py` |
| 4.4 | Vérifier explicitement | Authentification jeton + posture |
| 4.5 | Moindre privilège | Matrice RBAC dans `policies.py` |
| 4.6 | Supposer compromission | Refus depuis zone IT |
| 4.7 | Vérifier continuellement | TTL jeton + audit JSON |
| 4.8 | Micro-segmentation | Réseaux Docker isolés |

---

## 🔑 Concepts clés

### Authentification
- Jetons en clair (démo)
- TTL (expiration)
- Validation IAM

### Politique (RBAC)
- Rôles: `admin-it`, `operator-ot`, `maintenance`
- Ressources: `plc`, `scada`
- Actions: `READ`, `WRITE`, `EXECUTE`

### Segmentation
- 4 réseaux Docker isolés
- Passerelle unique conduit
- Aucune communication directe

### Audit
- Logs JSON en temps réel
- Décisions ALLOW/DENY
- Raison du blocage

---

## 💡 Ressources externes

- [NIST SP 800-207](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-207.pdf) — Zero Trust Architecture
- [IEC 62443](https://en.wikipedia.org/wiki/IEC_62443) — Industrial Automation and Control Systems Security
- [Purdue Model](https://en.wikipedia.org/wiki/Purdue_Enterprise_Reference_Architecture) — Niveaux OT/IT

---

## ❓ FAQ

### Q: Combien de temps pour le TP?
**A:** 2-3h (selon le niveau)

### Q: Est-ce gratuit?
**A:** Oui! Codespaces (60h/mois) ou Oracle (illimité)

### Q: Puis-je modifier le labo?
**A:** Bien sûr! Fork le repo et customize

### Q: Les données sont-elles sécurisées?
**A:** C'est un lab simulé, pour étudiants uniquement

---

## 📞 Support

- 🐛 Issues: [GitHub Issues](https://github.com/raezon/zero-trust-ot-lab/issues)
- 💬 Discussions: [GitHub Discussions](https://github.com/raezon/zero-trust-ot-lab/discussions)
- 📧 Email: amardjebabla10@gmail.com

---

## 📄 License

MIT License — Libre d'utilisation à but éducatif

---

<div align="center">

**Made with ❤️ for Industrial Security Education**

[⬆ Back to top](#-documentation--zero-trust-ot-lab)

</div>
