# Linxo Agent V2.0 - Documentation Complète

> **Version 2.0** - Architecture refactorisée, fiable et multi-environnement

---

## Table des matières

1. [Vue d'ensemble](#vue-densemble)
2. [Nouveautés de la V2.0](#nouveautés-de-la-v20)
3. [Prérequis](#prérequis)
4. [Installation locale (Windows/macOS/Linux)](#installation-locale)
5. [Configuration](#configuration)
6. [Utilisation](#utilisation)
7. [Déploiement sur VPS](#déploiement-sur-vps)
8. [Dépannage](#dépannage)
9. [Architecture technique](#architecture-technique)

---

## Vue d'ensemble

Linxo Agent est un système automatisé qui :

1. ✅ Se connecte à votre compte Linxo
2. ✅ Télécharge vos transactions bancaires au format CSV
3. ✅ Analyse vos dépenses (fixes vs variables)
4. ✅ Compare vos dépenses à votre budget
5. ✅ Vous envoie un rapport détaillé par email
6. ✅ Vous envoie un résumé par SMS

**Le tout de manière automatique, fiable et sécurisée.**

---

## Nouveautés de la V2.0

### 🎯 Problèmes résolus

- ❌ **AVANT** : Chemins hardcodés pour Linux uniquement → Ne fonctionnait pas sur Windows
- ✅ **MAINTENANT** : Détection automatique de l'environnement (Windows/Linux/macOS)

- ❌ **AVANT** : Configuration fragmentée (`.env`, `config_linxo.json`, `api_secrets.json`)
- ✅ **MAINTENANT** : Une seule source de vérité (`.env`)

- ❌ **AVANT** : Système de notifications fragmenté (OVH/Brevo)
- ✅ **MAINTENANT** : Système unifié via SMTP Gmail + OVH SMS

- ❌ **AVANT** : Pas de gestion d'erreurs robuste
- ✅ **MAINTENANT** : Gestion complète des erreurs et logs clairs

### 🚀 Nouvelles fonctionnalités

- **Configuration unifiée** : Tout se configure depuis le fichier `.env`
- **Multi-environnement** : Fonctionne en local (dev) et sur VPS (prod) sans modification
- **Architecture modulaire** : Modules séparés pour chaque fonctionnalité
- **Logs clairs** : Messages d'erreur explicites avec format `[TYPE] message`
- **Mode test** : Possibilité de tester chaque module indépendamment
- **Arguments CLI** : Contrôle fin via ligne de commande

---

## Prérequis

### Logiciels requis

- **Python 3.8+**
- **Google Chrome** (pour Selenium)
- **ChromeDriver** compatible avec votre version de Chrome

### Comptes et credentials requis

1. **Compte Linxo** (email + mot de passe)
2. **Compte Gmail** avec **App Password** (pas le mot de passe principal)
   - Créer ici : https://myaccount.google.com/apppasswords
3. **Compte OVH SMS** (optionnel pour les SMS)
   - Service name, app secret

---

## Installation locale

### 1. Cloner le projet

```bash
git clone <votre-repo>
cd LINXO
```

### 2. Installer les dépendances Python

```bash
pip install -r requirements.txt
```

### 3. Configurer le fichier `.env`

Copier le fichier exemple et le remplir :

```bash
cp .env.example .env
```

Éditer `.env` avec vos vraies informations :

```bash
# Linxo Credentials
LINXO_EMAIL=votre-email@example.com
LINXO_PASSWORD=votre-mot-de-passe

# Email Configuration (Gmail)
SENDER_EMAIL=votre-gmail@gmail.com
SENDER_PASSWORD=votre-app-password-gmail
NOTIFICATION_EMAIL=destinataire1@example.com, destinataire2@example.com

# SMS Configuration (OVH)
OVH_EMAIL_ENVOI=email2sms@ovh.net
OVH_APP_SECRET=votre-secret
OVH_SERVICE_NAME=sms-xxXXXXXX-X
SMS_SENDER=VotreNom
SMS_RECIPIENT=+33XXXXXXXXX, +33YYYYYYYYY

# Budget Configuration
BUDGET_VARIABLE=1300

# Domain Configuration (pour VPS uniquement)
DOMAIN_NAME=votre-domaine.com
ADMIN_EMAIL=admin@votre-domaine.com
```

### 4. Générer le fichier `api_secrets.json`

```bash
cd linxo_agent
python generate_api_secrets.py
```

Cela créera automatiquement `api_secrets.json` depuis votre `.env`.

### 5. Vérifier la configuration

```bash
python linxo_agent.py --config-check
```

Vous devriez voir un résumé de votre configuration.

---

## Configuration

### Structure des fichiers de configuration

```
LINXO/
├── .env                          # Configuration principale (SENSIBLE - ne pas committer)
├── .env.example                  # Template de configuration
├── api_secrets.json              # Généré automatiquement depuis .env
├── linxo_agent/
│   ├── depenses_recurrentes.json # Liste des dépenses fixes
│   └── config_linxo.json         # OBSOLÈTE (V1) - ne plus utiliser
```

### Fichier `depenses_recurrentes.json`

Ce fichier liste vos dépenses récurrentes (fixes) :

```json
{
  "depenses_fixes": [
    {
      "libelle": "CA CONSUMER FINANCE",
      "compte": "LCL",
      "identifiant": "SOFINCO",
      "commentaire": "Rachat crédit",
      "montant": 982.0,
      "categorie": "CREDITS"
    }
  ],
  "totaux": {
    "budget_variable_max": 1300
  }
}
```

**Note** : Le budget dans `.env` a priorité sur celui du JSON.

---

## Utilisation

### Workflow complet (recommandé)

Exécute toutes les étapes : téléchargement → analyse → notifications

```bash
python linxo_agent.py
```

### Analyser un CSV sans télécharger

Utilise le dernier CSV disponible dans `data/` :

```bash
python linxo_agent.py --skip-download
```

### Analyser un fichier CSV spécifique

```bash
python linxo_agent.py --csv-file /chemin/vers/export.csv
```

### Tester sans envoyer de notifications

Utile pour vérifier que tout fonctionne :

```bash
python linxo_agent.py --skip-notifications
```

### Analyser un CSV existant sans notifications

Mode test complet :

```bash
python linxo_agent.py --csv-file data/export.csv --skip-notifications
```

### Tester les modules individuellement

**Tester la connexion Linxo :**
```bash
cd linxo_agent
python linxo_connexion.py
```

**Tester l'analyse :**
```bash
cd linxo_agent
python analyzer.py
```

**Tester les notifications :**
```bash
cd linxo_agent
python notifications.py
```

---

## Déploiement sur VPS

### Préparer le déploiement

1. Le système détectera automatiquement l'environnement VPS (Linux)
2. Les chemins seront automatiquement adaptés (`/home/ubuntu/...`)

### Installation sur VPS

```bash
# 1. Copier le projet sur le VPS
scp -r LINXO ubuntu@votre-vps-ip:~/

# 2. Se connecter au VPS
ssh ubuntu@votre-vps-ip

# 3. Installer Python et dépendances
cd ~/LINXO
sudo apt update
sudo apt install python3 python3-pip google-chrome-stable
pip3 install -r requirements.txt

# 4. Configurer le .env sur le VPS
nano .env
# (remplir avec vos vraies informations)

# 5. Générer api_secrets.json
cd linxo_agent
python3 generate_api_secrets.py

# 6. Tester
python3 ../linxo_agent.py --skip-notifications
```

### Automatiser avec cron

```bash
# Éditer le crontab
crontab -e

# Ajouter cette ligne pour exécuter tous les jours à 20h00
0 20 * * * cd /home/ubuntu/LINXO && /usr/bin/python3 linxo_agent.py >> /home/ubuntu/logs/cron.log 2>&1
```

---

## Dépannage

### Problème : "Module 'dotenv' not found"

**Solution :**
```bash
pip install python-dotenv
```

### Problème : "Credentials Linxo manquants"

**Causes possibles :**
1. Fichier `.env` absent ou mal placé
2. Variables non renseignées dans `.env`

**Solution :**
```bash
# Vérifier que .env existe
ls -la .env

# Vérifier le contenu
cat .env | grep LINXO_EMAIL

# Régénérer api_secrets.json
cd linxo_agent
python generate_api_secrets.py
```

### Problème : "Impossible d'initialiser le navigateur"

**Solution :**
- Vérifier que Chrome est installé
- Installer ChromeDriver :
  ```bash
  # Ubuntu/Debian
  sudo apt install chromium-chromedriver

  # macOS
  brew install chromedriver

  # Windows
  # Télécharger depuis https://chromedriver.chromium.org/
  ```

### Problème : "Email non reçu"

**Causes possibles :**
1. Utilisation du mot de passe Gmail principal au lieu de l'App Password
2. App Password invalide
3. Serveur SMTP Gmail bloque la connexion

**Solution :**
1. Créer un nouveau App Password : https://myaccount.google.com/apppasswords
2. Mettre à jour `SENDER_PASSWORD` dans `.env`
3. Régénérer `api_secrets.json`
4. Tester :
   ```bash
   cd linxo_agent
   python notifications.py
   ```

### Problème : "SMS non reçu"

**Solution :**
1. Vérifier les credentials OVH dans `.env`
2. Vérifier le crédit SMS sur OVH Manager
3. Vérifier le format du numéro : `+33XXXXXXXXX` (sans espaces)

---

## Architecture technique

### Modules principaux

```
linxo_agent/
├── config.py              # Configuration unifiée multi-environnement
├── linxo_connexion.py     # Connexion Selenium + téléchargement CSV
├── analyzer.py            # Analyse des dépenses
├── notifications.py       # Envoi email + SMS
└── generate_api_secrets.py # Génération api_secrets.json

linxo_agent.py            # Point d'entrée principal (orchestrateur)
```

### Flux de données

```
.env → config.py → [tous les modules]
                ↓
     linxo_agent.py (orchestrateur)
                ↓
     ┌──────────┴───────────┬──────────────┐
     ↓                      ↓              ↓
linxo_connexion.py     analyzer.py    notifications.py
     ↓                      ↓              ↓
   CSV file          Analyse result     Email + SMS
```

### Détection d'environnement

Le module `config.py` détecte automatiquement :

- **Windows** : Utilise les chemins relatifs dans le projet
- **Linux (VPS)** : Utilise `/home/ubuntu/...` si disponible
- **Linux (local)** : Utilise les chemins relatifs dans le projet

---

## Support

Pour toute question ou problème :

1. Vérifier cette documentation
2. Vérifier les logs dans `logs/`
3. Exécuter `python linxo_agent.py --config-check`
4. Tester les modules individuellement

---

## Licence

Usage personnel uniquement.

---

**Version 2.0** - Décembre 2024
Refactorisé pour fiabilité, simplicité et multi-environnement.
