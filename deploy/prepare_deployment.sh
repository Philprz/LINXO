#!/bin/bash
###############################################################################
# Script de préparation pour le déploiement
# Crée une archive propre avec uniquement les fichiers nécessaires
###############################################################################

echo "==========================================================================="
echo "  Préparation du package de déploiement"
echo "==========================================================================="
echo ""

# Couleurs
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

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
# Configuration
###############################################################################

DEPLOY_NAME="linxo_deploy_$(date +%Y%m%d_%H%M%S)"
DEPLOY_DIR="/tmp/$DEPLOY_NAME"
ARCHIVE_NAME="${DEPLOY_NAME}.tar.gz"

log_info "Nom du package : $ARCHIVE_NAME"

###############################################################################
# Création du dossier temporaire
###############################################################################

log_info "Création du dossier de déploiement..."

mkdir -p "$DEPLOY_DIR"
mkdir -p "$DEPLOY_DIR/linxo_agent"
mkdir -p "$DEPLOY_DIR/deploy"

###############################################################################
# Copie des fichiers essentiels
###############################################################################

log_info "Copie des fichiers Python..."

# Vérifier que nous sommes dans le bon dossier
if [ ! -d "linxo_agent" ]; then
    log_error "Ce script doit être exécuté depuis la racine du projet"
    log_error "Structure attendue : ./linxo_agent/, ./deploy/, etc."
    exit 1
fi

# Copie des fichiers Python (uniquement les versions RELIABLE)
cp linxo_agent/linxo_connexion.py "$DEPLOY_DIR/linxo_agent/" 2>/dev/null || log_warn "linxo_connexion.py non trouvé"
cp linxo_agent/agent_linxo_csv_v3_RELIABLE.py "$DEPLOY_DIR/linxo_agent/" 2>/dev/null || log_warn "agent_linxo_csv_v3_RELIABLE.py non trouvé"
cp linxo_agent/run_linxo_e2e.py "$DEPLOY_DIR/linxo_agent/" 2>/dev/null || log_warn "run_linxo_e2e.py non trouvé"
cp linxo_agent/run_analysis.py "$DEPLOY_DIR/linxo_agent/" 2>/dev/null || log_warn "run_analysis.py non trouvé"
cp linxo_agent/send_notifications.py "$DEPLOY_DIR/linxo_agent/" 2>/dev/null || log_warn "send_notifications.py non trouvé"

# Copie des fichiers de configuration
log_info "Copie des fichiers de configuration..."
cp linxo_agent/depenses_recurrentes.json "$DEPLOY_DIR/linxo_agent/" 2>/dev/null || log_warn "depenses_recurrentes.json non trouvé"

# Note : config_linxo.json contient des credentials, on copie l'exemple
cp deploy/config_linxo.json.example "$DEPLOY_DIR/linxo_agent/config_linxo.json.example" 2>/dev/null || log_warn "config_linxo.json.example non trouvé"
cp deploy/api_secrets.json.example "$DEPLOY_DIR/linxo_agent/api_secrets.json.example" 2>/dev/null || log_warn "api_secrets.json.example non trouvé"

# Copie de la documentation
log_info "Copie de la documentation..."
cp linxo_agent/README_V3_RELIABLE.md "$DEPLOY_DIR/linxo_agent/" 2>/dev/null || log_warn "README_V3_RELIABLE.md non trouvé"

# Copie des scripts de déploiement
log_info "Copie des scripts de déploiement..."
cp deploy/install_vps.sh "$DEPLOY_DIR/deploy/" 2>/dev/null || log_warn "install_vps.sh non trouvé"
cp deploy/setup_ssl.sh "$DEPLOY_DIR/deploy/" 2>/dev/null || log_warn "setup_ssl.sh non trouvé"
cp deploy/cleanup.sh "$DEPLOY_DIR/deploy/" 2>/dev/null || log_warn "cleanup.sh non trouvé"
cp deploy/config_linxo.json.example "$DEPLOY_DIR/deploy/" 2>/dev/null || log_warn "config_linxo.json.example non trouvé"
cp deploy/api_secrets.json.example "$DEPLOY_DIR/deploy/" 2>/dev/null || log_warn "api_secrets.json.example non trouvé"

# Copie des fichiers racine
log_info "Copie des fichiers racine..."
cp requirements.txt "$DEPLOY_DIR/" 2>/dev/null || log_warn "requirements.txt non trouvé"
cp .env.example "$DEPLOY_DIR/" 2>/dev/null || log_warn ".env.example non trouvé"
cp .gitignore "$DEPLOY_DIR/" 2>/dev/null || log_warn ".gitignore non trouvé"
cp README.md "$DEPLOY_DIR/" 2>/dev/null || log_warn "README.md non trouvé"
cp GUIDE_DEPLOIEMENT_VPS.md "$DEPLOY_DIR/" 2>/dev/null || log_warn "GUIDE_DEPLOIEMENT_VPS.md non trouvé"

###############################################################################
# Création de README pour le déploiement
###############################################################################

log_info "Création du README de déploiement..."

cat > "$DEPLOY_DIR/DEPLOYMENT_README.txt" <<'EOF'
=============================================================================
  LINXO AGENT - PACKAGE DE DÉPLOIEMENT
=============================================================================

Ce package contient tous les fichiers nécessaires pour déployer
Linxo Agent sur votre VPS OVH.

CONTENU :
---------
  linxo_agent/          Fichiers Python de l'application
  deploy/               Scripts d'installation et configuration
  requirements.txt      Dépendances Python
  GUIDE_DEPLOIEMENT_VPS.md   Guide complet de déploiement

ÉTAPES DE DÉPLOIEMENT :
-----------------------

1. Transférer ce package sur le VPS :
   scp linxo_deploy_YYYYMMDD_HHMMSS.tar.gz ubuntu@152.228.218.1:~/

2. Se connecter au VPS :
   ssh ubuntu@152.228.218.1

3. Extraire le package :
   cd ~
   tar -xzf linxo_deploy_YYYYMMDD_HHMMSS.tar.gz
   cd linxo_deploy_YYYYMMDD_HHMMSS/

4. Installer le système :
   chmod +x deploy/install_vps.sh
   sudo bash deploy/install_vps.sh

5. Copier les fichiers :
   cp -r linxo_agent/* /home/ubuntu/linxo_agent/

6. Configurer les credentials :
   nano /home/ubuntu/linxo_agent/config_linxo.json
   nano /home/ubuntu/.api_secret_infos/api_secrets.json

7. Configurer SSL :
   chmod +x deploy/setup_ssl.sh
   sudo bash deploy/setup_ssl.sh

8. Tester :
   cd /home/ubuntu/linxo_agent
   source venv/bin/activate
   python3 run_analysis.py

POUR PLUS DE DÉTAILS :
----------------------
Consultez le fichier GUIDE_DEPLOIEMENT_VPS.md

=============================================================================
EOF

###############################################################################
# Création de l'archive
###############################################################################

log_info "Création de l'archive..."

cd /tmp
tar -czf "$ARCHIVE_NAME" "$DEPLOY_NAME/"

if [ $? -eq 0 ]; then
    log_info "Archive créée avec succès : /tmp/$ARCHIVE_NAME"
else
    log_error "Échec de la création de l'archive"
    exit 1
fi

###############################################################################
# Nettoyage
###############################################################################

log_info "Nettoyage du dossier temporaire..."
rm -rf "$DEPLOY_DIR"

###############################################################################
# Résumé et instructions
###############################################################################

ARCHIVE_SIZE=$(du -h "/tmp/$ARCHIVE_NAME" | cut -f1)

echo ""
echo "==========================================================================="
echo -e "${GREEN}  Package de déploiement créé avec succès !${NC}"
echo "==========================================================================="
echo ""
echo "📦 Archive : /tmp/$ARCHIVE_NAME"
echo "📊 Taille : $ARCHIVE_SIZE"
echo ""
echo "Contenu :"
echo "  ✅ Fichiers Python (versions RELIABLE uniquement)"
echo "  ✅ Scripts d'installation et configuration"
echo "  ✅ Documentation complète"
echo "  ✅ Fichiers de configuration (exemples)"
echo ""
echo "Prochaines étapes :"
echo ""
echo "1. Transférer l'archive sur le VPS :"
echo "   ${YELLOW}scp /tmp/$ARCHIVE_NAME ubuntu@152.228.218.1:~/${NC}"
echo ""
echo "2. Se connecter au VPS :"
echo "   ${YELLOW}ssh ubuntu@152.228.218.1${NC}"
echo ""
echo "3. Extraire et déployer :"
echo "   ${YELLOW}tar -xzf $ARCHIVE_NAME${NC}"
echo "   ${YELLOW}cd ${DEPLOY_NAME}${NC}"
echo "   ${YELLOW}cat DEPLOYMENT_README.txt${NC}"
echo ""
echo "4. Suivre le guide complet :"
echo "   ${YELLOW}less GUIDE_DEPLOIEMENT_VPS.md${NC}"
echo ""
echo "==========================================================================="
echo ""
