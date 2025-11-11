# Diagnostic : Cron ne s'exécute pas à 10h

## 🔍 Problème identifié

Le rapport quotidien n'a pas été généré aujourd'hui à 10h sur le VPS (`linxo@152.228.218.1`).

### Cause probable

La tâche cron est encore configurée avec l'ancien workflow `run_linxo_e2e.py` (et parfois à 20h) alors que la configuration officielle est :

```
0 10 * * * /home/linxo/LINXO/run_daily_report.sh
```

## 📋 Vérifications rapides

1. **Lister le cron actuel**
   ```bash
   ssh linxo@152.228.218.1 "crontab -l"
   ```
   - ✅ Attendu : une seule ligne `run_daily_report.sh`
   - ❌ À corriger : toute ligne contenant `run_linxo_e2e.py`, `cd /home/ubuntu`, ou une heure différente de `0 10`.

2. **Vérifier les logs générés**
   ```bash
   ssh linxo@152.228.218.1 "ls -lt ~/LINXO/logs/ | head -5"
   ssh linxo@152.228.218.1 "tail -100 ~/LINXO/logs/cron.log"
   ```

3. **Consulter les logs système cron**
   ```bash
   ssh linxo@152.228.218.1 "grep CRON /var/log/syslog | tail -20"
   ```

## 🔧 Solutions

### Option A – Modifier manuellement la ligne cron (recommandé)

```bash
ssh linxo@152.228.218.1
crontab -e
```
Remplacer toute ligne existante par :
```
0 10 * * * /home/linxo/LINXO/run_daily_report.sh
```
Sauvegarder puis quitter (`Ctrl+O`, `Enter`, `Ctrl+X` avec nano).

### Option B – Script local de correction

```bash
cat <<'EOS' > change_cron_hour.sh
#!/bin/bash
VPS_HOST="linxo@152.228.218.1"
NEW_HOUR="10"
ssh "$VPS_HOST" <<'EOF'
crontab -l > /tmp/current_cron
sed -i 's#^0 [0-9]\+ \* \* \*.*run_linxo_e2e.py.*#0 10 * * * /home/linxo/LINXO/run_daily_report.sh#' /tmp/current_cron
if ! grep -q 'run_daily_report.sh' /tmp/current_cron; then
    echo "0 10 * * * /home/linxo/LINXO/run_daily_report.sh" >> /tmp/current_cron
fi
crontab /tmp/current_cron
rm /tmp/current_cron
crontab -l
