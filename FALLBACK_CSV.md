# Fallback de Filtrage CSV

## Problème

Linxo utilise des **classes CSS obfusquées** qui changent régulièrement lors des déploiements. Cela rend difficile la sélection fiable de "Ce mois-ci" dans l'interface web.

**Conséquence** : Si la sélection échoue, Linxo télécharge **toutes les transactions depuis 2016** (plusieurs milliers), ce qui :
- Ralentit considérablement l'analyse
- Consomme beaucoup de mémoire
- Génère des rapports avec des données hors période

## Solution

### Architecture à deux niveaux

```
┌─────────────────────────────────────────────────┐
│  NIVEAU 1: Sélection Web (méthode préférée)    │
│  - Essaie de cliquer sur "Recherche avancée"   │
│  - Essaie de sélectionner "Ce mois-ci"         │
│  - Utilise plusieurs sélecteurs de fallback    │
└─────────────────┬───────────────────────────────┘
                  │
                  │ ✓ Succès → Télécharge déjà filtré
                  │
                  ├──────────────────────────────────┐
                  │                                  │
           ✓ SUCCÈS                           ✗ ÉCHEC
                  │                                  │
                  ▼                                  ▼
┌─────────────────────────────┐  ┌──────────────────────────────────┐
│  Pas de filtrage nécessaire │  │  NIVEAU 2: Filtrage CSV         │
│  CSV déjà filtré par Linxo  │  │  - Analyse la plage de dates    │
└─────────────────────────────┘  │  - Filtre pour le mois courant  │
                                  │  - Remplace le fichier original │
                                  └──────────────────────────────────┘
```

### Module csv_filter.py

#### Fonctions principales

**1. `filter_csv_by_month(csv_path, year=None, month=None)`**
```python
# Filtre un CSV pour ne garder que le mois courant
filtered = filter_csv_by_month(csv_path)
```

**2. `get_csv_date_range(csv_path)`**
```python
# Retourne (date_min, date_max)
date_range = get_csv_date_range(csv_path)
```

#### Intégration dans linxo_connexion.py

```python
# ÉTAPE 3: Sélection du mois
select_found = False  # Flag pour savoir si la sélection a réussi
# ... tentatives de sélection ...

# ÉTAPE 6: Fallback si échec
if not select_found:
    print("[ETAPE 6] Filtrage du CSV pour le mois courant (fallback)...")
    filter_csv_by_month(target_csv)
```

### Logs

#### Cas 1 : Sélection web réussie
```
[ETAPE 3] Selection de 'Ce mois-ci' dans le menu deroulant...
[OK] 'Ce mois-ci' selectionne (option avec value='3')
[INFO] Selection web reussie, pas besoin de filtrage
```

#### Cas 2 : Fallback activé
```
[ETAPE 3] Selection de 'Ce mois-ci' dans le menu deroulant...
[WARNING] Methode 'attribut data-dashname' echouee
[WARNING] Methode 'option contenant 'Ce mois-ci'' echouee
[WARNING] Methode 'option avec value='3'' echouee
[WARNING] Impossible de selectionner 'Ce mois-ci'
[ETAPE 6] Filtrage du CSV pour le mois courant (fallback)...
[INFO] Periode dans le CSV: 01/01/2016 -> 06/11/2025
[FILTER] Filtrage du CSV pour 11/2025
[FILTER] 127 transactions trouvees sur 8456 au total
[SUCCESS] CSV filtre pour le mois courant
```

## Avantages

✅ **Robustesse** : Fonctionne même si l'interface Linxo change
✅ **Performance** : Filtre en quelques secondes (vs. analyse de 8000+ transactions)
✅ **Transparence** : Logs détaillés pour le debugging
✅ **Zéro impact** : Si la sélection web fonctionne, rien ne change
✅ **Testable** : Tests unitaires inclus (test_csv_filter.py)

## Tests

```bash
# Tester le module de filtrage
python test_csv_filter.py

# Tester sur un vrai CSV Linxo
python -m linxo_agent.csv_filter path/to/linxo.csv
```

## Format CSV Linxo

Le filtrage attend ce format :
```csv
Date;Libellé;Montant;Catégorie
05/11/2024;CARREFOUR;-45.50;Alimentation
10/11/2024;SALAIRE;2500.00;Revenus
```

**Configuration par défaut** :
- Colonne de date : `"Date"`
- Format : `"%d/%m/%Y"` (jour/mois/année)
- Séparateur : `;` (point-virgule)

Ces paramètres peuvent être modifiés dans les arguments de `filter_csv_by_month()`.
