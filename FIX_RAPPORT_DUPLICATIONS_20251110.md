# Fix: Rapports dupliqués et améliorations système
## Date: 10 novembre 2025

## 🔴 Problèmes identifiés

### 1. Rapports en double + alerte d'erreur
**Symptôme**: L'utilisateur a reçu 2 fois le même rapport budget, puis une alerte d'erreur
**Cause**: Le workflow cron n'incluait PAS le téléchargement du CSV avant l'analyse
- `run_daily_report.sh` appelait seulement `run_analysis.py`
- `run_analysis.py` utilise le dernier CSV disponible (même s'il est ancien)
- Résultat: rapport envoyé avec données obsolètes → duplication

### 2. Total frais fixes affiché à 0 €
**Symptôme**: "Frais fixes 873.55 € / 0 €" au lieu de "/ 3271 €"
**Cause**: Quand `depenses_recurrentes.json` est absent ou a une liste vide, `sum()` retourne 0 sans déclencher l'exception qui activerait le fallback

### 3. Pas de liens cliquables dans l'email
**Symptôme**: Textes "Frais fixes" et "Dépenses variables" non cliquables
**Besoin**: Liens vers les rapports HTML détaillés

---

## ✅ Corrections appliquées

### 1. Workflow cron corrigé - Téléchargement CSV ajouté
**Fichier**: `run_daily_report.sh`

**Changements**:
```bash
# AVANT (incorrect)
python linxo_agent/run_analysis.py

# APRÈS (correct)
# ÉTAPE 1: Télécharger le CSV depuis Linxo
python linxo_agent.py --skip-notifications

# Vérifier succès téléchargement
if [ $? -ne 0 ]; then
    exit 1  # Arrêter si échec
fi

# ÉTAPE 2: Analyser et envoyer rapport
python linxo_agent/run_analysis.py
```

**Résultat**:
- ✅ CSV téléchargé AVANT l'analyse
- ✅ Si téléchargement échoue → AUCUN rapport envoyé (seulement alerte technique)

### 2. Alerte technique en cas d'échec CSV
**Fichier**: `linxo_agent.py` (lignes 122-148)

**Ajouté**:
- Envoi d'alerte technique détaillée si téléchargement CSV échoue
- Message inclut causes possibles et actions recommandées
- Vérification screenshots d'erreur: `/tmp/csv_button_not_found.png`

**Code de sortie corrigé** (lignes 483-492):
```python
# Vérifier download_success AVANT analysis_success
if not results['download_success']:
    return 1  # Erreur fatale
elif results['analysis_success']:
    return 0  # Succès
else:
    return 1  # Autre erreur
```

### 3. Robustesse téléchargement CSV améliorée
**Fichier**: `linxo_agent/linxo_connexion.py`

**Changements**:

1. **Timeouts augmentés** (ligne 795):
   - `short_wait`: 5s → **10s**
   - Attente téléchargement: 10s → **15s**

2. **Retry logic ajoutée** (lignes 911-935):
   - **3 tentatives** pour cliquer sur bouton CSV
   - Pause de 2s entre chaque tentative
   - Test de tous les sélecteurs à chaque tentative

3. **Polling intelligent** (lignes 948-964):
   - Vérification fichier CSV toutes les 2s
   - Timeout total: 5s → **20s**
   - Détection immédiate quand fichier apparaît

**Résultat**:
- ✅ Meilleure résilience sur VPS lents
- ✅ Tolérance aux variations de latence réseau
- ✅ Détection rapide du fichier téléchargé

### 4. Total frais fixes corrigé
**Fichier**: `linxo_agent/notifications.py` (lignes 586-588)

**Ajouté**:
```python
# Si sum() retourne 0 (liste vide), utiliser le fallback
if budget_fixes_prevu == 0:
    budget_fixes_prevu = 3271.0  # Fallback (mise à jour 2025)
```

**Résultat**:
- ✅ Affichage correct: "Frais fixes 873.55 € / 3271 €"
- ✅ Fallback fonctionne même quand JSON absent ou vide

### 5. Liens cliquables ajoutés dans email
**Fichier**: `templates/email/daily_summary.html.j2` (lignes 247-249, 267-269)

**Ajouté**:
```html
<a href="{{ index_url }}" style="text-decoration: none; color: inherit; border-bottom: 1px dashed #007bff;">
    <span class="metric-label">Frais fixes 🔗</span>
</a>
```

**Style**:
- Bordure pointillée bleue sous le texte
- Icône 🔗 pour indiquer le lien
- Couleur héritée du texte parent
- Lien vers rapport HTML complet

**Résultat**:
- ✅ "Frais fixes 🔗" cliquable → rapport HTML
- ✅ "Dépenses variables 🔗" cliquable → rapport HTML

---

## 📊 Résumé des améliorations

| Problème | État | Solution |
|----------|------|----------|
| Rapports dupliqués | ✅ Corrigé | Téléchargement CSV ajouté au workflow |
| Aucun rapport si CSV échoue | ✅ Corrigé | Exit code + alerte technique |
| Total frais fixes = 0 € | ✅ Corrigé | Fallback 3271 € si liste vide |
| Pas de liens cliquables | ✅ Corrigé | Liens vers rapports HTML |
| Timeouts trop courts VPS | ✅ Amélioré | 10s, 15s, 20s au lieu de 5s |
| Échec téléchargement sporadique | ✅ Amélioré | Retry 3x + polling intelligent |

---

## 🧪 Tests recommandés

### Test 1: Workflow complet normal
```bash
cd /home/linxo/LINXO
bash run_daily_report.sh
```

**Vérifications**:
- ✅ CSV téléchargé dans `data/latest.csv`
- ✅ Email reçu avec frais fixes affichés correctement
- ✅ Liens cliquables dans l'email
- ✅ Exit code = 0

### Test 2: Simulation échec téléchargement
Modifier temporairement les sélecteurs CSS pour qu'ils ne matchent pas.

**Vérifications**:
- ✅ Aucun rapport budget envoyé
- ✅ Alerte technique reçue à phiperez@gmail.com
- ✅ Exit code = 1
- ✅ Screenshot sauvegardé: `/tmp/csv_button_not_found.png`

### Test 3: Vérifier fallback frais fixes
Renommer temporairement `depenses_recurrentes.json`:
```bash
mv data/depenses_recurrentes.json data/depenses_recurrentes.json.bak
python linxo_agent/run_analysis.py
```

**Vérifications**:
- ✅ Email affiche "/ 3271 €" (fallback)
- ✅ Pas d'erreur Python

### Test 4: Cliquer sur liens email
Ouvrir l'email reçu et cliquer sur:
- "Frais fixes 🔗"
- "Dépenses variables 🔗"

**Vérifications**:
- ✅ Redirige vers https://linxo.appliprz.ovh/reports/2025-11-10/index.html
- ✅ Rapport HTML s'affiche correctement
- ✅ Authentification basic auth fonctionne

---

## 📝 Configuration VPS requise

### Crontab mise à jour
```bash
# Vérifier que le cron appelle bien run_daily_report.sh
crontab -l

# Devrait afficher:
0 10 * * * cd /home/linxo/LINXO && bash run_daily_report.sh >> logs/daily_report_$(date +\%Y\%m\%d).log 2>&1
```

### Variables d'environnement requises (.env)
```bash
# Linxo
LINXO_EMAIL=philippe@melprz.fr
LINXO_PASSWORD=Elinxo31021225!

# Email notifications
SENDER_EMAIL=phiperez@gmail.com
NOTIFICATION_EMAIL=phiperez@gmail.com, caliemphi@gmail.com

# Rapports
REPORTS_BASE_URL=https://linxo.appliprz.ovh/reports
REPORTS_SIGNING_KEY=vzsLO33H_yweU27HxYiRxujGftujaoQ9gPPQBQcjuyQ

# Budget
BUDGET_VARIABLE=1700
```

---

## 🚀 Déploiement sur VPS

### 1. Push des changements
```bash
git add .
git commit -m "Fix: rapports dupliqués, frais fixes, et liens cliquables"
git push origin main
```

### 2. Pull sur VPS
```bash
ssh linxo@vps-6e2f6679.vps.ovh.net
cd /home/linxo/LINXO
git pull origin main
```

### 3. Test manuel complet
```bash
# Activer venv
source .venv/bin/activate

# Tester workflow complet
bash run_daily_report.sh

# Vérifier logs
tail -100 logs/daily_report_$(date +%Y%m%d).log
```

### 4. Vérifier cron
```bash
# Le cron s'exécutera automatiquement demain à 10h
# Pour forcer une exécution immédiate:
cd /home/linxo/LINXO && bash run_daily_report.sh
```

---

## 📚 Fichiers modifiés

```
run_daily_report.sh                         # Workflow cron (ajout téléchargement CSV)
linxo_agent.py                              # Alerte technique + code sortie
linxo_agent/linxo_connexion.py             # Robustesse téléchargement (timeouts, retry, polling)
linxo_agent/notifications.py               # Fallback frais fixes 3271€
templates/email/daily_summary.html.j2       # Liens cliquables
```

---

## ✨ Améliorations futures suggérées

### Logging avancé
- [ ] Logs dans fichiers rotatifs au lieu de stdout
- [ ] Niveaux DEBUG/INFO/WARNING/ERROR
- [ ] Rotation automatique (7 jours)

### Monitoring
- [ ] Dashboard de statut des téléchargements
- [ ] Graphique historique des réussites/échecs
- [ ] Alerte si 3 échecs consécutifs

### Interface Linxo
- [ ] Mise à jour automatique des sélecteurs si changement détecté
- [ ] Machine learning pour détecter patterns de changements
- [ ] Fallback vers API Linxo si disponible

---

## 🆘 Support

En cas de problème après déploiement:

1. **Consulter les logs VPS**:
   ```bash
   ssh linxo@vps-6e2f6679.vps.ovh.net
   tail -100 /home/linxo/LINXO/logs/daily_report_*.log
   ```

2. **Vérifier screenshots d'erreur**:
   ```bash
   ls -lt /tmp/*csv* /tmp/*valider* /tmp/*button*
   ```

3. **Tester manuellement**:
   ```bash
   cd /home/linxo/LINXO
   source .venv/bin/activate
   python linxo_agent.py --skip-notifications
   ```

4. **Consulter cette documentation**: `FIX_RAPPORT_DUPLICATIONS_20251110.md`

---

**Auteur**: Assistant Claude
**Date**: 10 novembre 2025
**Version**: 1.0
