# 🚀 Déploiement Final du Fix CSV

## ✅ Statut Actuel

- ✅ CSV sur le VPS filtré manuellement (12,984 → 44 transactions)
- ✅ Budget correct : 1,218€ au lieu de 622,299€
- ✅ Notifications envoyées avec les bons montants
- ⚠️ Module `csv_filter.py` sur le VPS encore avec l'ancienne version

## 🎯 Objectif

Déployer le module amélioré `csv_filter.py` qui détecte automatiquement l'encodage et le délimiteur pour que **les prochains téléchargements depuis Linxo soient automatiquement filtrés**.

## 📋 Instructions de Déploiement

### Sur le VPS (via SSH)

```bash
# 1. Se connecter au VPS
ssh linxo@vps-6e2f6679.vps.ovh.net

# 2. Aller dans le répertoire
cd /home/linxo/LINXO

# 3. Sauvegarder l'ancienne version (au cas où)
cp linxo_agent/csv_filter.py linxo_agent/csv_filter.py.backup

# 4. Récupérer la nouvelle version depuis GitHub
git pull origin main

# 5. Vérifier que le nouveau code est bien déployé
grep "Détecter automatiquement" linxo_agent/csv_filter.py
# Devrait afficher: # Détecter automatiquement l'encodage et le délimiteur

# 6. Tester le module avec le CSV existant
source .venv/bin/activate
python3 linxo_agent/csv_filter.py data/latest.csv

# Vous devriez voir:
# [FILTER] Détection: encodage=utf-16, délimiteur='\t'
# [FILTER] XX transactions trouvées sur YY au total
# [SUCCESS] Fichier filtré créé: ...
```

### Vérification du Bon Fonctionnement

```bash
# Vérifier que le CSV est bien filtré
python3 << 'EOF'
import csv
from datetime import datetime
from pathlib import Path

csv_path = Path('data/latest.csv')

# Détecter encodage
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
                from collections import Counter
                mois_counter = Counter((d.year, d.month) for d in dates)

                print(f"\nTransactions: {len(dates)}")
                print(f"Mois différents: {len(mois_counter)}")

                if len(mois_counter) == 1 and (now.year, now.month) in mois_counter:
                    print(f"✅ CSV CORRECTEMENT FILTRÉ pour {now.strftime('%B %Y')}")
                else:
                    print(f"❌ CSV contient plusieurs mois")
                    for (y, m), c in sorted(mois_counter.items())[-3:]:
                        print(f"   - {m:02d}/{y}: {c} transactions")
                break
        except:
            pass
EOF
```

## 🔄 Test du Workflow Complet

Pour tester que tout fonctionne de bout en bout:

```bash
# 1. Télécharger un nouveau CSV depuis Linxo (simulation ou réel)
# Le filtrage devrait être appliqué automatiquement lors du téléchargement
# via la fonction telecharger_csv_linxo() dans linxo_connexion.py

# 2. Vérifier les logs
tail -50 logs/linxo_agent.log | grep -i "filter\|filtrage"

# Vous devriez voir des lignes comme:
# [FILTER] Filtrage du CSV pour 11/2025
# [FILTER] Détection: encodage=utf-16, délimiteur='\t'
# [SUCCESS] CSV filtre pour le mois courant
```

## 📊 Résultat Attendu

Après déploiement, les **prochains téléchargements** depuis Linxo:

1. ✅ Téléchargent le CSV complet (historique)
2. ✅ **Détectent automatiquement** l'encodage (UTF-16) et le délimiteur (tab)
3. ✅ **Filtrent automatiquement** pour le mois courant
4. ✅ Remplacent le fichier par la version filtrée
5. ✅ L'analyse montre des montants réalistes (< 10,000€)

## 🔍 Dépannage

### Le filtrage ne s'applique pas

```bash
# Vérifier que le module est à jour
cd /home/linxo/LINXO
git log -1 --oneline linxo_agent/csv_filter.py
# Devrait afficher: de0bdb3 Improve CSV filter with automatic encoding...

# Forcer le re-filtrage
python3 linxo_agent/csv_filter.py data/latest.csv
```

### Le CSV est vide après filtrage

Si aucune transaction n'est trouvée pour le mois courant:
- Vérifiez que le CSV téléchargé contient bien des transactions récentes
- Le filtre cherche le mois et l'année actuels (`datetime.now()`)
- Si vous testez avec un vieux CSV, il est normal qu'il soit vide

## 📝 Notes Importantes

1. **Le CSV déjà filtré ne sera pas ré-analysé** : Le système vérifie si un CSV a déjà été traité aujourd'hui
2. **Pour tester, supprimez le fichier `.sent_history`** : `rm data/.sent_history`
3. **Le prochain téléchargement automatique** (via cron à 10h) utilisera automatiquement le nouveau filtre

---

**Date de création:** 2025-11-07
**Commit:** de0bdb3 - Improve CSV filter with automatic encoding and delimiter detection
**Status:** ✅ Fix testé et validé sur le VPS
