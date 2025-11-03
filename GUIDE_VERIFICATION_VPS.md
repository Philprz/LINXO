# Guide de Vérification du VPS

## 🚀 Méthode rapide (scripts automatiques)

### Sous Windows (PowerShell)
```powershell
.\check_vps_status.ps1
```

### Sous Linux/Mac (Bash)
```bash
chmod +x check_vps_status.sh
./check_vps_status.sh
```

## 🔍 Vérification manuelle étape par étape

### 1. Vérifier le cron configuré

```bash
ssh ubuntu@152.228.218.1 "crontab -l"
```

**Résultat attendu :**
```
0 10 * * * cd /home/ubuntu/LINXO && /home/ubuntu/LINXO/venv/bin/python3 run_linxo_e2e.py >> logs/cron.log 2>&1
```

✅ **Bon** : `0 10` = exécution à 10h00
❌ **Mauvais** : `0 20` = exécution à 20h00

**Si mauvais, corriger avec :**
```bash
# Option 1 : Script automatique
./fix_cron_hour.sh

# Option 2 : Manuel
ssh ubuntu@152.228.218.1
crontab -e
# Changer "0 20" en "0 10"
```

### 2. Vérifier que le service cron est actif

```bash
ssh ubuntu@152.228.218.1 "systemctl status cron"
```

**Résultat attendu :**
```
● cron.service - Regular background program processing daemon
   Active: active (running)
```

**Si inactif :**
```bash
ssh ubuntu@152.228.218.1 "sudo systemctl start cron && sudo systemctl enable cron"
```

### 3. Vérifier les fichiers nécessaires

```bash
# Vérifier que les dossiers existent
ssh ubuntu@152.228.218.1 "ls -la ~/LINXO/"

# Vérifier le virtualenv Python
ssh ubuntu@152.228.218.1 "~/LINXO/venv/bin/python3 --version"

# Vérifier le fichier .env
ssh ubuntu@152.228.218.1 "test -f ~/LINXO/.env && echo 'OK' || echo 'MANQUANT'"
```

### 4. Vérifier les logs récents

```bash
# Voir les logs cron (dernières exécutions)
ssh ubuntu@152.228.218.1 "ls -lt ~/LINXO/logs/ | head -10"

# Lire le dernier log
ssh ubuntu@152.228.218.1 "tail -100 ~/LINXO/logs/cron.log"

# Vérifier les logs système
ssh ubuntu@152.228.218.1 "grep CRON /var/log/syslog | grep linxo -i | tail -20"
```

### 5. Vérifier les fichiers CSV disponibles

```bash
# CSV dans data/
ssh ubuntu@152.228.218.1 "ls -lt ~/LINXO/data/*.csv | head -5"

# CSV dans downloads/
ssh ubuntu@152.228.218.1 "ls -lt ~/LINXO/downloads/*.csv | head -5"
```

**Note :** Il doit y avoir au moins un fichier CSV pour que le script puisse s'exécuter.

### 6. Vérifier les rapports HTML générés

```bash
# Vérifier les rapports locaux
ssh ubuntu@152.228.218.1 "ls -lt ~/LINXO/data/reports/ | head -10"

# Vérifier les rapports sur le serveur web
ssh ubuntu@152.228.218.1 "ls -lt /var/www/html/reports/ | head -10"
```

### 7. Vérifier Nginx (serveur web)

```bash
# Status du service
ssh ubuntu@152.228.218.1 "systemctl status nginx"

# Tester l'accès web
curl -I https://linxo.appliprz.ovh/reports/
```

**Résultat attendu :**
```
HTTP/2 401
www-authenticate: Basic realm="Reports Access"
```

Le code 401 est normal (demande d'authentification).

### 8. Test manuel d'exécution

Pour tester que tout fonctionne sans attendre le cron :

```bash
# Se connecter au VPS
ssh ubuntu@152.228.218.1

# Lancer le script manuellement
cd ~/LINXO
./venv/bin/python3 run_linxo_e2e.py
```

Vérifiez qu'il n'y a pas d'erreurs.

## 📊 Checklist de vérification complète

- [ ] ✅ Cron configuré pour 10h (`0 10 * * *`)
- [ ] ✅ Service cron actif
- [ ] ✅ Dossier `~/LINXO` existe
- [ ] ✅ Virtualenv Python fonctionnel
- [ ] ✅ Fichier `.env` présent
- [ ] ✅ Au moins un fichier CSV disponible
- [ ] ✅ Logs créés récemment
- [ ] ✅ Rapports HTML générés
- [ ] ✅ Service Nginx actif
- [ ] ✅ Accès web aux rapports (avec auth)
- [ ] ✅ Test manuel réussi

## 🔧 Problèmes courants

### Problème : "Permission denied" pour SSH

**Solution :**
```bash
# Vérifier la configuration SSH
ssh -v ubuntu@152.228.218.1

# Si nécessaire, reconfigurer la clé
ssh-copy-id ubuntu@152.228.218.1
```

### Problème : Cron ne s'exécute pas

**Diagnostic :**
```bash
# Voir les logs système
ssh ubuntu@152.228.218.1 "grep CRON /var/log/syslog | tail -50"

# Vérifier que cron est actif
ssh ubuntu@152.228.218.1 "systemctl status cron"

# Tester le script manuellement
ssh ubuntu@152.228.218.1 "cd ~/LINXO && ./venv/bin/python3 run_linxo_e2e.py"
```

**Solutions :**
1. Redémarrer cron : `sudo systemctl restart cron`
2. Vérifier la syntaxe du crontab : `crontab -l`
3. Vérifier les permissions : `ls -la ~/LINXO/run_linxo_e2e.py`

### Problème : Pas de fichier CSV

Le script ne peut pas s'exécuter sans fichier CSV.

**Solutions :**
1. Télécharger manuellement depuis Linxo
2. Vérifier le script de téléchargement automatique
3. Copier un CSV depuis votre machine locale :
   ```bash
   scp data/Linxo_*.csv ubuntu@152.228.218.1:~/LINXO/data/
   ```

### Problème : Rapports non accessibles

**Vérifications :**
```bash
# Nginx actif ?
ssh ubuntu@152.228.218.1 "systemctl status nginx"

# Fichiers présents ?
ssh ubuntu@152.228.218.1 "ls -la /var/www/html/reports/"

# Permissions correctes ?
ssh ubuntu@152.228.218.1 "ls -la /var/www/html/"
```

**Solutions :**
```bash
# Corriger les permissions
ssh ubuntu@152.228.218.1 "sudo chown -R ubuntu:www-data /var/www/html/reports && sudo chmod -R 755 /var/www/html/reports"

# Redémarrer Nginx
ssh ubuntu@152.228.218.1 "sudo systemctl restart nginx"

# Uploader manuellement les rapports
rsync -avz data/reports/ ubuntu@152.228.218.1:/var/www/html/reports/
```

## 📅 Vérification après la prochaine exécution

Demain, après 10h05, vérifiez :

```bash
# 1. Nouveau log créé ?
ssh ubuntu@152.228.218.1 "ls -lt ~/LINXO/logs/ | head -3"

# 2. Contenu du log
ssh ubuntu@152.228.218.1 "tail -100 ~/LINXO/logs/cron.log"

# 3. Nouveaux rapports générés ?
ssh ubuntu@152.228.218.1 "ls -lt /var/www/html/reports/ | head -5"

# 4. Notifications envoyées ?
# Vérifier vos emails et SMS
```

## 🆘 En cas de problème persistant

1. **Collectez les informations :**
   ```bash
   # Exécuter le script de diagnostic
   ./check_vps_status.ps1 > diagnostic_$(date +%Y%m%d).txt

   # Ou manuellement
   ssh ubuntu@152.228.218.1 "crontab -l" > cron.txt
   ssh ubuntu@152.228.218.1 "tail -200 ~/LINXO/logs/cron.log" > logs.txt
   ssh ubuntu@152.228.218.1 "systemctl status cron" > cron_status.txt
   ```

2. **Consultez la documentation :**
   - [DIAGNOSTIC_CRON.md](DIAGNOSTIC_CRON.md)
   - [INSTALLATION_CRON.md](INSTALLATION_CRON.md)
   - [CONFIGURATION_UPLOAD_RAPPORTS.md](CONFIGURATION_UPLOAD_RAPPORTS.md)

3. **Testez manuellement** pour identifier le problème spécifique

## 📞 Scripts utiles

- `check_vps_status.ps1` / `check_vps_status.sh` : Vérification complète
- `fix_cron_hour.sh` : Corriger l'heure d'exécution
- `upload_reports.py` : Upload manuel des rapports

## ✅ Tout est OK si...

- ✅ Le cron est configuré pour 10h
- ✅ Le service cron est actif
- ✅ Les logs montrent des exécutions récentes
- ✅ Les rapports HTML sont accessibles via l'URL
- ✅ Vous recevez les notifications (email + SMS)

---

**Date de dernière vérification :** $(date)
