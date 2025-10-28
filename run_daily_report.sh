#!/bin/bash
# Script d'exécution quotidienne du rapport Linxo
# À exécuter tous les jours à 10h via cron

# Configuration
LOG_DIR="/home/ubuntu/linxo_agent/logs"
LOG_FILE="$LOG_DIR/daily_report_$(date +%Y%m%d).log"
SCRIPT_DIR="/home/ubuntu/linxo_agent"
PYTHON_PATH="/usr/bin/python3"

# Créer le répertoire de logs si nécessaire
mkdir -p "$LOG_DIR"

# Rediriger toute la sortie vers le fichier de log
exec 1> >(tee -a "$LOG_FILE")
exec 2>&1

echo "=========================================="
echo "Démarrage du rapport quotidien Linxo"
echo "Date: $(date '+%Y-%m-%d %H:%M:%S')"
echo "=========================================="

# Se placer dans le bon répertoire
cd "$SCRIPT_DIR" || {
    echo "❌ Erreur: Impossible d'accéder au répertoire $SCRIPT_DIR"
    exit 1
}

# Activer l'environnement virtuel si vous en utilisez un
# Décommentez la ligne suivante si vous avez un virtualenv
# source /home/ubuntu/linxo_agent/venv/bin/activate

# Exécuter le script d'analyse
echo "🚀 Lancement de l'analyse..."
$PYTHON_PATH run_analysis.py

# Vérifier le code de retour
if [ $? -eq 0 ]; then
    echo "✅ Rapport généré avec succès"
    echo "=========================================="
    exit 0
else
    echo "❌ Erreur lors de la génération du rapport"
    echo "=========================================="
    exit 1
fi
