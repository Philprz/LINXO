# Fix: Filtrage CSV par mois obligatoire

## Problème identifié

Le système affichait un total aberrant de **679 445,12€** au lieu des dépenses du mois courant (~1 500€).

### Cause racine

Le CSV téléchargé depuis Linxo contenait **toutes les transactions historiques depuis 2016-2017**, pour deux raisons :

1. **La sélection web "Ce mois-ci" ne fonctionnait pas** car :
   - Le bouton "Valider" n'était **jamais cliqué** après la sélection
   - Les sélecteurs CSS n'étaient pas assez spécifiques pour l'interface GWT de Linxo

2. **Le filtrage CSV n'était pas toujours appliqué** :
   - Code conditionnel : `if not select_found:` filtrait uniquement si la sélection web échouait
   - Quand `select_found = True`, le filtrage était ignoré... mais le CSV contenait quand même toutes les données !

## Solutions implémentées

### 1. Amélioration de la sélection web (ÉTAPE 3 & 3.5)

**Fichier** : [linxo_connexion.py:817-895](linxo_agent/linxo_connexion.py#L817-L895)

#### A. Sélecteurs CSS GWT spécifiques

Ajout de sélecteurs adaptés à l'interface Google Web Toolkit de Linxo :

```python
select_locators = [
    ("selecteur GWT specifique", By.CSS_SELECTOR, "#gwt-container select"),
    ("selecteur GWT detaille", By.CSS_SELECTOR, "div.GJYWTJUCBY > select"),
    ("attribut data-dashname", By.CSS_SELECTOR, "select[data-dashname-rid*='period']"),
    ("option contenant 'Ce mois-ci'", By.XPATH, "//select[.//option[contains(text(), 'Ce mois-ci')]]"),
    ("option avec value='3'", By.XPATH, "//select[.//option[@value='3']]"),
    ("premier select visible", By.TAG_NAME, "select"),
]
```

#### B. Clic sur le bouton "Valider" (NOUVEAU !)

Ajout d'une **ÉTAPE 3.5** pour cliquer sur le bouton "Valider" après la sélection :

```python
# ÉTAPE 3.5: Cliquer sur le bouton "Valider" pour appliquer le filtre
if select_found:
    print("[ETAPE 3.5] Recherche du bouton 'Valider' pour appliquer le filtre...")

    valider_locators = [
        ("texte 'Valider'", By.XPATH, "//button[contains(text(), 'Valider')]"),
        ("texte 'Appliquer'", By.XPATH, "//button[contains(text(), 'Appliquer')]"),
        ("texte 'Filtrer'", By.XPATH, "//button[contains(text(), 'Filtrer')]"),
        ("texte 'OK'", By.XPATH, "//button[contains(text(), 'OK')]"),
        ("input type submit", By.CSS_SELECTOR, "input[type='submit']"),
        ("bouton dans le meme conteneur", By.XPATH, "//select/ancestor::div[1]//button"),
    ]

    # Cliquer et attendre 5 secondes pour le rafraîchissement
    valider_button.click()
    time.sleep(5)
```

**Améliorations** :
- ✅ 6 fallbacks différents pour trouver le bouton "Valider"
- ✅ Attente de 5 secondes après le clic pour le rafraîchissement de la page
- ✅ Screenshot de debug si le bouton n'est pas trouvé

### 2. Filtrage CSV systématique (ÉTAPE 6)

**Fichier** : [linxo_connexion.py:955-1035](linxo_agent/linxo_connexion.py#L955-L1035)

Le filtrage CSV est maintenant **toujours appliqué**, avec des logs de debug exhaustifs :

```python
# ÉTAPE 6: TOUJOURS filtrer par mois (car la sélection web ne fonctionne pas toujours)
print("\n" + "=" * 80)
print("[ETAPE 6] FILTRAGE DU CSV POUR LE MOIS COURANT")
print("=" * 80)

try:
    # Tentative d'import du module de filtrage CSV
    print("[DEBUG] Tentative d'import du module csv_filter...")
    from .csv_filter import filter_csv_by_month, get_csv_date_range
    print("[DEBUG] Import du module csv_filter: OK")

    # Compter le nombre de lignes avant filtrage
    with open(target_csv, 'r', encoding='utf-8') as f:
        line_count = sum(1 for _ in f)
    print(f"[DEBUG] Nombre de lignes AVANT filtrage: {line_count}")

    # Afficher la plage de dates AVANT filtrage
    date_range = get_csv_date_range(target_csv)
    if date_range:
        min_date, max_date = date_range
        print(f"[INFO] Periode dans le CSV AVANT filtrage: {min_date.strftime('%d/%m/%Y')} -> {max_date.strftime('%d/%m/%Y')}")

    # Filtrer pour le mois courant
    filtered_csv = filter_csv_by_month(target_csv)

    if filtered_csv:
        print("[SUCCESS] CSV filtre pour le mois courant")

        # Compter le nombre de lignes après filtrage
        with open(target_csv, 'r', encoding='utf-8') as f:
            line_count_after = sum(1 for _ in f)

        print(f"[SUCCESS] Filtrage termine! {line_count} -> {line_count_after} lignes")

except ImportError as e:
    print(f"[ERREUR CRITIQUE] Impossible d'importer le module csv_filter: {e}")
    traceback.print_exc()
    print("[WARNING] Le rapport contiendra toutes les donnees historiques!")
```

**Améliorations** :
- ✅ Logs de debug à chaque étape
- ✅ Vérification explicite de l'import du module
- ✅ Comptage des lignes avant/après filtrage
- ✅ Gestion d'erreurs spécifiques (ImportError, FileNotFoundError, Exception)
- ✅ Messages d'alerte clairs si le filtrage échoue

### 3. Script de diagnostic VPS

**Fichier** : [diagnostic_vps_filtering.sh](diagnostic_vps_filtering.sh)

Nouveau script pour diagnostiquer pourquoi le filtrage ne fonctionne pas :

```bash
#!/bin/bash
# Vérifie :
# - Version Git sur le VPS
# - Présence du fichier csv_filter.py
# - Possibilité d'importer le module
# - Logs récents
```

**Utilisation** :
```bash
bash diagnostic_vps_filtering.sh
```

## Module de filtrage : [csv_filter.py](linxo_agent/csv_filter.py)

Le module fournit :

- `filter_csv_by_month(input_csv, year, month)` : Filtre le CSV pour un mois donné
- `get_csv_date_range(csv_path)` : Retourne la plage de dates dans un CSV

## Comment tester

### Méthode 1 : Diagnostic complet

```bash
# 1. Lancer le diagnostic
bash diagnostic_vps_filtering.sh

# 2. Analyser les résultats pour identifier le problème
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

#### Dans les logs - Sélection web

```
[ETAPE 3] Selection de 'Ce mois-ci' dans le menu deroulant...
[OK] 'Ce mois-ci' selectionne (selecteur GWT specifique)

[ETAPE 3.5] Recherche du bouton 'Valider' pour appliquer le filtre...
[OK] Bouton 'Valider' clique (texte 'Valider')
```

#### Dans les logs - Filtrage CSV

```
================================================================================
[ETAPE 6] FILTRAGE DU CSV POUR LE MOIS COURANT
================================================================================
[DEBUG] Tentative d'import du module csv_filter...
[DEBUG] Import du module csv_filter: OK
[DEBUG] Fichier CSV a filtrer: /home/linxo/LINXO/data/csv/latest.csv
[DEBUG] Taille du fichier: 987654 octets
[DEBUG] Nombre de lignes AVANT filtrage: 8943
[DEBUG] Analyse de la plage de dates...
[INFO] Periode dans le CSV AVANT filtrage: 31/12/2016 -> 07/11/2025
[DEBUG] Lancement du filtrage...
[FILTER] Filtrage du CSV pour 11/2025
[FILTER] 156 transactions trouvées sur 8943 au total
[SUCCESS] CSV filtré créé: /home/linxo/LINXO/data/csv/filtered_latest.csv
[INFO] Fichier original remplacé par la version filtrée
[SUCCESS] CSV filtre pour le mois courant
[DEBUG] Nombre de lignes APRES filtrage: 157
[INFO] Periode dans le CSV APRES filtrage: 01/11/2025 -> 07/11/2025
[SUCCESS] Filtrage termine! 8943 -> 157 lignes
================================================================================
```

#### Dans le rapport final

```
TOTAL VARIABLES: 1500.00E   (au lieu de 622297.72E)
BUDGET ET STATUT: [VERT] OK  (au lieu de [ROUGE] ALERTE)
```

## Troubleshooting

### Problème : Aucun log `[ETAPE 6]` n'apparaît

**Cause** : Le code modifié ne s'exécute pas sur le VPS

**Solutions** :
1. Vérifier que `git pull` a bien récupéré les changements
2. Lancer le diagnostic : `bash diagnostic_vps_filtering.sh`
3. Vérifier quel fichier Python est utilisé (linxo_agent.py vs run_linxo_e2e.py)

### Problème : `ImportError: No module named 'csv_filter'`

**Cause** : Le fichier csv_filter.py n'existe pas ou n'est pas dans le bon dossier

**Solutions** :
1. Vérifier : `ls -l linxo_agent/csv_filter.py`
2. Si manquant : `git pull` ou copier le fichier manuellement

### Problème : Le rapport affiche toujours 679k€

**Cause** : Le filtrage CSV échoue silencieusement

**Solutions** :
1. Chercher dans les logs : `grep -i "erreur\|warning" rapport_linxo_*.txt`
2. Vérifier les permissions : `ls -l data/csv/latest.csv`
3. Tester manuellement : `python -c "from linxo_agent.csv_filter import filter_csv_by_month; filter_csv_by_month('data/csv/latest.csv')"`

### Problème : Le bouton "Valider" n'est pas trouvé

**Cause** : L'interface Linxo a changé

**Solutions** :
1. Consulter le screenshot : `cat /tmp/valider_button_not_found.png`
2. Inspecter la page manuellement pour trouver le nouveau sélecteur
3. Ajouter le nouveau sélecteur dans `valider_locators`

## Commits

- `183fbaa` - Force CSV filtering by month to prevent analyzing historical data
- `f100f30` - Add deployment and test script for CSV filtering fix
- `b074839` - Add documentation for CSV filtering fix
- `XXXXXX` - Add GWT selectors and "Valider" button click for robust period selection
- `XXXXXX` - Improve CSV filtering logs with detailed debug information

## Notes techniques

### Structure de l'interface Linxo

Linxo utilise **Google Web Toolkit (GWT)** qui génère des classes CSS dynamiques :
- Classes comme `GJYWTJUCDV`, `GJYWTJUCOGC` peuvent changer
- Les sélecteurs CSS doivent être robustes avec plusieurs fallbacks
- Le sélecteur complet trouvé par inspection :
  ```css
  #gwt-container > div > div.GJYWTJUCDV > div > table > tbody > tr > td.GJYWTJUCOGC > div.GJYWTJUCPGC > div.GJYWTJUCAHC.GJYWTJUCFU > div:nth-child(1) > div > div.GJYWTJUCBY > select
  ```

### Workflow complet

1. **Connexion** → `se_connecter_linxo()`
2. **Navigation** → Page Historique
3. **Recherche avancée** → Clic sur "Recherche avancée"
4. **Sélection période** → Sélectionner "Ce mois-ci" (value="3")
5. **Validation** → ⚡ **NOUVEAU** : Cliquer sur "Valider"
6. **Attente** → 5 secondes pour rafraîchissement
7. **Téléchargement** → Clic sur bouton CSV
8. **Filtrage CSV** → ⚡ **TOUJOURS** appliqué, même si sélection web réussit
9. **Analyse** → Utilisation du CSV filtré

### Sécurité multicouche

Le système implémente une approche **défense en profondeur** :

1. **Couche 1** : Sélection web (peut échouer)
2. **Couche 2** : Bouton "Valider" (peut être introuvable)
3. **Couche 3** : ⚡ **Filtrage CSV systématique** (toujours appliqué)

→ Même si les couches 1 et 2 échouent, la couche 3 garantit des données correctes !
