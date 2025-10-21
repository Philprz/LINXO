# 🎯 COMMENCEZ ICI - Linxo Agent

> **Projet nettoyé et prêt pour le déploiement !**

---

## 📖 Quelle documentation lire ?

Selon votre besoin, commencez par le bon fichier :

### 🚀 Je veux déployer rapidement

➡️ **[QUICK_START.txt](QUICK_START.txt)**
- Format texte simple
- Étapes visuelles
- Toutes les commandes
- Temps : 30-60 minutes

### 📚 Je veux comprendre le projet

➡️ **[README.md](README.md)**
- Vue d'ensemble complète
- Fonctionnalités détaillées
- Architecture du système
- Guide d'utilisation

### 🔧 Je veux les détails techniques du déploiement

➡️ **[GUIDE_DEPLOIEMENT_VPS.md](GUIDE_DEPLOIEMENT_VPS.md)**
- Guide complet (50+ pages)
- Configuration DNS
- Installation pas-à-pas
- Configuration SSL
- Dépannage avancé

### 📊 Je veux savoir ce qui a été fait

➡️ **[RESUME_PROJET.md](RESUME_PROJET.md)**
- Situation initiale
- Travail effectué
- Nettoyage et organisation
- Fichiers créés
- Checklist finale

### 📁 Je veux voir tous les fichiers créés

➡️ **[FICHIERS_CREES.md](FICHIERS_CREES.md)**
- Liste de tous les fichiers
- Rôle de chaque fichier
- Scripts disponibles
- Templates de configuration

---

## 🎯 Déploiement en 3 étapes

### 1️⃣ Préparer (5 minutes)

```bash
# Sur votre machine locale
cd /c/Users/PhilippePEREZ/OneDrive/LINXO
bash deploy/prepare_deployment.sh
```

### 2️⃣ Transférer (2 minutes)

```bash
# Sur votre machine locale
scp /tmp/linxo_deploy_*.tar.gz ubuntu@152.228.218.1:~/
```

### 3️⃣ Installer (10 minutes)

```bash
# Sur le VPS
ssh ubuntu@152.228.218.1
tar -xzf linxo_deploy_*.tar.gz
cd linxo_deploy_*/
sudo bash deploy/install_vps.sh
```

**Puis suivre les instructions dans [QUICK_START.txt](QUICK_START.txt)**

---

## 🔑 Prérequis à préparer AVANT

- [ ] **DNS configuré** : `linxo.votredomaine.com` → `152.228.218.1`
- [ ] **Gmail App Password** : https://myaccount.google.com/apppasswords
- [ ] **Credentials OVH SMS** : application_key, application_secret, consumer_key
- [ ] **Credentials Linxo** : email, mot de passe

---

## 📂 Structure du projet (nettoyée)

```
linxo_agent/
├── linxo_connexion.py                # Module de connexion
├── agent_linxo_csv_v3_RELIABLE.py    # Moteur d'analyse ✅
├── run_linxo_e2e.py                  # Orchestrateur complet
├── run_analysis.py                   # Script simplifié
├── send_notifications.py             # Notifications
├── depenses_recurrentes.json         # Config dépenses
└── config_linxo.json                 # Config principale

deploy/
├── install_vps.sh                    # Installation VPS
├── setup_ssl.sh                      # Configuration SSL
├── cleanup.sh                        # Nettoyage projet
├── prepare_deployment.sh             # Création package
├── config_linxo.json.example         # Template config
└── api_secrets.json.example          # Template secrets

Documentation/
├── README.md                         # Vue d'ensemble
├── QUICK_START.txt                   # Démarrage rapide
├── GUIDE_DEPLOIEMENT_VPS.md          # Guide complet
├── RESUME_PROJET.md                  # Résumé exécutif
└── FICHIERS_CREES.md                 # Liste fichiers
```

---

## ✅ Checklist de déploiement

Cochez au fur et à mesure :

### Préparation
- [ ] DNS configuré et propagé
- [ ] Credentials Gmail App Password créé
- [ ] Credentials OVH SMS récupérés
- [ ] Credentials Linxo prêts

### Installation
- [ ] Package créé (`prepare_deployment.sh`)
- [ ] Package transféré sur VPS (`scp`)
- [ ] Script d'installation exécuté (`install_vps.sh`)
- [ ] Fichiers Python copiés
- [ ] `config_linxo.json` créé et rempli
- [ ] `api_secrets.json` créé et rempli
- [ ] Permissions sécurisées (chmod 600)

### SSL
- [ ] Script SSL exécuté (`setup_ssl.sh`)
- [ ] Certificat créé et valide
- [ ] Nginx configuré
- [ ] HTTPS accessible

### Tests
- [ ] Test manuel réussi (`python3 run_analysis.py`)
- [ ] Email reçu
- [ ] SMS reçu
- [ ] Cron configuré (`crontab -l`)
- [ ] Logs propres

### Validation finale
- [ ] HTTPS accessible avec cadenas vert
- [ ] Test SSL Grade A (ssllabs.com)
- [ ] Système fonctionne en automatique

---

## 🆘 Problèmes courants

### Email non reçu
➡️ Vérifier que vous utilisez un **App Password** Gmail (pas le mot de passe principal)
➡️ Créer sur : https://myaccount.google.com/apppasswords

### SMS non reçu
➡️ Vérifier les credentials OVH dans `api_secrets.json`
➡️ Vérifier le crédit SMS sur OVH Manager

### Erreur de connexion Linxo
➡️ Vérifier email/password dans `config_linxo.json`
➡️ Vérifier Chrome et ChromeDriver installés

**Plus de solutions dans [GUIDE_DEPLOIEMENT_VPS.md](GUIDE_DEPLOIEMENT_VPS.md) section Dépannage**

---

## 🎉 Résultat final

Une fois déployé, le système :

✅ S'exécute automatiquement tous les jours à 20h00
✅ Se connecte à Linxo
✅ Télécharge les transactions
✅ Analyse les dépenses (fixes vs variables)
✅ Compare au budget
✅ Envoie un email avec rapport détaillé
✅ Envoie un SMS avec résumé

Le tout de manière :
- 🔒 Sécurisée (HTTPS)
- 🎯 Fiable (100% de précision)
- 🤖 Automatique (aucune intervention)

---

## 📞 Ressources

- **OVH Manager** : https://www.ovh.com/manager/
- **Test SSL** : https://www.ssllabs.com/ssltest/
- **DNS Checker** : https://dnschecker.org/
- **Gmail App Passwords** : https://myaccount.google.com/apppasswords

---

## 🚀 Par où commencer ?

1. **Lire [QUICK_START.txt](QUICK_START.txt)** pour un déploiement rapide
2. **Ou lire [README.md](README.md)** pour comprendre le projet en détail
3. **Puis suivre [GUIDE_DEPLOIEMENT_VPS.md](GUIDE_DEPLOIEMENT_VPS.md)** pour le déploiement complet

---

**Le projet est prêt ! Bon déploiement ! 🎯**
