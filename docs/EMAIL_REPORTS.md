# Rapports HTML par Famille - Documentation

## Vue d'ensemble

Le système de rapports HTML génère automatiquement des pages web consultables pour visualiser vos dépenses par famille. Les emails de notification contiennent désormais uniquement un résumé avec des liens cliquables vers ces rapports hébergés de manière sécurisée.

## Architecture

```
┌─────────────────┐
│  Linxo Agent    │  Analyse CSV
│  (linxo_agent.py)│  → Génère rapports HTML
└────────┬────────┘
         │
         ├─→ data/reports/YYYY-MM-DD/
         │   ├── index.html (liste des familles)
         │   ├── family-alimentation.html
         │   ├── family-transports.html
         │   └── ...
         │
         └─→ Email avec liens cliquables
             ↓
     ┌───────────────────┐
     │ FastAPI Server    │  Port 8810 (local)
     │ Basic Auth        │  → Sert les rapports
     │ + Token HMAC      │
     └─────────┬─────────┘
               │
     ┌─────────┴─────────┐
     │   Caddy (HTTPS)   │  Port 443 (public)
     │ reverse_proxy     │  → linxo.itspirit.ovh/reports
     └───────────────────┘
```

## Configuration

### 1. Variables d'environnement (.env)

```bash
# URL publique (OBLIGATOIRE)
REPORTS_BASE_URL=https://linxo.itspirit.ovh/reports

# Basic Auth (OBLIGATOIRE)
REPORTS_BASIC_USER=linxo
REPORTS_BASIC_PASS=un_mot_de_passe_fort

# Token HMAC (RECOMMANDÉ)
# Génération: python -c "import secrets; print(secrets.token_urlsafe(32))"
REPORTS_SIGNING_KEY=votre_cle_secrete_longue

# Port serveur (OPTIONNEL)
REPORTS_PORT=8810
```

**Important**: `REPORTS_BASE_URL` doit correspondre à l'URL publique finale (après Caddy).

### 2. Installation des dépendances

```bash
# Activer le virtualenv
source .venv/bin/activate

# Installer les nouvelles dépendances
pip install -r requirements.txt
```

## Déploiement sur VPS

### Option 1: Déploiement automatique (recommandé)

```bash
# Depuis le répertoire LINXO
sudo bash scripts/deploy_report_server.sh
```

Ce script:
- Vérifie l'environnement
- Crée le service systemd
- Active et démarre le serveur
- Vérifie le health check

### Option 2: Déploiement manuel

1. **Créer le service systemd**

```bash
sudo nano /etc/systemd/system/linxo-reports.service
```

```ini
[Unit]
Description=Linxo Report Server
After=network.target

[Service]
Type=simple
User=linxo
Group=linxo
WorkingDirectory=/home/linxo/LINXO
Environment="PYTHONPATH=/home/linxo/LINXO"
EnvironmentFile=/home/linxo/LINXO/.env
ExecStart=/home/linxo/LINXO/.venv/bin/uvicorn linxo_agent.report_server.app:app --host 0.0.0.0 --port ${REPORTS_PORT:-8810}
Restart=on-failure
RestartSec=5s
StandardOutput=journal
StandardError=journal

# Security
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/home/linxo/LINXO/data

[Install]
WantedBy=multi-user.target
```

2. **Activer et démarrer**

```bash
sudo systemctl daemon-reload
sudo systemctl enable linxo-reports
sudo systemctl start linxo-reports
```

3. **Vérifier le statut**

```bash
sudo systemctl status linxo-reports
curl http://127.0.0.1:8810/healthz
```

### Configuration Caddy (Reverse Proxy HTTPS)

1. **Editer la configuration Caddy**

```bash
sudo nano /etc/caddy/Caddyfile
```

2. **Ajouter la configuration**

```caddy
linxo.itspirit.ovh {
    # Autres routes existantes...

    # Route pour les rapports
    route /reports* {
        reverse_proxy 127.0.0.1:8810
    }
}
```

**Note**: L'authentification Basic Auth est gérée par l'application FastAPI. Vous pouvez optionnellement ajouter une couche supplémentaire via Caddy:

```caddy
linxo.itspirit.ovh {
    route /reports* {
        # Optionnel: Basic Auth côté Caddy (double protection)
        basicauth {
            linxo $2a$14$hash_bcrypt_genere
        }
        reverse_proxy 127.0.0.1:8810
    }
}
```

Pour générer le hash bcrypt:
```bash
caddy hash-password
```

3. **Recharger Caddy**

```bash
sudo systemctl reload caddy
```

## Utilisation

### Workflow automatique

Le workflow complet s'exécute via:

```bash
python linxo_agent.py
```

Étapes:
1. Téléchargement CSV depuis Linxo
2. Analyse des dépenses
3. **Génération des rapports HTML** (nouvelle étape)
4. Envoi des notifications avec liens

### Test manuel du serveur

```bash
# Démarrer le serveur en mode développement
python -m linxo_agent.report_server.app

# Dans un autre terminal, tester
curl -u linxo:votre_password http://localhost:8810/healthz
```

### Structure des rapports générés

```
data/reports/
└── 2025-01-15/
    ├── index.html              # Vue d'ensemble (toutes les familles)
    ├── family-alimentation.html
    ├── family-transports.html
    ├── family-restaurants-cafes.html
    ├── family-logement-energie.html
    └── ...
```

### Format des URLs

**Sans token (nécessite Basic Auth)**:
```
https://linxo.itspirit.ovh/reports/2025-01-15/index.html
https://linxo.itspirit.ovh/reports/2025-01-15/family-alimentation.html
```

**Avec token HMAC (bypass Basic Auth pendant 24h)**:
```
https://linxo.itspirit.ovh/reports/2025-01-15/index.html?t=abc123...
```

Le token permet un accès direct depuis les liens dans l'email, sans avoir à saisir username/password.

## Sécurité

### Authentification

Trois niveaux de protection possibles:

1. **Basic Auth (obligatoire)**: Défini dans `.env`
   - Username/password requis pour accéder aux rapports
   - Comparaison en temps constant (anti timing attack)

2. **Token HMAC (recommandé)**: Défini dans `.env`
   - URLs signées avec expiration (24h par défaut)
   - Permet l'accès direct depuis l'email
   - Révocable en changeant `REPORTS_SIGNING_KEY`

3. **Caddy Basic Auth (optionnel)**: Double couche
   - Protection supplémentaire au niveau du reverse proxy

### En-têtes de sécurité

Le serveur ajoute automatiquement:
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Referrer-Policy: strict-origin-when-cross-origin`

### Protection Path Traversal

Le serveur vérifie que tous les chemins demandés restent dans `data/reports/`.

### Bonnes pratiques

- Utilisez un mot de passe fort pour `REPORTS_BASIC_PASS`
- Générez une clé aléatoire longue pour `REPORTS_SIGNING_KEY`
- Ne committez JAMAIS le fichier `.env`
- Changez régulièrement les secrets
- Surveillez les logs: `sudo journalctl -u linxo-reports -f`

## Gestion et maintenance

### Commandes systemd

```bash
# Voir le statut
sudo systemctl status linxo-reports

# Voir les logs en temps réel
sudo journalctl -u linxo-reports -f

# Voir les derniers logs
sudo journalctl -u linxo-reports -n 100

# Redémarrer le service
sudo systemctl restart linxo-reports

# Arrêter le service
sudo systemctl stop linxo-reports
```

### Nettoyage des anciens rapports

Les rapports s'accumulent dans `data/reports/`. Pour nettoyer:

```bash
# Supprimer les rapports de plus de 30 jours
find /home/linxo/LINXO/data/reports -type d -mtime +30 -exec rm -rf {} +
```

Ajoutez un cron job pour automatiser:

```bash
# Editer la crontab de l'utilisateur linxo
crontab -e

# Ajouter (exécution quotidienne à 3h du matin)
0 3 * * * find /home/linxo/LINXO/data/reports -type d -mtime +30 -exec rm -rf {} + 2>/dev/null
```

### Rotation des logs

Les logs systemd sont gérés par journald. Configuration dans `/etc/systemd/journald.conf`:

```ini
[Journal]
SystemMaxUse=500M
MaxRetentionSec=1month
```

Puis:
```bash
sudo systemctl restart systemd-journald
```

## Dépannage

### Le service ne démarre pas

```bash
# Vérifier les logs détaillés
sudo journalctl -u linxo-reports -n 50 --no-pager

# Vérifier la configuration
cat /etc/systemd/system/linxo-reports.service

# Vérifier le fichier .env
ls -la /home/linxo/LINXO/.env

# Tester manuellement
su - linxo
cd /home/linxo/LINXO
source .venv/bin/activate
python -m linxo_agent.report_server.app
```

### Erreur "REPORTS_BASE_URL est requis"

Assurez-vous que `REPORTS_BASE_URL` est défini dans `.env`:

```bash
grep REPORTS_BASE_URL /home/linxo/LINXO/.env
```

### Les liens dans l'email ne fonctionnent pas

1. Vérifier que Caddy est correctement configuré:
   ```bash
   sudo systemctl status caddy
   curl https://linxo.itspirit.ovh/reports/healthz
   ```

2. Vérifier que `REPORTS_BASE_URL` correspond à l'URL Caddy:
   ```bash
   # Dans .env
   REPORTS_BASE_URL=https://linxo.itspirit.ovh/reports
   ```

3. Tester l'authentification:
   ```bash
   curl -u linxo:password https://linxo.itspirit.ovh/reports/healthz
   ```

### Erreur 404 sur les rapports

Les rapports sont générés quotidiennement. Si aucun rapport n'existe:

```bash
# Générer manuellement
python linxo_agent.py --skip-download --skip-notifications
```

### Permissions insuffisantes

```bash
# Vérifier les permissions
ls -la /home/linxo/LINXO/data/reports

# Corriger si nécessaire
sudo chown -R linxo:linxo /home/linxo/LINXO/data
```

## Monitoring

### Health Check

Endpoint disponible sans authentification:

```bash
curl http://127.0.0.1:8810/healthz
```

Réponse:
```json
{
  "status": "ok",
  "service": "linxo-report-server",
  "reports_dir_exists": true
}
```

### Métriques à surveiller

- **Uptime du service**: `systemctl is-active linxo-reports`
- **Utilisation disque**: `du -sh /home/linxo/LINXO/data/reports`
- **Logs d'erreur**: `journalctl -u linxo-reports -p err`
- **Temps de réponse**: Surveiller les logs d'accès

## FAQ

**Q: Puis-je désactiver les rapports HTML?**
R: Oui, ne définissez pas `REPORTS_BASE_URL`. L'email utilisera l'ancien format.

**Q: Les rapports contiennent-ils des données sensibles?**
R: Oui, c'est pourquoi l'authentification est obligatoire et les rapports ne sont pas indexables.

**Q: Combien de temps les tokens sont-ils valides?**
R: 24 heures par défaut. Modifiable dans `linxo_agent/reports.py`.

**Q: Puis-je partager un lien de rapport?**
R: Oui, mais l'authentification sera requise. Les liens avec token expirent après 24h.

**Q: Comment changer les secrets?**
R: Modifiez `.env`, puis redémarrez: `sudo systemctl restart linxo-reports`

## Support

Pour plus d'informations:
- Logs du serveur: `sudo journalctl -u linxo-reports -f`
- Code source: [linxo_agent/report_server/app.py](../linxo_agent/report_server/app.py)
- Configuration: [.env.example](../.env.example)

---

**Date de dernière mise à jour**: Janvier 2025
**Version**: 1.0.0
