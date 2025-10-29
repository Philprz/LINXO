#!/bin/bash
# Script de déploiement automatique du serveur de rapports Linxo
# Idempotent: peut être exécuté plusieurs fois sans problème

set -e  # Arrêter en cas d'erreur

# Couleurs pour l'affichage
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "═══════════════════════════════════════════════════════════════"
echo "  DÉPLOIEMENT DU SERVEUR DE RAPPORTS LINXO"
echo "═══════════════════════════════════════════════════════════════"
echo

# Configuration
INSTALL_DIR="/home/linxo/LINXO"
SERVICE_NAME="linxo-reports"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
VENV_PATH="${INSTALL_DIR}/.venv"
USER="linxo"
GROUP="linxo"

# Vérifier les droits root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}[ERREUR]${NC} Ce script doit être exécuté en tant que root"
    echo "Utilisez: sudo bash scripts/deploy_report_server.sh"
    exit 1
fi

echo -e "${GREEN}[1/6]${NC} Vérification de l'environnement..."

# Vérifier que le répertoire existe
if [ ! -d "$INSTALL_DIR" ]; then
    echo -e "${RED}[ERREUR]${NC} Le répertoire $INSTALL_DIR n'existe pas"
    exit 1
fi

# Vérifier que l'utilisateur existe
if ! id "$USER" &>/dev/null; then
    echo -e "${YELLOW}[INFO]${NC} Création de l'utilisateur $USER..."
    useradd -m -s /bin/bash "$USER"
fi

# Vérifier que le venv existe
if [ ! -d "$VENV_PATH" ]; then
    echo -e "${RED}[ERREUR]${NC} Le virtualenv n'existe pas: $VENV_PATH"
    echo "Créez-le avec: python3 -m venv $VENV_PATH"
    exit 1
fi

echo -e "${GREEN}✓${NC} Environnement OK"
echo

echo -e "${GREEN}[2/6]${NC} Vérification des dépendances Python..."

# Activer le venv et installer les dépendances
su - "$USER" -c "cd $INSTALL_DIR && source .venv/bin/activate && pip install -q -r requirements.txt"

echo -e "${GREEN}✓${NC} Dépendances installées"
echo

echo -e "${GREEN}[3/6]${NC} Création du service systemd..."

# Créer le fichier service
cat > "$SERVICE_FILE" << EOF
[Unit]
Description=Linxo Report Server
Documentation=https://github.com/your-repo/linxo
After=network.target

[Service]
Type=simple
User=$USER
Group=$GROUP
WorkingDirectory=$INSTALL_DIR
Environment="PYTHONPATH=$INSTALL_DIR"
Environment="PATH=$VENV_PATH/bin:\$PATH"
EnvironmentFile=$INSTALL_DIR/.env
ExecStart=$VENV_PATH/bin/uvicorn linxo_agent.report_server.app:app --host 0.0.0.0 --port \${REPORTS_PORT:-8810}
Restart=on-failure
RestartSec=5s
StandardOutput=journal
StandardError=journal
SyslogIdentifier=linxo-reports

# Security hardening
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$INSTALL_DIR/data

[Install]
WantedBy=multi-user.target
EOF

echo -e "${GREEN}✓${NC} Service créé: $SERVICE_FILE"
echo

echo -e "${GREEN}[4/6]${NC} Rechargement de systemd..."
systemctl daemon-reload

echo -e "${GREEN}✓${NC} Systemd rechargé"
echo

echo -e "${GREEN}[5/6]${NC} Activation et démarrage du service..."

# Activer le service au démarrage
systemctl enable "$SERVICE_NAME"

# Redémarrer le service (ou le démarrer s'il n'est pas actif)
systemctl restart "$SERVICE_NAME"

# Attendre un peu pour que le service démarre
sleep 2

echo -e "${GREEN}✓${NC} Service démarré"
echo

echo -e "${GREEN}[6/6]${NC} Vérification du statut..."

# Vérifier que le service est actif
if systemctl is-active --quiet "$SERVICE_NAME"; then
    echo -e "${GREEN}✓${NC} Le service est actif"

    # Tenter de vérifier le health check
    PORT=$(grep -oP 'REPORTS_PORT=\K\d+' "$INSTALL_DIR/.env" 2>/dev/null || echo "8810")

    if command -v curl &> /dev/null; then
        sleep 1
        if curl -s "http://127.0.0.1:$PORT/healthz" > /dev/null; then
            echo -e "${GREEN}✓${NC} Health check OK sur http://127.0.0.1:$PORT/healthz"
        else
            echo -e "${YELLOW}[WARNING]${NC} Health check échoué, vérifiez les logs"
        fi
    fi
else
    echo -e "${RED}[ERREUR]${NC} Le service n'a pas démarré"
    echo
    echo "Logs du service:"
    journalctl -u "$SERVICE_NAME" -n 20 --no-pager
    exit 1
fi

echo
echo "═══════════════════════════════════════════════════════════════"
echo -e "${GREEN}  DÉPLOIEMENT TERMINÉ AVEC SUCCÈS${NC}"
echo "═══════════════════════════════════════════════════════════════"
echo
echo "Commandes utiles:"
echo "  - Voir le statut:     sudo systemctl status $SERVICE_NAME"
echo "  - Voir les logs:      sudo journalctl -u $SERVICE_NAME -f"
echo "  - Redémarrer:         sudo systemctl restart $SERVICE_NAME"
echo "  - Arrêter:            sudo systemctl stop $SERVICE_NAME"
echo
echo "URL de test (local):   http://127.0.0.1:$PORT"
echo
echo "⚠️  N'oubliez pas de configurer Caddy pour l'accès HTTPS"
echo "    Voir docs/EMAIL_REPORTS.md pour la configuration Caddy"
echo
