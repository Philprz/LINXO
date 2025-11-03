# Diagnostic : Cron ne s'exécute pas à 10h

## 🔍 Problème identifié

Le programme ne s'est pas exécuté aujourd'hui à 10h00 sur le VPS.

### Cause probable

Il existe une **incohérence** entre :
- **Documentation** ([INSTALLATION_CRON.md](INSTALLATION_CRON.md:55)) : Cron configuré pour `0 10 * * *` (10h00)
- **Script d'installation** ([install_vps.sh](deploy/install_vps.sh:153)) : Cron configuré pour `0 20 * * *` (20h00)

## 📋 Vérification

### 1. Vérifier la configuration actuelle du cron sur le VPS

```bash
# Se connecter au VPS
ssh ubuntu@152.228.218.1

# Voir le cron actuel
crontab -l
```

Vous devriez voir quelque chose comme :
```
0 20 * * * cd /home/ubuntu/LINXO && /home/ubuntu/LINXO/venv/bin/python3 run_linxo_e2e.py >> logs/cron.log 2>&1
```

### 2. Vérifier les logs récents

```bash
# Sur le VPS
ls -lt ~/LINXO/logs/ | head -10

# Voir le dernier log
tail -100 ~/LINXO/logs/cron.log
```

### 3. Vérifier les logs système du cron

```bash
# Sur le VPS
grep CRON /var/log/syslog | tail -20
```

## 🔧 Solution

### Option A : Modifier le cron pour 10h (recommandé)

```bash
# Se connecter au VPS
ssh ubuntu@152.228.218.1

# Éditer le crontab
crontab -e

# Modifier la ligne de :
# 0 20 * * * cd /home/ubuntu/LINXO && ...
# à :
# 0 10 * * * cd /home/ubuntu/LINXO && ...

# Sauvegarder et quitter
```

### Option B : Utiliser un script pour changer l'heure

Créez ce script sur votre machine locale :

```bash
#!/bin/bash
# Script pour changer l'heure d'exécution du cron sur le VPS

VPS_HOST="ubuntu@152.228.218.1"
NEW_HOUR="10"  # Changer cette valeur pour l'heure souhaitée

echo "Changement de l'heure du cron sur le VPS..."
echo "Nouvelle heure : ${NEW_HOUR}h00"

# Se connecter au VPS et modifier le cron
ssh $VPS_HOST << 'EOF'
# Sauvegarder le cron actuel
crontab -l > /tmp/current_cron

# Remplacer l'heure dans le cron
sed -i 's/^0 [0-9]\+ \* \* \*/0 10 * * */g' /tmp/current_cron

# Réinstaller le cron modifié
crontab /tmp/current_cron

# Afficher le nouveau cron
echo "Nouveau crontab :"
crontab -l

# Nettoyer
rm /tmp/current_cron
EOF

echo "Cron modifié avec succès!"
```

Exécutez :
```bash
chmod +x change_cron_hour.sh
./change_cron_hour.sh
```

### Option C : Réinstaller avec la bonne heure

Modifier d'abord le script d'installation :

```bash
# Éditer le fichier
nano deploy/install_vps.sh

# Trouver la ligne 153 :
CRON_CMD="0 20 * * * cd $APP_DIR && $APP_DIR/venv/bin/python3 run_linxo_e2e.py >> logs/cron.log 2>&1"

# Modifier en :
CRON_CMD="0 10 * * * cd $APP_DIR && $APP_DIR/venv/bin/python3 run_linxo_e2e.py >> logs/cron.log 2>&1"

# Sauvegarder
```

Puis réinstaller le cron :
```bash
ssh ubuntu@152.228.218.1
cd ~/LINXO
# Supprimer l'ancien cron
crontab -l | grep -v "run_linxo_e2e.py" | crontab -
# Réinstaller avec le script
./deploy/install_vps.sh
```

## 🧪 Test manuel

Pour tester que le script fonctionne sans attendre 10h :

```bash
# Se connecter au VPS
ssh ubuntu@152.228.218.1

# Lancer manuellement
cd ~/LINXO
./venv/bin/python3 run_linxo_e2e.py

# Vérifier les logs
tail -100 logs/cron.log
```

## 📊 Vérification après modification

### 1. Confirmer le nouveau cron

```bash
ssh ubuntu@152.228.218.1 "crontab -l"
```

Vous devriez voir :
```
0 10 * * * cd /home/ubuntu/LINXO && /home/ubuntu/LINXO/venv/bin/python3 run_linxo_e2e.py >> logs/cron.log 2>&1
```

### 2. Vérifier demain à 10h05

Le lendemain à 10h05, vérifiez qu'un nouveau log a été créé :

```bash
ssh ubuntu@152.228.218.1 "ls -lt ~/LINXO/logs/ | head -3"
ssh ubuntu@152.228.218.1 "tail -50 ~/LINXO/logs/cron.log"
```

### 3. Configurer une alerte

Si vous voulez être notifié en cas de problème, vous pouvez ajouter une notification par email dans le cron :

```bash
MAILTO=votre_email@example.com
0 10 * * * cd /home/ubuntu/LINXO && /home/ubuntu/LINXO/venv/bin/python3 run_linxo_e2e.py >> logs/cron.log 2>&1
```

## 🛠️ Correction du script d'installation

Pour éviter ce problème à l'avenir, modifiez le script d'installation :

```bash
# Fichier : deploy/install_vps.sh
# Ligne 153

# AVANT (mauvais) :
CRON_CMD="0 20 * * * cd $APP_DIR && $APP_DIR/venv/bin/python3 run_linxo_e2e.py >> logs/cron.log 2>&1"

# APRÈS (correct) :
CRON_CMD="0 10 * * * cd $APP_DIR && $APP_DIR/venv/bin/python3 run_linxo_e2e.py >> logs/cron.log 2>&1"
```

## 📝 Causes possibles si le cron ne fonctionne toujours pas

### 1. Le service cron n'est pas démarré

```bash
ssh ubuntu@152.228.218.1 "sudo systemctl status cron"

# Si arrêté, démarrer :
ssh ubuntu@152.228.218.1 "sudo systemctl start cron"
ssh ubuntu@152.228.218.1 "sudo systemctl enable cron"
```

### 2. Problème de chemin ou de permissions

```bash
# Vérifier que le script existe
ssh ubuntu@152.228.218.1 "ls -la ~/LINXO/run_linxo_e2e.py"

# Vérifier que le virtualenv est actif
ssh ubuntu@152.228.218.1 "~/LINXO/venv/bin/python3 --version"

# Tester le script manuellement
ssh ubuntu@152.228.218.1 "cd ~/LINXO && ./venv/bin/python3 run_linxo_e2e.py"
```

### 3. Le fichier CSV n'est pas téléchargé

Le script ne peut s'exécuter que si un fichier CSV est disponible. Vérifiez :

```bash
ssh ubuntu@152.228.218.1 "ls -lt ~/LINXO/data/*.csv | head -5"
ssh ubuntu@152.228.218.1 "ls -lt ~/LINXO/downloads/*.csv | head -5"
```

### 4. Variables d'environnement manquantes

Le cron n'a pas accès aux variables d'environnement du shell. Assurez-vous que le fichier `.env` est bien lu :

```bash
# Vérifier que .env existe
ssh ubuntu@152.228.218.1 "cat ~/LINXO/.env | grep -v PASSWORD | grep -v KEY"

# Le script devrait charger .env automatiquement via python-dotenv
```

## ✅ Checklist de diagnostic

- [ ] Cron configuré pour la bonne heure (10h au lieu de 20h)
- [ ] Service cron actif (`systemctl status cron`)
- [ ] Script `run_linxo_e2e.py` existe et est exécutable
- [ ] Environnement virtuel Python fonctionnel
- [ ] Fichier `.env` présent avec les bonnes variables
- [ ] Fichiers CSV disponibles pour traitement
- [ ] Logs accessibles dans `~/LINXO/logs/`
- [ ] Pas d'erreurs dans `/var/log/syslog` pour le cron

## 📞 Support

Si le problème persiste après ces vérifications :

1. Collectez les informations :
   ```bash
   ssh ubuntu@152.228.218.1 "crontab -l" > cron_current.txt
   ssh ubuntu@152.228.218.1 "tail -200 ~/LINXO/logs/cron.log" > last_execution.log
   ssh ubuntu@152.228.218.1 "grep CRON /var/log/syslog | tail -50" > syslog_cron.txt
   ```

2. Vérifiez ces fichiers pour identifier le problème exact

3. Consultez la documentation :
   - [INSTALLATION_CRON.md](INSTALLATION_CRON.md)
   - [README.md](README.md)
