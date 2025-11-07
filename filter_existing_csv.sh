#!/bin/bash
# Script pour filtrer le CSV existant sur le VPS

echo "=========================================="
echo "FILTRAGE DU CSV EXISTANT"
echo "=========================================="
echo

cd /home/linxo/LINXO

# Vérifier que le CSV existe
if [ ! -f data/latest.csv ]; then
    echo "ERREUR: data/latest.csv n'existe pas!"
    exit 1
fi

echo "[1/4] État AVANT filtrage:"
python3 << 'EOF'
import csv
from datetime import datetime
from pathlib import Path
from collections import Counter

csv_path = Path('data/latest.csv')

# Essayer différents encodages
for encoding in ['utf-16', 'utf-8', 'latin-1']:
    try:
        # Essayer différents délimiteurs
        for delimiter in ['\t', ';', ',']:
            try:
                dates = []
                montants = []

                with open(csv_path, 'r', encoding=encoding) as f:
                    reader = csv.DictReader(f, delimiter=delimiter)

                    # Vérifier si c'est le bon format
                    if 'Date' not in reader.fieldnames:
                        continue

                    for row in reader:
                        try:
                            date_str = row['Date']
                            date_obj = datetime.strptime(date_str, '%d/%m/%Y')
                            dates.append(date_obj)

                            montant_str = row.get('Montant', '0').replace(',', '.')
                            montant = float(montant_str)
                            if montant < 0:
                                montants.append(abs(montant))
                        except:
                            pass

                if dates:
                    print(f"\n{'='*60}")
                    print(f"Encodage: {encoding}, Délimiteur: {repr(delimiter)}")
                    print(f"Transactions: {len(dates)}")
                    print(f"Plus ancienne: {min(dates).strftime('%d/%m/%Y')}")
                    print(f"Plus récente: {max(dates).strftime('%d/%m/%Y')}")
                    print(f"Total dépenses: {sum(montants):,.2f}€")

                    mois_counter = Counter((d.year, d.month) for d in dates)
                    print(f"Nombre de mois: {len(mois_counter)}")
                    print('='*60)

                    # Sauvegarde pour le filtrage
                    import json
                    with open('/tmp/csv_info.json', 'w') as f:
                        json.dump({
                            'encoding': encoding,
                            'delimiter': delimiter
                        }, f)
                    break

            except Exception as e:
                continue
        else:
            continue
        break
    except Exception as e:
        continue
EOF

if [ ! -f /tmp/csv_info.json ]; then
    echo "ERREUR: Impossible de lire le CSV!"
    exit 1
fi

echo
echo "[2/4] Application du filtrage avec le module csv_filter..."

source .venv/bin/activate

# Créer un script Python qui gère l'encodage et le délimiteur correctement
python3 << 'EOF'
import csv
import json
from datetime import datetime
from pathlib import Path

# Charger les infos du CSV
with open('/tmp/csv_info.json', 'r') as f:
    csv_info = json.load(f)

encoding = csv_info['encoding']
delimiter = csv_info['delimiter']

print(f"Utilisation de: encoding={encoding}, delimiter={repr(delimiter)}")

csv_path = Path('data/latest.csv')
now = datetime.now()
year = now.year
month = now.month

print(f"\nFiltrage pour {month:02d}/{year}...")

# Lire toutes les lignes
filtered_rows = []
fieldnames = None
total_rows = 0

with open(csv_path, 'r', encoding=encoding) as f:
    reader = csv.DictReader(f, delimiter=delimiter)
    fieldnames = list(reader.fieldnames)

    for row in reader:
        total_rows += 1
        try:
            date_str = row['Date']
            date_obj = datetime.strptime(date_str, '%d/%m/%Y')

            if date_obj.year == year and date_obj.month == month:
                filtered_rows.append(row)
        except:
            continue

print(f"Transactions filtrées: {len(filtered_rows)}/{total_rows}")

if not filtered_rows:
    print(f"ERREUR: Aucune transaction pour {month:02d}/{year}!")
    exit(1)

# Créer un fichier filtré AVEC LE BON ENCODAGE
output_path = Path('data/latest_filtered.csv')

# IMPORTANT: Écrire avec le MÊME encodage et délimiteur
with open(output_path, 'w', encoding=encoding, newline='') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=delimiter)
    writer.writeheader()
    writer.writerows(filtered_rows)

print(f"Fichier filtré créé: {output_path}")

# Remplacer l'original
import shutil
shutil.move(str(output_path), str(csv_path))
print("Fichier original remplacé!")
EOF

echo
echo "[3/4] Vérification APRÈS filtrage:"
python3 << 'EOF'
import csv
from datetime import datetime
from pathlib import Path
from collections import Counter
import json

csv_path = Path('data/latest.csv')

# Recharger les infos
with open('/tmp/csv_info.json', 'r') as f:
    csv_info = json.load(f)

encoding = csv_info['encoding']
delimiter = csv_info['delimiter']

dates = []
montants = []

with open(csv_path, 'r', encoding=encoding) as f:
    reader = csv.DictReader(f, delimiter=delimiter)

    for row in reader:
        try:
            date_str = row['Date']
            date_obj = datetime.strptime(date_str, '%d/%m/%Y')
            dates.append(date_obj)

            montant_str = row.get('Montant', '0').replace(',', '.')
            montant = float(montant_str)
            if montant < 0:
                montants.append(abs(montant))
        except:
            pass

if dates:
    print(f"\n{'='*60}")
    print(f"Transactions: {len(dates)}")
    print(f"Plus ancienne: {min(dates).strftime('%d/%m/%Y')}")
    print(f"Plus récente: {max(dates).strftime('%d/%m/%Y')}")
    print(f"Total dépenses: {sum(montants):,.2f}€")

    now = datetime.now()
    mois_counter = Counter((d.year, d.month) for d in dates)

    if len(mois_counter) == 1 and (now.year, now.month) in mois_counter:
        print(f"\n✅ FILTRAGE RÉUSSI!")
        print(f"   Toutes les transactions sont de {now.strftime('%B %Y')}")
    else:
        print(f"\n❌ PROBLÈME!")
        print(f"   {len(mois_counter)} mois différents trouvés")
        for (annee, mois), count in sorted(mois_counter.items())[-5:]:
            print(f"   - {mois:02d}/{annee}: {count} transactions")
    print('='*60)
EOF

echo
echo "[4/4] Relancer l'analyse..."
python3 linxo_agent/run_analysis.py

echo
echo "=========================================="
echo "TERMINÉ!"
echo "=========================================="
