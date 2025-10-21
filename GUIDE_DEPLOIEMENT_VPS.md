# 🚀 Guide de Déploiement - Linxo Agent sur VPS OVH

## 📋 Table des matières

1. [Prérequis](#prérequis)
2. [Configuration DNS](#configuration-dns)
3. [Préparation des fichiers](#préparation-des-fichiers)
4. [Installation sur le VPS](#installation-sur-le-vps)
5. [Configuration SSL](#configuration-ssl)
6. [Vérification et tests](#vérification-et-tests)
7. [Maintenance](#maintenance)
8. [Dépannage](#dépannage)

---

## 🔧 Prérequis

### VPS OVH

D'après votre capture d'écran :
- **Modèle** : VPS-1
- **vCores** : 4
- **Mémoire** : 8 Go
- **Stockage** : 75 Go
- **OS** : Ubuntu 25.04
- **IPv4** : 152.228.218.1
- **IPv6** : 2001:41d0:305:2100::a6a6
- **Zone** : Gravelines (GRA) - France

### Domaine

- Un nom de domaine que vous avez acheté
- Accès aux paramètres DNS du domaine

### Informations nécessaires

- [ ] Email Linxo
- [ ] Mot de passe Linxo
- [ ] App Password Gmail (pour les notifications email)
- [ ] Credentials OVH SMS (application_key, application_secret, consumer_key)
- [ ] Numéros de téléphone pour les SMS
- [ ] Nom de domaine

---

## 🌐 Configuration DNS

### 1. Accéder à la gestion DNS de votre domaine

Selon votre registrar (OVH, Gandi, CloudFlare, etc.), accédez à la zone DNS.

### 2. Créer un enregistrement A

Ajoutez un enregistrement de type **A** :

```
Type: A
Nom: linxo (ou @  si vous voulez utiliser le domaine racine)
Valeur: 152.228.218.1
TTL: 300 (5 minutes)
```

**Exemple** :
- Si votre domaine est `example.com`
- Et vous créez `linxo.example.com`
- Alors l'enregistrement A pointe `linxo.example.com` → `152.228.218.1`

### 3. Vérification DNS

Attendez quelques minutes (jusqu'à 1h selon les registrars) puis testez :

```bash
# Depuis votre machine locale
nslookup linxo.votredomaine.com
# ou
dig linxo.votredomaine.com
```

Vous devez voir l'IP `152.228.218.1` dans la réponse.

---

## 📦 Préparation des fichiers

### 1. Sur votre machine locale

Créez un dossier pour préparer les fichiers :

```bash
cd ~/Desktop
mkdir linxo_deploy
cd linxo_deploy
```

### 2. Copier les fichiers essentiels

Copiez **uniquement** les fichiers nécessaires depuis votre projet :

```
linxo_deploy/
├── linxo_agent/
│   ├── linxo_connexion.py
│   ├── agent_linxo_csv_v3_RELIABLE.py
│   ├── run_linxo_e2e.py
│   ├── run_analysis.py
│   ├── send_notifications.py
│   └── depenses_recurrentes.json
├── deploy/
│   ├── install_vps.sh
│   ├── setup_ssl.sh
│   ├── config_linxo.json.example
│   └── api_secrets.json.example
└── requirements.txt
```

**NE PAS COPIER** :
- Le dossier `BACKUP_AVANT_NETTOYAGE/`
- Les fichiers de test (`test_*.py`)
- Les rapports et logs
- Les anciennes versions (`*_v2.py`, etc.)

### 3. Créer l'archive

```bash
cd ~/Desktop
tar -czf linxo_deploy.tar.gz linxo_deploy/
```

---

## 🖥️ Installation sur le VPS

### 1. Connexion SSH au VPS

```bash
ssh ubuntu@152.228.218.1
```

Si c'est votre première connexion, acceptez l'empreinte SSH.

**Note** : Si vous avez configuré une clé SSH dans OVH, utilisez-la. Sinon, utilisez le mot de passe fourni par OVH.

### 2. Mise à jour initiale

```bash
sudo apt update
sudo apt upgrade -y
```

### 3. Transfert des fichiers

Depuis votre machine **locale** (dans un autre terminal) :

```bash
scp ~/Desktop/linxo_deploy.tar.gz ubuntu@152.228.218.1:~/
```

### 4. Extraction sur le VPS

De retour sur le VPS :

```bash
cd ~
tar -xzf linxo_deploy.tar.gz
cd linxo_deploy
```

### 5. Exécution du script d'installation

```bash
chmod +x deploy/install_vps.sh
sudo bash deploy/install_vps.sh
```

Le script va :
- ✅ Installer Python 3, pip, venv
- ✅ Installer Google Chrome et ChromeDriver
- ✅ Installer les dépendances système
- ✅ Créer la structure de répertoires
- ✅ Créer l'environnement virtuel Python
- ✅ Installer les packages Python
- ✅ Configurer le cron job

**Durée estimée** : 5-10 minutes

### 6. Copier les fichiers Python

```bash
cp linxo_deploy/linxo_agent/*.py /home/ubuntu/linxo_agent/
cp linxo_deploy/linxo_agent/*.json /home/ubuntu/linxo_agent/
```

### 7. Créer les fichiers de configuration

#### a) Configuration Linxo

```bash
nano /home/ubuntu/linxo_agent/config_linxo.json
```

Contenu :

```json
{
  "linxo": {
    "url": "https://wwws.linxo.com/auth.page#Login",
    "email": "philippe@melprz.fr",
    "password": "VOTRE_MOT_DE_PASSE"
  },
  "budget": {
    "variable": 1323.73
  },
  "notification": {
    "email": "phiperez@gmail.com",
    "sender_email": "phiperez@gmail.com",
    "telephone": "+33626267421"
  }
}
```

**Sauvegardez** : `Ctrl + X`, puis `Y`, puis `Entrée`

#### b) Configuration API Secrets

```bash
nano /home/ubuntu/.api_secret_infos/api_secrets.json
```

Contenu :

```json
{
  "gmail": {
    "email": "phiperez@gmail.com",
    "password": "VOTRE_APP_PASSWORD_GMAIL"
  },
  "ovh_sms": {
    "application_key": "VOTRE_APP_KEY",
    "application_secret": "VOTRE_APP_SECRET",
    "consumer_key": "VOTRE_CONSUMER_KEY",
    "service_name": "sms-serviceXXXXXX-X",
    "sender": "LinxoAgent"
  },
  "notification_recipients": {
    "emails": [
      "phiperez@gmail.com",
      "caliemphi@gmail.com"
    ],
    "phones": [
      "+33626267421",
      "+33611435899"
    ]
  }
}
```

**Sauvegardez** : `Ctrl + X`, puis `Y`, puis `Entrée`

#### c) Sécuriser les fichiers

```bash
chmod 600 /home/ubuntu/.api_secret_infos/api_secrets.json
chmod 644 /home/ubuntu/linxo_agent/config_linxo.json
```

---

## 🔒 Configuration SSL

### 1. Vérifier que le DNS est propagé

Depuis le VPS :

```bash
nslookup linxo.votredomaine.com
```

Vous devez voir `152.228.218.1`.

### 2. Exécuter le script SSL

```bash
cd ~/linxo_deploy
chmod +x deploy/setup_ssl.sh
sudo bash deploy/setup_ssl.sh
```

Le script va vous demander :

1. **Nom de domaine** : `linxo.votredomaine.com`
2. **Email admin** : `votre-email@example.com`
3. **DNS configuré ?** : `y`
4. **Méthode de validation** : `1` (Standalone - recommandé)
5. **Configurer Nginx ?** : `y` (recommandé)

**Durée estimée** : 3-5 minutes

### 3. Vérification

```bash
sudo certbot certificates
```

Vous devez voir votre certificat listé avec une date d'expiration (90 jours).

### 4. Test SSL

Ouvrez votre navigateur et allez sur :

```
https://linxo.votredomaine.com
```

Vous devriez voir la page par défaut de Nginx avec un cadenas vert (SSL actif).

Testez la qualité du certificat sur : https://www.ssllabs.com/ssltest/

---

## ✅ Vérification et tests

### 1. Test manuel de l'application

```bash
cd /home/ubuntu/linxo_agent
source venv/bin/activate
python3 run_analysis.py
```

**Vérifiez** :
- ✅ Le script se connecte à Linxo
- ✅ Le CSV est analysé
- ✅ Un email est envoyé
- ✅ Un SMS est envoyé

### 2. Vérifier les logs

```bash
ls -lh /home/ubuntu/logs/
cat /home/ubuntu/logs/e2e_*.log
```

### 3. Vérifier le cron

```bash
crontab -l
```

Vous devez voir :

```
0 20 * * * cd /home/ubuntu/linxo_agent && /home/ubuntu/linxo_agent/venv/bin/python3 run_linxo_e2e.py >> logs/cron.log 2>&1
```

### 4. Test du cron (optionnel)

Pour tester immédiatement sans attendre 20h :

```bash
cd /home/ubuntu/linxo_agent && /home/ubuntu/linxo_agent/venv/bin/python3 run_linxo_e2e.py >> logs/cron.log 2>&1
```

---

## 🔧 Maintenance

### Logs

#### Consulter les derniers logs

```bash
# Logs du cron
tail -f /home/ubuntu/linxo_agent/logs/cron.log

# Logs E2E
ls -lt /home/ubuntu/logs/ | head -10
cat /home/ubuntu/logs/e2e_YYYYMMDD_HHMMSS.log
```

#### Nettoyer les vieux logs (plus de 30 jours)

```bash
find /home/ubuntu/logs/ -name "*.log" -mtime +30 -delete
find /home/ubuntu/data/ -name "*.csv" -mtime +30 -delete
```

### Renouvellement SSL

Le certificat SSL se renouvelle **automatiquement** tous les 90 jours via un cron job.

#### Test du renouvellement

```bash
sudo certbot renew --dry-run
```

#### Renouvellement manuel (si nécessaire)

```bash
sudo certbot renew
sudo systemctl reload nginx
```

### Mise à jour du code

Si vous modifiez le code :

1. Sur votre machine locale, modifiez les fichiers
2. Créez une nouvelle archive
3. Transférez sur le VPS
4. Remplacez les fichiers

```bash
# Sur votre machine locale
cd ~/Desktop/linxo_deploy
# (après modifications)
tar -czf linxo_update.tar.gz linxo_agent/
scp linxo_update.tar.gz ubuntu@152.228.218.1:~/

# Sur le VPS
cd ~
tar -xzf linxo_update.tar.gz
cp -r linxo_agent/*.py /home/ubuntu/linxo_agent/
```

### Mise à jour des dépendances

```bash
cd /home/ubuntu/linxo_agent
source venv/bin/activate
pip install --upgrade selenium webdriver-manager requests
```

---

## 🆘 Dépannage

### Problème : Le cron ne s'exécute pas

**Diagnostic** :

```bash
# Vérifier que cron est actif
sudo systemctl status cron

# Vérifier les logs système
sudo grep CRON /var/log/syslog | tail -20
```

**Solution** :

```bash
sudo systemctl start cron
sudo systemctl enable cron
```

### Problème : Erreur de connexion à Linxo

**Diagnostic** :

```bash
# Vérifier les credentials
cat /home/ubuntu/linxo_agent/config_linxo.json

# Tester manuellement
cd /home/ubuntu/linxo_agent
source venv/bin/activate
python3 -c "
import json
with open('config_linxo.json') as f:
    print(json.load(f))
"
```

**Solutions** :
- Vérifier que l'email et le mot de passe sont corrects
- Vérifier que Chrome et ChromeDriver sont installés : `google-chrome --version && chromedriver --version`

### Problème : Email non reçu

**Diagnostic** :

```bash
# Vérifier les credentials Gmail
cat /home/ubuntu/.api_secret_infos/api_secrets.json

# Tester l'envoi d'email
cd /home/ubuntu/linxo_agent
source venv/bin/activate
python3 send_notifications.py
```

**Solutions** :
- Vérifier que vous utilisez un **App Password** Gmail (pas votre mot de passe principal)
- Créer un App Password : https://myaccount.google.com/apppasswords
- Vérifier que l'authentification à 2 facteurs est activée sur Gmail

### Problème : SMS non reçu

**Diagnostic** :

```bash
# Vérifier les credentials OVH
cat /home/ubuntu/.api_secret_infos/api_secrets.json

# Tester l'API OVH SMS
cd /home/ubuntu/linxo_agent
source venv/bin/activate
python3 test_sms_ovh.py
```

**Solutions** :
- Vérifier les credentials OVH (application_key, application_secret, consumer_key)
- Vérifier le crédit SMS sur votre compte OVH
- Vérifier le service_name : `sms-serviceXXXXXX-X`

### Problème : SSL ne fonctionne pas

**Diagnostic** :

```bash
# Vérifier les certificats
sudo certbot certificates

# Vérifier Nginx
sudo nginx -t
sudo systemctl status nginx
```

**Solutions** :

```bash
# Redémarrer Nginx
sudo systemctl restart nginx

# Renouveler le certificat
sudo certbot renew --force-renewal
sudo systemctl reload nginx
```

### Problème : ChromeDriver incompatible

**Symptôme** : Erreur `session not created: This version of ChromeDriver only supports Chrome version XX`

**Solution** :

```bash
# Vérifier les versions
google-chrome --version
chromedriver --version

# Télécharger la bonne version de ChromeDriver
CHROME_VERSION=$(google-chrome --version | grep -oP '\d+\.\d+\.\d+')
CHROMEDRIVER_VERSION=$(curl -s "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_${CHROME_VERSION%%.*}")
wget -N "https://chromedriver.storage.googleapis.com/${CHROMEDRIVER_VERSION}/chromedriver_linux64.zip" -P /tmp
sudo unzip -o /tmp/chromedriver_linux64.zip -d /usr/local/bin/
sudo chmod +x /usr/local/bin/chromedriver
rm /tmp/chromedriver_linux64.zip

# Vérifier
chromedriver --version
```

---

## 📊 Commandes utiles

### Statut des services

```bash
# Nginx
sudo systemctl status nginx

# Cron
sudo systemctl status cron

# Certificats SSL
sudo certbot certificates
```

### Surveillance

```bash
# Espace disque
df -h

# Mémoire
free -h

# CPU
top

# Processus Chrome (si bloqué)
ps aux | grep chrome
# Tuer si nécessaire
pkill chrome
```

### Sauvegardes

```bash
# Sauvegarder la configuration
tar -czf backup_config_$(date +%Y%m%d).tar.gz \
  /home/ubuntu/linxo_agent/*.json \
  /home/ubuntu/.api_secret_infos/

# Restaurer
tar -xzf backup_config_YYYYMMDD.tar.gz -C /
```

---

## 🎯 Checklist finale

Avant de considérer le déploiement comme terminé :

- [ ] DNS configuré et propagé
- [ ] VPS accessible via SSH
- [ ] Python 3, Chrome, ChromeDriver installés
- [ ] Fichiers Python copiés dans `/home/ubuntu/linxo_agent/`
- [ ] Fichier `config_linxo.json` créé et sécurisé
- [ ] Fichier `api_secrets.json` créé et sécurisé (chmod 600)
- [ ] Certificat SSL installé et valide
- [ ] Nginx configuré avec redirection HTTPS
- [ ] Test manuel réussi (`python3 run_analysis.py`)
- [ ] Email de notification reçu
- [ ] SMS de notification reçu
- [ ] Cron job configuré (20h00 tous les jours)
- [ ] Logs vérifiés et propres
- [ ] Renouvellement SSL automatique testé (`certbot renew --dry-run`)

---

## 📞 Support et ressources

### Documentation

- [Guide d'utilisation V3 RELIABLE](linxo_agent/README_V3_RELIABLE.md)
- [Documentation OVH VPS](https://docs.ovh.com/fr/vps/)
- [Documentation Let's Encrypt](https://letsencrypt.org/docs/)
- [Documentation Certbot](https://certbot.eff.org/instructions)

### Liens utiles

- **OVH Manager** : https://www.ovh.com/manager/
- **Test SSL** : https://www.ssllabs.com/ssltest/
- **DNS Checker** : https://dnschecker.org/
- **Gmail App Passwords** : https://myaccount.google.com/apppasswords

### Commandes de diagnostic rapide

```bash
# Check everything
cd /home/ubuntu/linxo_agent
echo "=== Python version ==="
python3 --version
echo "=== Chrome version ==="
google-chrome --version
echo "=== ChromeDriver version ==="
chromedriver --version
echo "=== Config files ==="
ls -lh config_linxo.json depenses_recurrentes.json
ls -lh ~/.api_secret_infos/api_secrets.json
echo "=== Cron jobs ==="
crontab -l
echo "=== SSL certificates ==="
sudo certbot certificates
echo "=== Nginx status ==="
sudo systemctl status nginx --no-pager
echo "=== Recent logs ==="
ls -lt logs/ | head -5
```

---

## 🎉 Félicitations !

Votre système Linxo Agent est maintenant déployé sur votre VPS OVH avec SSL activé !

Le système va :
- ✅ Se connecter automatiquement à Linxo tous les jours à 20h
- ✅ Télécharger les transactions
- ✅ Analyser les dépenses
- ✅ Envoyer un rapport par email
- ✅ Envoyer une alerte par SMS si nécessaire

**Le tout de manière sécurisée avec HTTPS !** 🔒

---

**Version** : 1.0
**Date** : Octobre 2025
**Auteur** : Système déployé pour Philippe PEREZ
