# Configuration VPS - Informations importantes

## 🖥️ Serveur VPS

- **IP** : `152.228.218.1`
- **OS** : Debian
- **Utilisateur** : `linxo`
- **Domaine** : `linxo.appliprz.ovh`

## 📁 Chemins importants

### Répertoires application
- **Application** : `/home/linxo/LINXO/`
- **Virtualenv Python** : `/home/linxo/LINXO/venv/`
- **Logs** : `/home/linxo/LINXO/logs/`
- **Data CSV** : `/home/linxo/LINXO/data/`
- **Downloads CSV** : `/home/linxo/LINXO/downloads/`

### Répertoires web (Nginx)
- **Rapports HTML** : `/var/www/html/reports/`
- **Fichiers statiques** : `/var/www/html/static/`
- **Configuration Nginx** : `/etc/nginx/sites-available/linxo`

## ⏰ Configuration Cron

- **Heure d'exécution** : 10h00 (heure locale du serveur)
- **Format cron** : `0 10 * * *`
- **Commande** : `cd /home/linxo/LINXO && /home/linxo/LINXO/venv/bin/python3 run_linxo_e2e.py >> logs/cron.log 2>&1`

## 🔐 Connexion SSH

### Configuration recommandée

Dans votre `~/.ssh/config` (Windows : `C:\Users\VotreNom\.ssh\config`) :

```
Host linxo-vps
    HostName 152.228.218.1
    User linxo
    IdentityFile ~/.ssh/id_ed25519  # ou votre clé SSH
    ServerAliveInterval 60
```

Puis vous pouvez vous connecter simplement avec :
```bash
ssh linxo-vps
```

## 🔧 Commandes utiles

### Se connecter au VPS
```bash
ssh linxo@152.228.218.1
```

### Vérifier le cron
```bash
ssh linxo@152.228.218.1 "crontab -l"
```

### Voir les logs récents
```bash
ssh linxo@152.228.218.1 "tail -100 ~/LINXO/logs/cron.log"
```

### Tester l'exécution manuelle
```bash
ssh linxo@152.228.218.1 "cd ~/LINXO && ./venv/bin/python3 run_linxo_e2e.py"
```

### Uploader les rapports
```bash
rsync -avz data/reports/ linxo@152.228.218.1:/var/www/html/reports/
```

## 🌐 URLs

- **Index rapports** : `https://linxo.appliprz.ovh/reports/{date}/index.html`
- **Rapport famille** : `https://linxo.appliprz.ovh/reports/{date}/family-{slug}.html`

**Authentification** :
- Utilisateur : (défini dans `.env` - `REPORTS_BASIC_USER`)
- Mot de passe : (défini dans `.env` - `REPORTS_BASIC_PASS`)

## 📋 Variables d'environnement

À définir dans `/home/linxo/LINXO/.env` :

```bash
# VPS Configuration
VPS_HOST=152.228.218.1
VPS_USER=linxo
VPS_REPORTS_PATH=/var/www/html/reports
VPS_STATIC_PATH=/var/www/html/static

# Reports Configuration
REPORTS_BASE_URL=https://linxo.appliprz.ovh/reports
REPORTS_SIGNING_KEY=votre_cle_secrete
REPORTS_BASIC_USER=linxo
REPORTS_BASIC_PASS=votre_mot_de_passe
```

## ⚙️ Services système

### Cron
```bash
ssh linxo@152.228.218.1 "systemctl status cron"
```

### Nginx
```bash
ssh linxo@152.228.218.1 "sudo systemctl status nginx"
```

## 🛠️ Différences vs documentation

**⚠️ ATTENTION** : Certains scripts et documentation utilisent `ubuntu` comme utilisateur et Ubuntu comme OS. Les bonnes valeurs sont :

| ❌ Ancien (incorrect) | ✅ Nouveau (correct) |
|---------------------|---------------------|
| `ubuntu@152.228.218.1` | `linxo@152.228.218.1` |
| `/home/ubuntu/LINXO` | `/home/linxo/LINXO` |
| Ubuntu | Debian |

## 📝 Scripts mis à jour

Les scripts suivants ont été corrigés avec les bonnes valeurs :

- ✅ `check_vps_status.sh`
- ✅ `check_vps_status.ps1`
- ✅ `fix_cron_hour.sh`
- ✅ `.env.example` (variables VPS_*)

## 🔍 Vérifications à faire

Utilisez ces scripts pour vérifier votre VPS :

```bash
# PowerShell (Windows)
.\check_vps_status.ps1

# Bash (Linux/Mac/Git Bash)
./check_vps_status.sh
```

---

**Dernière mise à jour** : 2025-11-03
