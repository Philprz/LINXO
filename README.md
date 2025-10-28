# Linxo Agent - Gestionnaire Automatisé de Budget

> Système automatisé d'analyse de dépenses bancaires avec notifications HTML et SMS

## Vue d'ensemble

Linxo Agent est un système Python qui automatise l'analyse de vos dépenses bancaires exportées depuis Linxo.fr. Il classe automatiquement vos transactions en dépenses fixes et variables, génère des rapports HTML épurés, et envoie des notifications par email et SMS.

### Caractéristiques principales

- ✅ **Analyse automatique** des exports CSV de Linxo
- ✅ **Classification intelligente** : dépenses fixes vs variables
- ✅ **Détection avancée** : préautorisations carburant, virements internes
- ✅ **Emails HTML magnifiques** avec design moderne
- ✅ **Notifications SMS** avec conseils budget
- ✅ **Système de feux tricolores** pour le suivi budgétaire
- ✅ **Architecture modulaire** facile à maintenir

---

## Architecture

```
linxo_agent/
├── analyzer.py                    # Analyse moderne des dépenses
├── notifications.py               # Gestionnaire email HTML + SMS
├── report_formatter_v2.py         # Formatage HTML épuré
├── config.py                      # Configuration unifiée
├── linxo_connexion.py             # Connexion automatique à Linxo
├── linxo_driver_factory.py        # Factory driver Selenium
├── linxo_2fa.py                   # Gestion 2FA email
└── run_analysis.py                # Orchestrateur moderne

linxo_agent.py                     # Workflow complet (connexion + analyse)
requirements.txt                   # Dépendances Python
.env                               # Configuration environnement
```

### Modules principaux

#### `analyzer.py` - Analyse des dépenses
- Lecture et parsing des exports CSV Linxo
- Classification des transactions (fixes/variables)
- Détection des exclusions (relevés différés, virements internes)
- Détection des préautorisations carburant (150€, 120€)
- Génération de rapports texte

#### `notifications.py` - Notifications
- Envoi d'emails HTML via SMTP Gmail
- Envoi de SMS via OVH (méthode email-to-SMS)
- Formatage automatique des messages
- Support des pièces jointes

#### `report_formatter_v2.py` - Formatage HTML
- Templates HTML épurés et modernes
- Design responsive (gradient violet, barres de progression)
- Tableaux des transactions bien formatés
- Conseils budget personnalisés

#### `config.py` - Configuration
- Gestion unifiée de la configuration
- Support des variables d'environnement (.env)
- Chargement des secrets API
- Détection automatique de l'environnement (local/VPS)

---

## Installation

### Prérequis

- Python 3.9+
- Google Chrome (pour la connexion automatique)
- ChromeDriver (pour Selenium)

### Installation locale

```bash
# Cloner le projet
git clone https://github.com/votre-username/linxo-agent.git
cd linxo-agent

# Créer l'environnement virtuel
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# ou
.venv\Scripts\activate  # Windows

# Installer les dépendances
pip install -r requirements.txt

# Copier et configurer les fichiers d'environnement
cp .env.example .env
nano .env  # Configurer vos variables

# Créer le fichier de secrets API
cp api_secrets.json.example api_secrets.json
nano api_secrets.json  # Configurer vos credentials
```

### Configuration

#### Fichier `.env`

```env
# Environnement (LOCAL ou VPS)
ENV=LOCAL

# Répertoire racine du projet
BASE_DIR=/chemin/vers/LINXO

# Budget mensuel pour les dépenses variables (en euros)
BUDGET_VARIABLE=1400

# Emails de notification (séparés par des virgules)
NOTIFICATION_EMAILS=votre.email@gmail.com

# Numéros de téléphone pour SMS (format international, séparés par des virgules)
SMS_RECIPIENTS=+33612345678,+33687654321
```

#### Fichier `api_secrets.json`

```json
{
  "SMTP_GMAIL": {
    "secrets": {
      "SMTP_EMAIL": "votre.email@gmail.com",
      "SMTP_PASSWORD": "votre_mot_de_passe_app",
      "SMTP_SERVER": "smtp.gmail.com",
      "SMTP_PORT": 587
    }
  },
  "OVH_SMS": {
    "secrets": {
      "COMPTE_SMS": "sms-xxxxx",
      "UTILISATEUR_SMS": "votre_user",
      "MOT_DE_PASSE_SMS": "votre_mdp",
      "EXPEDITEUR_SMS": "+33612345678",
      "OVH_EMAIL": "sms@ovh.net"
    }
  },
  "LINXO": {
    "secrets": {
      "EMAIL": "votre.email@linxo.fr",
      "PASSWORD": "votre_mdp_linxo"
    }
  }
}
```

---

## Utilisation

### Analyse manuelle (sans téléchargement)

```bash
# Analyser le dernier CSV téléchargé
python linxo_agent/run_analysis.py

# Analyser un fichier CSV spécifique
python linxo_agent/run_analysis.py chemin/vers/fichier.csv
```

### Workflow complet (connexion + téléchargement + analyse)

```bash
# Workflow complet automatisé
python linxo_agent.py

# Sauter le téléchargement (utiliser le dernier CSV)
python linxo_agent.py --skip-download

# Sauter les notifications (pour les tests)
python linxo_agent.py --skip-notifications
```

### Automatisation quotidienne (Cron)

Sur Linux/VPS, ajouter cette ligne à votre crontab :

```bash
# Exécution quotidienne à 10h
0 10 * * * /home/linxo/LINXO/run_daily_report.sh
```

---

## Fonctionnalités Détaillées

### Classification des Dépenses

#### Dépenses Fixes
Identifiées automatiquement via :
- **Label "Récurrent"** de Linxo
- **Pattern matching** avec `depenses_recurrentes.json`
- **Identifiant unique** pour différencier les dépenses similaires

#### Dépenses Variables
Toutes les autres dépenses non classées comme fixes.

### Exclusions Intelligentes

Le système exclut automatiquement :
- **Relevés différés de carte** (déjà comptabilisés lors des achats)
- **Virements internes** (transferts entre vos propres comptes)
- **Préautorisations carburant** (montants ronds de 120€ ou 150€)

### Système de Feux Tricolores

- 🟢 **VERT** : Budget sous contrôle
- 🟠 **ORANGE** : Attention, rythme de dépenses élevé
- 🔴 **ROUGE** : Budget dépassé

### Conseils Budget Personnalisés

Le système calcule :
- Budget théorique basé sur l'avancement du mois
- Budget quotidien restant
- Écart par rapport au rythme normal de dépenses

---

## Déploiement sur VPS

Consultez le guide détaillé : [MIGRATION_VPS_HTML.md](MIGRATION_VPS_HTML.md)

### Étapes rapides

```bash
# 1. Backup du système actuel
ssh linxo@votre-vps.com
cp -r LINXO LINXO_BACKUP_$(date +%Y%m%d)

# 2. Synchroniser les fichiers
git pull

# 3. Vérifier les dépendances
cd /home/linxo/LINXO
source .venv/bin/activate
python -c "from linxo_agent.analyzer import analyser_csv; print('OK')"

# 4. Tester manuellement
python linxo_agent/run_analysis.py

# 5. Vérifier les emails HTML reçus
```

---

## Structure des Données

### Export CSV Linxo

Format attendu (séparé par tabulations ou point-virgules) :

```
Date,Libellé,Notes,Montant,Catégorie,Nom du compte,Labels
01/10/2025,SPOTIFY,-10.99,Musique,Compte Courant,Récurrent
```

### Configuration des Dépenses Récurrentes

Fichier `linxo_agent/depenses_recurrentes.json` :

```json
{
  "depenses_fixes": [
    {
      "libelle": "SPOTIFY",
      "identifiant": "",
      "montant": 10.99,
      "categorie": "Abonnements",
      "commentaire": "Abonnement Spotify Premium"
    }
  ]
}
```

---

## Emails HTML

Le système génère des emails HTML magnifiques avec :

- **Design moderne** : Gradient violet, police system-ui
- **Barres de progression** : Visualisation du budget consommé
- **Tableaux détaillés** : Toutes les transactions classées
- **Responsive** : S'adapte aux mobiles et desktop
- **Conseils personnalisés** : Recommandations budget en temps réel

---

## Développement

### Tests

```bash
# Analyser un CSV de test
python linxo_agent/run_analysis.py data/test.csv

# Tester les notifications
python linxo_agent/notifications.py
```

### Structure du Code

Suivez ces principes :
- **Modules autonomes** : Chaque module a une responsabilité unique
- **Configuration centralisée** : Tout passe par `config.py`
- **Gestion d'erreurs** : Try/except avec logs clairs
- **Documentation** : Docstrings sur toutes les fonctions

---

## Troubleshooting

### Problème : Email non reçu

```bash
# Vérifier les credentials SMTP
python -c "from linxo_agent.notifications import NotificationManager; NotificationManager().send_email('Test', 'Corps du test')"
```

### Problème : Connexion Linxo échoue

```bash
# Tester le module de connexion
python -c "from linxo_agent.linxo_connexion import LinxoConnexion; LinxoConnexion().tester_connexion()"
```

### Problème : CSV non parsé correctement

```bash
# Vérifier l'encodage du fichier
file -i data/latest.csv

# Le système détecte automatiquement : utf-8, utf-16, latin-1, cp1252
```

---

## Roadmap

- [ ] Interface web pour visualiser les dépenses
- [ ] Support de multiples comptes bancaires
- [ ] Catégorisation automatique par machine learning
- [ ] Alertes prédictives de dépassement budget
- [ ] Export vers Excel/PDF

---

## Changelog

### Version 2.0 (Octobre 2025) - Architecture Moderne

- ✅ Emails HTML épurés et modernes
- ✅ Détection des préautorisations carburant
- ✅ Amélioration de la classification des dépenses
- ✅ Configuration unifiée via `.env`
- ✅ Architecture modulaire refactorisée

### Version 1.0 (Septembre 2025) - RELIABLE

- ✅ Analyse CSV de base
- ✅ Emails texte brut
- ✅ Notifications SMS

---

## Contribuer

Les contributions sont les bienvenues !

1. Fork le projet
2. Créer une branche (`git checkout -b feature/AmazingFeature`)
3. Commit vos changements (`git commit -m 'Add AmazingFeature'`)
4. Push vers la branche (`git push origin feature/AmazingFeature`)
5. Ouvrir une Pull Request

---

## Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.

---

## Support

Pour toute question ou problème :
- Ouvrir une issue sur GitHub
- Contact : philippe.perez@email.com

---

## Remerciements

- **Linxo.fr** pour leur excellent service de gestion bancaire
- **OVH** pour leur API SMS
- **Claude Code (Anthropic)** pour l'assistance au développement

---

**Made with ❤️ by Philippe PEREZ**
