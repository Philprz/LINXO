# Installation de la solution undetected-chromedriver sur le VPS

## Problème identifié

Linxo **bloque les connexions en mode headless** avec Selenium standard. La solution est d'utiliser **undetected-chromedriver** qui contourne cette détection.

## Étape 1 : Transférer les nouveaux fichiers sur le VPS

Depuis votre machine Windows (PowerShell ou Git Bash) :

```bash
# Transférer les fichiers modifiés
scp linxo_agent/linxo_connexion_undetected.py linxo@vps-6e2f6679:~/LINXO/linxo_agent/
scp test_undetected_chrome.py linxo@vps-6e2f6679:~/LINXO/
scp requirements.txt linxo@vps-6e2f6679:~/LINXO/

# Optionnel : transférer aussi le fichier de diagnostic
scp DIAGNOSTIC_VPS.md linxo@vps-6e2f6679:~/LINXO/
```

## Étape 2 : Se connecter au VPS

```bash
ssh linxo@vps-6e2f6679
cd ~/LINXO
source .venv/bin/activate
```

## Étape 3 : Installer undetected-chromedriver

```bash
# Installer la bibliothèque
pip install undetected-chromedriver

# Vérifier l'installation
python -c "import undetected_chromedriver; print('OK')"
```

## Étape 4 : Tester la connexion

```bash
# Test avec undetected-chromedriver
python test_undetected_chrome.py
```

**Si ça marche**, vous devriez voir :
```
[SUCCESS] CONNEXION RÉUSSIE AVEC UNDETECTED-CHROMEDRIVER!
```

## Étape 5 : Modifier le script principal

Si le test réussit, modifiez votre script principal pour utiliser la nouvelle méthode :

### Option A : Modifier run_linxo_e2e.py

Remplacez :
```python
from linxo_agent.linxo_connexion import initialiser_driver_linxo, se_connecter_linxo
```

Par :
```python
from linxo_agent.linxo_connexion_undetected import (
    initialiser_driver_linxo_undetected as initialiser_driver_linxo,
    se_connecter_linxo
)
```

### Option B : Créer un nouveau script

Créez un nouveau fichier `run_linxo_e2e_undetected.py` qui utilise directement le nouveau module.

## Dépannage

### Erreur "Chrome version not found"

```bash
# Vérifier la version de Chrome installée
google-chrome --version

# Si Chrome n'est pas installé ou version incorrecte
sudo apt-get update
sudo apt-get install google-chrome-stable
```

### Erreur "ChromeDriver not found"

undetected-chromedriver télécharge automatiquement ChromeDriver, mais en cas de problème :

```bash
# Donner les permissions
chmod +x ~/.local/share/undetected_chromedriver/*
```

### Erreur de mémoire

Si le VPS manque de RAM :

```bash
# Vérifier la mémoire disponible
free -h

# Créer un fichier swap si nécessaire (2GB)
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

## Commandes utiles

### Vérifier les processus Chrome

```bash
ps aux | grep chrome
```

### Nettoyer les processus zombies

```bash
pkill -9 chrome
pkill -9 chromedriver
```

### Voir les logs en temps réel

```bash
python test_undetected_chrome.py 2>&1 | tee test.log
```

### Récupérer les screenshots de diagnostic

```bash
# Depuis Windows
scp linxo@vps-6e2f6679:/tmp/*.png .
scp linxo@vps-6e2f6679:/tmp/*.html .
```

## Fichiers créés/modifiés

- ✅ `linxo_agent/linxo_connexion_undetected.py` - Nouveau module avec anti-détection
- ✅ `test_undetected_chrome.py` - Script de test
- ✅ `requirements.txt` - Mis à jour avec undetected-chromedriver
- ✅ `INSTALL_VPS.md` - Ce guide d'installation

## Avantages de undetected-chromedriver

1. **Contourne la détection** : Masque automatiquement les propriétés webdriver
2. **Gère les versions** : Télécharge automatiquement le ChromeDriver compatible
3. **Mode headless amélioré** : Headless non détectable
4. **Maintenance active** : Mise à jour régulière pour suivre les changements de Chrome

## Si ça ne marche toujours pas

Solutions alternatives (par ordre de complexité croissante) :

### 1. Xvfb (Serveur X virtuel)

Exécuter Chrome en mode graphique sur un serveur headless :

```bash
sudo apt-get install xvfb
xvfb-run --server-args="-screen 0 1920x1080x24" python test_undetected_chrome.py
```

### 2. VNC (Bureau distant)

Installer un bureau graphique complet :

```bash
sudo apt-get install xfce4 xfce4-goodies tightvncserver
vncserver
# Puis se connecter avec un client VNC
```

### 3. Playwright (Alternative à Selenium)

Utiliser Playwright au lieu de Selenium :

```bash
pip install playwright
playwright install chromium
```

### 4. Solution Cloud avec GUI

Utiliser une machine virtuelle avec interface graphique (AWS EC2 avec VNC, DigitalOcean Droplet avec desktop, etc.)

## Support

En cas de problème :
1. Vérifiez les logs
2. Vérifiez les screenshots dans `/tmp/`
3. Testez d'abord en local avec `test_undetected_chrome.py`
4. Vérifiez que Chrome est bien installé sur le VPS
