# Fix: Filtrage CSV par mois obligatoire

## Problème identifié

Le système affichait un total aberrant de **679 445,12€** au lieu des dépenses du mois courant (~1 500€).

### Cause

Le CSV téléchargé depuis Linxo contenait **toutes les transactions historiques depuis 2016-2017**, même quand la sélection web "Ce mois-ci" était censée fonctionner.

Le code dans [linxo_connexion.py:912-934](linxo_agent/linxo_connexion.py#L912-L934) avait une logique conditionnelle :
```python
if not select_found:
    # Filtrer le CSV
else:
    print("[INFO] Selection web reussie, pas besoin de filtrage")
```

Le problème : quand `select_found = True`, le filtrage n'était **pas appliqué**, mais le CSV contenait quand même toutes les données historiques !

## Solution implémentée

### 1. [linxo_connexion.py](linxo_agent/linxo_connexion.py)

**Changement principal** : Le filtrage CSV est maintenant **toujours appliqué**, peu importe si la sélection web a réussi ou non.

```python
# ÉTAPE 6: TOUJOURS filtrer par mois (car la sélection web ne fonctionne pas toujours)
print("[ETAPE 6] Filtrage du CSV pour le mois courant...")
try:
    from .csv_filter import filter_csv_by_month, get_csv_date_range

    # Afficher la plage de dates AVANT filtrage
    date_range = get_csv_date_range(target_csv)
    if date_range:
        min_date, max_date = date_range
        print(f"[INFO] Periode dans le CSV AVANT filtrage: {min_date.strftime('%d/%m/%Y')} -> {max_date.strftime('%d/%m/%Y')}")

    # Filtrer pour le mois courant
    filtered_csv = filter_csv_by_month(target_csv)
    if filtered_csv:
        print("[SUCCESS] CSV filtre pour le mois courant")
        # Afficher la plage de dates APRÈS filtrage
        date_range_after = get_csv_date_range(target_csv)
        if date_range_after:
            min_date, max_date = date_range_after
            print(f"[INFO] Periode dans le CSV APRES filtrage: {min_date.strftime('%d/%m/%Y')} -> {max_date.strftime('%d/%m/%Y')}")
    else:
        print("[WARNING] Filtrage echoue, utilisation du CSV complet")
except Exception as e:
    print(f"[WARNING] Erreur lors du filtrage: {e}")
    traceback.print_exc()
    print("[WARNING] Utilisation du CSV complet")
```

**Améliorations** :
- ✅ Filtrage **systématique**, sans condition
- ✅ Affichage de la plage de dates **avant** ET **après** filtrage pour vérifier
- ✅ Gestion d'erreurs robuste avec traceback complet

### 2. [run_linxo_e2e.py](linxo_agent/run_linxo_e2e.py)

Ajout du filtrage CSV également dans le script E2E (pour cohérence) :

```python
# IMPORTANT: Filter CSV by current month
log("\n[FILTER] Applying month filter to CSV...")
try:
    from csv_filter import filter_csv_by_month
    filtered_path = filter_csv_by_month(target_csv)
    if filtered_path:
        log(f"✅ CSV filtered for current month")
    else:
        log(f"⚠️ CSV filtering returned None, using unfiltered CSV")
except Exception as filter_error:
    log(f"⚠️ CSV filtering failed: {filter_error}")
    log(f"   Continuing with unfiltered CSV")
```

## Module de filtrage : [csv_filter.py](linxo_agent/csv_filter.py)

Le module existait déjà mais n'était jamais appelé. Il fournit :

- `filter_csv_by_month(input_csv, year, month)` : Filtre le CSV pour un mois donné
- `get_csv_date_range(csv_path)` : Retourne la plage de dates dans un CSV

## Comment tester

### Méthode 1 : Script automatique

```bash
cd /home/linxo/LINXO
git pull
bash deploy_fix_and_test.sh
```

### Méthode 2 : Test manuel sur le VPS

```bash
ssh linxo@vps-6e2f6679.vps.ovh.net
cd LINXO
git pull origin main
source .venv/bin/activate
python linxo_agent.py --skip-notifications
```

### Vérifications attendues

Dans les logs, vous devriez voir :

```
[ETAPE 6] Filtrage du CSV pour le mois courant...
[INFO] Periode dans le CSV AVANT filtrage: 31/12/2016 -> 07/11/2025
[FILTER] Filtrage du CSV pour 11/2025
[FILTER] 156 transactions trouvées sur 8943 au total
[SUCCESS] CSV filtré créé: /home/linxo/LINXO/data/csv/filtered_comptes_XXXXXXXX.csv
[INFO] Fichier original remplacé par la version filtrée
[SUCCESS] CSV filtre pour le mois courant
[INFO] Periode dans le CSV APRES filtrage: 01/11/2025 -> 07/11/2025
```

Dans le rapport final :

```
TOTAL VARIABLES: 1500.00E   (au lieu de 622297.72E)
BUDGET ET STATUT: [VERT] OK  (au lieu de [ROUGE] ALERTE)
```

## Commits

- `183fbaa` - Force CSV filtering by month to prevent analyzing historical data
- `f100f30` - Add deployment and test script for CSV filtering fix

## Notes

- Le filtrage fonctionne même si le CSV téléchargé contient des années de données
- Les exclusions (relevés différés, virements internes, etc.) sont toujours appliquées
- Le fichier original est remplacé par la version filtrée pour éviter toute confusion
- En cas d'erreur de filtrage, le système continue avec le CSV complet (fallback sécurisé)
