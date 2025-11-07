# Guide de test sur le VPS

## Pré-requis

Les changements suivants ont été implémentés :
- ✅ Sélecteurs CSS GWT pour le dropdown de période
- ✅ Clic sur le bouton "Valider" après la sélection
- ✅ Filtrage CSV systématique avec logs détaillés
- ✅ Script de diagnostic

## Étape 1 : Diagnostic (optionnel mais recommandé)

Depuis votre machine Windows :

```powershell
bash diagnostic_vps_filtering.sh
```

Ce script va :
1. Vérifier la version Git sur le VPS
2. Afficher le code de filtrage CSV
3. Tester l'import du module csv_filter
4. Vérifier la présence du fichier csv_filter.py
5. Analyser les logs récents

**Résultat attendu** :
```
✅ Import réussi !
✅ linxo_agent/csv_filter.py existe
```

Si le diagnostic échoue, voir la section [Troubleshooting](#troubleshooting).

## Étape 2 : Test complet sur le VPS

### Connexion au VPS

```bash
ssh linxo@vps-6e2f6679.vps.ovh.net
cd LINXO
```

### Récupérer les derniers changements

```bash
git pull origin main
```

**Vérifier** que le commit apparaît :
```bash
git log -1 --oneline
```

Vous devriez voir :
```
be47869 Add GWT selectors, "Valider" button click, and improved CSV filtering logs
```

### Activer l'environnement virtuel

```bash
source .venv/bin/activate
```

### Lancer l'analyse (sans notifications pour le test)

```bash
python linxo_agent.py --skip-notifications
```

## Étape 3 : Vérifier les logs

### Logs attendus - Sélection web

Cherchez ces lignes dans la sortie :

```
[ETAPE 3] Selection de 'Ce mois-ci' dans le menu deroulant...
[OK] 'Ce mois-ci' selectionne (selecteur GWT specifique)

[ETAPE 3.5] Recherche du bouton 'Valider' pour appliquer le filtre...
[OK] Bouton 'Valider' clique (texte 'Valider')
```

✅ **Si vous voyez ces lignes** → La sélection web fonctionne !
⚠️ **Si vous voyez des [WARNING]** → La sélection web a échoué, mais le filtrage CSV devrait compenser

### Logs attendus - Filtrage CSV

Cherchez cette section (très visible avec les `====`) :

```
================================================================================
[ETAPE 6] FILTRAGE DU CSV POUR LE MOIS COURANT
================================================================================
[DEBUG] Tentative d'import du module csv_filter...
[DEBUG] Import du module csv_filter: OK
[DEBUG] Fichier CSV a filtrer: /home/linxo/LINXO/data/csv/latest.csv
[DEBUG] Nombre de lignes AVANT filtrage: 8943
[INFO] Periode dans le CSV AVANT filtrage: 31/12/2016 -> 07/11/2025
[DEBUG] Lancement du filtrage...
[FILTER] Filtrage du CSV pour 11/2025
[FILTER] 156 transactions trouvées sur 8943 au total
[SUCCESS] CSV filtre pour le mois courant
[DEBUG] Nombre de lignes APRES filtrage: 157
[INFO] Periode dans le CSV APRES filtrage: 01/11/2025 -> 07/11/2025
[SUCCESS] Filtrage termine! 8943 -> 157 lignes
================================================================================
```

✅ **Si vous voyez cette section** → Le filtrage CSV fonctionne !
❌ **Si cette section n'apparaît PAS** → Problème grave, voir [Troubleshooting](#troubleshooting)

### Logs attendus - Rapport final

À la fin de l'exécution, cherchez :

```
TOTAL VARIABLES: 1500.00E   (ou similaire, ~1500€)
BUDGET ET STATUT: [VERT] OK
```

✅ **Si le total est ~1500€** → Tout fonctionne correctement !
❌ **Si le total est 679445€** → Le filtrage a échoué

## Étape 4 : Consulter le rapport généré

```bash
# Voir le dernier rapport
ls -lt reports/rapport_linxo_*.txt | head -1

# Lire le rapport
cat reports/rapport_linxo_*.txt | tail -50
```

Vérifiez :
- Total variables : **~1500€** (pas 679k€)
- Nombre de transactions : **~150-200** (pas 8000+)
- Dates : **Novembre 2025 uniquement**

## Étape 5 : Vérifier le CSV filtré

```bash
# Voir les premières transactions du CSV
head -20 data/csv/latest.csv

# Compter les lignes
wc -l data/csv/latest.csv
```

**Résultat attendu** :
- Environ **150-200 lignes** (pas 9000+)
- Toutes les dates sont en **Novembre 2025**

## Troubleshooting

### Problème : [ETAPE 6] n'apparaît pas

**Diagnostic** :
```bash
# Vérifier que le code modifié est bien présent
sed -n '955,960p' linxo_agent/linxo_connexion.py
```

Vous devriez voir :
```python
# ÉTAPE 6: TOUJOURS filtrer par mois (car la sélection web ne fonctionne pas toujours)
print("\n" + "=" * 80)
print("[ETAPE 6] FILTRAGE DU CSV POUR LE MOIS COURANT")
```

**Si ce n'est pas le cas** :
1. Re-faire `git pull origin main`
2. Vérifier qu'il n'y a pas de conflit : `git status`
3. Si problème persiste, copier manuellement le fichier

### Problème : ImportError csv_filter

**Diagnostic** :
```bash
# Vérifier que le fichier existe
ls -l linxo_agent/csv_filter.py

# Tester l'import manuellement
python -c "from linxo_agent.csv_filter import filter_csv_by_month; print('OK')"
```

**Si le fichier n'existe pas** :
```bash
git status
git pull origin main --force
```

### Problème : Le rapport affiche toujours 679k€

**Diagnostic détaillé** :
```bash
# 1. Vérifier le CSV téléchargé
wc -l data/csv/latest.csv
# Devrait être ~150 lignes, pas 9000+

# 2. Chercher les erreurs dans les logs
grep -i "erreur\|error\|warning" reports/rapport_linxo_*.txt | tail -20

# 3. Tester le filtrage manuellement
python << 'EOF'
from pathlib import Path
from linxo_agent.csv_filter import filter_csv_by_month, get_csv_date_range

csv_path = Path("data/csv/latest.csv")
date_range = get_csv_date_range(csv_path)
if date_range:
    print(f"Période: {date_range[0]} -> {date_range[1]}")

result = filter_csv_by_month(csv_path)
print(f"Résultat: {result}")
EOF
```

### Problème : Le bouton "Valider" n'est pas trouvé

**Ce n'est pas grave !** Le filtrage CSV devrait compenser.

Mais si vous voulez débugger :
```bash
# Voir le screenshot de debug
ls -l /tmp/valider_button_not_found.png

# Télécharger le screenshot pour inspection
scp linxo@vps-6e2f6679.vps.ovh.net:/tmp/valider_button_not_found.png ./
```

Ensuite, inspectez manuellement la page Linxo pour trouver le bon sélecteur.

## Validation finale

✅ **Test réussi si** :
- [ETAPE 6] FILTRAGE DU CSV apparaît dans les logs
- Le nombre de lignes passe de ~9000 à ~150
- La période passe de 2016-2025 à 01/11/2025-07/11/2025
- Le rapport final affiche ~1500€ (pas 679k€)

❌ **Test échoué si** :
- [ETAPE 6] n'apparaît pas dans les logs
- ImportError sur csv_filter
- Le rapport affiche toujours 679k€

## Prochaines étapes

Une fois le test validé :

1. **Activer les notifications** :
   ```bash
   python linxo_agent.py  # Sans --skip-notifications
   ```

2. **Vérifier le cron quotidien** :
   ```bash
   crontab -l
   ```

3. **Monitorer les prochaines exécutions automatiques**

## Notes

- Le filtrage CSV est **toujours appliqué** maintenant, même si la sélection web réussit
- C'est une approche "défense en profondeur" pour garantir des données correctes
- Les logs détaillés permettent de diagnostiquer rapidement tout problème

---

**Besoin d'aide ?** Consultez [FIX_FILTRAGE_CSV.md](FIX_FILTRAGE_CSV.md) pour la documentation complète.
