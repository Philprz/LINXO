#!/bin/bash
# Script de test du filtrage CSV sur le VPS

set -e  # Stop on error

VPS_USER="linxo"
VPS_HOST="vps-6e2f6679.vps.ovh.net"
REMOTE_DIR="/home/linxo/LINXO"

echo "=========================================="
echo "TEST DU FILTRAGE CSV SUR LE VPS"
echo "=========================================="
echo

# Copier le script de diagnostic
echo "[1/4] Copie du script de diagnostic..."
scp diagnostic_csv.py "${VPS_USER}@${VPS_HOST}:${REMOTE_DIR}/"

echo
echo "[2/4] Vérification du fichier CSV actuel..."
ssh "${VPS_USER}@${VPS_HOST}" << 'ENDSSH'
cd /home/linxo/LINXO
if [ -f data/latest.csv ]; then
    echo "✓ Fichier data/latest.csv trouvé"
    ls -lh data/latest.csv
else
    echo "✗ Fichier data/latest.csv NON TROUVÉ!"
    exit 1
fi
ENDSSH

echo
echo "[3/4] Exécution du diagnostic..."
ssh "${VPS_USER}@${VPS_HOST}" << 'ENDSSH'
cd /home/linxo/LINXO
source .venv/bin/activate
python3 diagnostic_csv.py data/latest.csv
ENDSSH

echo
echo "[4/4] Test du module csv_filter..."
ssh "${VPS_USER}@${VPS_HOST}" << 'ENDSSH'
cd /home/linxo/LINXO
source .venv/bin/activate

echo "Test d'import du module csv_filter:"
python3 -c "
import sys
sys.path.insert(0, 'linxo_agent')
try:
    from csv_filter import filter_csv_by_month, get_csv_date_range
    print('✓ Module csv_filter importé avec succès')
except ImportError as e:
    print(f'✗ ERREUR: Impossible d\'importer csv_filter: {e}')
    sys.exit(1)
"

echo
echo "Test de la fonction filter_csv_by_month:"
python3 linxo_agent/csv_filter.py data/latest.csv || echo "✗ Le filtrage a échoué!"

ENDSSH

echo
echo "=========================================="
echo "TEST TERMINÉ"
echo "=========================================="
