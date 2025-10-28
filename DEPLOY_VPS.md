# Déploiement sur VPS OVH Debian 12

## Résumé des modifications

Le code a été modifié pour résoudre l'erreur `user data directory is already in use` sur votre VPS :

### Changements apportés dans `linxo_agent/linxo_connexion.py` :

1. ✅ Ajout d'un répertoire `--user-data-dir` unique : `.chrome_user_data/`
2. ✅ Détection automatique de l'environnement serveur (absence de $DISPLAY)
3. ✅ Activation automatique du mode headless sur serveur
4. ✅ Ajout d'options Chrome optimisées pour VPS :
   - `--disable-gpu`
   - `--disable-software-rasterizer`
   - `--remote-debugging-port=9222`
   - `--headless=new` (automatique sur serveur)

### Nouveaux fichiers créés :

- `cleanup_chrome.sh` : Script de nettoyage des processus Chrome zombies
- `test_chrome_vps.py` : Script de test de configuration Chrome
- `VPS_SETUP.md` : Guide complet de configuration VPS
- `DEPLOY_VPS.md` : Ce fichier (guide de déploiement)

## Procédure de déploiement

### 1. Transférer les fichiers sur le VPS

```bash
# Sur votre machine locale (Windows)
# Option A : Via Git (recommandé)
git add .
git commit -m "fix: resolve Chrome user-data-dir conflict on VPS"
git push

# Sur le VPS
cd /home/linxo/LINXO
git pull

# Option B : Via SCP
scp -r linxo_agent/ linxo@votre-vps:/home/linxo/LINXO/
scp cleanup_chrome.sh test_chrome_vps.py linxo@votre-vps:/home/linxo/LINXO/
```

### 2. Sur le VPS, nettoyer l'environnement

```bash
# Se connecter au VPS
ssh linxo@votre-vps

# Aller dans le répertoire
cd /home/linxo/LINXO

# Rendre les scripts exécutables
chmod +x cleanup_chrome.sh test_chrome_vps.py

# Nettoyer les processus Chrome existants
./cleanup_chrome.sh
```

### 3. Tester la configuration Chrome

```bash
# Activer l'environnement virtuel
source .venv/bin/activate

# Lancer le test
python test_chrome_vps.py
```

**Si le test réussit :** Passez à l'étape 4.

**Si le test échoue :** Consultez la section "Résolution de problèmes" ci-dessous.

### 4. Tester l'agent Linxo

```bash
# Test simple sans notifications
python linxo_agent.py --skip-notifications

# Si le test précédent fonctionne, test complet
python linxo_agent.py
```

### 5. Vérifier les résultats

```bash
# Vérifier que le CSV a été téléchargé
ls -lh data/

# Vérifier le rapport généré
ls -lh reports/

# Lire le dernier rapport
cat reports/rapport_linxo_*.txt | tail -50
```

## Résolution de problèmes

### Problème : "session not created" persiste

```bash
# 1. Vérifier qu'aucun processus Chrome ne tourne
ps aux | grep chrome

# 2. Tuer tous les processus Chrome
pkill -9 chrome
pkill -9 chromedriver

# 3. Supprimer complètement le répertoire user-data
rm -rf /home/linxo/LINXO/.chrome_user_data

# 4. Réessayer
python linxo_agent.py --skip-notifications
```

### Problème : Chrome n'est pas installé ou version incorrecte

```bash
# Vérifier l'installation
google-chrome --version
chromedriver --version

# Si manquant, installer (voir VPS_SETUP.md section "Installation des dépendances Chrome")
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo dpkg -i google-chrome-stable_current_amd64.deb
sudo apt-get install -f
```

### Problème : Dépendances système manquantes

```bash
sudo apt-get update
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

### Problème : Permissions insuffisantes

```bash
# Vérifier les permissions
ls -la /home/linxo/LINXO

# Corriger si nécessaire
sudo chown -R linxo:linxo /home/linxo/LINXO
chmod +x /home/linxo/LINXO/cleanup_chrome.sh
chmod +x /home/linxo/LINXO/test_chrome_vps.py
```

### Problème : Port 9222 déjà utilisé

```bash
# Trouver le processus utilisant le port
sudo lsof -i :9222

# Tuer le processus (remplacer PID par le numéro trouvé)
sudo kill -9 PID

# Alternative : modifier le port dans linxo_connexion.py ligne 328
# Changer --remote-debugging-port=9222 en 9223 ou autre
```

## Configuration pour exécution automatique (cron)

Une fois que tout fonctionne correctement :

```bash
# Éditer la crontab
crontab -e

# Ajouter une ligne pour exécution automatique
# Exemple : tous les jours à 8h du matin
0 8 * * * cd /home/linxo/LINXO && /home/linxo/LINXO/.venv/bin/python linxo_agent.py >> /home/linxo/LINXO/logs/cron.log 2>&1
```

Créer le dossier logs si nécessaire :
```bash
mkdir -p /home/linxo/LINXO/logs
```

## Vérification de l'état du système

Avant chaque exécution, vous pouvez vérifier :

```bash
# Processus Chrome
ps aux | grep chrome | wc -l

# Espace disque
df -h

# Derniers logs
tail -50 logs/cron.log

# Fichiers CSV téléchargés
ls -lht data/*.csv | head -5
```

## Workflow recommandé

```bash
# 1. Nettoyer avant chaque exécution manuelle
./cleanup_chrome.sh

# 2. Exécuter l'agent
python linxo_agent.py

# 3. Vérifier les résultats
cat reports/rapport_linxo_*.txt | tail
```

## Support

Pour toute question ou problème :

1. Consultez les logs détaillés : `logs/cron.log`
2. Exécutez le test : `python test_chrome_vps.py`
3. Vérifiez les processus : `ps aux | grep chrome`
4. Lisez la documentation complète : `VPS_SETUP.md`

## Checklist de déploiement

- [ ] Code transféré sur le VPS (git pull ou scp)
- [ ] Scripts rendus exécutables (chmod +x)
- [ ] Processus Chrome nettoyés (cleanup_chrome.sh)
- [ ] Test Chrome réussi (test_chrome_vps.py)
- [ ] Test agent sans notifications réussi
- [ ] Test agent complet réussi
- [ ] Cron job configuré (optionnel)
- [ ] Documentation lue (VPS_SETUP.md)

## Prochaines étapes

Une fois le déploiement réussi :

1. Configurer le cron job pour exécution automatique
2. Mettre en place une surveillance des logs
3. Configurer des alertes en cas d'échec (optionnel)
4. Documenter votre configuration spécifique

---

**Date de création :** $(date +%Y-%m-%d)
**Version du code :** 2.1 (fix VPS Chrome user-data-dir)
