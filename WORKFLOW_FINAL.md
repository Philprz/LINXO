# Workflow Final - Agent Budget Linxo

## Vue d'ensemble

Le système implémente un workflow **robuste avec auto-correction** pour garantir que seules les données du mois en cours sont analysées.

## Workflow Détaillé

### Phase 1 : Téléchargement du CSV

```
1. Connexion à Linxo
   └─> Utilise linxo_driver_factory.py (auto-détection VPS/Local)

2. Navigation vers Historique
   └─> URL: https://wwws.linxo.com/secured/history.page
   └─> Note: L'URL directe avec #Search ne fonctionne pas sans clic préalable

3. Sélection de période (avec auto-correction)
   ├─> Clic sur "Recherche avancée" (15+ méthodes de fallback)
   ├─> Sélection "Ce mois-ci" (10+ méthodes de fallback)
   └─> Validation du filtre (7+ méthodes de fallback)

4. Téléchargement CSV
   └─> Clic sur bouton "CSV" (6+ méthodes de fallback)
```

### Phase 2 : Validation et Correction Automatique

```
5. Test du CSV téléchargé
   │
   ├─> Scénario A: CSV contient UNIQUEMENT 11/2025
   │   └─> ✅ ANALYSE IMMÉDIATE
   │
   ├─> Scénario B: CSV contient autres périodes (ex: 2017-2025)
   │   ├─> 🔧 FILTRAGE CSV obligatoire
   │   ├─> Re-validation stricte post-filtrage
   │   │   ├─> Si OK → ✅ ANALYSE + 🔍 DIAGNOSTIC EN ARRIÈRE-PLAN
   │   │   └─> Si KO → ❌ ARRÊT + 📧 ALERTE ADMIN
   │   │
   │   └─> Diagnostic en arrière-plan :
   │       ├─> Capture HTML de la page
   │       ├─> Analyse tous les sélecteurs
   │       ├─> Identifie les méthodes fonctionnelles
   │       └─> 🔧 AUTO-CORRIGE period_selector.py
   │
   └─> Scénario C: Échec de filtrage
       └─> ❌ ARRÊT + 📧 ALERTE ADMIN
```

## Fichiers Modifiés/Créés

### 1. [linxo_connexion.py](linxo_agent/linxo_connexion.py)

**Lignes 783-802** : Utilisation du PeriodSelector auto-adaptatif

**Lignes 987-1021** : Lancement diagnostic en arrière-plan si filtrage nécessaire
```python
if line_count != line_count_after:  # Si on a dû filtrer
    # Lancer diagnostic_linxo_html.py en arrière-plan
    subprocess.Popen(...)
```

### 2. [period_selector.py](linxo_agent/period_selector.py) ⭐ NOUVEAU

Module auto-adaptatif qui teste plusieurs méthodes :
- `click_advanced_search()` : 5 méthodes de fallback
- `select_current_month()` : 5 méthodes de fallback
- `click_validation_button()` : 7 méthodes de fallback

### 3. [diagnostic_linxo_html.py](diagnostic_linxo_html.py) ⭐ NOUVEAU

Script de diagnostic avec auto-correction :
- Capture HTML à chaque étape
- Analyse tous les sélecteurs (select, buttons, etc.)
- Génère rapport JSON + TXT
- **AUTO-CORRIGE** `period_selector.py` avec les bons sélecteurs

### 4. [csv_filter.py](linxo_agent/csv_filter.py)

**Lignes 51-84** : Détection encodage améliorée (UTF-16 LE/BE, cp1252)

### 5. [linxo_agent.py](linxo_agent.py)

**Lignes 124-147** : Alerte admin déjà existante (utilisée en cas d'échec)

## Alertes Admin

### Quand l'alerte est envoyée

L'alerte est envoyée **uniquement** en cas d'échec critique :
- Échec de téléchargement du CSV
- Échec du filtrage CSV (aucune transaction pour le mois)
- CSV filtré contient des dates hors période

### Destinataire

Email : `phiperez@gmail.com`

### Contenu de l'alerte

```
Sujet: [LINXO] Échec de téléchargement du CSV depuis Linxo

Le téléchargement du CSV depuis Linxo a échoué.

Causes possibles:
1. Interface Linxo modifiée (sélecteurs CSS/boutons changés)
2. Problème de connexion ou timeout
3. Authentification échouée
4. Bouton CSV non trouvé sur la page

Actions recommandées:
1. Vérifier les screenshots d'erreur: /tmp/csv_button_not_found.png
2. Consulter les logs: ~/LINXO/logs/daily_report_*.log
3. Tester manuellement: python linxo_agent.py --skip-notifications
```

## Diagnostic Auto-Correctif

### Comment ça fonctionne

1. **Déclenchement** : Automatique si filtrage CSV nécessaire
2. **Exécution** : En arrière-plan (ne bloque pas l'analyse)
3. **Capture** : HTML + Screenshots à chaque étape
4. **Analyse** : Tous les sélecteurs disponibles
5. **Correction** : Mise à jour automatique de `period_selector.py`

### Fichiers générés

```
diagnostic_html/
├── 20251110_172418_01_historique_initial.html
├── 20251110_172418_01_historique_initial.png
├── 20251110_172418_02_apres_recherche_avancee.html
├── 20251110_172418_02_apres_recherche_avancee.png
├── 20251110_172418_03_apres_selection_periode.html
├── 20251110_172418_03_apres_selection_periode.png
├── 20251110_172418_04_apres_validation.html
├── 20251110_172418_04_apres_validation.png
├── 20251110_172418_rapport.json
└── 20251110_172418_rapport.txt
```

### Sauvegarde

Avant toute modification, le fichier original est sauvegardé :
```
linxo_agent/period_selector.py.bak
```

## Scripts de Test

### 1. Test complet du workflow
```bash
python linxo_agent.py --skip-notifications
```

### 2. Test de sélection de période
```bash
python test_period_selection.py
```

### 3. Test du filtrage CSV
```bash
python test_csv_filtering_strict.py
```

### 4. Diagnostic manuel
```bash
python diagnostic_linxo_html.py
```

## Logs et Débogage

### Logs détaillés

Le système affiche des logs très verbeux pour faciliter le débogage :

```
[ETAPE 2-3] Selection de periode avec auto-correction...
[PERIOD] SELECTION DE PERIODE AVEC AUTO-CORRECTION
[PERIOD] Tentative de clic sur 'Recherche avancee'...
  [Tentative] data-dashname=AdvancedResearch
  [SUCCESS] Clic reussi: data-dashname=AdvancedResearch
[PERIOD] Selection de 'Ce mois-ci'...
  [Tentative] Select par ID #gwt-container
    [INFO] Options disponibles:
      - Aujourd'hui (value=1)
      - Hier (value=2)
      - Ce mois-ci (value=3) [CURRENT]
    [SUCCESS] Selection par value=3
[SUCCESS] Periode 'Ce mois-ci' selectionnee avec succes
```

### Screenshots d'erreur

En cas d'échec, des screenshots sont automatiquement sauvegardés :
- `/tmp/csv_button_not_found.png`
- `/tmp/valider_button_not_found.png`
- `/tmp/2fa_after_submit.png`

## Statistiques de Robustesse

Le système teste au total **38+ méthodes différentes** :

| Étape | Nombre de méthodes de fallback |
|-------|-------------------------------|
| Recherche avancée | 5 méthodes |
| Sélection période | 5 méthodes × 3 approches = 15 |
| Bouton validation | 7 méthodes |
| Bouton CSV | 6 méthodes |
| Encodage CSV | 6 encodages × 3 délimiteurs = 18 |

## Exemple de Sortie Réussie

```
[ETAPE 6] FILTRAGE OBLIGATOIRE DU CSV POUR LE MOIS COURANT
[INFO] Periode dans le CSV AVANT filtrage: 01/02/2017 -> 10/11/2025
[FILTER] Filtrage du CSV pour 11/2025
[FILTER] Detection reussie: encodage=utf-16, delimiteur='\t'
[FILTER] 87 transactions trouvées sur 5243 au total
[INFO] Periode dans le CSV APRES filtrage: 01/11/2025 -> 10/11/2025
[VALIDATION OK] Toutes les transactions sont du mois courant (11/2025)
[SUCCESS] Filtrage termine et valide! 5243 -> 88 lignes

[DIAGNOSTIC] La selection web a echoue (filtrage necessaire)
[DIAGNOSTIC] Lancement du diagnostic en arriere-plan...
[DIAGNOSTIC] Diagnostic lance en arriere-plan
[DIAGNOSTIC] Script: /home/linxo/LINXO/diagnostic_linxo_html.py
```

## Prochaine Exécution

Lors de la **prochaine exécution** (après diagnostic) :
1. Le système utilisera les **nouveaux sélecteurs** trouvés par le diagnostic
2. La sélection web devrait **réussir directement**
3. Le CSV téléchargé contiendra **uniquement le mois en cours**
4. **Aucun filtrage** ne sera nécessaire
5. L'analyse sera **plus rapide**

## Maintenance

### Vérifier que le diagnostic a bien corrigé le code

```bash
# Vérifier le fichier period_selector.py
grep "AUTO-CORRECTED" linxo_agent/period_selector.py

# Comparer avec la sauvegarde
diff linxo_agent/period_selector.py linxo_agent/period_selector.py.bak
```

### Restaurer la sauvegarde si nécessaire

```bash
mv linxo_agent/period_selector.py.bak linxo_agent/period_selector.py
```

## Support

En cas de problème, consultez :
1. Les logs dans `~/LINXO/logs/`
2. Les rapports de diagnostic dans `diagnostic_html/`
3. Les screenshots d'erreur dans `/tmp/`
4. L'email d'alerte admin reçu

---

**Dernière mise à jour** : 2025-11-10
**Version** : 2.0 - Auto-correction implémentée
