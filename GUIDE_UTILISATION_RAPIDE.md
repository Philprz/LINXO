# 🚀 GUIDE D'UTILISATION RAPIDE - LINXO AGENT

## 📋 COMMANDES PRINCIPALES

### 1. Workflow Complet (Production)
```bash
# Exécution complète : téléchargement + analyse + notifications
python linxo_agent.py
```

### 2. Analyse sans Téléchargement (Utiliser CSV existant)
```bash
# Utilise le dernier CSV disponible dans data/
python linxo_agent.py --skip-download
```

### 3. Test sans Notifications
```bash
# Analyse sans envoyer d'emails/SMS
python linxo_agent.py --skip-download --skip-notifications
```

### 4. Analyser un CSV Spécifique
```bash
# Spécifier un fichier CSV particulier
python linxo_agent.py --csv-file data/export_custom.csv --skip-notifications
```

### 5. Vérifier la Configuration
```bash
# Afficher la configuration actuelle
python linxo_agent.py --config-check
```

---

## 🧪 COMMANDES DE TEST

### Test Analyseur
```bash
python test_analyzer.py
```
**Résultat:** Analyse complète avec statistiques détaillées

### Test Rapport HTML
```bash
python test_html_report.py
```
**Résultat:** Génère `reports/rapport_test.html`

### Test Module Analyzer Direct
```bash
cd linxo_agent && python analyzer.py
```
**Résultat:** Test du module analyzer en standalone

### Test Module Notifications
```bash
cd linxo_agent && python notifications.py
```
**Résultat:** Test interactif des notifications (email/SMS)

---

## 📊 STRUCTURE DES FICHIERS

```
LINXO/
├── linxo_agent.py           # Point d'entrée principal
├── test_analyzer.py         # Test de l'analyseur
├── test_html_report.py      # Test génération HTML
├── requirements.txt         # Dépendances Python
├── .env                     # Configuration (SENSIBLE)
├── api_secrets.json         # Secrets API (SENSIBLE)
│
├── linxo_agent/            # Modules principaux
│   ├── config.py           # Configuration unifiée
│   ├── analyzer.py         # Analyse des transactions
│   ├── linxo_connexion.py  # Connexion Selenium
│   ├── notifications.py    # Envoi email/SMS
│   ├── report_formatter_v2.py  # Formatage rapports
│   ├── config_linxo.json   # Config Linxo (legacy)
│   └── depenses_recurrentes.json  # 40 règles de détection
│
├── data/                   # Fichiers CSV téléchargés
│   └── latest.csv
│
├── reports/                # Rapports générés
│   ├── rapport_linxo_YYYYMMDD_HHMMSS.txt
│   └── rapport_test.html
│
└── logs/                   # Logs d'exécution
```

---

## ⚙️ CONFIGURATION

### Fichier .env (Variables d'Environnement)
```bash
# Linxo
LINXO_URL=https://wwws.linxo.com/auth.page#Login
LINXO_EMAIL=votre@email.com
LINXO_PASSWORD=votre_mot_de_passe

# Budget
BUDGET_VARIABLE=1300

# Email SMTP (Gmail)
SENDER_EMAIL=votre@gmail.com
SENDER_PASSWORD=mot_de_passe_application_gmail
NOTIFICATION_EMAIL=destinataire1@email.com,destinataire2@email.com

# SMS OVH
OVH_EMAIL_ENVOI=email2sms@ovh.net
OVH_APP_SECRET=votre_secret_ovh
OVH_SERVICE_NAME=sms-XXXXX-X
SMS_SENDER=VotreNom
SMS_RECIPIENT=+33612345678,+33698765432
```

### Fichier depenses_recurrentes.json
Format des règles de détection:
```json
{
  "depenses_fixes": [
    {
      "libelle": "EDF",
      "identifiant": "clients particuli",
      "categorie": "Énergie",
      "montant": 117.14
    },
    {
      "libelle": "Free",
      "identifiant": "Telecom",
      "categorie": "Internet/Téléphone",
      "montant": 47.98
    }
  ],
  "totaux": {
    "budget_variable_max": 1300
  }
}
```

---

## 📧 FORMATS DE SORTIE

### Rapport Texte
Fichier: `reports/rapport_linxo_YYYYMMDD_HHMMSS.txt`
- Transactions exclues
- Dépenses fixes détaillées
- Dépenses variables détaillées
- Statut budget avec conseils

### Rapport HTML
Style moderne et épuré avec:
- En-tête dégradé violet
- Barres de progression visuelles
- Tableaux triés par montant
- Responsive design
- Conseils budget encadrés

### SMS
Format compact (max 160 caractères):
```
🔴 BUDGET DÉPASSÉ!
💰 3178€ / 1300€
⚠️ +1878€ de dépassement
📅 J23/31
💡 Limiter au strict nécessaire
```

---

## 🔍 RÉSULTATS D'ANALYSE TYPE

```
================================================================================
RAPPORT D'ANALYSE DES DEPENSES LINXO
================================================================================

TRANSACTIONS EXCLUES
- Virements internes
- Relevés différés carte débit
- Catégories exclues

DEPENSES FIXES (19 transactions | 1056.98€)
- Abonnements
- Assurances
- Énergie
- Télécom
- Crédits

DEPENSES VARIABLES (64 transactions | 3178.04€)
- Courses
- Restaurants
- Shopping
- Services en ligne
- Santé
- Autres dépenses

BUDGET ET STATUT
Budget variables alloué:  1300.00€
Dépenses variables:       3178.04€
DEPASSEMENT:              1878.04€

CONSEIL DE VOTRE AGENT BUDGET
- Analyse de l'avancement du mois
- Calcul du budget journalier restant
- Recommandations personnalisées
```

---

## 🎯 EXEMPLES D'UTILISATION

### Scénario 1: Analyse Quotidienne
```bash
# Chaque jour, télécharger et analyser sans notifications
python linxo_agent.py --skip-notifications
```

### Scénario 2: Rapport Hebdomadaire
```bash
# Chaque lundi, rapport complet avec notifications
python linxo_agent.py
```

### Scénario 3: Analyse d'un Export Manuel
```bash
# Analyser un CSV téléchargé manuellement
python linxo_agent.py --csv-file Downloads/export_octobre.csv --skip-notifications
```

### Scénario 4: Test Nouvelle Configuration
```bash
# Vérifier la configuration
python linxo_agent.py --config-check

# Tester l'analyse
python linxo_agent.py --skip-download --skip-notifications
```

---

## 🔧 DÉPANNAGE

### Problème: Module non trouvé
```bash
# Réinstaller les dépendances
pip install -r requirements.txt
```

### Problème: Erreur d'encodage CSV
- L'analyseur détecte automatiquement l'encodage
- Supporte: UTF-8, UTF-16, Latin-1, CP1252

### Problème: Échec connexion Linxo
```bash
# Vérifier les credentials dans .env
cat .env | grep LINXO

# Utiliser un CSV existant
python linxo_agent.py --skip-download
```

### Problème: Échec envoi email
- Vérifier mot de passe application Gmail (pas le mot de passe normal)
- Activer l'authentification à 2 facteurs Gmail
- Créer un "mot de passe d'application" dédié

### Problème: Échec envoi SMS OVH
- Vérifier le solde du compte SMS OVH
- Vérifier le format: `sms-XXXXX-X`
- Vérifier que l'utilisateur SMS est bien configuré

---

## 📊 INDICATEURS DE SUCCÈS

### Statut Budget
- 🟢 **VERT**: < 80% du budget utilisé
- 🟠 **ORANGE**: 80-100% du budget utilisé
- 🔴 **ROUGE**: > 100% du budget (dépassement)

### Messages de Statut
```
[OK]      - Opération réussie
[INFO]    - Information
[WARNING] - Avertissement
[ERREUR]  - Erreur
[SUCCESS] - Succès complet
```

---

## 🚀 DÉPLOIEMENT VPS (À VENIR)

### Cron Job Recommandé
```cron
# Exécution quotidienne à 9h00
0 9 * * * cd /home/ubuntu && /usr/bin/python3 linxo_agent.py --skip-download >> logs/linxo_agent.log 2>&1

# Exécution hebdomadaire avec téléchargement (lundi 9h)
0 9 * * 1 cd /home/ubuntu && /usr/bin/python3 linxo_agent.py >> logs/linxo_agent.log 2>&1
```

---

## 📝 NOTES IMPORTANTES

1. **Sécurité**
   - Ne jamais commiter `.env` ou `api_secrets.json`
   - Protéger les fichiers CSV (données personnelles)
   - Utiliser des mots de passe application, pas les mots de passe principaux

2. **Performance**
   - L'analyse d'un CSV prend ~2-3 secondes
   - Le téléchargement via Selenium prend ~15-30 secondes
   - L'envoi des notifications prend ~5-10 secondes

3. **Maintenance**
   - Mettre à jour `depenses_recurrentes.json` quand de nouveaux abonnements apparaissent
   - Vérifier les logs régulièrement
   - Nettoyer les anciens rapports (garder 30 jours)

---

**Version:** 2.0
**Dernière mise à jour:** 23/10/2025
**Statut:** ✅ Production Ready
