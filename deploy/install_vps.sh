#!/bin/bash
###############################################################################
# Linxo Agent - Installation automatique sur VPS Ubuntu
# Ce script installe et configure le système complet
###############################################################################

set -e  # Exit on error

echo "==========================================================================="
echo "  Linxo Agent - Installation VPS"
echo "==========================================================================="
echo ""

# Couleurs pour les messages
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Fonction pour afficher les messages
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

###############################################################################
# 1. Mise à jour du système
###############################################################################

log_info "Mise à jour du système..."
sudo apt update
sudo apt upgrade -y

###############################################################################
# 2. Installation des dépendances système
###############################################################################

log_info "Installation des dépendances système..."

# Python et pip
sudo apt install -y python3 python3-pip python3-venv

# Chrome et ChromeDriver pour Selenium
log_info "Installation de Google Chrome..."
wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
sudo sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list'
sudo apt update
sudo apt install -y google-chrome-stable

# ChromeDriver
log_info "Installation de ChromeDriver..."
CHROME_VERSION=$(google-chrome --version | grep -oP '\d+\.\d+\.\d+')
CHROMEDRIVER_VERSION=$(curl -s "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_${CHROME_VERSION%%.*}")
wget -N "https://chromedriver.storage.googleapis.com/${CHROMEDRIVER_VERSION}/chromedriver_linux64.zip" -P /tmp
sudo unzip -o /tmp/chromedriver_linux64.zip -d /usr/local/bin/
sudo chmod +x /usr/local/bin/chromedriver
rm /tmp/chromedriver_linux64.zip

# Autres dépendances système
sudo apt install -y \
    xvfb \
    unzip \
    wget \
    curl \
    git \
    certbot

log_info "Dépendances système installées avec succès"

###############################################################################
# 3. Création de la structure de répertoires
###############################################################################

log_info "Création de la structure de répertoires..."

# Répertoire principal
APP_DIR="/home/ubuntu/linxo_agent"
mkdir -p "$APP_DIR"
cd "$APP_DIR"

# Sous-répertoires
mkdir -p data
mkdir -p downloads
mkdir -p logs
mkdir -p reports
mkdir -p .api_secret_infos

log_info "Structure créée dans $APP_DIR"

###############################################################################
# 4. Installation de l'application
###############################################################################

log_info "Configuration de l'environnement Python..."

# Création de l'environnement virtuel
python3 -m venv venv
source venv/bin/activate

# Installation des dépendances Python
log_info "Installation des dépendances Python..."
pip install --upgrade pip

# Installation des packages
pip install selenium==4.15.2
pip install webdriver-manager==4.0.1
pip install requests==2.31.0
pip install python-dotenv==1.0.0

log_info "Dépendances Python installées"

###############################################################################
# 5. Configuration des fichiers
###############################################################################

log_info "Les fichiers de l'application doivent être copiés manuellement"
log_warn "Copiez les fichiers suivants depuis votre machine locale :"
echo "Modules principaux :"
echo "  - linxo_agent/analyzer.py                (analyse moderne)"
echo "  - linxo_agent/notifications.py           (email HTML + SMS)"
echo "  - linxo_agent/report_formatter_v2.py     (formatage HTML)"
echo "  - linxo_agent/config.py                  (configuration unifiée)"
echo ""
echo "Modules connexion :"
echo "  - linxo_agent/linxo_connexion.py"
echo "  - linxo_agent/linxo_driver_factory.py"
echo "  - linxo_agent/linxo_2fa.py"
echo ""
echo "Scripts orchestrateurs :"
echo "  - linxo_agent/run_analysis.py            (orchestrateur moderne)"
echo "  - linxo_agent.py                         (workflow complet)"
echo ""
echo "Configuration :"
echo "  - linxo_agent/depenses_recurrentes.json"
echo "  - .env                                   (variables environnement)"
echo "  - api_secrets.json                       (credentials)"
echo ""
log_warn "Puis configurez vos credentials dans .env et api_secrets.json"

###############################################################################
# 6. Configuration du Cron
###############################################################################

log_info "Configuration du cron job..."

# Configuration : Exécution à 10h00 (heure locale du serveur)
CRON_CMD="0 10 * * * cd $APP_DIR && $APP_DIR/venv/bin/python3 run_linxo_e2e.py >> logs/cron.log 2>&1"

# Vérifier si le cron existe déjà
if crontab -l 2>/dev/null | grep -q "run_linxo_e2e.py"; then
    log_warn "Le cron job existe déjà"
else
    # Ajouter le cron job
    (crontab -l 2>/dev/null; echo "$CRON_CMD") | crontab -
    log_info "Cron job ajouté : Exécution quotidienne à 10h00"
fi

###############################################################################
# 7. Configuration des permissions
###############################################################################

log_info "Configuration des permissions..."

chmod +x "$APP_DIR"/*.py 2>/dev/null || true
chmod 600 "$APP_DIR/.api_secret_infos"/* 2>/dev/null || true
chmod 644 "$APP_DIR"/*.json 2>/dev/null || true

###############################################################################
# 8. Test de l'installation
###############################################################################

log_info "Vérification de l'installation..."

echo ""
echo "Vérification des versions :"
python3 --version
google-chrome --version
chromedriver --version
echo ""

###############################################################################
# Résumé
###############################################################################

echo ""
echo "==========================================================================="
echo -e "${GREEN}  Installation terminée avec succès !${NC}"
echo "==========================================================================="
echo ""
echo "Prochaines étapes :"
echo ""
echo "1. Copiez vos fichiers Python et JSON dans $APP_DIR"
echo ""
echo "2. Créez et configurez le fichier .env :"
echo "   cp .env.example .env"
echo "   nano .env"
echo ""
echo "3. Créez le fichier de configuration JSON :"
echo "   nano $APP_DIR/config_linxo.json"
echo ""
echo "4. Créez le fichier API secrets :"
echo "   nano $APP_DIR/.api_secret_infos/api_secrets.json"
echo ""
echo "5. Testez l'installation :"
echo "   cd $APP_DIR"
echo "   source venv/bin/activate"
echo "   python3 run_analysis.py"
echo ""
echo "6. Configurez le certificat SSL (voir deploy/setup_ssl.sh)"
echo ""
echo "==========================================================================="
echo ""
