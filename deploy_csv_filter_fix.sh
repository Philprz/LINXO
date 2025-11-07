#!/bin/bash
# Script de déploiement du fix CSV filter

set -e

VPS_USER="linxo"
VPS_HOST="vps-6e2f6679.vps.ovh.net"
REMOTE_DIR="/home/linxo/LINXO"

echo "=========================================="
echo "DÉPLOIEMENT DU FIX CSV_FILTER"
echo "=========================================="
echo

echo "[1/3] Copie du fichier corrigé vers le VPS..."
scp linxo_agent/csv_filter.py "${VPS_USER}@${VPS_HOST}:${REMOTE_DIR}/linxo_agent/"

echo
echo "[2/3] Test du module corrigé..."
ssh "${VPS_USER}@${VPS_HOST}" << 'ENDSSH'
cd /home/linxo/LINXO
source .venv/bin/activate

echo "Test d'import:"
python3 -c "
import sys
sys.path.insert(0, 'linxo_agent')
from csv_filter import filter_csv_by_month
print('✓ Module importé avec succès')
"

echo
echo "Test de filtrage sur latest.csv:"
python3 linxo_agent/csv_filter.py data/latest.csv

ENDSSH

echo
echo "[3/3] Création d'un script de re-filtrage..."
ssh "${VPS_USER}@${VPS_HOST}" << 'ENDSSH'
cd /home/linxo/LINXO

# Créer un script pour re-filtrer le CSV existant
cat > refilter_csv.sh << 'EOF'
#!/bin/bash
# Script pour re-filtrer le CSV existant

cd /home/linxo/LINXO
source .venv/bin/activate

echo "Re-filtrage du CSV existant..."
python3 linxo_agent/csv_filter.py data/latest.csv

echo
echo "Vérification du résultat:"
python3 << 'PYEOF'
import csv
from datetime import datetime
from pathlib import Path

csv_path = Path('data/latest.csv')
dates = []

with open(csv_path, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f, delimiter=';')
    for row in reader:
        try:
            date_str = row['Date']
            date_obj = datetime.strptime(date_str, '%d/%m/%Y')
            dates.append(date_obj)
        except:
            pass

if dates:
    print(f"Transactions: {len(dates)}")
    print(f"Plus ancienne: {min(dates).strftime('%d/%m/%Y')}")
    print(f"Plus récente: {max(dates).strftime('%d/%m/%Y')}")

    now = datetime.now()
    mois_ok = all(d.year == now.year and d.month == now.month for d in dates)

    if mois_ok:
        print(f"\n✅ Toutes les transactions sont du mois courant ({now.strftime('%B %Y')})")
    else:
        print(f"\n⚠️  Certaines transactions ne sont PAS du mois courant")
PYEOF
EOF

chmod +x refilter_csv.sh
echo "✓ Script refilter_csv.sh créé"

ENDSSH

echo
echo "=========================================="
echo "DÉPLOIEMENT TERMINÉ"
echo "=========================================="
echo
echo "Pour re-filtrer le CSV existant, exécutez sur le VPS:"
echo "  cd /home/linxo/LINXO && ./refilter_csv.sh"
echo
echo "Pour vérifier les résultats:"
echo "  cd /home/linxo/LINXO && source .venv/bin/activate && python run_analysis.py"
echo
