# Guide de déploiement WhatsApp sur VPS

## Étape 1: Transférer les fichiers depuis Windows

```bash
# Sur votre PC Windows (Git Bash)
cd "c:\Users\PhilippePEREZ\OneDrive\LINXO"

# Transférer le profil WhatsApp authentifié
scp whatsapp_profile.tar.gz linxo@152.228.218.1:/home/linxo/LINXO/

# Transférer le script Xvfb
scp run_whatsapp_with_xvfb.sh linxo@152.228.218.1:/home/linxo/LINXO/

# Optionnel: transférer tous les fichiers modifiés
scp linxo_agent/whatsapp_sender.py linxo@152.228.218.1:/home/linxo/LINXO/linxo_agent/
```

## Étape 2: Installation des dépendances sur le VPS

Connectez-vous au VPS:
```bash
ssh linxo@152.228.218.1
cd /home/linxo/LINXO
```

Installez Xvfb et Chrome:
```bash
# Mise à jour du système
sudo apt update

# Installation de Xvfb (serveur X virtuel)
sudo apt install -y xvfb

# Installation de Google Chrome
wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
sudo sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list'
sudo apt update
sudo apt install -y google-chrome-stable

# Vérifier l'installation
google-chrome --version
# Devrait afficher: Google Chrome 130.x.x.x

# Vérifier Xvfb
which Xvfb
# Devrait afficher: /usr/bin/Xvfb
```

## Étape 3: Extraire le profil WhatsApp

```bash
cd /home/linxo/LINXO

# Extraire l'archive
tar -xzf whatsapp_profile.tar.gz

# Vérifier
ls -la whatsapp_profile/
# Devrait montrer le répertoire Default/

# Nettoyer
rm whatsapp_profile.tar.gz

# Rendre le script exécutable
chmod +x run_whatsapp_with_xvfb.sh
```

## Étape 4: Tester WhatsApp avec Xvfb

```bash
cd /home/linxo/LINXO

# Activer l'environnement virtuel
source .venv/bin/activate

# Test avec Xvfb
./run_whatsapp_with_xvfb.sh test
```

Si tout fonctionne, vous devriez voir:
```
Demarrage de Xvfb sur :99...
Xvfb demarre (PID: xxxxx)
Lancement du test WhatsApp...
[OK] Configuration chargee depuis: /home/linxo/LINXO/.env
...
Session WhatsApp déjà active - authentification réussie
...
Contact 'Liste de courses' sélectionné
...
Message envoyé avec succès
```

## Étape 5: Intégrer au workflow automatique

Modifiez votre crontab pour utiliser Xvfb:

```bash
crontab -e
```

Ajoutez ou modifiez la ligne pour utiliser Xvfb:
```cron
# Analyse quotidienne à 8h avec WhatsApp hebdomadaire
0 8 * * * cd /home/linxo/LINXO && DISPLAY=:99 /home/linxo/LINXO/.venv/bin/python /home/linxo/LINXO/linxo_agent.py >> /home/linxo/linxo_cron.log 2>&1
```

**Ou** créez un service systemd pour Xvfb (recommandé):

```bash
sudo nano /etc/systemd/system/xvfb.service
```

Contenu du service:
```ini
[Unit]
Description=X Virtual Frame Buffer Service
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/Xvfb :99 -screen 0 1920x1080x24 -ac +extension GLX +render -noreset
Restart=always
RestartSec=10
User=linxo

[Install]
WantedBy=multi-user.target
```

Activer le service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable xvfb
sudo systemctl start xvfb
sudo systemctl status xvfb
```

Puis dans votre crontab:
```cron
# Analyse quotidienne à 8h avec Xvfb permanent
0 8 * * * cd /home/linxo/LINXO && DISPLAY=:99 /home/linxo/LINXO/.venv/bin/python /home/linxo/LINXO/linxo_agent.py >> /home/linxo/linxo_cron.log 2>&1
```

## Dépannage

### Chrome ne démarre pas
```bash
# Vérifier que Chrome est installé
google-chrome --version

# Tester Chrome manuellement avec Xvfb
export DISPLAY=:99
Xvfb :99 -screen 0 1920x1080x24 &
google-chrome --version
```

### Profil WhatsApp corrompu
Si le profil ne fonctionne plus après le transfert:
```bash
# Supprimer le profil
rm -rf /home/linxo/LINXO/whatsapp_profile

# Retransférer depuis Windows
# (Sur Windows)
cd "c:\Users\PhilippePEREZ\OneDrive\LINXO"
tar -czf whatsapp_profile.tar.gz whatsapp_profile/
scp whatsapp_profile.tar.gz linxo@152.228.218.1:/home/linxo/LINXO/

# (Sur VPS)
tar -xzf whatsapp_profile.tar.gz
```

### Session WhatsApp expirée
Si WhatsApp demande de rescanner le QR code:
- Option 1: Utilisez VNC pour voir l'écran du VPS et scanner
- Option 2: Rescan en local puis retransfère le profil

### Logs pour déboguer
```bash
# Voir les logs du dernier run
tail -f /home/linxo/linxo_cron.log

# Test manuel avec logs détaillés
cd /home/linxo/LINXO
source .venv/bin/activate
DISPLAY=:99 python setup_whatsapp.py --test
```

## Architecture finale

```
┌──────────────────────────────────────┐
│         Cron (quotidien 8h)          │
└─────────────┬────────────────────────┘
              │
              ▼
┌──────────────────────────────────────┐
│        linxo_agent.py                │
│  - Scrape Linxo                      │
│  - Analyse transactions              │
│  - Génère rapports                   │
└─────────────┬────────────────────────┘
              │
              ▼
┌──────────────────────────────────────┐
│    NotificationManager               │
│  1. Email → quotidien (HTML complet) │
│  2. SMS → quotidien (résumé)         │
│  3. WhatsApp → hebdomadaire (résumé) │
└─────────────┬────────────────────────┘
              │
              ▼ (WhatsApp)
┌──────────────────────────────────────┐
│    Xvfb + Chrome + Selenium          │
│  - Display virtuel :99               │
│  - WhatsApp Web                      │
│  - Profil persistant                 │
└──────────────────────────────────────┘
```

## Notes importantes

1. **Xvfb doit tourner** avant de lancer Chrome (via service systemd ou script wrapper)
2. **DISPLAY=:99** doit être exporté dans l'environnement
3. Le **profil WhatsApp** est transféré depuis Windows (déjà authentifié)
4. **Fréquence WhatsApp** configurée à `weekly` dans `.env`
5. Le fichier `.last_whatsapp_notification` track la dernière notification
