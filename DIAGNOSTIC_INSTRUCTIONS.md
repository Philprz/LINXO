# Instructions de diagnostic CSV

## 1. Connectez-vous au VPS

```bash
ssh linxo@vps-6e2f6679.vps.ovh.net
cd /home/linxo/LINXO
```

## 2. Vérifiez le CSV actuel

```bash
# Voir la taille du fichier
ls -lh data/latest.csv

# Compter les lignes
wc -l data/latest.csv
```

## 3. Exécutez le diagnostic

```bash
# Copier ce script dans un fichier temporaire
cat > /tmp/diag_csv.py << 'EOF'
import csv
from datetime import datetime
from collections import Counter
from pathlib import Path

csv_path = "/home/linxo/LINXO/data/latest.csv"

print("=" * 80)
print(f"Diagnostic de: {csv_path}")
print(f"Taille: {Path(csv_path).stat().st_size} octets")
print()

dates = []
montants = []

with open(csv_path, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f, delimiter=';')
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
    print(f"Transactions: {len(dates)}")
    print(f"Plus ancienne: {min(dates).strftime('%d/%m/%Y')}")
    print(f"Plus récente: {max(dates).strftime('%d/%m/%Y')}")
    print()

    # Par mois
    mois_counter = Counter((d.year, d.month) for d in dates)
    print(f"Nombre de mois différents: {len(mois_counter)}")
    for (annee, mois), count in sorted(mois_counter.items()):
        print(f"  {mois:02d}/{annee}: {count} transactions")
    print()

    total = sum(montants)
    print(f"Total dépenses: {total:,.2f} €")

    now = datetime.now()
    if len(mois_counter) == 1 and (now.year, now.month) in mois_counter:
        print(f"\n✅ CSV filtré sur le mois courant!")
    else:
        print(f"\n❌ CSV contient {len(mois_counter)} mois (devrait être 1)!")
        print(f"   Mois attendu: {now.month:02d}/{now.year}")

print("=" * 80)
EOF

# Exécuter le diagnostic
source .venv/bin/activate
python3 /tmp/diag_csv.py
```

## 4. Testez le filtrage manuellement

```bash
source .venv/bin/activate

# Tester le module csv_filter
python3 << 'EOF'
import sys
sys.path.insert(0, '/home/linxo/LINXO/linxo_agent')

from csv_filter import filter_csv_by_month, get_csv_date_range
from pathlib import Path

csv_path = Path('/home/linxo/LINXO/data/latest.csv')

print("Test du filtrage CSV...")
print(f"Fichier source: {csv_path}")

# Voir la plage de dates AVANT
date_range = get_csv_date_range(csv_path)
if date_range:
    min_date, max_date = date_range
    print(f"AVANT: {min_date.strftime('%d/%m/%Y')} -> {max_date.strftime('%d/%m/%Y')}")

# Appliquer le filtre
result = filter_csv_by_month(csv_path)

if result:
    print(f"\n✅ Filtrage réussi!")

    # Voir la plage APRÈS
    date_range = get_csv_date_range(csv_path)
    if date_range:
        min_date, max_date = date_range
        print(f"APRÈS: {min_date.strftime('%d/%m/%Y')} -> {max_date.strftime('%d/%m/%Y')}")
else:
    print(f"\n❌ Filtrage échoué!")
EOF
```

## 5. Vérifiez les logs du dernier téléchargement

```bash
# Voir les logs les plus récents
tail -100 logs/linxo_agent.log | grep -i "filtr\|csv"
```

## Copiez-collez les résultats ici

Après avoir exécuté ces commandes, copiez-collez les résultats pour que je puisse diagnostiquer le problème.
