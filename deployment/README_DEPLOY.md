# Guide de Déploiement - Interface d'Administration Linxo

## Vue d'ensemble

Ce guide décrit le processus complet de déploiement de l'interface d'administration Linxo sur votre VPS (152.228.218.1).

## Prérequis

### Sur votre machine locale

- Accès SSH au VPS configuré
- Clé SSH `~/.ssh/id_ed25519` configurée
- rsync installé

### Sur le VPS

- Debian 12 (ou compatible)
- Python 3.9+
- Nginx
- Sudo access pour l'utilisateur `linxo`

## Architecture de Déploiement

```
Internet (HTTPS)
    ↓
Nginx (Port 443) + SSL Let's Encrypt
    ↓
FastAPI/Uvicorn (Port 8810)
    ↓
Application Linxo Admin
```

## Étapes de Déploiement

### Option 1 : Déploiement Automatique (Recommandé)

Le script `deploy.sh` automatise tout le processus :

```bash
cd /path/to/LINXO
chmod +x deployment/deploy.sh
./deployment/deploy.sh
```

Le script effectue automatiquement :
1. ✅ Vérification des prérequis
2. ✅ Synchronisation des fichiers (rsync)
3. ✅ Installation des dépendances Python
4. ✅ Configuration du service systemd
5. ✅ Configuration de Nginx
6. ✅ Configuration SSL Let's Encrypt
7. ✅ Redémarrage des services
8. ✅ Tests de connectivité

**Durée estimée** : 3-5 minutes

---

### Option 2 : Déploiement Manuel

#### Étape 1 : Synchroniser les fichiers

```bash
rsync -avz --progress \
    --exclude='.git' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.venv' \
    . linxo@152.228.218.1:/home/linxo/LINXO/
```

#### Étape 2 : Installer les dépendances sur le VPS

```bash
ssh linxo@152.228.218.1

cd /home/linxo/LINXO
source .venv/bin/activate
pip install fastapi uvicorn python-dotenv psutil jinja2 python-multipart
```

#### Étape 3 : Configurer le service systemd

```bash
# Sur votre machine locale
scp deployment/linxo-admin.service linxo@152.228.218.1:/tmp/

# Sur le VPS
ssh linxo@152.228.218.1
sudo cp /tmp/linxo-admin.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable linxo-admin.service
sudo systemctl start linxo-admin.service

# Vérifier le statut
sudo systemctl status linxo-admin.service
```

#### Étape 4 : Configurer Nginx

```bash
# Sur votre machine locale
scp deployment/nginx-admin.conf linxo@152.228.218.1:/tmp/

# Sur le VPS
ssh linxo@152.228.218.1
sudo cp /tmp/nginx-admin.conf /etc/nginx/sites-available/linxo-admin
sudo ln -s /etc/nginx/sites-available/linxo-admin /etc/nginx/sites-enabled/

# Tester la configuration
sudo nginx -t

# Recharger Nginx
sudo systemctl reload nginx
```

#### Étape 5 : Configurer SSL avec Let's Encrypt

```bash
ssh linxo@152.228.218.1

# Installer certbot si nécessaire
sudo apt-get update
sudo apt-get install -y certbot python3-certbot-nginx

# Obtenir le certificat
sudo certbot --nginx -d linxo.appliprz.ovh

# Le renouvellement automatique est configuré par défaut
```

#### Étape 6 : Vérifier le déploiement

```bash
# Test health check
curl https://linxo.appliprz.ovh/healthz

# Test interface admin (avec authentification)
curl -u admin:AdminLinxo@2025 https://linxo.appliprz.ovh/admin/api/status
```

---

## Configuration

### Variables d'Environnement

Le fichier `.env` doit contenir :

```bash
# Admin Interface
ADMIN_USER=admin
ADMIN_PASS=AdminLinxo@2025

# Report Server
REPORTS_PORT=8810
REPORTS_BASIC_USER=linxo
REPORTS_BASIC_PASS=Lisemma@1972
REPORTS_SIGNING_KEY=vzsLO33H_yweU27HxYiRxujGftujaoQ9gPPQBQcjuyQ
```

**Important** : Changez `ADMIN_PASS` avant le déploiement en production !

### Sécurité

#### Restriction par IP (Optionnel)

Pour restreindre l'accès admin à certaines IPs, éditez `/etc/nginx/sites-available/linxo-admin` :

```nginx
location /admin {
    allow 192.168.1.0/24;      # Votre réseau local
    allow XXX.XXX.XXX.XXX;     # Votre IP publique
    deny all;

    proxy_pass http://linxo_admin;
    # ...
}
```

Puis rechargez Nginx : `sudo systemctl reload nginx`

#### Fail2Ban (Recommandé)

Installez fail2ban pour protéger contre les attaques par force brute :

```bash
sudo apt-get install fail2ban

# Configuration pour Basic Auth
sudo nano /etc/fail2ban/jail.local
```

Ajoutez :

```ini
[nginx-http-auth]
enabled = true
port = http,https
logpath = /var/log/nginx/linxo-admin-error.log
maxretry = 3
bantime = 3600
```

Redémarrez : `sudo systemctl restart fail2ban`

---

## Gestion du Service

### Commandes Systemd

```bash
# Démarrer le service
sudo systemctl start linxo-admin

# Arrêter le service
sudo systemctl stop linxo-admin

# Redémarrer le service
sudo systemctl restart linxo-admin

# Voir le statut
sudo systemctl status linxo-admin

# Voir les logs en temps réel
sudo journalctl -u linxo-admin -f

# Activer au démarrage
sudo systemctl enable linxo-admin

# Désactiver au démarrage
sudo systemctl disable linxo-admin
```

### Logs

#### Logs du service systemd
```bash
sudo journalctl -u linxo-admin -n 100 --no-pager
```

#### Logs de l'application
```bash
tail -f /home/linxo/LINXO/logs/admin-server.log
tail -f /home/linxo/LINXO/logs/admin-server-error.log
```

#### Logs Nginx
```bash
tail -f /var/log/nginx/linxo-admin-access.log
tail -f /var/log/nginx/linxo-admin-error.log
```

---

## Mise à Jour

### Déployer une nouvelle version

```bash
# Depuis votre machine locale
cd /path/to/LINXO
./deployment/deploy.sh
```

Ou manuellement :

```bash
# 1. Synchroniser les fichiers
rsync -avz --exclude='.venv' . linxo@152.228.218.1:/home/linxo/LINXO/

# 2. Redémarrer le service sur le VPS
ssh linxo@152.228.218.1 "sudo systemctl restart linxo-admin"
```

### Mettre à jour uniquement la configuration

```bash
# Si vous avez modifié .env ou nginx-admin.conf
scp .env linxo@152.228.218.1:/home/linxo/LINXO/
scp deployment/nginx-admin.conf linxo@152.228.218.1:/tmp/

ssh linxo@152.228.218.1
sudo cp /tmp/nginx-admin.conf /etc/nginx/sites-available/linxo-admin
sudo nginx -t && sudo systemctl reload nginx
sudo systemctl restart linxo-admin
```

---

## Tests Post-Déploiement

### 1. Test de Connectivité

```bash
# Health check
curl https://linxo.appliprz.ovh/healthz

# Devrait retourner : {"status":"ok","service":"linxo-report-server","reports_dir_exists":true}
```

### 2. Test d'Authentification

```bash
# Sans auth (devrait retourner 401)
curl -i https://linxo.appliprz.ovh/admin

# Avec auth (devrait retourner 200)
curl -u admin:AdminLinxo@2025 https://linxo.appliprz.ovh/admin/api/status
```

### 3. Test des Actions

1. Ouvrir https://linxo.appliprz.ovh/admin dans un navigateur
2. Se connecter avec `admin` / `AdminLinxo@2025`
3. Vérifier le dashboard
4. Tester une action (ex: Test Email)
5. Vérifier la page Logs
6. Vérifier la page Configuration

### 4. Test de Performance

```bash
# Test de charge basique
ab -n 100 -c 10 -A admin:AdminLinxo@2025 https://linxo.appliprz.ovh/admin/api/status
```

---

## Dépannage

### Le service ne démarre pas

```bash
# Voir les logs détaillés
sudo journalctl -u linxo-admin -n 50 --no-pager

# Vérifier les permissions
ls -la /home/linxo/LINXO/logs
sudo chown -R linxo:linxo /home/linxo/LINXO

# Tester manuellement
cd /home/linxo/LINXO
source .venv/bin/activate
python -m uvicorn linxo_agent.report_server.app:app --host 0.0.0.0 --port 8810
```

### Nginx retourne 502 Bad Gateway

```bash
# Vérifier que le service est actif
sudo systemctl status linxo-admin

# Vérifier que le port 8810 est ouvert
sudo netstat -tlnp | grep 8810

# Tester la connexion locale
curl http://localhost:8810/healthz
```

### Certificat SSL non valide

```bash
# Renouveler manuellement
sudo certbot renew --force-renewal

# Vérifier la date d'expiration
sudo certbot certificates

# Tester la configuration SSL
sudo nginx -t
```

### Erreur "Module admin non disponible"

```bash
# Vérifier la structure des fichiers
ls -R /home/linxo/LINXO/linxo_agent/report_server/admin/

# Réinstaller les dépendances
cd /home/linxo/LINXO
source .venv/bin/activate
pip install --force-reinstall fastapi uvicorn jinja2
```

---

## Monitoring

### Uptime Monitoring

Configurez un monitoring externe (ex: UptimeRobot) sur :
- `https://linxo.appliprz.ovh/healthz`

### Alertes Email

Le système Linxo envoie déjà des alertes email. Pour monitorer le serveur :

```bash
# Installer monit
sudo apt-get install monit

# Configuration pour linxo-admin
sudo nano /etc/monit/conf.d/linxo-admin
```

Contenu :

```
check process linxo-admin matching "linxo_agent.report_server"
    start program = "/bin/systemctl start linxo-admin"
    stop program = "/bin/systemctl stop linxo-admin"
    if failed host 127.0.0.1 port 8810 protocol http request /healthz then restart
    if 3 restarts within 5 cycles then alert
```

---

## Rollback (Retour Arrière)

En cas de problème après une mise à jour :

```bash
ssh linxo@152.228.218.1

# Revenir à la version précédente (si vous avez un git)
cd /home/linxo/LINXO
git log --oneline -5
git checkout <commit-precedent>

# Ou restaurer depuis une sauvegarde
sudo cp -r /home/linxo/LINXO_backup /home/linxo/LINXO

# Redémarrer
sudo systemctl restart linxo-admin
```

---

## Sauvegarde

### Sauvegarde Automatique

Créez un script de sauvegarde :

```bash
sudo nano /usr/local/bin/backup-linxo.sh
```

Contenu :

```bash
#!/bin/bash
BACKUP_DIR="/home/linxo/backups"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Sauvegarder les fichiers importants
tar -czf $BACKUP_DIR/linxo_$DATE.tar.gz \
    /home/linxo/LINXO/.env \
    /home/linxo/LINXO/linxo_agent \
    /home/linxo/LINXO/data

# Garder seulement les 7 dernières sauvegardes
find $BACKUP_DIR -name "linxo_*.tar.gz" -mtime +7 -delete
```

Rendez-le exécutable et ajoutez au cron :

```bash
sudo chmod +x /usr/local/bin/backup-linxo.sh
(crontab -l ; echo "0 2 * * * /usr/local/bin/backup-linxo.sh") | crontab -
```

---

## Support

En cas de problème :

1. Consultez les logs (voir section Logs ci-dessus)
2. Vérifiez le statut des services : `sudo systemctl status linxo-admin nginx`
3. Testez les endpoints : `curl https://linxo.appliprz.ovh/healthz`

---

**Version** : 1.0
**Date** : 2025-11-11
**Auteur** : Claude Code
