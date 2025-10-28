# Configuration VPS Debian 12 pour Linxo Agent

## Problème : "user data directory is already in use"

Ce problème survient lorsque Chrome ne peut pas accéder à son répertoire de données utilisateur, généralement causé par:
- Des processus Chrome zombies en arrière-plan
- Des fichiers de lock non nettoyés après un crash
- Plusieurs instances qui tentent d'utiliser le même profil

## Solution 1 : Utiliser le script de nettoyage

```bash
# Rendre le script exécutable (première fois uniquement)
chmod +x cleanup_chrome.sh

# Exécuter le nettoyage
./cleanup_chrome.sh

# Relancer l'agent
python linxo_agent.py
```

## Solution 2 : Nettoyage manuel

```bash
# 1. Tuer tous les processus Chrome
pkill -9 chrome
pkill -9 chromedriver

# 2. Supprimer les fichiers de lock
rm -rf /home/linxo/LINXO/.chrome_user_data

# 3. Relancer
python linxo_agent.py
```

## Solution 3 : Vérifier les processus en cours

```bash
# Lister les processus Chrome
ps aux | grep chrome

# Tuer un processus spécifique (remplacer PID)
kill -9 PID
```

## Configuration automatique du mode headless

Le code détecte maintenant automatiquement si vous êtes sur un serveur (pas de $DISPLAY) et active le mode headless. Vous n'avez rien à faire !

## Installation des dépendances Chrome sur Debian 12

Si Chrome n'est pas installé :

```bash
# Installer Chrome
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo dpkg -i google-chrome-stable_current_amd64.deb
sudo apt-get install -f

# Vérifier l'installation
google-chrome --version

# Installer ChromeDriver (correspond à votre version de Chrome)
# Adapter la version selon votre Chrome
wget https://chromedriver.storage.googleapis.com/114.0.5735.90/chromedriver_linux64.zip
unzip chromedriver_linux64.zip
sudo mv chromedriver /usr/local/bin/
sudo chmod +x /usr/local/bin/chromedriver

# Vérifier ChromeDriver
chromedriver --version
```

## Configurer un cron job pour exécution automatique

```bash
# Éditer la crontab
crontab -e

# Exemples de planification :
# Tous les jours à 8h00
0 8 * * * cd /home/linxo/LINXO && /home/linxo/LINXO/.venv/bin/python linxo_agent.py >> /home/linxo/LINXO/logs/cron.log 2>&1

# Tous les lundis à 9h00
0 9 * * 1 cd /home/linxo/LINXO && /home/linxo/LINXO/.venv/bin/python linxo_agent.py >> /home/linxo/LINXO/logs/cron.log 2>&1

# Le 1er de chaque mois à 7h00
0 7 1 * * cd /home/linxo/LINXO && /home/linxo/LINXO/.venv/bin/python linxo_agent.py >> /home/linxo/LINXO/logs/cron.log 2>&1
```

## Résolution de problèmes courants

### Chrome ne démarre pas en mode headless

Vérifiez les dépendances manquantes :
```bash
sudo apt-get install -y \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libatspi2.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libwayland-client0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxkbcommon0 \
    libxrandr2 \
    xdg-utils
```

### Port 9222 déjà utilisé

Si le port de debugging 9222 est occupé :
```bash
# Trouver le processus
sudo lsof -i :9222

# Le tuer
sudo kill -9 PID
```

### Permissions insuffisantes

```bash
# S'assurer que tous les fichiers appartiennent au bon utilisateur
cd /home/linxo
sudo chown -R linxo:linxo LINXO/

# Donner les permissions d'exécution
chmod +x /home/linxo/LINXO/cleanup_chrome.sh
```

## Test de l'installation

```bash
# Test simple
cd /home/linxo/LINXO
python linxo_agent.py --config-check

# Test sans notifications (pour vérifier que Chrome fonctionne)
python linxo_agent.py --skip-notifications
```

## Logs et debugging

```bash
# Créer un dossier logs si absent
mkdir -p /home/linxo/LINXO/logs

# Lancer avec logs détaillés
python linxo_agent.py 2>&1 | tee logs/debug_$(date +%Y%m%d_%H%M%S).log

# Voir les derniers logs
tail -f logs/cron.log
```

## Améliorations apportées

✅ Détection automatique de l'environnement serveur
✅ Mode headless activé automatiquement sans $DISPLAY
✅ Répertoire user-data unique pour éviter les conflits
✅ Port de debugging dédié (9222)
✅ Options Chrome optimisées pour VPS (no-sandbox, disable-gpu, etc.)
✅ Script de nettoyage automatique des processus zombies

## Support

En cas de problème persistant, vérifiez :
1. Les logs détaillés avec la commande ci-dessus
2. Que Chrome est bien installé : `google-chrome --version`
3. Que ChromeDriver correspond à votre version de Chrome
4. Les permissions du dossier LINXO
5. Qu'aucun processus zombie ne tourne : `ps aux | grep chrome`
