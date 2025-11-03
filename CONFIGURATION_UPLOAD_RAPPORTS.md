# Configuration de l'Upload des Rapports HTML vers le VPS

## Problème résolu

Avant cette mise à jour, les rapports HTML étaient générés localement dans `data/reports/` mais **n'étaient jamais copiés sur le VPS**, ce qui rendait les URLs inaccessibles.

Maintenant, les rapports sont automatiquement synchronisés vers le VPS après leur génération.

## Prérequis

### 1. SSH configuré avec clé publique

Pour que l'upload automatique fonctionne, vous devez configurer l'authentification SSH par clé publique :

```bash
# Sur votre machine locale/Windows (Git Bash ou WSL)
ssh-keygen -t ed25519 -C "votre_email@example.com"

# Copier la clé publique vers le VPS
ssh-copy-id ubuntu@152.228.218.1

# Tester la connexion
ssh ubuntu@152.228.218.1 "echo 'Connexion OK'"
```

### 2. Rsync installé

**Sur Windows (Git Bash)** :
- Rsync est généralement inclus avec Git Bash
- Vérifiez : `which rsync`

**Sur le VPS (Ubuntu)** :
```bash
sudo apt-get update
sudo apt-get install -y rsync
```

## Configuration

### 1. Variables d'environnement

Ajoutez ces variables dans votre fichier `.env` :

```bash
# Configuration VPS pour upload des rapports
VPS_HOST=152.228.218.1
VPS_USER=ubuntu
VPS_REPORTS_PATH=/var/www/html/reports
VPS_STATIC_PATH=/var/www/html/static
```

### 2. Configuration du serveur web (Nginx)

Sur le VPS, vérifiez que Nginx est configuré pour servir les rapports :

```bash
# Se connecter au VPS
ssh ubuntu@152.228.218.1

# Éditer la configuration Nginx
sudo nano /etc/nginx/sites-available/linxo
```

Ajoutez/vérifiez cette section :

```nginx
server {
    listen 443 ssl;
    server_name linxo.appliprz.ovh;

    ssl_certificate /etc/letsencrypt/live/linxo.appliprz.ovh/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/linxo.appliprz.ovh/privkey.pem;

    # Racine du site
    root /var/www/html;
    index index.html;

    # Servir les rapports HTML
    location /reports/ {
        auth_basic "Reports Access";
        auth_basic_user_file /etc/nginx/.htpasswd;
        try_files $uri $uri/ =404;
    }

    # Servir les fichiers statiques (CSS, etc.)
    location /static/ {
        auth_basic "Reports Access";
        auth_basic_user_file /etc/nginx/.htpasswd;
        try_files $uri $uri/ =404;
    }
}
```

Redémarrez Nginx :

```bash
sudo nginx -t
sudo systemctl reload nginx
```

### 3. Créer les répertoires sur le VPS

```bash
# Sur le VPS
sudo mkdir -p /var/www/html/reports
sudo mkdir -p /var/www/html/static/reports
sudo chown -R ubuntu:www-data /var/www/html/reports
sudo chown -R ubuntu:www-data /var/www/html/static
sudo chmod -R 755 /var/www/html/reports
sudo chmod -R 755 /var/www/html/static
```

## Utilisation

### Automatique

Lors de l'exécution normale du script `run_analysis.py`, les rapports sont automatiquement uploadés après leur génération :

```bash
python linxo_agent/run_analysis.py
```

Le processus inclut maintenant :
1. ✅ Analyse des dépenses
2. ✅ Génération des rapports HTML localement
3. ✅ **Upload des rapports vers le VPS** (nouveau!)
4. ✅ Envoi des notifications (email + SMS)

### Manuel

Vous pouvez aussi uploader manuellement les rapports :

```bash
# Upload des rapports HTML
python linxo_agent/upload_reports.py

# Ou via rsync directement
rsync -avz --delete data/reports/ ubuntu@152.228.218.1:/var/www/html/reports/
rsync -avz static/reports/ ubuntu@152.228.218.1:/var/www/html/static/reports/
```

## Vérification

### 1. Vérifier l'upload

Après l'exécution, les rapports devraient être visibles sur le VPS :

```bash
# Se connecter au VPS
ssh ubuntu@152.228.218.1

# Lister les rapports
ls -la /var/www/html/reports/
ls -la /var/www/html/static/reports/
```

### 2. Tester l'accès web

Ouvrez dans votre navigateur :
```
https://linxo.appliprz.ovh/reports/2025-11-03/index.html
```

Vous devriez voir :
- Une demande d'authentification (Basic Auth)
- Puis la page d'index des rapports avec les familles de dépenses

## Dépannage

### Erreur "Permission denied"

```bash
# Sur le VPS, vérifier les permissions
ls -la /var/www/html/

# Corriger si nécessaire
sudo chown -R ubuntu:www-data /var/www/html/reports
sudo chmod -R 755 /var/www/html/reports
```

### Erreur "rsync: command not found"

```bash
# Sur Windows (Git Bash)
where rsync

# Sur le VPS
which rsync

# Installer si nécessaire
sudo apt-get install rsync
```

### Erreur "Connection refused"

Vérifiez que vous pouvez vous connecter en SSH :

```bash
ssh ubuntu@152.228.218.1 "echo test"
```

Si cela échoue, configurez votre clé SSH (voir Prérequis).

### Les rapports ne s'affichent pas

1. Vérifiez que Nginx fonctionne :
   ```bash
   ssh ubuntu@152.228.218.1 "sudo systemctl status nginx"
   ```

2. Vérifiez les logs Nginx :
   ```bash
   ssh ubuntu@152.228.218.1 "sudo tail -f /var/log/nginx/error.log"
   ```

3. Vérifiez l'authentification Basic Auth :
   ```bash
   ssh ubuntu@152.228.218.1 "sudo cat /etc/nginx/.htpasswd"
   ```

## Nouvelles fonctionnalités ajoutées

### 1. Avancement dans le temps
Les rapports affichent maintenant une barre de progression comparant :
- Le pourcentage du budget dépensé
- Le pourcentage du mois écoulé
- Un indicateur visuel "Aujourd'hui"

### 2. Conseil du LLM
Le conseil budgétaire généré automatiquement est maintenant intégré dans chaque rapport de famille.

### 3. Upload automatique vers VPS
Les rapports sont automatiquement synchronisés vers le VPS après génération, rendant les URLs accessibles immédiatement.

## Architecture

```
Workflow complet :
┌─────────────────────┐
│   run_analysis.py   │
└──────────┬──────────┘
           │
           ├─> 1. Analyse CSV
           ├─> 2. Génération rapports locaux (data/reports/)
           ├─> 3. Upload vers VPS (nouveau!)
           │    └─> rsync → ubuntu@VPS:/var/www/html/reports/
           └─> 4. Envoi notifications
```

## Fichiers modifiés

- `linxo_agent/reports.py` : Ajout budget_max et conseil_llm
- `linxo_agent/run_analysis.py` : Intégration upload VPS
- `linxo_agent/upload_reports.py` : **NOUVEAU** - Module d'upload
- `templates/reports/family.html.j2` : Ajout sections avancement + conseil
- `static/reports/styles.css` : Styles pour nouvelles sections
- `.env.example` : Variables VPS

## Support

En cas de problème, vérifiez les logs :
- **Local** : Sortie console de `run_analysis.py`
- **VPS** : `/var/log/nginx/error.log` et `/var/log/nginx/access.log`
