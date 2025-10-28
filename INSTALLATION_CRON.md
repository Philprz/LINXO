# Installation de la tâche cron pour le rapport quotidien Linxo

## 📋 Prérequis
- Accès SSH à votre VPS
- Les fichiers du projet dans `/home/linxo/LINXO/`
- Python 3 installé avec environnement virtuel `.venv`

## 🚀 Étapes d'installation

### 1. Transférer les fichiers sur le VPS

Depuis votre machine locale, transférez le script :

```bash
scp run_daily_report.sh linxo@VOTRE_VPS_IP:/home/linxo/LINXO/
```

### 2. Connectez-vous au VPS

```bash
ssh linxo@VOTRE_VPS_IP
```

### 3. Rendre le script exécutable

```bash
cd ~/LINXO
chmod +x run_daily_report.sh
```

### 4. Tester le script manuellement

```bash
./run_daily_report.sh
```

Vérifiez que tout fonctionne correctement et qu'un rapport est envoyé.

### 5. Configurer la tâche cron

Ouvrez l'éditeur crontab :

```bash
crontab -e
```

Ajoutez cette ligne pour exécuter le rapport tous les jours à 10h00 :

```bash
0 10 * * * /home/linxo/LINXO/run_daily_report.sh
```

**Explication de la syntaxe cron :**
- `0` = minute (0)
- `10` = heure (10h du matin)
- `*` = tous les jours du mois
- `*` = tous les mois
- `*` = tous les jours de la semaine

Sauvegardez et quittez l'éditeur (CTRL+X puis Y puis ENTRÉE si nano).

### 6. Vérifier que la tâche cron est enregistrée

```bash
crontab -l
```

Vous devriez voir votre ligne de cron.

### 7. Vérifier les logs du système cron

```bash
grep CRON /var/log/syslog | tail -20
```

## 📁 Logs

Les logs de chaque exécution seront sauvegardés dans :
```
/home/linxo/LINXO/logs/daily_report_YYYYMMDD.log
```

Pour consulter le dernier log :
```bash
ls -lt ~/LINXO/logs/ | head -5
tail -100 ~/LINXO/logs/daily_report_$(date +%Y%m%d).log
```

## 🔧 Personnalisation

### Changer l'heure d'exécution

Pour exécuter à **8h30** au lieu de 10h :
```bash
30 8 * * * /home/linxo/LINXO/run_daily_report.sh
```

Pour exécuter **deux fois par jour** (10h et 18h) :
```bash
0 10,18 * * * /home/linxo/LINXO/run_daily_report.sh
```

Pour exécuter **du lundi au vendredi uniquement** à 10h :
```bash
0 10 * * 1-5 /home/linxo/LINXO/run_daily_report.sh
```

## ⚠️ Résolution de problèmes

### Le cron ne s'exécute pas

1. Vérifiez que le service cron est actif :
```bash
sudo systemctl status cron
```

2. Vérifiez les logs cron :
```bash
grep CRON /var/log/syslog | tail -50
```

3. Vérifiez les permissions du script :
```bash
ls -l ~/LINXO/run_daily_report.sh
```

### Les emails ne sont pas envoyés

1. Vérifiez que les variables d'environnement sont accessibles au cron
2. Ajoutez les variables au début du crontab :
```bash
RESEND_API_KEY=votre_clé
EMAIL_FROM=votre@email.com
EMAIL_TO=destinataire@email.com
```

3. Ou créez un fichier `.env` et chargez-le dans le script

### Tester l'exécution avec une minute de délai

Pour tester rapidement, ajoutez temporairement une tâche qui s'exécute dans 2 minutes :
```bash
# Si il est 14h35, mettez :
37 14 * * * /home/linxo/LINXO/run_daily_report.sh
```

Attendez 2 minutes et vérifiez les logs.

## 📊 Monitoring

Pour surveiller les exécutions quotidiennes :

```bash
# Voir les 10 derniers logs
ls -lt ~/LINXO/logs/ | head -11

# Compter les succès/échecs
grep "✅" ~/LINXO/logs/*.log | wc -l
grep "❌" ~/LINXO/logs/*.log | wc -l
```

## 🔄 Désactivation temporaire

Pour désactiver temporairement le cron sans le supprimer, commentez la ligne :
```bash
crontab -e
# Ajoutez un # devant la ligne :
# 0 10 * * * /home/linxo/LINXO/run_daily_report.sh
```

## 🗑️ Suppression complète

Pour supprimer complètement la tâche cron :
```bash
crontab -e
# Supprimez la ligne, sauvegardez et quittez
```
