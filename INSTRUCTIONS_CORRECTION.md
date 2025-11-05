# Instructions de correction du VPS

**Date**: 2025-11-05
**Problème**: Les notifications (email + SMS) ne sont pas envoyées malgré l'exécution du cron

---

## ✅ Ce qui fonctionne déjà

Le diagnostic a confirmé que :
- ✅ Le cron s'exécute bien à 10h00
- ✅ Le service cron est actif
- ✅ L'analyse des dépenses fonctionne (428.02€ détectés aujourd'hui)
- ✅ Les rapports HTML sont générés localement

---

## ❌ Problèmes identifiés

1. **rsync manquant** → Impossible d'uploader les rapports HTML vers le serveur web
2. **Notifications échouent** → Email et SMS non envoyés (probablement config .env)
3. **Permissions** → Peut-être un problème d'accès aux répertoires web

---

## 🔧 Correction

### Méthode 1 : Script automatique (RECOMMANDÉ)

Depuis votre VPS (vous y êtes déjà connecté) :

```bash
# Vous êtes déjà sur le VPS dans ~/LINXO
# Téléchargez le script de correction depuis votre PC

# Sur votre PC (ouvrez un autre terminal):
scp fix_vps_issues.sh linxo@152.228.218.1:~/LINXO/

# Retour sur le VPS:
chmod +x fix_vps_issues.sh
./fix_vps_issues.sh
```

Ce script va :
1. Installer rsync
2. Vérifier/recréer l'environnement virtuel Python
3. Installer les dépendances
4. Vérifier le fichier .env
5. Corriger les permissions des répertoires
6. Préparer le système pour le prochain envoi

### Méthode 2 : Correction manuelle

Si vous préférez faire les corrections manuellement sur le VPS :

#### 1. Installer rsync
```bash
sudo apt-get update
sudo apt-get install -y rsync
```

#### 2. Vérifier l'environnement Python
```bash
cd ~/LINXO

# Vérifier que .venv fonctionne
.venv/bin/python3 --version

# Si erreur, recréer:
rm -rf .venv
python3 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt
```

#### 3. Vérifier le fichier .env
```bash
# Vérifier qu'il existe
cat .env | grep -E "^(SMTP_|OVH_SMS_)" | grep -v "PASSWORD\|SECRET\|KEY"

# Si des variables manquent, éditez:
nano .env
```

Variables essentielles pour les notifications :
- `SMTP_SERVER`
- `SMTP_PORT`
- `SMTP_USER`
- `SMTP_PASSWORD`
- `OVH_SMS_ENDPOINT`
- `OVH_SMS_APPLICATION_KEY`
- `OVH_SMS_APPLICATION_SECRET`
- `OVH_SMS_CONSUMER_KEY`
- `OVH_SMS_SERVICE_NAME`
- `PHONE_NUMBER`

#### 4. Corriger les permissions des répertoires web
```bash
sudo mkdir -p /var/www/html/reports /var/www/html/static
sudo chown -R linxo:linxo /var/www/html/reports /var/www/html/static
sudo chmod -R 755 /var/www/html/reports /var/www/html/static
```

#### 5. Tester le script
```bash
cd ~/LINXO
./run_daily_report.sh
```

---

## 🧪 Test de la correction

Après avoir appliqué les corrections, testez :

```bash
cd ~/LINXO
./run_daily_report.sh
```

Vérifiez dans les logs que :
1. ✅ L'analyse s'exécute
2. ✅ Les rapports HTML sont générés
3. ✅ Les rapports sont uploadés vers /var/www/html/reports (pas d'erreur rsync)
4. ✅ Un email est envoyé
5. ✅ Un SMS est envoyé

---

## 📧 Si les notifications échouent toujours

### Problème possible : Configuration SMTP

Vérifiez les credentials email dans `.env` :

```bash
# Tester la connexion SMTP (sans envoyer d'email)
.venv/bin/python3 -c "
import os
from dotenv import load_dotenv
import smtplib

load_dotenv()

server = os.getenv('SMTP_SERVER')
port = int(os.getenv('SMTP_PORT', 587))
user = os.getenv('SMTP_USER')
password = os.getenv('SMTP_PASSWORD')

print(f'Connexion à {server}:{port}...')
try:
    smtp = smtplib.SMTP(server, port)
    smtp.starttls()
    smtp.login(user, password)
    print('✅ Connexion SMTP réussie!')
    smtp.quit()
except Exception as e:
    print(f'❌ Erreur SMTP: {e}')
"
```

### Problème possible : Configuration OVH SMS

Vérifiez les credentials OVH dans `.env` :

```bash
# Vérifier que les variables sont bien définies
.venv/bin/python3 -c "
import os
from dotenv import load_dotenv

load_dotenv()

keys = ['OVH_SMS_ENDPOINT', 'OVH_SMS_APPLICATION_KEY',
        'OVH_SMS_APPLICATION_SECRET', 'OVH_SMS_CONSUMER_KEY',
        'OVH_SMS_SERVICE_NAME', 'PHONE_NUMBER']

missing = [k for k in keys if not os.getenv(k)]

if missing:
    print('❌ Variables manquantes:')
    for k in missing:
        print(f'  - {k}')
else:
    print('✅ Toutes les variables SMS sont définies')
"
```

---

## 📝 Logs à surveiller

### Logs de l'application
```bash
# Log d'aujourd'hui
tail -100 ~/LINXO/logs/daily_report_$(date +%Y%m%d).log

# Logs du cron
tail -100 ~/LINXO/logs/cron.log
```

### Vérifier que les rapports HTML sont accessibles

Après un test réussi :
```bash
ls -la /var/www/html/reports/$(date +%Y-%m-%d)/
```

Vous devriez voir :
- `index.html`
- `family-*.html` (un fichier par famille de dépenses)

---

## 🔄 Prochaine exécution automatique

Le cron est déjà bien configuré pour 10h. Demain à 10h00, le système :
1. Téléchargera automatiquement le dernier CSV depuis Linxo
2. Analysera les dépenses
3. Générera les rapports HTML
4. Enverra l'email avec les liens vers les rapports
5. Enverra le SMS avec le résumé

Pour vérifier demain à 10h05 :
```bash
tail -100 ~/LINXO/logs/daily_report_$(date +%Y%m%d).log
```

---

## 📞 Aide supplémentaire

Si après ces corrections le problème persiste :

1. **Collectez les informations** :
   ```bash
   # Dernier log complet
   cat ~/LINXO/logs/daily_report_$(date +%Y%m%d).log > ~/debug_report.txt

   # Variables d'environnement (sans les mots de passe)
   cat .env | grep -v "PASSWORD\|SECRET\|KEY" >> ~/debug_report.txt
   ```

2. **Vérifiez les erreurs spécifiques** dans les logs

3. **Testez manuellement l'envoi d'email** avec le module notifications

---

**Dernière mise à jour** : 2025-11-05
