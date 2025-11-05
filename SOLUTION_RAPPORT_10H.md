# Solution : Rapport quotidien non envoyé à 10h

**Date**: 2025-11-05
**Problème**: Le programme sur le VPS n'a pas envoyé son rapport à 10h

---

## 🔍 Diagnostic

### Causes probables identifiées

1. **Heure du cron incorrecte**
   - La documentation indique 10h mais le script d'installation configure 20h
   - Référence: [DIAGNOSTIC_CRON.md:11](DIAGNOSTIC_CRON.md#L11)

2. **Fichier CSV déjà traité**
   - Le système vérifie si le CSV a déjà été envoyé aujourd'hui
   - Si oui, il sort sans erreur et sans envoyer de rapport
   - Code: [run_analysis.py:45-54](linxo_agent/run_analysis.py#L45-L54)

3. **Absence de fichier CSV**
   - Si aucun fichier CSV n'est disponible, le script échoue
   - Une alerte technique devrait être envoyée dans ce cas
   - Code: [run_analysis.py:56-93](linxo_agent/run_analysis.py#L56-L93)

4. **Service cron inactif**
   - Le service cron pourrait être arrêté sur le VPS

5. **Environnement virtuel Python défaillant**
   - L'environnement Python pourrait être corrompu

---

## 🛠️ Solution

### Méthode recommandée : Script automatique

J'ai créé deux scripts pour diagnostiquer et corriger le problème :

#### 1. Diagnostic
```bash
./diagnostic_rapport_10h.sh
```

Ce script vérifie :
- Configuration du cron
- Statut du service cron
- Logs d'exécution
- Fichiers CSV disponibles
- Fichier already_sent.txt
- Environnement Python

#### 2. Correction
```bash
./fix_rapport_10h.sh
```

Ce script :
- Modifie le cron pour 10h00
- Vérifie et démarre le service cron si nécessaire
- Propose de réinitialiser le fichier already_sent.txt
- Vérifie les fichiers CSV disponibles
- Propose un test manuel

---

## 📋 Vérifications manuelles

### 1. Vérifier le cron actuel
```bash
ssh linxo@152.228.218.1 "crontab -l"
```

**Attendu**: `0 10 * * * ...` (et non `0 20 * * *`)

### 2. Vérifier les logs
```bash
ssh linxo@152.228.218.1 "ls -lt ~/LINXO/logs/daily_report_*.log | head -5"
ssh linxo@152.228.218.1 "tail -100 ~/LINXO/logs/daily_report_$(date +%Y%m%d).log"
```

### 3. Vérifier le fichier already_sent
```bash
ssh linxo@152.228.218.1 "cat ~/LINXO/data/already_sent.txt"
```

Si ce fichier contient le nom du dernier CSV, le script ne le retraitera pas.

### 4. Vérifier les fichiers CSV
```bash
ssh linxo@152.228.218.1 "ls -lt ~/LINXO/data/*.csv | head -3"
ssh linxo@152.228.218.1 "ls -lt ~/LINXO/downloads/*.csv | head -3"
```

---

## 🔧 Correction manuelle

Si vous préférez corriger manuellement :

### Étape 1: Corriger l'heure du cron

```bash
# Se connecter au VPS
ssh linxo@152.228.218.1

# Éditer le crontab
crontab -e

# Modifier la ligne pour qu'elle commence par:
0 10 * * * /home/linxo/LINXO/run_daily_report.sh

# Sauvegarder et quitter (Ctrl+X, puis Y, puis Enter)
```

### Étape 2: Vérifier le service cron

```bash
systemctl status cron

# Si inactif:
sudo systemctl start cron
sudo systemctl enable cron
```

### Étape 3: Réinitialiser le fichier already_sent (si nécessaire)

```bash
rm ~/LINXO/data/already_sent.txt
```

### Étape 4: Tester manuellement

```bash
cd ~/LINXO
./run_daily_report.sh
```

---

## 🧪 Test de la solution

Après avoir appliqué la correction :

### Test immédiat (recommandé)
```bash
ssh linxo@152.228.218.1 "cd ~/LINXO && ./run_daily_report.sh"
```

Vérifiez que :
- ✅ L'analyse s'exécute sans erreur
- ✅ Un email HTML est envoyé
- ✅ Un SMS est envoyé
- ✅ Les rapports HTML sont générés

### Test du cron (demain à 10h05)
```bash
# Vérifier que le script s'est exécuté
ssh linxo@152.228.218.1 "ls -lt ~/LINXO/logs/daily_report_*.log | head -1"

# Voir le log d'exécution
ssh linxo@152.228.218.1 "tail -100 ~/LINXO/logs/daily_report_$(date +%Y%m%d).log"
```

---

## 📊 Comportement du système

### Cas normaux

1. **Nouveau CSV disponible**
   - ✅ Analyse exécutée
   - ✅ Email et SMS envoyés
   - ✅ Rapports HTML générés
   - ✅ CSV marqué comme envoyé dans `already_sent.txt`

2. **CSV déjà traité aujourd'hui**
   - ℹ️ Message: "Le dernier fichier CSV a déjà été envoyé aujourd'hui"
   - ℹ️ Sortie avec code 0 (succès)
   - ❌ Aucun email/SMS envoyé (normal)

3. **Aucun CSV disponible**
   - ❌ Erreur: "Aucun fichier CSV disponible"
   - 📧 Alerte technique envoyée à phiperez@gmail.com
   - ❌ Sortie avec code 1 (erreur)

### Cas d'erreur avec alertes

Le système envoie des alertes techniques dans ces cas :
- Aucun fichier CSV disponible
- Échec d'analyse du CSV
- Erreur inattendue lors de l'analyse
- Échec d'envoi des notifications (email ET SMS)

---

## 📝 Fichiers créés

- **diagnostic_rapport_10h.sh** : Script de diagnostic complet
- **fix_rapport_10h.sh** : Script de correction automatique
- **SOLUTION_RAPPORT_10H.md** : Ce document (récapitulatif)

---

## 🔍 Logs à surveiller

### Logs de l'application
```bash
~/LINXO/logs/daily_report_YYYYMMDD.log
```

### Logs système du cron
```bash
grep CRON /var/log/syslog | grep linxo
```

### Logs Nginx (pour les rapports HTML)
```bash
/var/log/nginx/access.log
/var/log/nginx/error.log
```

---

## 📚 Documentation associée

- [VPS_CONFIG.md](VPS_CONFIG.md) - Configuration du VPS
- [DIAGNOSTIC_CRON.md](DIAGNOSTIC_CRON.md) - Diagnostic détaillé du cron
- [INSTALLATION_CRON.md](INSTALLATION_CRON.md) - Installation initiale
- [run_analysis.py](linxo_agent/run_analysis.py) - Code source du script
- [run_daily_report.sh](run_daily_report.sh) - Script d'exécution quotidienne

---

## ✅ Checklist de vérification

Avant de considérer le problème comme résolu :

- [ ] Cron configuré pour 10h (pas 20h)
- [ ] Service cron actif et démarré
- [ ] Fichier `.env` présent avec toutes les variables
- [ ] Environnement virtuel Python fonctionnel
- [ ] Au moins un fichier CSV disponible
- [ ] Test manuel réussi
- [ ] Email de test reçu
- [ ] SMS de test reçu
- [ ] Rapports HTML générés et accessibles

---

## 🆘 Si le problème persiste

1. **Exécutez le diagnostic complet**
   ```bash
   ./diagnostic_rapport_10h.sh > diagnostic_$(date +%Y%m%d).txt
   ```

2. **Consultez les logs**
   - Logs d'application : `~/LINXO/logs/`
   - Logs système : `/var/log/syslog`

3. **Vérifiez la connectivité**
   - Test SSH : `ssh linxo@152.228.218.1 "echo OK"`
   - Test SMTP : Vérifiez les credentials email dans `.env`
   - Test OVH SMS : Vérifiez les credentials SMS dans `.env`

4. **Vérifiez le téléchargement des CSV**
   - Le script de téléchargement automatique fonctionne-t-il ?
   - Y a-t-il des erreurs d'authentification Linxo ?

---

**Dernière mise à jour** : 2025-11-05 par Claude Code
