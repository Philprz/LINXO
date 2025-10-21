# Quick Start - Linxo Agent V2.0

> Mise en route rapide en 5 minutes

---

## ⚡ Installation Express (Local)

### 1. Installer les dépendances

```bash
pip install -r requirements.txt
```

### 2. Configurer le .env

Le fichier `.env` est déjà rempli avec vos informations. Vérifiez juste qu'il est correct :

```bash
cat .env
```

### 3. Générer api_secrets.json

```bash
cd linxo_agent
python generate_api_secrets.py
cd ..
```

### 4. Vérifier la configuration

```bash
python linxo_agent.py --config-check
```

Vous devriez voir :
```
================================================================================
CONFIGURATION LINXO AGENT
================================================================================
Environnement:          LOCAL
OS:                     Windows (ou Linux/macOS)
...
Email SMTP:             phiperez@gmail.com
Destinataires email:    2
Destinataires SMS:      2
Linxo email:            philippe@melprz.fr
================================================================================
```

### 5. Premier test (sans notifications)

```bash
python linxo_agent.py --skip-notifications
```

Ce test va :
- ✅ Ouvrir Chrome
- ✅ Se connecter à Linxo
- ✅ Télécharger le CSV
- ✅ Analyser vos dépenses
- ✅ Afficher le rapport
- ❌ NE PAS envoyer d'email/SMS (mode test)

**Durée** : ~2-3 minutes

---

## 🎯 Utilisation Courante

### Workflow complet (production)

```bash
python linxo_agent.py
```

Cette commande exécute tout le processus et envoie les notifications.

### Analyser un CSV existant

Si vous avez déjà un export CSV de Linxo :

```bash
python linxo_agent.py --csv-file chemin/vers/export.csv
```

### Analyser le dernier CSV sans re-télécharger

```bash
python linxo_agent.py --skip-download
```

---

## 🧪 Tests Rapides

### Tester les notifications (email + SMS)

```bash
cd linxo_agent
python notifications.py
```

Vous serez invité à :
1. Envoyer un email de test (o/n)
2. Envoyer un SMS de test (o/n)

### Tester la connexion Linxo

```bash
cd linxo_agent
python linxo_connexion.py
```

Le navigateur s'ouvrira et se connectera à Linxo. Vous pourrez tester le téléchargement CSV.

### Tester l'analyse

```bash
cd linxo_agent
python analyzer.py
```

Analysera le dernier CSV disponible dans `data/`.

---

## 🚨 Problèmes Courants

### "No module named 'dotenv'"

```bash
pip install python-dotenv
```

### "Credentials Linxo manquants"

Vérifier que `.env` contient :
```bash
LINXO_EMAIL=philippe@melprz.fr
LINXO_PASSWORD=Elinxo31021225!
```

Puis régénérer api_secrets.json :
```bash
cd linxo_agent
python generate_api_secrets.py
```

### "Impossible d'initialiser le navigateur"

Installer ChromeDriver :

**Windows** :
- Télécharger depuis https://chromedriver.chromium.org/
- Mettre dans PATH ou dans le projet

**Linux** :
```bash
sudo apt install chromium-chromedriver
```

**macOS** :
```bash
brew install chromedriver
```

### Email non reçu

Vous utilisez probablement le **mot de passe Gmail principal** au lieu d'un **App Password**.

**Solution** :
1. Aller sur https://myaccount.google.com/apppasswords
2. Créer un nouvel App Password
3. Copier le mot de passe (16 caractères sans espaces)
4. Mettre à jour dans `.env` :
   ```
   SENDER_PASSWORD=xxxxyyyyxxxxyyyy
   ```
5. Régénérer api_secrets.json :
   ```bash
   cd linxo_agent
   python generate_api_secrets.py
   ```

---

## 📦 Déploiement VPS (Production)

### 1. Copier le projet sur le VPS

```bash
scp -r LINXO ubuntu@152.228.218.1:~/
```

### 2. Se connecter au VPS

```bash
ssh ubuntu@152.228.218.1
```

### 3. Installer les dépendances

```bash
cd ~/LINXO
sudo apt update
sudo apt install python3 python3-pip google-chrome-stable chromium-chromedriver
pip3 install -r requirements.txt
```

### 4. Vérifier la configuration

Le `.env` est déjà configuré, vérifiez juste :

```bash
cat .env
```

### 5. Générer api_secrets.json

```bash
cd linxo_agent
python3 generate_api_secrets.py
cd ..
```

Le fichier sera créé dans `/home/ubuntu/.api_secret_infos/api_secrets.json` automatiquement.

### 6. Test sans notifications

```bash
python3 linxo_agent.py --skip-notifications
```

### 7. Test complet

```bash
python3 linxo_agent.py
```

### 8. Automatiser avec cron

```bash
crontab -e
```

Ajouter :
```
# Linxo Agent - Tous les jours à 20h00
0 20 * * * cd /home/ubuntu/LINXO && /usr/bin/python3 linxo_agent.py >> /home/ubuntu/logs/linxo_cron.log 2>&1
```

Vérifier le cron :
```bash
crontab -l
```

---

## 📚 Documentation Complète

Pour plus de détails, consultez [README_V2.md](README_V2.md).

---

## ✅ Checklist de Vérification

Avant de considérer que tout fonctionne, vérifiez :

- [ ] `python linxo_agent.py --config-check` affiche la bonne configuration
- [ ] `python linxo_agent.py --skip-notifications` télécharge le CSV et analyse
- [ ] Test email : Vous recevez l'email de test
- [ ] Test SMS : Vous recevez le SMS de test
- [ ] Workflow complet : `python linxo_agent.py` fonctionne de bout en bout
- [ ] Les rapports sont sauvegardés dans `reports/`
- [ ] Les logs sont dans `logs/`

---

## 🎉 Vous êtes prêt !

Le système est maintenant opérationnel. Vous pouvez :

- ✅ L'utiliser localement pour tester
- ✅ Le déployer sur le VPS pour l'automatiser
- ✅ Recevoir vos rapports budgétaires quotidiens

---

**Questions ?** Consultez [README_V2.md](README_V2.md) section "Dépannage".
