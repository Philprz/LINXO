# Interface d'Administration Linxo Agent

## Vue d'ensemble

L'interface d'administration permet de surveiller et contrôler le système Linxo Agent directement depuis votre navigateur web. Elle est intégrée au serveur de rapports FastAPI existant.

## Accès à l'interface

### URL d'accès

- **Local** : `http://localhost:8810/admin`
- **VPS** : `https://linxo.appliprz.ovh/admin`

### Authentification

L'interface est protégée par Basic Auth (distinct de l'accès aux rapports) :

- **Username** : `admin` (configurable via `ADMIN_USER` dans `.env`)
- **Password** : `AdminLinxo@2025` (configurable via `ADMIN_PASS` dans `.env`)

## Démarrage du serveur

### En local

```bash
cd /path/to/LINXO
python linxo_agent/report_server/app.py
```

Le serveur démarre sur le port `8810` (configurable via `REPORTS_PORT` dans `.env`)

### Sur le VPS

Le serveur devrait déjà être configuré pour démarrer automatiquement via systemd ou supervisord.

## Fonctionnalités disponibles

### Phase 1-2 : Dashboard (✅ Implémenté)

#### Indicateurs de santé système

1. **Statut du dernier Cron**
   - Indicateur visuel (vert/orange/rouge)
   - Message de statut
   - Horodatage de la dernière exécution
   - Rafraîchissement automatique toutes les 30 secondes

2. **Processus Chrome**
   - Nombre de processus actifs
   - Détails (PID, CPU, RAM) si des processus sont détectés
   - Bouton "Nettoyer" pour tuer les processus zombies

3. **Espace Disque**
   - Espace disponible en GB
   - Barre de progression avec code couleur :
     - Vert : < 75%
     - Orange : 75-90%
     - Rouge : > 90%

4. **Informations Système**
   - Plateforme OS
   - Hostname
   - Version Python
   - Taille des logs

5. **Statut des Répertoires**
   - Vérification de l'existence de `/data`, `/logs`, `/reports`
   - Badges visuels ✓ OK / ✗ Absent

### Phase 3 : Actions Manuelles (✅ Implémenté)

#### Actions disponibles

Toutes les actions s'exécutent de manière asynchrone avec affichage en temps réel de la sortie :

1. **▶️ Exécuter maintenant**
   - Lance une exécution complète (téléchargement + analyse + notifications)
   - Équivalent au cron quotidien
   - Affichage de la progression en temps réel

2. **📥 Télécharger CSV**
   - Télécharge le CSV depuis Linxo (sans envoyer de notifications)
   - Utile pour mettre à jour les données manuellement
   - Gère automatiquement la 2FA

3. **📊 Analyser dernier CSV**
   - Analyse le dernier CSV téléchargé
   - Ne nécessite pas de connexion à Linxo
   - Envoie les notifications email/SMS

4. **🔧 Lancer diagnostic**
   - Lance le diagnostic HTML complet
   - Teste tous les sélecteurs de période
   - Auto-corrige le code si nécessaire

5. **📧 Test Email**
   - Envoie un email de test aux destinataires configurés
   - Vérifie la configuration SMTP
   - Utile pour tester après modification des credentials

6. **📱 Test SMS**
   - Envoie un SMS de test via OVH
   - Vérifie la configuration OVH SMS
   - Permet de vérifier les numéros de destination

#### Suivi des tâches en temps réel

- **Console de sortie** : Affichage des logs en direct
- **Coloration syntaxique** :
  - Vert pour les succès
  - Rouge pour les erreurs
  - Orange pour les warnings
  - Bleu pour les infos
- **Statut temps réel** : Badge mis à jour toutes les 2 secondes
- **Durée d'exécution** : Affichée à la fin de la tâche
- **Auto-scroll** : La console défile automatiquement
- **Historique** : Toutes les tâches sont conservées pendant 24h

### Phase 4 : Visualiseur de Logs (🚧 À implémenter)

Fonctionnalités prévues :
- Affichage des logs cron avec coloration syntaxique
- Filtres par niveau (INFO, ERROR, SUCCESS, WARNING)
- Recherche full-text dans les logs
- Mode "tail -f" en temps réel
- Téléchargement de fichiers log

### Phase 5 : Configuration (🚧 À implémenter)

Fonctionnalités prévues :
- Édition du budget (BUDGET_VARIABLE)
- CRUD complet pour les dépenses récurrentes
- Gestion des destinataires email/SMS
- Configuration des seuils d'alerte
- Sauvegarde/restauration de configuration

## Navigation

L'interface dispose d'un menu de navigation en haut de page :

- **Dashboard** : Vue d'ensemble et statistiques
- **Logs** : Visualiseur de logs (Phase 4)
- **Configuration** : Gestion de la configuration (Phase 5)

## API Endpoints

### Endpoints publics (authentification admin requise)

- `GET /admin` - Dashboard principal
- `GET /admin/logs` - Page des logs
- `GET /admin/config` - Page de configuration
- `GET /admin/api/status` - Statut système en JSON (auto-refresh)
- `POST /admin/api/cleanup-chrome` - Nettoyer processus Chrome

### Endpoints Phase 3 (✅ Implémentés)

- `POST /admin/api/execute` - Exécuter analyse complète
- `POST /admin/api/download-csv` - Télécharger CSV uniquement
- `POST /admin/api/analyze` - Analyser le dernier CSV
- `POST /admin/api/diagnostic` - Lancer diagnostic auto-réparation
- `POST /admin/api/test-email` - Test notification email
- `POST /admin/api/test-sms` - Test notification SMS
- `GET /admin/api/task/{task_id}` - Récupérer statut d'une tâche
- `GET /admin/api/tasks` - Lister les tâches récentes

### Endpoints à venir (Phase 4-5)

- `GET /admin/api/logs` - Récupérer logs avec filtres
- `GET /admin/api/config` - Récupérer configuration
- `PUT /admin/api/config` - Mettre à jour configuration
- `GET /admin/api/budget` - Récupérer données budgétaires
- `POST /admin/api/expenses` - Ajouter dépense récurrente
- `PUT /admin/api/expenses/{id}` - Modifier dépense récurrente
- `DELETE /admin/api/expenses/{id}` - Supprimer dépense récurrente

## Configuration

### Variables d'environnement (.env)

```bash
# Admin Interface Configuration
ADMIN_USER=admin
ADMIN_PASS=AdminLinxo@2025
```

**Important** : Changez le mot de passe par défaut avant de déployer en production !

### Sécurité

L'interface d'administration :
- ✅ Est protégée par Basic Auth
- ✅ Utilise des comparaisons en temps constant pour éviter les timing attacks
- ✅ Inclut des en-têtes de sécurité (X-Frame-Options, CSP, etc.)
- ✅ Est distincte de l'authentification des rapports
- ✅ Nécessite HTTPS en production

### Recommandations de sécurité

1. **Mot de passe fort** : Utilisez un mot de passe complexe pour `ADMIN_PASS`
2. **HTTPS uniquement** : N'exposez jamais l'interface en HTTP sur Internet
3. **Restriction IP** : Envisagez de restreindre l'accès par IP via Nginx/firewall
4. **Logs d'audit** : Surveillez les logs d'accès pour détecter les tentatives suspectes
5. **Rotation des credentials** : Changez régulièrement le mot de passe admin

## Dépannage

### L'interface admin n'est pas accessible

1. Vérifiez que le serveur est démarré :
   ```bash
   ps aux | grep "report_server"
   ```

2. Vérifiez les logs du serveur :
   ```bash
   tail -f logs/report_server.log
   ```

3. Vérifiez que `ADMIN_PASS` est défini dans `.env`

4. Testez avec curl :
   ```bash
   curl -u admin:AdminLinxo@2025 http://localhost:8810/admin/api/status
   ```

### Le serveur ne démarre pas

1. Vérifiez que toutes les dépendances sont installées :
   ```bash
   pip install fastapi uvicorn psutil jinja2 python-dotenv
   ```

2. Vérifiez les permissions sur `.env` :
   ```bash
   chmod 600 .env
   ```

3. Vérifiez que le port 8810 n'est pas déjà utilisé :
   ```bash
   netstat -an | grep 8810
   ```

### Erreur "Module admin non disponible"

Cela signifie que le module admin n'a pas pu être importé. Vérifiez :
1. Que le dossier `linxo_agent/report_server/admin/` existe
2. Que les fichiers Python sont présents (routes.py, auth.py, __init__.py)
3. Qu'il n'y a pas d'erreurs de syntaxe dans ces fichiers

## Développement futur

### Roadmap

- **Phase 1-2** ✅ : Dashboard et monitoring système
- **Phase 3** ✅ : Actions manuelles et contrôles
- **Phase 4** 🚧 : Visualiseur de logs avancé
- **Phase 5** 🚧 : Gestion de configuration
- **Phase 6** 📋 : Analytics avancés et graphiques budgétaires

### Contribution

Pour contribuer au développement de l'interface :

1. Les templates HTML sont dans : `linxo_agent/report_server/admin/templates/`
2. Les routes API sont dans : `linxo_agent/report_server/admin/routes.py`
3. L'authentification est dans : `linxo_agent/report_server/admin/auth.py`

## Support

Pour toute question ou problème :
- Consultez les logs : `logs/report_server.log`
- Vérifiez la documentation du projet principal
- Contactez l'administrateur système

---

**Version** : 1.1.0 (Phases 1-3 implémentées)
**Date** : 2025-11-11
**Auteur** : Claude Code

## Changelog

### v1.1.0 - Phase 3 : Actions Manuelles (2025-11-11)
- ✅ Exécution asynchrone des tâches avec suivi en temps réel
- ✅ Affichage de la sortie des commandes en direct
- ✅ Coloration syntaxique des logs
- ✅ 6 actions manuelles fonctionnelles :
  - Exécution complète
  - Téléchargement CSV
  - Analyse seule
  - Diagnostic auto-réparation
  - Test email
  - Test SMS
- ✅ Historique des tâches pendant 24h
- ✅ Auto-refresh du statut des tâches toutes les 2s
- ✅ Affichage de la durée d'exécution

### v1.0.0 - Phases 1-2 : Dashboard (2025-11-11)
- ✅ Interface d'administration de base
- ✅ Monitoring système temps réel
- ✅ Nettoyage processus Chrome
- ✅ Auto-refresh du dashboard toutes les 30s
- ✅ Indicateurs visuels (vert/orange/rouge)
- ✅ Authentification Basic Auth sécurisée
