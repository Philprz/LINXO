# Migration VPS vers Emails HTML

## Résumé de la Migration

**Objectif** : Migrer le VPS du système RELIABLE (emails texte brut) vers le système moderne (emails HTML + analyse améliorée)

**Avantages** :
- ✅ Emails HTML magnifiques et lisibles
- ✅ Détection améliorée des préautorisations carburant
- ✅ Meilleure gestion des virements ponctuels
- ✅ Système d'identifiant pour différencier les dépenses similaires
- ✅ Architecture modulaire et maintenable

---

## État Actuel

### Sur le VPS (Ubuntu)
- **Script exécuté** : `/home/linxo/LINXO/linxo_agent/run_analysis.py`
- **Configuration cron** : Tous les jours à 10h via `/home/linxo/LINXO/run_daily_report.sh`
- **Version utilisée** : `agent_linxo_csv_v3_RELIABLE` (emails texte brut)

### Nouveau Système (Déjà testé localement)
- **Script modifié** : `linxo_agent/run_analysis.py`
- **Modules utilisés** :
  - `analyzer.py` - Analyse moderne améliorée
  - `notifications.py` - Gestionnaire email HTML + SMS
  - `report_formatter_v2.py` - Formatage HTML épuré
  - `config.py` - Configuration unifiée

---

## Étapes de Déploiement

### 1. Backup de Sécurité sur le VPS

```bash
# Connexion SSH au VPS
ssh linxo@votre-vps.com

# Créer un backup de l'ancien système
cd /home/linxo
cp -r LINXO LINXO_BACKUP_$(date +%Y%m%d_%H%M%S)

# Vérifier le backup
ls -la LINXO_BACKUP_*
```

### 2. Synchroniser les Fichiers Modifiés

Depuis votre machine locale (Windows), synchronisez les fichiers vers le VPS :

```bash
# Option A: Via Git (recommandé)
cd C:\Users\PhilippePEREZ\OneDrive\LINXO
git add linxo_agent/run_analysis.py
git commit -m "Migrate to modern HTML email system"
git push

# Puis sur le VPS
ssh linxo@votre-vps.com
cd /home/linxo/LINXO
git pull

# Option B: Via SCP (alternatif)
scp C:\Users\PhilippePEREZ\OneDrive\LINXO\linxo_agent\run_analysis.py linxo@votre-vps:/home/linxo/LINXO/linxo_agent/
```

### 3. Vérifier que les Dépendances sont Présentes

```bash
# Sur le VPS
ssh linxo@votre-vps.com
cd /home/linxo/LINXO
source .venv/bin/activate

# Vérifier que les modules existent
python -c "from linxo_agent.analyzer import analyser_csv; print('analyzer OK')"
python -c "from linxo_agent.notifications import NotificationManager; print('notifications OK')"
python -c "from linxo_agent.report_formatter_v2 import formater_email_html_v2; print('formatter OK')"
python -c "from linxo_agent.config import get_config; print('config OK')"
```

### 4. Test Manuel sur le VPS

```bash
# Test avec le dernier CSV disponible
cd /home/linxo/LINXO
source .venv/bin/activate
python linxo_agent/run_analysis.py

# Vérifier les logs pour s'assurer que :
# - L'analyse se déroule correctement
# - L'email HTML est envoyé
# - Le SMS est envoyé
```

### 5. Vérifier le Cron (optionnel)

Le script cron `run_daily_report.sh` n'a pas besoin d'être modifié car il appelle déjà `python linxo_agent/run_analysis.py`.

```bash
# Vérifier que le cron est actif
crontab -l

# Le cron devrait contenir quelque chose comme :
# 0 10 * * * /home/linxo/LINXO/run_daily_report.sh
```

### 6. Vérifier les Emails

Après le test, vérifiez vos emails :
- ✅ Vous devriez recevoir un email **HTML** magnifique
- ✅ Avec un design moderne (gradient violet, barres de progression)
- ✅ Tableaux des transactions bien formatés
- ✅ Conseils budget personnalisés

---

## Rollback (Si Besoin)

Si quelque chose ne fonctionne pas, vous pouvez revenir à l'ancienne version :

```bash
# Sur le VPS
ssh linxo@votre-vps.com
cd /home/linxo

# Restaurer le backup
rm -rf LINXO
cp -r LINXO_BACKUP_YYYYMMDD_HHMMSS LINXO

# Ou via Git
cd LINXO
git log  # Trouver le commit précédent
git checkout <commit-hash-ancien>
```

---

## Vérifications Post-Déploiement

### ✅ Checklist

- [ ] Backup de l'ancien système créé
- [ ] Fichiers synchronisés sur le VPS
- [ ] Dépendances Python vérifiées
- [ ] Test manuel réussi
- [ ] Email HTML reçu et vérifié
- [ ] SMS reçu et vérifié
- [ ] Rapport sauvegardé dans `/home/linxo/LINXO/reports/`

---

## Notes Importantes

### Différences Fonctionnelles

**L'ancien système (RELIABLE)** :
- Email en texte brut (difficile à lire)
- Calcul de similarité avec SequenceMatcher (peut créer des faux positifs)
- Pas de détection des préautorisations carburant

**Le nouveau système (Moderne)** :
- Email HTML épuré et lisible
- Détection améliorée des préautorisations (150€, 120€)
- Meilleure gestion des virements ponctuels (remboursement, avance)
- Système d'identifiant pour différencier les dépenses

### Fichiers Clés

- `linxo_agent/run_analysis.py` - Point d'entrée (MODIFIÉ)
- `linxo_agent/analyzer.py` - Analyse moderne
- `linxo_agent/notifications.py` - Emails HTML + SMS
- `linxo_agent/report_formatter_v2.py` - Formatage HTML
- `linxo_agent/config.py` - Configuration unifiée
- `run_daily_report.sh` - Script cron (INCHANGÉ)

---

## Support

En cas de problème :
1. Vérifier les logs : `cat /home/linxo/LINXO/logs/daily_report_$(date +%Y%m%d).log`
2. Tester manuellement : `python linxo_agent/run_analysis.py`
3. Revenir au backup si nécessaire

---

**Date de création** : 28/10/2025
**Auteur** : Philippe PEREZ avec Claude Code
