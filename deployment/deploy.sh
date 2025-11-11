#!/bin/bash
# Script de déploiement de l'interface d'administration sur le VPS
# Usage: ./deploy.sh

set -e  # Arrêter en cas d'erreur

echo "=========================================="
echo "  Déploiement Interface Admin Linxo"
echo "=========================================="
echo ""

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Variables
VPS_HOST="152.228.218.1"
VPS_USER="linxo"
VPS_PATH="/home/linxo/LINXO"
LOCAL_PATH="."

echo -e "${YELLOW}[1/8]${NC} Vérification des prérequis..."

# Vérifier que nous sommes dans le bon répertoire
if [ ! -f "linxo_agent.py" ]; then
    echo -e "${RED}Erreur: Ce script doit être exécuté depuis le répertoire LINXO${NC}"
    exit 1
fi

echo -e "${GREEN}✓${NC} Prérequis OK"
echo ""

echo -e "${YELLOW}[2/8]${NC} Synchronisation des fichiers vers le VPS..."

# Synchroniser les fichiers (exclure les fichiers inutiles)
rsync -avz --progress \
    --exclude='.git' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.venv' \
    --exclude='data/ml' \
    --exclude='diagnostic_html' \
    --exclude='.env.local' \
    ${LOCAL_PATH}/ ${VPS_USER}@${VPS_HOST}:${VPS_PATH}/

echo -e "${GREEN}✓${NC} Fichiers synchronisés"
echo ""

echo -e "${YELLOW}[3/8]${NC} Installation des dépendances Python sur le VPS..."

ssh ${VPS_USER}@${VPS_HOST} << 'ENDSSH'
cd /home/linxo/LINXO

# Activer l'environnement virtuel ou le créer
if [ ! -d ".venv" ]; then
    echo "Création de l'environnement virtuel..."
    python3 -m venv .venv
fi

source .venv/bin/activate

# Installer/mettre à jour les dépendances
pip install --upgrade pip
pip install fastapi uvicorn python-dotenv psutil jinja2
pip install python-multipart  # Pour les requêtes multipart/form-data

echo "Dépendances installées"
ENDSSH

echo -e "${GREEN}✓${NC} Dépendances installées"
echo ""

echo -e "${YELLOW}[4/8]${NC} Configuration du service systemd..."

# Copier le fichier service
scp deployment/linxo-admin.service ${VPS_USER}@${VPS_HOST}:/tmp/

ssh ${VPS_USER}@${VPS_HOST} << 'ENDSSH'
# Copier le service (nécessite sudo)
sudo cp /tmp/linxo-admin.service /etc/systemd/system/
sudo chmod 644 /etc/systemd/system/linxo-admin.service

# Recharger systemd
sudo systemctl daemon-reload

# Activer le service au démarrage
sudo systemctl enable linxo-admin.service

echo "Service systemd configuré"
ENDSSH

echo -e "${GREEN}✓${NC} Service systemd configuré"
echo ""

echo -e "${YELLOW}[5/8]${NC} Configuration de Nginx..."

# Copier la configuration Nginx
scp deployment/nginx-admin.conf ${VPS_USER}@${VPS_HOST}:/tmp/

ssh ${VPS_USER}@${VPS_HOST} << 'ENDSSH'
# Copier la config Nginx
sudo cp /tmp/nginx-admin.conf /etc/nginx/sites-available/linxo-admin

# Créer le lien symbolique si pas déjà fait
if [ ! -L /etc/nginx/sites-enabled/linxo-admin ]; then
    sudo ln -s /etc/nginx/sites-available/linxo-admin /etc/nginx/sites-enabled/
fi

# Tester la configuration
sudo nginx -t

echo "Configuration Nginx OK"
ENDSSH

echo -e "${GREEN}✓${NC} Nginx configuré"
echo ""

echo -e "${YELLOW}[6/8]${NC} Configuration SSL Let's Encrypt..."

ssh ${VPS_USER}@${VPS_HOST} << 'ENDSSH'
# Vérifier si certbot est installé
if ! command -v certbot &> /dev/null; then
    echo "Installation de certbot..."
    sudo apt-get update
    sudo apt-get install -y certbot python3-certbot-nginx
fi

# Vérifier si le certificat existe déjà
if [ ! -d "/etc/letsencrypt/live/linxo.appliprz.ovh" ]; then
    echo "Obtention du certificat SSL..."
    sudo certbot --nginx -d linxo.appliprz.ovh --non-interactive --agree-tos -m phiperez@gmail.com
else
    echo "Certificat SSL déjà présent"
fi

# Renouvellement automatique (cron si pas déjà configuré)
if ! sudo crontab -l 2>/dev/null | grep -q certbot; then
    (sudo crontab -l 2>/dev/null; echo "0 3 * * * certbot renew --quiet") | sudo crontab -
    echo "Renouvellement automatique SSL configuré"
fi

ENDSSH

echo -e "${GREEN}✓${NC} SSL configuré"
echo ""

echo -e "${YELLOW}[7/8]${NC} Redémarrage des services..."

ssh ${VPS_USER}@${VPS_HOST} << 'ENDSSH'
# Redémarrer le service Linxo Admin
sudo systemctl restart linxo-admin.service

# Attendre que le service démarre
sleep 3

# Vérifier le statut
if sudo systemctl is-active --quiet linxo-admin.service; then
    echo "Service linxo-admin: ACTIF"
else
    echo "ERREUR: Service linxo-admin n'a pas démarré correctement"
    sudo systemctl status linxo-admin.service --no-pager -l
    exit 1
fi

# Recharger Nginx
sudo systemctl reload nginx

echo "Services redémarrés"
ENDSSH

echo -e "${GREEN}✓${NC} Services redémarrés"
echo ""

echo -e "${YELLOW}[8/8]${NC} Tests de connectivité..."

# Test health check
echo "Test du endpoint /healthz..."
if curl -f -s https://linxo.appliprz.ovh/healthz > /dev/null; then
    echo -e "${GREEN}✓${NC} Health check OK"
else
    echo -e "${RED}✗${NC} Health check ÉCHOUÉ"
fi

echo ""
echo "=========================================="
echo -e "${GREEN}  Déploiement terminé avec succès ! ${NC}"
echo "=========================================="
echo ""
echo "Interface d'administration accessible à :"
echo "  https://linxo.appliprz.ovh/admin"
echo ""
echo "Identifiants :"
echo "  Username: admin"
echo "  Password: AdminLinxo@2025"
echo ""
echo "Commandes utiles sur le VPS :"
echo "  - Statut du service    : sudo systemctl status linxo-admin"
echo "  - Logs du service      : sudo journalctl -u linxo-admin -f"
echo "  - Logs applicatifs     : tail -f ~/LINXO/logs/admin-server.log"
echo "  - Redémarrer le service: sudo systemctl restart linxo-admin"
echo ""
