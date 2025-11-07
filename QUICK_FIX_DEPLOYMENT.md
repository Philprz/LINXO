# 🚀 Déploiement Rapide du Fix CSV

## Le Problème
Le CSV filtrage ne fonctionnait pas, causant l'analyse de **622 299€** de données historiques au lieu du mois courant uniquement.

## La Solution
Le bug dans `csv_filter.py` a été corrigé. Le code essayait d'accéder à `reader.fieldnames` après la fermeture du fichier, causant un échec silencieux du filtrage.

## Déploiement sur le VPS

### Méthode 1: Commandes directes (RECOMMANDÉ)

```bash
# 1. Se connecter au VPS
ssh linxo@vps-6e2f6679.vps.ovh.net

# 2. Aller dans le répertoire LINXO
cd /home/linxo/LINXO

# 3. Pull les derniers changements
git pull origin main

# 4. Re-filtrer le CSV existant pour le mois en cours
source .venv/bin/activate
python3 linxo_agent/csv_filter.py data/latest.csv

# 5. Vérifier que le filtrage a fonctionné
python3 << 'EOF'
import csv
from datetime import datetime
from pathlib import Path

csv_path = Path('data/latest.csv')
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
    print(f"\n{'='*60}")
    print(f"Transactions dans latest.csv: {len(dates)}")
    print(f"Date la plus ancienne: {min(dates).strftime('%d/%m/%Y')}")
    print(f"Date la plus récente: {max(dates).strftime('%d/%m/%Y')}")
    print(f"Total dépenses: {sum(montants):,.2f}€")

    now = datetime.now()
    from collections import Counter
    mois_counter = Counter((d.year, d.month) for d in dates)

    if len(mois_counter) == 1 and (now.year, now.month) in mois_counter:
        print(f"\n✅ FILTRAGE RÉUSSI!")
        print(f"   Toutes les transactions sont de {now.strftime('%B %Y')}")
    else:
        print(f"\n❌ PROBLÈME DÉTECTÉ!")
        print(f"   Le CSV contient {len(mois_counter)} mois différents")
        for (annee, mois), count in sorted(mois_counter.items()):
            print(f"   - {mois:02d}/{annee}: {count} transactions")
    print('='*60)
EOF

# 6. Relancer l'analyse
python3 linxo_agent/run_analysis.py
```

### Méthode 2: Utiliser le script automatisé

```bash
# Sur votre machine locale
cd /c/Users/PhilippePEREZ/OneDrive/LINXO
bash deploy_csv_filter_fix.sh
```

## Résultat Attendu

**AVANT le fix:**
- Transactions: ~milliers
- Montant total: 622 299€ (données historiques)
- Plage de dates: Plusieurs mois/années

**APRÈS le fix:**
- Transactions: ~50-200 (selon votre activité)
- Montant total: < 10 000€ (dépenses du mois courant)
- Plage de dates: Uniquement novembre 2025

## Vérification Finale

Après déploiement, vérifiez les rapports:

```bash
# Sur le VPS
cd /home/linxo/LINXO
tail -50 reports/rapport_linxo_*.txt | grep -A 5 "BUDGET ET STATUT"
```

Vous devriez voir un montant réaliste (< 10 000€) au lieu de 622 299€.

## Prochaines Étapes

Une fois le fix déployé et vérifié:

1. **Télécharger un nouveau CSV** depuis Linxo (avec le bouton "Valider" qui fonctionne maintenant)
2. **Le filtrage sera automatiquement appliqué** lors du téléchargement
3. **Les futurs rapports quotidiens** seront corrects

## En Cas de Problème

Si le filtrage ne fonctionne toujours pas:

1. Vérifiez les logs: `tail -100 logs/linxo_agent.log | grep FILTER`
2. Exécutez le diagnostic: `python3 diagnostic_csv.py data/latest.csv`
3. Copiez-collez les résultats dans le chat

---

**Date du fix:** 2025-11-07
**Commit:** e364093 diagnostic_csv + test_csv_filtering.sh
**Fichiers modifiés:** linxo_agent/csv_filter.py
