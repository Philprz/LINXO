#!/bin/bash
###############################################################################
# Script de nettoyage du projet Linxo
# Supprime les fichiers inutiles, doublons et anciennes versions
###############################################################################

echo "==========================================================================="
echo "  Linxo Agent - Nettoyage du projet"
echo "==========================================================================="
echo ""

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
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

# Fonction pour demander confirmation
confirm() {
    read -p "$1 (y/n): " response
    case "$response" in
        [yY][eE][sS]|[yY])
            return 0
            ;;
        *)
            return 1
            ;;
    esac
}

###############################################################################
# Sauvegarde avant nettoyage
###############################################################################

log_warn "Ce script va supprimer les fichiers inutiles"
echo ""
echo "Fichiers qui seront CONSERVÉS :"
echo "  ✅ linxo_agent/linxo_connexion.py"
echo "  ✅ linxo_agent/agent_linxo_csv_v3_RELIABLE.py"
echo "  ✅ linxo_agent/run_linxo_e2e.py"
echo "  ✅ linxo_agent/run_analysis.py"
echo "  ✅ linxo_agent/send_notifications.py"
echo "  ✅ linxo_agent/depenses_recurrentes.json"
echo "  ✅ linxo_agent/config_linxo.json"
echo "  ✅ requirements.txt"
echo "  ✅ .env.example"
echo "  ✅ .gitignore"
echo "  ✅ GUIDE_DEPLOIEMENT_VPS.md"
echo "  ✅ deploy/"
echo ""
echo "Fichiers qui seront SUPPRIMÉS :"
echo "  ❌ Anciennes versions (*_v2.py, etc.)"
echo "  ❌ Fichiers de test (test_*.py)"
echo "  ❌ Rapports et logs"
echo "  ❌ Fichiers temporaires"
echo "  ❌ Documentation en PDF"
echo "  ❌ BACKUP_AVANT_NETTOYAGE/ (déjà sauvegardé)"
echo ""

if ! confirm "Voulez-vous créer une sauvegarde avant de continuer ?"; then
    log_error "Nettoyage annulé"
    exit 0
fi

# Créer une sauvegarde
BACKUP_NAME="backup_before_cleanup_$(date +%Y%m%d_%H%M%S).tar.gz"
log_info "Création de la sauvegarde : $BACKUP_NAME"

tar -czf "$BACKUP_NAME" \
    --exclude='BACKUP_AVANT_NETTOYAGE' \
    --exclude='chrome_linxo_profile' \
    --exclude='data' \
    --exclude='*.tar.gz' \
    .

log_info "Sauvegarde créée : $BACKUP_NAME"

echo ""
if ! confirm "Voulez-vous continuer avec le nettoyage ?"; then
    log_error "Nettoyage annulé"
    exit 0
fi

###############################################################################
# Nettoyage
###############################################################################

log_info "Début du nettoyage..."

# Compter les fichiers avant
FILES_BEFORE=$(find . -type f | wc -l)

###############################################################################
# 1. Supprimer les fichiers de test
###############################################################################

log_info "Suppression des fichiers de test..."

find . -maxdepth 1 -name "test_*.py" -type f -delete
find linxo_agent/ -name "test_*.py" -type f -delete 2>/dev/null || true

###############################################################################
# 2. Supprimer les anciennes versions
###############################################################################

log_info "Suppression des anciennes versions..."

# Dans linxo_agent/
rm -f linxo_agent/agent_linxo_csv.py 2>/dev/null || true
rm -f linxo_agent/agent_linxo_csv_v2.py 2>/dev/null || true
rm -f linxo_agent/analyze_and_notify.py 2>/dev/null || true
rm -f linxo_agent/analyze_and_notify_v2_FIXED.py 2>/dev/null || true
rm -f linxo_agent/daily_linxo_analysis.py 2>/dev/null || true
rm -f linxo_agent/compare_csv.py 2>/dev/null || true
rm -f linxo_agent/test_validation_complete.py 2>/dev/null || true
rm -f linxo_agent/test_sms_ovh.py 2>/dev/null || true

###############################################################################
# 3. Supprimer les rapports et logs
###############################################################################

log_info "Suppression des rapports et logs..."

# Rapports markdown
find . -maxdepth 1 -name "RAPPORT_*.md" -type f -delete
find . -maxdepth 1 -name "CORRECTION_*.md" -type f -delete
find . -maxdepth 1 -name "SYNTHESE_*.md" -type f -delete
find . -maxdepth 1 -name "COMPARAISON_*.md" -type f -delete
find . -maxdepth 1 -name "CONFIG_FINALE.md" -type f -delete
find . -maxdepth 1 -name "E2E_*.md" -type f -delete
find . -maxdepth 1 -name "EXECUTIVE_*.md" -type f -delete
find . -maxdepth 1 -name "RESUME_*.md" -type f -delete

# Rapports dans linxo_agent/
find linxo_agent/ -name "RAPPORT_*.md" -type f -delete 2>/dev/null || true
find linxo_agent/ -name "*.txt" ! -name "COMMANDES_UTILES.txt" -type f -delete 2>/dev/null || true
find linxo_agent/ -name "BEFORE_AFTER_*.md" -type f -delete 2>/dev/null || true
find linxo_agent/ -name "COMPARAISON_*.md" -type f -delete 2>/dev/null || true
find linxo_agent/ -name "CONFIG_FINALE.md" -type f -delete 2>/dev/null || true
find linxo_agent/ -name "CORRECTION_*.md" -type f -delete 2>/dev/null || true

# PDFs
find . -name "*.pdf" -type f -delete

# JSON de test/rapport
rm -f test_e2e_report.json 2>/dev/null || true
rm -f test_e2e_report_simplified.json 2>/dev/null || true
rm -f test_e2e_final_report.json 2>/dev/null || true

###############################################################################
# 4. Supprimer les fichiers README multiples
###############################################################################

log_info "Nettoyage des fichiers README..."

# Garder seulement le principal
find linxo_agent/ -name "README_*.md" ! -name "README_V3_RELIABLE.md" -type f -delete 2>/dev/null || true
rm -f README_TEST_REPORTS.md 2>/dev/null || true

###############################################################################
# 5. Supprimer les scripts shell inutiles
###############################################################################

log_info "Suppression des scripts shell obsolètes..."

find linxo_agent/ -name "*.sh" ! -name "COMMANDES_TEST_DEPLOIEMENT.sh" -type f -delete 2>/dev/null || true

###############################################################################
# 6. Nettoyer les dossiers de données
###############################################################################

log_info "Nettoyage des dossiers de données..."

# Garder la structure mais vider le contenu
find data/ -type f -delete 2>/dev/null || true
find Downloads/ -type f -delete 2>/dev/null || true
find Uploads/ -type f -delete 2>/dev/null || true
find reports/ -type f -delete 2>/dev/null || true
find linxo_agent/data/ -type f -delete 2>/dev/null || true

###############################################################################
# 7. Supprimer BACKUP_AVANT_NETTOYAGE (déjà sauvegardé)
###############################################################################

log_warn "Suppression du dossier BACKUP_AVANT_NETTOYAGE..."

if confirm "Êtes-vous sûr de vouloir supprimer BACKUP_AVANT_NETTOYAGE/ ?"; then
    rm -rf BACKUP_AVANT_NETTOYAGE/
    log_info "BACKUP_AVANT_NETTOYAGE/ supprimé"
else
    log_warn "BACKUP_AVANT_NETTOYAGE/ conservé"
fi

###############################################################################
# Résumé
###############################################################################

# Compter les fichiers après
FILES_AFTER=$(find . -type f | wc -l)
FILES_DELETED=$((FILES_BEFORE - FILES_AFTER))

echo ""
echo "==========================================================================="
echo -e "${GREEN}  Nettoyage terminé !${NC}"
echo "==========================================================================="
echo ""
echo "Statistiques :"
echo "  - Fichiers avant : $FILES_BEFORE"
echo "  - Fichiers après : $FILES_AFTER"
echo "  - Fichiers supprimés : $FILES_DELETED"
echo ""
echo "Sauvegarde créée : $BACKUP_NAME"
echo ""
log_info "Structure finale recommandée :"
echo ""
echo "linxo_agent/"
echo "├── linxo_connexion.py                    # Module de connexion"
echo "├── agent_linxo_csv_v3_RELIABLE.py        # Moteur d'analyse"
echo "├── run_linxo_e2e.py                      # Orchestrateur complet"
echo "├── run_analysis.py                       # Script simplifié"
echo "├── send_notifications.py                 # Envoi email/SMS"
echo "├── depenses_recurrentes.json             # Configuration des dépenses"
echo "├── config_linxo.json                     # Configuration principale"
echo "├── README_V3_RELIABLE.md                 # Documentation"
echo "├── data/                                 # Données (vide)"
echo "├── logs/                                 # Logs (vide)"
echo "└── .api_secret_infos/                    # Secrets (à créer)"
echo ""
echo "deploy/"
echo "├── install_vps.sh                        # Installation automatique"
echo "├── setup_ssl.sh                          # Configuration SSL"
echo "├── cleanup.sh                            # Ce script"
echo "├── config_linxo.json.example             # Template config"
echo "└── api_secrets.json.example              # Template secrets"
echo ""
echo "Fichiers racine :"
echo "├── requirements.txt                      # Dépendances Python"
echo "├── .env.example                          # Template environnement"
echo "├── .gitignore                            # Git ignore"
echo "└── GUIDE_DEPLOIEMENT_VPS.md              # Guide de déploiement"
echo ""
echo "==========================================================================="
echo ""
log_info "Vous pouvez maintenant déployer sur le VPS !"
echo ""
