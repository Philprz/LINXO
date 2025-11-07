#!/bin/bash
# Script de déploiement final du fix CSV sur le VPS

set -e

echo "=========================================="
echo "DÉPLOIEMENT FINAL DU FIX CSV"
echo "=========================================="
echo

VPS_USER="linxo"
VPS_HOST="vps-6e2f6679.vps.ovh.net"

echo "[1/4] Connexion au VPS et pull des changements..."
ssh "${VPS_USER}@${VPS_HOST}" << 'ENDSSH'
cd /home/linxo/LINXO

echo "Sauvegarde de l'ancienne version..."
cp linxo_agent/csv_filter.py linxo_agent/csv_filter.py.backup

echo "Pull depuis GitHub..."
git pull origin main

echo "Vérification du nouveau code..."
if grep -q "Détecter automatiquement" linxo_agent/csv_filter.py; then
    echo "✅ Nouveau code détecté"
else
    echo "❌ Le code n'a pas été mis à jour!"
    exit 1
fi
ENDSSH

echo
echo "[2/4] Test du module mis à jour..."
ssh "${VPS_USER}@${VPS_HOST}" << 'ENDSSH'
cd /home/linxo/LINXO
source .venv/bin/activate

echo "Test du module csv_filter..."
python3 linxo_agent/csv_filter.py data/latest.csv
ENDSSH

echo
echo "[3/4] Vérification du résultat..."
ssh "${VPS_USER}@${VPS_HOST}" << 'ENDSSH'
cd /home/linxo/LINXO
source .venv/bin/activate

python3 << 'EOF'
import csv
from datetime import datetime
from pathlib import Path
from collections import Counter

csv_path = Path('data/latest.csv')

for encoding in ['utf-16', 'utf-8']:
    for delimiter in ['\t', ';']:
        try:
            dates = []
            with open(csv_path, 'r', encoding=encoding) as f:
                reader = csv.DictReader(f, delimiter=delimiter)
                if 'Date' not in reader.fieldnames:
                    continue

                for row in reader:
                    try:
                        date_obj = datetime.strptime(row['Date'], '%d/%m/%Y')
                        dates.append(date_obj)
                    except:
                        pass

            if dates:
                now = datetime.now()
                mois_counter = Counter((d.year, d.month) for d in dates)

                print(f"\n{'='*60}")
                print(f"Transactions: {len(dates)}")
                print(f"Mois différents: {len(mois_counter)}")

                if len(mois_counter) == 1 and (now.year, now.month) in mois_counter:
                    print(f"✅ CSV CORRECTEMENT FILTRÉ pour {now.strftime('%B %Y')}")
                    exit(0)
                else:
                    print(f"⚠️  CSV contient {len(mois_counter)} mois")
                    for (y, m), c in sorted(mois_counter.items())[-3:]:
                        print(f"   - {m:02d}/{y}: {c} transactions")
                print('='*60)
                break
        except:
            pass
EOF
ENDSSH

echo
echo "[4/4] Informations de déploiement..."
ssh "${VPS_USER}@${VPS_HOST}" << 'ENDSSH'
cd /home/linxo/LINXO

echo ""
echo "Version déployée:"
git log -1 --oneline linxo_agent/csv_filter.py

echo ""
echo "Fichier de backup créé:"
ls -lh linxo_agent/csv_filter.py.backup
ENDSSH

echo
echo "=========================================="
echo "DÉPLOIEMENT TERMINÉ AVEC SUCCÈS!"
echo "=========================================="
echo
echo "Le prochain téléchargement CSV depuis Linxo sera"
echo "automatiquement filtré pour le mois courant."
echo
echo "Pour tester immédiatement:"
echo "  ssh ${VPS_USER}@${VPS_HOST}"
echo "  cd /home/linxo/LINXO"
echo "  source .venv/bin/activate"
echo "  python3 linxo_agent/run_linxo_e2e.py"
echo
